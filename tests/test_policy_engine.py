from skillguard.policy import PolicyEngine, RiskEngine
from skillguard.schemas import Detector, RiskCategory, RiskFinding, Severity


def finding(severity: Severity, rule_id: str = "TEST", category: RiskCategory = RiskCategory.PERMISSION_RISK) -> RiskFinding:
    return RiskFinding(id=rule_id, category=category, severity=severity, title=rule_id, description="test", evidence="test", recommendation="fix", detector=Detector.STATIC, confidence=1.0, rule_id=rule_id)


def test_critical_blocks() -> None:
    assert PolicyEngine().decide([finding(Severity.CRITICAL)]) == "BLOCK"


def test_high_reviews() -> None:
    assert PolicyEngine().decide([finding(Severity.HIGH)]) == "REVIEW"


def test_safe_allows() -> None:
    assert PolicyEngine().decide([]) == "ALLOW"


def test_score_bounded_and_critical_weighted() -> None:
    engine = RiskEngine()
    assert 0 <= engine.score([finding(Severity.CRITICAL)]) <= 100
    assert engine.score([finding(Severity.CRITICAL)]) > engine.score([finding(Severity.LOW)])


def test_score_deduplicates_same_root() -> None:
    engine = RiskEngine()
    one = finding(Severity.HIGH, "SAME")
    duplicate = finding(Severity.HIGH, "SAME")
    duplicate.id = "other"
    assert engine.score([one, duplicate]) == engine.score([one])


def test_deduplication_does_not_mutate_input_ids() -> None:
    original = finding(Severity.HIGH, "ORIGINAL")
    result = RiskEngine().deduplicate([original])
    assert original.id == "ORIGINAL"
    assert result[0].id == "SG-0001"
