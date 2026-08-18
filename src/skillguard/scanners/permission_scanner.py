from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from skillguard.schemas import Detector, RiskCategory, RiskFinding, Severity, SkillPackage


@dataclass(frozen=True)
class PermissionRule:
    rule_id: str
    pattern: re.Pattern[str]
    title: str
    severity: Severity
    description: str
    recommendation: str
    tags: tuple[str, ...] = ()


class PermissionScanner:
    RULES = (
        PermissionRule("EXEC_SHELL", re.compile(r"\b(?:os\.system|subprocess\.(?:run|Popen|call|check_call|check_output)|shell\s*=\s*True)\b"), "Shell or process execution", Severity.HIGH, "The package can execute operating-system commands.", "Use an allowlist, avoid shell=True, validate arguments, and require confirmation for consequential commands.", ("shell",)),
        PermissionRule("EXEC_DYNAMIC", re.compile(r"(?<![A-Za-z0-9_])(?:eval|exec)\s*\("), "Dynamic code execution", Severity.HIGH, "The package dynamically evaluates code.", "Remove dynamic evaluation or strictly constrain and validate the input.", ("shell",)),
        PermissionRule("FILE_DELETE", re.compile(r"\b(?:os\.(?:remove|unlink)|shutil\.rmtree|Path\([^\n]*\)\.unlink|\.unlink\s*\()"), "File deletion capability", Severity.HIGH, "The package can delete files or directories.", "Limit deletion scope, preview targets, and require explicit user confirmation.", ("delete",)),
        PermissionRule("NETWORK_WRITE", re.compile(r"\b(?:requests|httpx)\.(?:post|put|patch)\s*\(|\brequests\.request\s*\(\s*[\"'](?:POST|PUT|PATCH)[\"']|\bcurl\b[^\n]*(?:-X\s*(?:POST|PUT|PATCH)|--data(?:-binary)?|-d\s|--upload-file|-T\s)|\bwget\b[^\n]*--post-(?:data|file)", re.IGNORECASE), "Outbound data transmission", Severity.HIGH, "The package can send data to an external destination.", "Document destinations and payloads and require confirmation before transmitting user data.", ("network_write",)),
        PermissionRule("NETWORK_READ", re.compile(r"\b(?:requests|httpx)\.get\s*\(|\burllib\.request\.(?:urlopen|urlretrieve)\s*\(|\bcurl\b(?![^\n]*(?:-X\s*(?:POST|PUT|PATCH)|--data(?:-binary)?|-d\s|--upload-file|-T\s))|\bwget\b(?![^\n]*--post-(?:data|file))", re.IGNORECASE), "External network access", Severity.MEDIUM, "The package fetches data from an external service.", "Validate destinations, use timeouts, and handle network failures.", ("network_read",)),
        PermissionRule("SENSITIVE_PATH", re.compile(r"(?:~/\.ssh|\.ssh[/\\]|\.aws[/\\]|(?:^|[/\\])\.env\b|credentials|id_rsa)"), "Sensitive path access", Severity.HIGH, "The package references a path commonly containing credentials.", "Avoid broad credential access and request narrowly scoped data explicitly.", ("sensitive_path",)),
        PermissionRule("INFINITE_LOOP", re.compile(r"\bwhile\s+(?:True|1)\s*:"), "Potential unbounded loop", Severity.MEDIUM, "The package contains a loop with no visible bound.", "Add termination, timeout, and cancellation conditions.", ("quality",)),
    )

    CONFIRMATION = re.compile(r"(?i)\b(?:confirm|confirmation|ask (?:the )?user|user approval|explicit approval|确认|批准)\b")
    NEGATED_CONFIRMATION = re.compile(r"(?i)\b(?:silently|without (?:asking|confirmation)|do not ask|no confirmation|无需确认|静默)\b")
    MALICIOUS_SHELL = re.compile(r"(?i)(?:rm\s+-rf|powershell.+-enc|curl.+\|\s*(?:sh|bash)|reverse shell|/bin/sh\s+-c)")
    ACTION_TERMS: dict[str, re.Pattern[str]] = {
        "delete": re.compile(r"(?i)\b(?:delet\w*|remove\w*|unlink\w*|clean(?:up)?\w*)\b|删除|移除|清理"),
        "network_write": re.compile(r"(?i)\b(?:send|upload|post|publish|transmit|email|message|update|write)\w*\b|发送|上传|发布|外传"),
        "shell": re.compile(r"(?i)\b(?:command|shell|script|execute|run|process|build)\w*\b|命令|脚本|执行"),
        "sensitive_path": re.compile(r"(?i)\b(?:credential|secret|ssh|aws|private key)\b|凭证|密钥"),
    }

    def scan(self, package: SkillPackage) -> list[RiskFinding]:
        findings: list[RiskFinding] = []
        for file in package.files:
            if not file.path.lower().endswith((".py", ".js", ".ts", ".sh")):
                continue
            for number, line in enumerate(file.content.splitlines(), start=1):
                for rule in self.RULES:
                    if not rule.pattern.search(line):
                        continue
                    confirmation_present = self._has_action_confirmation(package.markdown_content, rule.tags)
                    silent_context = self._has_action_negation(package.markdown_content, rule.tags)
                    severity = rule.severity
                    metadata: dict[str, object] = {"tags": list(rule.tags), "confirmation_present": confirmation_present}
                    if "delete" in rule.tags and not confirmation_present:
                        metadata["block_condition"] = "unconfirmed_file_deletion"
                        severity = Severity.CRITICAL
                    if "network_write" in rule.tags and silent_context:
                        metadata["block_condition"] = "silent_exfiltration"
                        severity = Severity.CRITICAL
                    if "shell" in rule.tags and self.MALICIOUS_SHELL.search(line):
                        metadata["block_condition"] = "malicious_shell"
                        severity = Severity.CRITICAL
                    digest = hashlib.sha1(f"{file.path}:{number}:{rule.rule_id}".encode()).hexdigest()[:10]
                    category = RiskCategory.ENGINEERING_QUALITY_RISK if "quality" in rule.tags else RiskCategory.PERMISSION_RISK
                    findings.append(RiskFinding(
                        id=f"perm-{digest}", category=category, severity=severity,
                        title=rule.title, description=rule.description, evidence=line.strip()[:300],
                        file_path=file.path, line_number=number, recommendation=rule.recommendation,
                        detector=Detector.STATIC, confidence=0.96, rule_id=rule.rule_id, metadata=metadata,
                    ))
        return findings

    @classmethod
    def _relevant_segments(cls, markdown: str, tags: tuple[str, ...]) -> list[str]:
        action_patterns = [cls.ACTION_TERMS[tag] for tag in tags if tag in cls.ACTION_TERMS]
        if not action_patterns:
            return []
        segments = re.split(r"(?<=[.!?。！？])\s+|\n+", markdown)
        return [segment for segment in segments if any(pattern.search(segment) for pattern in action_patterns)]

    @classmethod
    def _has_action_confirmation(cls, markdown: str, tags: tuple[str, ...]) -> bool:
        return any(
            cls.CONFIRMATION.search(segment) and not cls.NEGATED_CONFIRMATION.search(segment)
            for segment in cls._relevant_segments(markdown, tags)
        )

    @classmethod
    def _has_action_negation(cls, markdown: str, tags: tuple[str, ...]) -> bool:
        return any(cls.NEGATED_CONFIRMATION.search(segment) for segment in cls._relevant_segments(markdown, tags))
