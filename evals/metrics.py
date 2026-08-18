from __future__ import annotations

from typing import Any


def compute_metrics(records: list[dict[str, Any]]) -> dict[str, float | int | None]:
    total = len(records)
    correct = sum(record["predicted_decision"] == record["expected_decision"] for record in records)
    expected_high = sum(len(set(record["expected_risks"])) for record in records if record["expected_decision"] == "BLOCK")
    detected_high = sum(
        len(set(record["expected_risks"]) & set(record["predicted_high_risks"]))
        for record in records if record["expected_decision"] == "BLOCK"
    )
    safe = [record for record in records if record["expected_decision"] == "ALLOW"]
    false_high = sum(bool(record["predicted_high_risks"]) for record in safe)
    predicted_risks = sum(len(set(record["predicted_risks"])) for record in records)
    true_predicted = sum(len(set(record["predicted_risks"]) & set(record["expected_risks"])) for record in records)
    structured = [record for record in records if record.get("structured_audit_attempted", False)]
    successes = sum(bool(record.get("structured_audit_succeeded", False)) for record in structured)
    return {
        "sample_count": total,
        "decision_accuracy": correct / total if total else 0.0,
        "high_risk_recall": detected_high / expected_high if expected_high else None,
        "false_positive_rate": false_high / len(safe) if safe else None,
        "finding_precision": true_predicted / predicted_risks if predicted_risks else None,
        "structured_output_pass_rate": successes / len(structured) if structured else None,
    }
