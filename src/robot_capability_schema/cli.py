"""CLI 入口。

提供三个子命令：
- validate: 校验 YAML 配置
- list: 列出能力
- docs: 生成 Markdown 文档
"""

from __future__ import annotations


import argparse
import logging
import sys
from pathlib import Path

from .docs_generator import generate_markdown
from .formatter import format_list, format_validation
from .parser import ParseError, RobotCapabilityParser
from .validator import RobotCapabilityValidator

logger = logging.getLogger("robot_capability_schema")


def _ensure_yaml(path: Path) -> Path:
    """确保文件存在且是 YAML。"""
    if not path.exists():
        print(f"错误: 文件不存在: {path}", file=sys.stderr)
        sys.exit(1)
    return path


def cmd_validate(args: argparse.Namespace) -> None:
    """执行 validate 命令。"""
    path = _ensure_yaml(Path(args.yaml_file))
    parser = RobotCapabilityParser()

    try:
        data = parser.parse(path)
    except ParseError as exc:
        print(f"校验失败: {exc}", file=sys.stderr)
        sys.exit(1)

    validator = RobotCapabilityValidator()
    result = validator.validate(data)
    print(format_validation(result))

    if not result.is_valid:
        sys.exit(1)


def cmd_list(args: argparse.Namespace) -> None:
    """执行 list 命令。"""
    path = _ensure_yaml(Path(args.yaml_file))
    parser = RobotCapabilityParser()

    try:
        data = parser.parse(path)
    except ParseError as exc:
        print(f"解析失败: {exc}", file=sys.stderr)
        sys.exit(1)

    capabilities = data.get("robot", {}).get("capabilities", {})
    print(format_list(capabilities))


def cmd_docs(args: argparse.Namespace) -> None:
    """执行 docs 命令。"""
    path = _ensure_yaml(Path(args.yaml_file))
    parser = RobotCapabilityParser()

    try:
        data = parser.parse(path)
    except ParseError as exc:
        print(f"解析失败: {exc}", file=sys.stderr)
        sys.exit(1)

    md = generate_markdown(data)
    output_path = args.output or None
    if output_path:
        Path(output_path).write_text(md, encoding="utf-8")
        print(f"文档已生成: {output_path}")
    else:
        print(md)


    args.func(args)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Robot Capability Schema CLI")
    subparsers = parser.add_subparsers(dest="command")

    # validate
    validate_parser = subparsers.add_parser("validate", help="Validate YAML config")
    validate_parser.add_argument("yaml_file", type=str, help="Path to YAML file")
    validate_parser.set_defaults(command="validate", func=cmd_validate)

    # list
    list_parser = subparsers.add_parser("list", help="List capabilities")
    list_parser.add_argument("yaml_file", type=str, help="Path to YAML file")
    list_parser.set_defaults(command="list", func=cmd_list)

    # docs
    docs_parser = subparsers.add_parser("docs", help="Generate Markdown docs")
    docs_parser.add_argument("yaml_file", type=str, help="Path to YAML file")
    docs_parser.add_argument("-o", "--output", type=str, help="Output file path")
    docs_parser.set_defaults(command="docs", func=cmd_docs)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
