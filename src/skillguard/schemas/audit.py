from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Decision(StrEnum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class Detector(StrEnum):
    STATIC = "STATIC"
    LLM = "LLM"
    POLICY = "POLICY"


class RiskCategory(StrEnum):
    SEMANTIC_RISK = "SEMANTIC_RISK"
    PERMISSION_RISK = "PERMISSION_RISK"
    SECRET_RISK = "SECRET_RISK"
    TRIGGER_RISK = "TRIGGER_RISK"
    ENGINEERING_QUALITY_RISK = "ENGINEERING_QUALITY_RISK"


class RiskFinding(BaseModel):
    id: str
    category: RiskCategory
    severity: Severity
    title: str
    description: str
    evidence: str
    file_path: str | None = None
    line_number: int | None = None
    recommendation: str
    detector: Detector
    confidence: float = Field(ge=0.0, le=1.0)
    rule_id: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class SkillFile(BaseModel):
    path: str
    content: str
    size: int = Field(ge=0)


class SkillPackage(BaseModel):
    root_path: Path
    skill_name: str
    description: str = ""
    markdown_content: str
    files: list[SkillFile]
    file_tree: list[str]
    skipped_files: list[str] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}


class AuditMetadata(BaseModel):
    semantic_audit_status: str
    scanned_files: int
    skipped_files: list[str] = Field(default_factory=list)
    policy_version: str = "1"


class AuditResult(BaseModel):
    skill_name: str
    overall_score: int = Field(ge=0, le=100)
    decision: Decision
    findings: list[RiskFinding]
    summary: str
    metadata: AuditMetadata

    @field_validator("findings")
    @classmethod
    def unique_ids(cls, value: list[RiskFinding]) -> list[RiskFinding]:
        ids = [item.id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError("finding ids must be unique")
        return value

