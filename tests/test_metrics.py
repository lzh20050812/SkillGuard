from evals.metrics import compute_metrics


def record(*, expected="ALLOW", predicted="ALLOW", attempted=False, succeeded=False):
    return {
        "expected_decision": expected,
        "predicted_decision": predicted,
        "expected_risks": [],
        "predicted_risks": [],
        "predicted_high_risks": [],
        "structured_audit_attempted": attempted,
        "structured_audit_succeeded": succeeded,
    }


def test_structured_pass_rate_is_per_attempted_sample() -> None:
    metrics = compute_metrics([
        record(attempted=True, succeeded=True),
        record(attempted=True, succeeded=False),
        record(attempted=False, succeeded=False),
    ])
    assert metrics["structured_output_pass_rate"] == 0.5


def test_missing_baseline_prediction_is_incorrect() -> None:
    metrics = compute_metrics([record(expected="REVIEW", predicted=None)])
    assert metrics["decision_accuracy"] == 0.0
