from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, Field, ValidationError

from skillguard.schemas import Detector, RiskCategory, RiskFinding, Severity, SkillPackage

from .prompts import SYSTEM_PROMPT, user_prompt

LOGGER = logging.getLogger(__name__)


class LLMClient(Protocol):
    def generate_structured(self, system_prompt: str, user_prompt: str) -> str: ...


class OpenAICompatibleClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None) -> None:
        from openai import OpenAI

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"), base_url=base_url or os.getenv("OPENAI_BASE_URL") or None)

    def generate_structured(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        )
        return response.choices[0].message.content or "{}"


class SemanticFinding(BaseModel):
    category: RiskCategory
    severity: Severity
    title: str
    description: str
    evidence: str
    file_path: str | None = None
    line_number: int | None = None
    recommendation: str
    confidence: float = Field(ge=0, le=1)


class SemanticResponse(BaseModel):
    findings: list[SemanticFinding] = Field(default_factory=list)


@dataclass
class SemanticAuditOutcome:
    findings: list[RiskFinding]
    status: str
    structured_attempts: int = 0
    structured_successes: int = 0


class SemanticAuditor:
    def __init__(self, client: LLMClient | None = None, enabled: bool = True, max_chars: int = 80_000) -> None:
        self.client = client
        self.enabled = enabled
        self.max_chars = max_chars

    def audit(self, package: SkillPackage, static_findings: list[RiskFinding]) -> SemanticAuditOutcome:
        if not self.enabled:
            return SemanticAuditOutcome([], "disabled")
        client = self.client
        if client is None:
            if not os.getenv("OPENAI_API_KEY"):
                return SemanticAuditOutcome([], "skipped:no_api_key")
            try:
                client = OpenAICompatibleClient()
            except Exception as exc:
                LOGGER.warning("Cannot initialize semantic auditor: %s", exc)
                return SemanticAuditOutcome([], "skipped:client_error")

        package_text = "\n\n".join(f"### {file.path}\n{file.content}" for file in package.files)[: self.max_chars]
        static_json = json.dumps([f.model_dump(mode="json") for f in static_findings], ensure_ascii=False)
        prompt = user_prompt(package_text, static_json)
        attempts = 0
        for attempt in range(2):
            attempts += 1
            try:
                raw = client.generate_structured(SYSTEM_PROMPT, prompt + ("\nYour prior output was invalid. Return only valid JSON." if attempt else ""))
            except Exception as exc:
                LOGGER.warning("Semantic audit provider failed: %s", exc)
                return SemanticAuditOutcome([], "failed:provider_error", attempts, 0)
            try:
                parsed = SemanticResponse.model_validate_json(raw)
                candidates = [
                    RiskFinding(
                        id=f"llm-{index:03d}", detector=Detector.LLM, rule_id="LLM_SEMANTIC",
                        **item.model_dump(),
                    )
                    for index, item in enumerate(parsed.findings, start=1)
                ]
                findings = self._ground_findings(package, candidates)
                return SemanticAuditOutcome(findings, "completed", attempts, 1)
            except (ValidationError, json.JSONDecodeError) as exc:
                LOGGER.warning("Semantic audit schema attempt %d failed: %s", attempts, exc)
        return SemanticAuditOutcome([], "failed:invalid_output", attempts, 0)

    @staticmethod
    def _ground_findings(package: SkillPackage, findings: list[RiskFinding]) -> list[RiskFinding]:
        files = {file.path: file.content for file in package.files}
        grounded: list[RiskFinding] = []
        for finding in findings:
            evidence = finding.evidence.strip()
            if not evidence:
                LOGGER.warning("Discarding LLM finding without evidence: %s", finding.title)
                continue
            candidate_paths = [finding.file_path] if finding.file_path in files else list(files)
            match_path: str | None = None
            match_line: int | None = None
            for path in candidate_paths:
                if path is None:
                    continue
                content = files[path]
                offset = content.find(evidence)
                if offset >= 0:
                    match_path = path
                    match_line = content.count("\n", 0, offset) + 1
                    break
            if match_path is None:
                LOGGER.warning("Discarding ungrounded LLM finding: %s", finding.title)
                continue
            finding.file_path = match_path
            finding.line_number = match_line
            grounded.append(finding)
        return grounded
