"""YAML 解析器。

将 YAML 文件读取并转换为 Pydantic 模型对象。
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


class ParseError(Exception):
    """解析错误。"""

    pass


class RobotCapabilityParser:
    """YAML 解析器。

    将 YAML 字典树转换为 Pydantic 模型。
    """

    SUPPORTED_VERSIONS = {"0.1"}

    def parse(self, path: Path) -> dict:
        """解析 YAML 文件，返回包含元信息和能力列表的字典。

        Args:
            path: YAML 文件路径

        Returns:
            包含 schema_version、robot、capabilities 的字典

        Raises:
            ParseError: 解析失败时抛出
        """
        try:
            text = path.read_text(encoding="utf-8")
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise ParseError(f"YAML 语法错误: {exc}") from exc

        if not isinstance(data, dict):
            raise ParseError("YAML 文件内容必须是一个映射（字典）")

        self._check_version(data)
        self._check_required_fields(data)

        return data

    def _check_version(self, data: dict) -> None:
        """检查 schema 版本号。"""
        version = data.get("schema_version")
        if version is None:
            raise ParseError("缺少 schema_version 字段")
        if version not in self.SUPPORTED_VERSIONS:
            raise ParseError(
                f"不支持的 schema_version: {version}。"
                f"当前支持: {', '.join(sorted(self.SUPPORTED_VERSIONS))}"
            )

    def _check_required_fields(self, data: dict) -> None:
        """检查必填字段。"""
        if "robot" not in data:
            raise ParseError("缺少 robot 字段")

        robot = data["robot"]
        if not isinstance(robot, dict):
            raise ParseError("robot 字段必须是一个映射（字典）")

        if "name" not in robot:
            raise ParseError("缺少 robot.name 字段")

        if "capabilities" not in robot:
            raise ParseError("缺少 robot.capabilities 字段")

        caps = robot["capabilities"]
        if not isinstance(caps, dict):
            raise ParseError("robot.capabilities 字段必须是一个映射（字典）")

        if len(caps) == 0:
            raise ParseError("robot.capabilities 不能为空")

        for cap_name, cap_data in caps.items():
            if not isinstance(cap_data, dict):
                raise ParseError(f"capabilities.{cap_name} 必须是一个映射（字典）")
            if "kind" not in cap_data:
                raise ParseError(f"capabilities.{cap_name} 缺少 kind 字段")
