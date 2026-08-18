from pathlib import Path

from skillguard.llm import SemanticAuditor
from skillguard.parser import SkillParser


class FakeClient:
    def __init__(self, responses: list[str]):
        self.responses = iter(responses)

    def generate_structured(self, system_prompt: str, user_prompt: str) -> str:
        return next(self.responses)


class FailingClient:
    def generate_structured(self, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("provider unavailable")


def package(tmp_path: Path):
    (tmp_path / "SKILL.md").write_text("# Demo\nFocused helper.", encoding="utf-8")
    return SkillParser().parse(tmp_path)


def test_semantic_retry_then_success(tmp_path: Path) -> None:
    valid = '{"findings": [{"category":"TRIGGER_RISK","severity":"MEDIUM","title":"Broad","description":"broad","evidence":"Focused helper.","file_path":"SKILL.md","line_number":99,"recommendation":"narrow","confidence":0.8}]}'
    outcome = SemanticAuditor(client=FakeClient(["bad", valid])).audit(package(tmp_path), [])
    assert outcome.status == "completed"
    assert outcome.structured_attempts == 2
    assert len(outcome.findings) == 1
    assert outcome.findings[0].line_number == 2


def test_semantic_invalid_output_fails_open(tmp_path: Path) -> None:
    outcome = SemanticAuditor(client=FakeClient(["bad", "also bad"])).audit(package(tmp_path), [])
    assert outcome.status == "failed:invalid_output"
    assert outcome.findings == []


def test_provider_error_does_not_retry(tmp_path: Path) -> None:
    outcome = SemanticAuditor(client=FailingClient()).audit(package(tmp_path), [])
    assert outcome.status == "failed:provider_error"
    assert outcome.structured_attempts == 1


def test_ungrounded_semantic_finding_is_discarded(tmp_path: Path) -> None:
    response = '{"findings": [{"category":"SEMANTIC_RISK","severity":"CRITICAL","title":"Invented","description":"invented","evidence":"text that is not in the package","file_path":"missing.py","line_number":1,"recommendation":"remove","confidence":0.9}]}'
    outcome = SemanticAuditor(client=FakeClient([response])).audit(package(tmp_path), [])
    assert outcome.status == "completed"
    assert outcome.findings == []
