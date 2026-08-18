from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import yaml

from skillguard.schemas import RiskFinding


class RiskEngine:
    def __init__(self, policy_path: str | Path | None = None) -> None:
        path = Path(policy_path) if policy_path else Path(__file__).resolve().parents[3] / "policies" / "risk_taxonomy.yaml"
        self.config = yaml.safe_load(path.read_text(encoding="utf-8"))

    @staticmethod
    def deduplicate(findings: list[RiskFinding]) -> list[RiskFinding]:
        best: dict[tuple[str, str, int | None, str], RiskFinding] = {}
        order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        for finding in findings:
            identity = finding.title.lower() if finding.rule_id == "LLM_SEMANTIC" else finding.rule_id or finding.title.lower()
            key = (identity, finding.file_path or "", finding.line_number, finding.category.value)
            existing = best.get(key)
            if existing is None or (order[finding.severity.value], finding.confidence) > (order[existing.severity.value], existing.confidence):
                best[key] = finding
        result = [finding.model_copy(deep=True) for finding in best.values()]
        result.sort(key=lambda f: (-order[f.severity.value], f.file_path or "", f.line_number or 0, f.id))
        for index, finding in enumerate(result, start=1):
            finding.id = f"SG-{index:04d}"
        return result

    def score(self, findings: list[RiskFinding]) -> int:
        weights = self.config["score_weights"]
        caps = self.config["score_category_caps"]
        floor = float(self.config["deduplication"]["confidence_floor"])
        repeat = float(self.config["deduplication"]["repeated_root_multiplier"])
        category_scores: dict[str, float] = defaultdict(float)
        roots: dict[tuple[str, str], int] = defaultdict(int)
        for finding in self.deduplicate(findings):
            root = (finding.category.value, finding.rule_id or finding.title.lower())
            multiplier = 1.0 if roots[root] == 0 else repeat
            roots[root] += 1
            category_scores[finding.category.value] += weights[finding.severity.value] * max(floor, finding.confidence) * multiplier
        total = sum(min(value, float(caps.get(category, 100))) for category, value in category_scores.items())
        return max(0, min(100, round(total)))
