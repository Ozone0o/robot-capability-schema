"""格式化器测试。"""


from robot_capability_schema.formatter import format_list, format_validation
from robot_capability_schema.validator import ValidationResult


class TestFormatValidation:
    """测试校验结果格式化。"""

    def test_valid_result(self):
        result = ValidationResult()
        output = format_validation(result)
        assert "校验通过" in output
        assert len(result.errors) == 0

    def test_invalid_result(self):
        result = ValidationResult()
        result.add_error("test error 1")
        result.add_error("test error 2")
        output = format_validation(result)
        assert "校验失败" in output
        assert "test error 1" in output
        assert "test error 2" in output
        assert "2 个错误" in output

    def test_with_warnings(self):
        result = ValidationResult()
        result.add_warning("unknown kind")
        output = format_validation(result)
        assert "警告" in output
        assert "unknown kind" in output


class TestFormatList:
    """测试能力列表格式化。"""

    def test_list_with_properties(self):
        caps = {
            "head": {
                "kind": "pan_tilt",
                "description": "头部云台",
                "properties": [
                    {"name": "yaw_min", "value": -90},
                    {"name": "yaw_max", "value": 90},
                ],
                "constraints": {"pitch_min": -30, "pitch_max": 60},
            },
            "gesture": {
                "kind": "discrete_action",
                "actions": ["wave", "point"],
            },
        }
        output = format_list(caps)
        assert "能力列表" in output
        assert "2 个" in output
        assert "head" in output
        assert "pan_tilt" in output
        assert "wave" in output
