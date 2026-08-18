from __future__ import annotations

import json

from skillguard.schemas import AuditResult


class ReportGenerator:
    @staticmethod
    def json(result: AuditResult, indent: int = 2) -> str:
        return json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=indent)

    @staticmethod
    def markdown(result: AuditResult) -> str:
        lines = [
            "# SkillGuard Audit Report", "", f"**Skill:** {result.skill_name}",
            f"**Risk Score:** {result.overall_score} / 100", f"**Decision:** {result.decision.value}",
            f"**Semantic Audit:** {result.metadata.semantic_audit_status}", "", "## Summary", "", result.summary,
            "", "## Findings", "",
        ]
        if not result.findings:
            lines.append("No security or quality findings detected.")
        for finding in result.findings:
            location = finding.file_path or "package"
            if finding.line_number:
                location += f":{finding.line_number}"
            lines.extend([
                f"### [{finding.severity.value}] {finding.title}", "",
                f"- **Category:** {finding.category.value}", f"- **Detector:** {finding.detector.value}",
                f"- **Location:** `{location}`", f"- **Confidence:** {finding.confidence:.2f}",
                f"- **Evidence:** `{finding.evidence}`", f"- **Recommendation:** {finding.recommendation}", "",
            ])
        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def terminal(result: AuditResult) -> str:
        lines = [
            "SkillGuard Audit Report", "", f"Skill: {result.skill_name}",
            f"Risk Score: {result.overall_score} / 100", f"Decision: {result.decision.value}",
            f"Semantic Audit: {result.metadata.semantic_audit_status}", "", "Findings:",
        ]
        if not result.findings:
            lines.append("  None")
        for finding in result.findings:
            location = finding.file_path or "package"
            if finding.line_number:
                location += f":{finding.line_number}"
            lines.extend([f"  [{finding.severity.value}] {finding.title}", f"    File: {location}", f"    {finding.recommendation}"])
        return "\n".join(lines)

