from pathlib import Path

import pytest

from skillguard.parser import SkillParser, SkillParserError


def test_parser_reads_supported_files(tmp_path: Path) -> None:
    (tmp_path / "SKILL.md").write_text("---\nname: Demo\ndescription: Focused demo.\n---\n# Demo", encoding="utf-8")
    (tmp_path / "tool.py").write_text("print('ok')", encoding="utf-8")
    package = SkillParser().parse(tmp_path)
    assert package.skill_name == "Demo"
    assert {file.path for file in package.files} == {"SKILL.md", "tool.py"}


def test_parser_requires_skill_md(tmp_path: Path) -> None:
    with pytest.raises(SkillParserError, match="SKILL.md"):
        SkillParser().parse(tmp_path)


def test_parser_skips_binary(tmp_path: Path) -> None:
    (tmp_path / "SKILL.md").write_text("# Demo\nSafe.", encoding="utf-8")
    (tmp_path / "data.json").write_bytes(b"\x00\x01\x02")
    package = SkillParser().parse(tmp_path)
    assert any("binary" in item for item in package.skipped_files)


def test_parser_skips_large_file(tmp_path: Path) -> None:
    (tmp_path / "SKILL.md").write_text("# Demo\nSafe.", encoding="utf-8")
    (tmp_path / "large.py").write_text("x" * 100, encoding="utf-8")
    package = SkillParser(max_file_size=50).parse(tmp_path)
    assert any("too large" in item for item in package.skipped_files)


def test_parser_stops_enumerating_at_entry_limit(tmp_path: Path) -> None:
    (tmp_path / "SKILL.md").write_text("# Demo\nSafe.", encoding="utf-8")
    for index in range(5):
        (tmp_path / f"ignored-{index}.txt").write_text("x", encoding="utf-8")
    package = SkillParser(max_entries=3).parse(tmp_path)
    assert len(package.file_tree) == 3
    assert any("entry limit exceeded" in item for item in package.skipped_files)
