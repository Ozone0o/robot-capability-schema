"""The ``axiom`` command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .codegen import generate_json, generate_python, generate_typescript
from .diff import diff_documents, format_diff
from .docs import generate_markdown
from .matching import format_compatibility, match_requirements
from .schema import AxiomParseError, AxiomParser, iter_capabilities, iter_hardware
from .validator import AxiomValidator, ValidationResult

INIT_TEMPLATE = """axiom: "1.0"

robot:
  name: my-robot
  description: Describe this robot and the contract it exposes.

hardware:
  sensors: {}
  actuators: {}

capabilities:
  sensors: {}
  actuators: {}
  skills: {}
  limitations: []

interfaces: []

constraints:
  safety: []

requirements: []
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="axiom",
        description="Axiom — the capability contract for robots.",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    subparsers = parser.add_subparsers(dest="command")

    init = subparsers.add_parser("init", help="Create a starter robot.yaml contract")
    init.add_argument("path", nargs="?", default="robot.yaml", help="Output path")
    init.add_argument("--force", action="store_true", help="Overwrite an existing file")
    init.set_defaults(handler=cmd_init)

    validate = subparsers.add_parser("validate", help="Validate an Axiom contract")
    validate.add_argument("path", nargs="?", default="robot.yaml")
    validate.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    validate.add_argument(
        "--allow-extensions", action="store_true", help="Allow unknown top-level fields"
    )
    validate.set_defaults(handler=cmd_validate)

    lint = subparsers.add_parser("lint", help="Check contract quality and portability")
    lint.add_argument("path", nargs="?", default="robot.yaml")
    lint.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    lint.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    lint.add_argument(
        "--allow-extensions", action="store_true", help="Allow unknown top-level fields"
    )
    lint.set_defaults(handler=cmd_lint)

    docs = subparsers.add_parser("docs", help="Generate Markdown capability documentation")
    docs.add_argument("path", nargs="?", default="robot.yaml")
    docs.add_argument("-o", "--output", help="Write to a file instead of stdout")
    docs.set_defaults(handler=cmd_docs)

    generate = subparsers.add_parser("generate", help="Generate an integration interface")
    generate.add_argument("path", nargs="?", default="robot.yaml")
    generate.add_argument(
        "--language",
        choices=("python", "typescript", "json"),
        default="python",
        help="Target language (default: python)",
    )
    generate.add_argument("-o", "--output", help="Write to a file instead of stdout")
    generate.set_defaults(handler=cmd_generate)

    diff = subparsers.add_parser("diff", help="Compare two robot capability contracts")
    diff.add_argument("old_path")
    diff.add_argument("new_path")
    diff.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    diff.set_defaults(handler=cmd_diff)

    match = subparsers.add_parser("match", help="Check robot capabilities against requirements")
    match.add_argument("robot_file")
    match.add_argument(
        "requirements_file",
        nargs="?",
        help="A skill or requirement manifest (optional when --requires is used)",
    )
    match.add_argument("--requires", nargs="+", help="Required capability names")
    match.add_argument("--skill", help="Select one skill from the requirement document")
    match.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    match.set_defaults(handler=cmd_match)

    list_command = subparsers.add_parser("list", help="List declared capabilities")
    list_command.add_argument("path", nargs="?", default="robot.yaml")
    list_command.set_defaults(handler=cmd_list)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        return 1
    try:
        return int(args.handler(args))
    except AxiomParseError as exc:
        print(f"Axiom error: {exc}", file=sys.stderr)
    except ValueError as exc:
        print(f"Axiom error: {exc}", file=sys.stderr)
    return 2


def cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if path.exists() and not args.force:
        print(f"File already exists: {path} (use --force to replace)", file=sys.stderr)
        return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(INIT_TEMPLATE, encoding="utf-8")
    print(f"Created Axiom contract: {path}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    data = _load(args.path)
    result = AxiomValidator(allow_extensions=args.allow_extensions).validate(data)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_validation(result, label="Validation")
    return 0 if result.is_valid else 1


def cmd_lint(args: argparse.Namespace) -> int:
    data = _load(args.path)
    result = AxiomValidator(allow_extensions=args.allow_extensions).lint(data)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_validation(result, label="Lint")
    return 0 if result.is_valid and (not args.strict or not result.warnings) else 1


def cmd_docs(args: argparse.Namespace) -> int:
    data = _load(args.path)
    output = generate_markdown(data)
    _write_or_print(output, args.output, "documentation")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    data = _load(args.path)
    if args.language == "python":
        output = generate_python(data)
    elif args.language == "typescript":
        output = generate_typescript(data)
    else:
        output = generate_json(data)
    _write_or_print(output, args.output, f"{args.language} interface")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    old = _load(args.old_path)
    new = _load(args.new_path)
    result = diff_documents(old, new)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(format_diff(result))
    return 0


def cmd_match(args: argparse.Namespace) -> int:
    first = _load(args.robot_file, require_robot=False)
    second = _load(args.requirements_file, require_robot=False) if args.requirements_file else None

    robot = first
    requirement_document = second
    if second is not None and _has_robot(second) and not _has_robot(first):
        robot, requirement_document = second, first

    result = match_requirements(
        robot,
        requirement_document,
        requirements=args.requires,
        skill=args.skill,
    )
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(format_compatibility(result))
    return 0 if result.compatible else 1


def cmd_list(args: argparse.Namespace) -> int:
    data = _load(args.path)
    entries = [
        entry
        for entry in (*iter_hardware(data), *iter_capabilities(data))
        if entry.name
    ]
    print(f"Capabilities ({len(entries)}):")
    for entry in entries:
        print(f"  {entry.name} [{entry.category}]")
    return 0


def _load(path: str, *, require_robot: bool = True) -> dict[str, Any]:
    return AxiomParser().parse(Path(path), require_robot=require_robot)


def _has_robot(data: dict[str, Any]) -> bool:
    return isinstance(data.get("robot"), dict) and bool(data["robot"].get("name"))


def _print_validation(result: ValidationResult, *, label: str) -> None:
    if result.is_valid:
        print(f"{label} passed: valid Axiom contract")
    else:
        print(f"{label} failed: {len(result.errors)} error(s)")
        for error in result.errors:
            print(f"  - {error}")
    if result.warnings:
        print(f"Warnings ({len(result.warnings)}):")
        for warning in result.warnings:
            print(f"  - {warning}")


def _write_or_print(content: str, output: str | None, label: str) -> None:
    if output:
        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(f"Generated {label}: {target}")
    else:
        print(content, end="" if content.endswith("\n") else "\n")


if __name__ == "__main__":
    raise SystemExit(main())
