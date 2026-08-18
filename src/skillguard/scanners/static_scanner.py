from __future__ import annotations

import hashlib
import re

from skillguard.schemas import Detector, RiskCategory, RiskFinding, Severity, SkillPackage

from .permission_scanner import PermissionScanner
from .secret_scanner import SecretScanner


class StaticScanner:
    BROAD_TRIGGER = re.compile(r"(?i)\b(?:any request|anything related to|all user queries|every user (?:query|question)|regardless of (?:the )?topic|whenever possible|always use this skill|any task|任何请求|所有用户查询)\b")
    PROMPT_INJECTION = re.compile(r"(?i)\b(?:ignore (?:all |any )?(?:previous|prior|system|safety)(?: safety| system)? instructions?|disregard (?:all )?(?:earlier|previous|system|safety) (?:rules|instructions)|override (?:the )?(?:system|safety)|bypass (?:safety|security)|reveal (?:the )?system prompt|do not ask (?:the )?user|忽略.{0,8}指令|绕过.{0,8}(?:安全|限制))\b")
    SILENT_HIGH_RISK = re.compile(r"(?i)(?:silently|without (?:asking|confirmation)|do not ask).{0,80}(?:upload|send|delete|execute|run)|(?:upload|send|delete|execute|run).{0,80}(?:silently|without (?:asking|confirmation))")

    def __init__(self) -> None:
        self.permission = PermissionScanner()
        self.secrets = SecretScanner()

    def scan(self, package: SkillPackage) -> list[RiskFinding]:
        findings = self.secrets.scan(package) + self.permission.scan(package)
        findings.extend(self._semantic_guardrails(package))
        return findings

    def _semantic_guardrails(self, package: SkillPackage) -> list[RiskFinding]:
        findings: list[RiskFinding] = []
        for number, line in enumerate(package.markdown_content.splitlines(), start=1):
            for rule_id, pattern, category, severity, title, recommendation, block in (
                ("TRIGGER_BROAD", self.BROAD_TRIGGER, RiskCategory.TRIGGER_RISK, Severity.MEDIUM, "Overly broad trigger scope", "Narrow the description to explicit user intents and exclusions.", None),
                ("PROMPT_INJECTION", self.PROMPT_INJECTION, RiskCategory.SEMANTIC_RISK, Severity.CRITICAL, "Prompt injection or safety bypass instruction", "Remove instructions that override higher-priority policy or user control.", "prompt_injection"),
                ("SILENT_HIGH_RISK", self.SILENT_HIGH_RISK, RiskCategory.SEMANTIC_RISK, Severity.CRITICAL, "Silent sensitive action", "Require informed user confirmation and disclose the exact action and data involved.", "silent_sensitive_action"),
            ):
                if not pattern.search(line):
                    continue
                digest = hashlib.sha1(f"SKILL.md:{number}:{rule_id}".encode()).hexdigest()[:10]
                metadata = {"block_condition": block} if block else {}
                findings.append(RiskFinding(
                    id=f"static-{digest}", category=category, severity=severity, title=title,
                    description="The skill instructions contain security-relevant semantics.", evidence=line.strip()[:300],
                    file_path="SKILL.md", line_number=number, recommendation=recommendation,
                    detector=Detector.STATIC, confidence=0.95, rule_id=rule_id, metadata=metadata,
                ))
        return findings
