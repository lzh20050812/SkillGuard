import json

from skillguard.main import audit_skill
from skillguard.reporting import ReportGenerator


def test_json_and_markdown_reports() -> None:
    result = audit_skill("examples/safe_skill", semantic=False)
    payload = json.loads(ReportGenerator.json(result))
    assert payload["decision"] == "ALLOW"
    assert "# SkillGuard Audit Report" in ReportGenerator.markdown(result)
    assert "WeatherSummary" in ReportGenerator.markdown(result)

