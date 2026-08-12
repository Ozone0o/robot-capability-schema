"""CLI 入口。

提供三个子命令：
- validate: 校验 YAML 配置
- list: 列出能力
- docs: 生成 Markdown 文档
- generate-python: 生成 Python 接口骨架
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .docs_generator import generate_markdown
from .formatter import format_list, format_validation
from .parser import ParseError, RobotCapabilityParser
from .python_generator import generate_python
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


def cmd_generate_python(args: argparse.Namespace) -> None:
    """执行 generate-python 命令。"""
    path = _ensure_yaml(Path(args.yaml_file))
    parser = RobotCapabilityParser()

    try:
        data = parser.parse(path)
    except ParseError as exc:
        print(f"解析失败: {exc}", file=sys.stderr)
        sys.exit(1)

    code = generate_python(data)
    output_path = args.output or None
    if output_path:
        Path(output_path).write_text(code, encoding="utf-8")
        print(f"Python 骨架已生成: {output_path}")
    else:
        print(code)


def main() -> None:
    """主入口。"""
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(
        prog="robot-cap",
        description="机器人能力描述工具 - 校验、列出和生成功能说明",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # validate
    p_validate = subparsers.add_parser("validate", help="校验 YAML 配置")
    p_validate.add_argument("yaml_file", help="YAML 文件路径")
    p_validate.set_defaults(func=cmd_validate)

    # list
    p_list = subparsers.add_parser("list", help="列出能力")
    p_list.add_argument("yaml_file", help="YAML 文件路径")
    p_list.set_defaults(func=cmd_list)

    # docs
    p_docs = subparsers.add_parser("docs", help="生成 Markdown 文档")
    p_docs.add_argument("yaml_file", help="YAML 文件路径")
    p_docs.add_argument("-o", "--output", help="输出文件路径（默认输出到终端）")
    p_docs.set_defaults(func=cmd_docs)

    # generate-python
    p_gen = subparsers.add_parser("generate-python", help="生成 Python 接口骨架")
    p_gen.add_argument("yaml_file", help="YAML 文件路径")
    p_gen.add_argument("-o", "--output", help="输出文件路径（默认输出到终端）")
    p_gen.set_defaults(func=cmd_generate_python)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)
