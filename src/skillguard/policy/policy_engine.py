from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

from skillguard.schemas import Decision, RiskFinding


class PolicyEngine:
    def __init__(self, policy_path: str | Path | None = None) -> None:
        path = Path(policy_path) if policy_path else Path(__file__).resolve().parents[3] / "policies" / "permission_policy.yaml"
        self.config = yaml.safe_load(path.read_text(encoding="utf-8"))

    def decide(self, findings: list[RiskFinding]) -> Decision:
        block = self.config["block"]
        if any(f.severity.value in block["severities"] for f in findings):
            return Decision.BLOCK
        conditions = set(block["conditions"])
        if any(f.metadata.get("block_condition") in conditions for f in findings):
            return Decision.BLOCK
        review = self.config["review"]
        if any(f.severity.value in review["severities"] for f in findings):
            return Decision.REVIEW
        counts = Counter(f.severity.value for f in findings)
        if counts["MEDIUM"] >= int(review["medium_count"]):
            return Decision.REVIEW
        review_categories = set(review["categories"])
        if any(f.category.value in review_categories and f.severity.value == "MEDIUM" for f in findings):
            return Decision.REVIEW
        return Decision.ALLOW
