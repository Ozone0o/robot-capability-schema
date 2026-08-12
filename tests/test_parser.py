"""解析器测试。"""

from pathlib import Path

import pytest

from robot_capability_schema.parser import ParseError, RobotCapabilityParser

FIXTURES = Path(__file__).parent / "fixtures"


class TestParseValid:
    """测试合法配置解析。"""

    def test_parse_simple_robot(self):
        parser = RobotCapabilityParser()
        data = parser.parse(FIXTURES / "valid_simple.yaml")
        assert data["schema_version"] == "0.1"
        assert data["robot"]["name"] == "test_robot"
        assert "head" in data["robot"]["capabilities"]

    def test_parse_with_metadata(self):
        parser = RobotCapabilityParser()
        data = parser.parse(FIXTURES / "valid_with_meta.yaml")
        assert data["robot"]["manufacturer"] == "TestCo"


class TestParseErrors:
    """测试解析错误。"""

    def test_missing_schema_version(self):
        parser = RobotCapabilityParser()
        with pytest.raises(ParseError, match="缺少 schema_version"):
            parser.parse(FIXTURES / "missing_version.yaml")

    def test_unsupported_version(self):
        parser = RobotCapabilityParser()
        with pytest.raises(ParseError, match="不支持的 schema_version"):
            parser.parse(FIXTURES / "bad_version.yaml")

    def test_missing_robot_field(self):
        parser = RobotCapabilityParser()
        with pytest.raises(ParseError, match="缺少 robot 字段"):
            parser.parse(FIXTURES / "missing_robot.yaml")

    def test_missing_capabilities(self):
        parser = RobotCapabilityParser()
        with pytest.raises(ParseError, match="缺少 robot.capabilities 字段"):
            parser.parse(FIXTURES / "missing_capabilities.yaml")

    def test_empty_capabilities(self):
        parser = RobotCapabilityParser()
        with pytest.raises(ParseError, match="不能为空"):
            parser.parse(FIXTURES / "empty_capabilities.yaml")

    def test_missing_capability_kind(self):
        parser = RobotCapabilityParser()
        with pytest.raises(ParseError, match="缺少 kind 字段"):
            parser.parse(FIXTURES / "missing_kind.yaml")

    def test_invalid_yaml(self):
        parser = RobotCapabilityParser()
        with pytest.raises(ParseError, match="YAML 语法错误"):
            parser.parse(FIXTURES / "invalid_syntax.yaml")
