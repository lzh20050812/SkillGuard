from __future__ import annotations

import re
import os
from pathlib import Path

import yaml

from skillguard.schemas import SkillFile, SkillPackage
from skillguard.utils.file_utils import is_probably_binary


class SkillParserError(ValueError):
    pass


class SkillParser:
    ALLOWED_SUFFIXES = {".md", ".py", ".js", ".ts", ".sh", ".json", ".yaml", ".yml"}
    IGNORED_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

    def __init__(self, max_file_size: int = 512_000, max_files: int = 500, max_entries: int = 2_000) -> None:
        self.max_file_size = max_file_size
        self.max_files = max_files
        self.max_entries = max_entries

    def parse(self, root: str | Path) -> SkillPackage:
        root_path = Path(root).expanduser().resolve()
        if not root_path.is_dir():
            raise SkillParserError(f"Skill directory does not exist: {root}")
        skill_md = root_path / "SKILL.md"
        if not skill_md.is_file():
            raise SkillParserError(f"SKILL.md not found in {root_path}")

        markdown = self._read_required(skill_md)
        name, description = self._metadata(markdown, root_path.name)
        files: list[SkillFile] = []
        tree: list[str] = []
        skipped: list[str] = []

        entries_seen = 0
        limit_reached = False
        for current, dir_names, file_names in os.walk(root_path, followlinks=False):
            dir_names[:] = sorted(name for name in dir_names if name not in self.IGNORED_DIRS)
            for file_name in sorted(file_names):
                entries_seen += 1
                if entries_seen > self.max_entries:
                    skipped.append(f"<remaining files> (entry limit exceeded: {self.max_entries})")
                    limit_reached = True
                    break
                path = Path(current) / file_name
                relative = path.relative_to(root_path).as_posix()
                tree.append(relative)
                if path.is_symlink():
                    skipped.append(f"{relative} (symbolic link)")
                    continue
                if len(files) >= self.max_files:
                    skipped.append(f"{relative} (file limit exceeded)")
                    continue
                if path.suffix.lower() not in self.ALLOWED_SUFFIXES:
                    skipped.append(f"{relative} (unsupported type)")
                    continue
                try:
                    size = path.stat().st_size
                except OSError:
                    skipped.append(f"{relative} (unreadable)")
                    continue
                if size > self.max_file_size:
                    skipped.append(f"{relative} (too large: {size} bytes)")
                    continue
                if is_probably_binary(path):
                    skipped.append(f"{relative} (binary)")
                    continue
                try:
                    content = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    skipped.append(f"{relative} (decode error)")
                    continue
                files.append(SkillFile(path=relative, content=content, size=size))
            if limit_reached:
                break

        return SkillPackage(
            root_path=root_path,
            skill_name=name,
            description=description,
            markdown_content=markdown,
            files=files,
            file_tree=tree,
            skipped_files=skipped,
        )

    def _read_required(self, path: Path) -> str:
        if path.stat().st_size > self.max_file_size:
            raise SkillParserError("SKILL.md exceeds maximum file size")
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise SkillParserError(f"Cannot read SKILL.md: {exc}") from exc

    @staticmethod
    def _metadata(markdown: str, fallback_name: str) -> tuple[str, str]:
        name, description = fallback_name, ""
        front = re.match(r"^---\s*\n(.*?)\n---\s*\n", markdown, flags=re.DOTALL)
        if front:
            try:
                data = yaml.safe_load(front.group(1)) or {}
                name = str(data.get("name") or name)
                description = str(data.get("description") or "")
            except yaml.YAMLError:
                pass
        if name == fallback_name:
            heading = re.search(r"^#\s+(.+)$", markdown, flags=re.MULTILINE)
            if heading:
                name = heading.group(1).strip()
        if not description:
            body = front and markdown[front.end():] or markdown
            for paragraph in re.split(r"\n\s*\n", body):
                cleaned = " ".join(line.strip() for line in paragraph.splitlines() if not line.lstrip().startswith("#"))
                if cleaned:
                    description = cleaned[:500]
                    break
        return name, description
