from __future__ import annotations

import argparse
import sys
from pathlib import Path

from skillguard.main import audit_skill
from skillguard.parser import SkillParserError
from skillguard.reporting import ReportGenerator
from skillguard.utils.logger import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skillguard", description="Pre-install Agent Skill security audit")
    parser.add_argument("--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit", help="audit a local Skill package")
    audit.add_argument("path")
    audit.add_argument("--format", choices=("text", "json", "markdown"), default="text")
    audit.add_argument("--output", type=Path)
    audit.add_argument("--no-semantic", action="store_true", help="disable LLM semantic auditing")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(args.verbose)
    try:
        result = audit_skill(args.path, semantic=not args.no_semantic)
    except SkillParserError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"audit failed: {exc}", file=sys.stderr)
        return 1
    generator = ReportGenerator()
    rendered = generator.json(result) if args.format == "json" else generator.markdown(result) if args.format == "markdown" else generator.terminal(result)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
