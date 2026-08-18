from __future__ import annotations

import hashlib
import re

from skillguard.schemas import Detector, RiskCategory, RiskFinding, Severity, SkillPackage


class SecretScanner:
    """Conservative scanner for credential *values*, not environment references."""

    PATTERNS: tuple[tuple[str, re.Pattern[str], Severity], ...] = (
        ("OpenAI-style API key", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"), Severity.CRITICAL),
        ("GitHub token", re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"), Severity.CRITICAL),
        ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"), Severity.CRITICAL),
        ("Bearer token", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{16,}"), Severity.CRITICAL),
        ("Private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), Severity.CRITICAL),
        (
            "Hard-coded credential",
            re.compile(
                r"(?i)\b(?:api[_-]?key|access[_-]?token|secret|password|passwd)\b\s*[:=]\s*[\"']([^\"'\n]{8,})[\"']"
            ),
            Severity.CRITICAL,
        ),
    )
    PLACEHOLDERS = re.compile(r"(?i)^(?:your[_ -]?|example|sample|test|dummy|changeme|xxx|<|\$\{|process\.env|os\.getenv)")

    def scan(self, package: SkillPackage) -> list[RiskFinding]:
        findings: list[RiskFinding] = []
        for file in package.files:
            for number, line in enumerate(file.content.splitlines(), start=1):
                for label, pattern, severity in self.PATTERNS:
                    match = pattern.search(line)
                    if not match:
                        continue
                    candidate = match.group(1) if match.lastindex else match.group(0)
                    if self._is_placeholder(candidate):
                        continue
                    digest = hashlib.sha1(f"{file.path}:{number}:{label}".encode()).hexdigest()[:10]
                    findings.append(
                        RiskFinding(
                            id=f"secret-{digest}", category=RiskCategory.SECRET_RISK, severity=severity,
                            title=f"{label} detected", description="A credential-like value is embedded in the package.",
                            evidence=self._redact(line.strip()), file_path=file.path, line_number=number,
                            recommendation="Remove the value, rotate it if real, and load credentials from a secret manager or environment variable.",
                            detector=Detector.STATIC, confidence=0.98, rule_id="SECRET_HARDCODED",
                        )
                    )
                    break
        return findings

    @classmethod
    def _is_placeholder(cls, candidate: str) -> bool:
        normalized = candidate.strip().lower()
        if cls.PLACEHOLDERS.search(normalized):
            return True
        prefixed = bool(re.match(r"^(?:sk-|ghp_|github_pat_|akia|asia)", normalized))
        value = re.sub(r"^(?:sk-|ghp_|github_pat_|akia|asia)", "", normalized)
        if re.match(r"^(?:example|sample|test|dummy|demo|fake|placeholder|x{3,})", value):
            return True
        return prefixed and any(marker in value for marker in ("example", "dummy", "placeholder", "changeme"))

    @staticmethod
    def _redact(line: str) -> str:
        line = re.sub(r"\bsk-[A-Za-z0-9_-]{8,}\b", "sk-***REDACTED***", line)
        line = re.sub(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{8,}\b", "token_***REDACTED***", line)
        line = re.sub(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b", "AKIA***REDACTED***", line)
        line = re.sub(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1***REDACTED***", line)
        return re.sub(r"(?i)((?:api[_-]?key|access[_-]?token|secret|password|passwd)\s*[:=]\s*[\"'])[^\"']+", r"\1***REDACTED***", line)
