from pathlib import Path

from skillguard.parser import SkillParser
from skillguard.scanners import StaticScanner


def scan(tmp_path: Path, code: str, instructions: str = "A focused helper."):
    (tmp_path / "SKILL.md").write_text(f"# Demo\n\n{instructions}", encoding="utf-8")
    (tmp_path / "tool.py").write_text(code, encoding="utf-8")
    return StaticScanner().scan(SkillParser().parse(tmp_path))


def test_hardcoded_token_detected(tmp_path: Path) -> None:
    findings = scan(tmp_path, 'API_KEY = "sk-abcdefghijklmnop1234"')
    assert any(f.rule_id == "SECRET_HARDCODED" for f in findings)


def test_environment_token_not_detected(tmp_path: Path) -> None:
    findings = scan(tmp_path, 'API_KEY = os.getenv("API_KEY")')
    assert not any(f.category.value == "SECRET_RISK" for f in findings)


def test_environment_reference_does_not_hide_other_secret(tmp_path: Path) -> None:
    findings = scan(tmp_path, 'API_KEY = os.getenv("API_KEY"); password = "RealPassword123!"')
    assert any(f.category.value == "SECRET_RISK" for f in findings)


def test_aws_key_evidence_is_redacted(tmp_path: Path) -> None:
    findings = scan(tmp_path, "AWS_ACCESS_KEY_ID = 'AKIA1234567890ABCDEF'")
    secret = next(f for f in findings if f.category.value == "SECRET_RISK")
    assert "1234567890ABCDEF" not in secret.evidence


def test_documented_example_aws_key_is_not_reported(tmp_path: Path) -> None:
    findings = scan(tmp_path, "AWS_ACCESS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE'")
    assert not any(f.category.value == "SECRET_RISK" for f in findings)


def test_network_download_is_not_classified_as_data_transmission(tmp_path: Path) -> None:
    findings = scan(tmp_path, "import urllib.request\ndata = urllib.request.urlopen(url).read()")
    assert any(f.rule_id == "NETWORK_READ" for f in findings)
    assert not any(f.rule_id == "NETWORK_WRITE" for f in findings)


def test_curl_upload_is_not_double_counted_as_download(tmp_path: Path) -> None:
    findings = scan(tmp_path, "curl --upload-file report.json https://example.invalid")
    assert any(f.rule_id == "NETWORK_WRITE" for f in findings)
    assert not any(f.rule_id == "NETWORK_READ" for f in findings)


def test_sensitive_capabilities(tmp_path: Path) -> None:
    findings = scan(tmp_path, "subprocess.run(cmd)\nrequests.post(url)\nos.remove(path)", "Ask user confirmation before deletion.")
    assert {"EXEC_SHELL", "NETWORK_WRITE", "FILE_DELETE"} <= {f.rule_id for f in findings}


def test_delete_without_confirmation_is_critical(tmp_path: Path) -> None:
    findings = scan(tmp_path, "os.remove(path)")
    deletion = next(f for f in findings if f.rule_id == "FILE_DELETE")
    assert deletion.severity.value == "CRITICAL"


def test_unrelated_confirmation_does_not_authorize_deletion(tmp_path: Path) -> None:
    findings = scan(tmp_path, "os.remove(path)", "Ask for confirmation before sending email. Delete temporary files when done.")
    deletion = next(f for f in findings if f.rule_id == "FILE_DELETE")
    assert deletion.severity.value == "CRITICAL"


def test_action_specific_confirmation_authorizes_deletion(tmp_path: Path) -> None:
    findings = scan(tmp_path, "os.remove(path)", "Preview targets and ask for confirmation before deletion.")
    deletion = next(f for f in findings if f.rule_id == "FILE_DELETE")
    assert deletion.severity.value == "HIGH"
