from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

from skillguard.llm import LLMClient, SemanticAuditor
from skillguard.parser import SkillParser
from skillguard.policy import PolicyEngine, RiskEngine
from skillguard.schemas.audit import AuditMetadata, AuditResult
from skillguard.scanners import StaticScanner


def audit_skill(
    path: str | Path,
    *,
    semantic: bool = True,
    llm_client: LLMClient | None = None,
    parser: SkillParser | None = None,
) -> AuditResult:
    load_dotenv()
    package = (parser or SkillParser()).parse(path)
    static_findings = StaticScanner().scan(package)
    semantic_outcome = SemanticAuditor(client=llm_client, enabled=semantic).audit(package, static_findings)
    risk_engine = RiskEngine()
    findings = risk_engine.deduplicate(static_findings + semantic_outcome.findings)
    score = risk_engine.score(findings)
    decision = PolicyEngine().decide(findings)
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.severity.value] = counts.get(finding.severity.value, 0) + 1
    breakdown = ", ".join(f"{count} {severity}" for severity, count in counts.items()) or "no findings"
    return AuditResult(
        skill_name=package.skill_name,
        overall_score=score,
        decision=decision,
        findings=findings,
        summary=f"{decision.value}: {breakdown}. Decision is policy-derived; score is informational.",
        metadata=AuditMetadata(
            semantic_audit_status=semantic_outcome.status,
            scanned_files=len(package.files),
            skipped_files=package.skipped_files,
            policy_version=str(PolicyEngine().config.get("version", "1")),
        ),
    )

