"""校验器测试。"""


from robot_capability_schema.validator import RobotCapabilityValidator


class TestValidateValid:
    """测试合法配置校验。"""

    def test_valid_simple(self):
        data = {
            "schema_version": "0.1",
            "robot": {
                "name": "test",
                "capabilities": {
                    "head": {
                        "kind": "pan_tilt",
                        "constraints": {
                            "yaw_min": -90,
                            "yaw_max": 90,
                            "pitch_min": -30,
                            "pitch_max": 60,
                        },
                    },
                },
            },
        }
        result = RobotCapabilityValidator().validate(data)
        assert result.is_valid

    def test_valid_unknown_kind(self):
        data = {
            "schema_version": "0.1",
            "robot": {
                "name": "test",
                "capabilities": {
                    "arm": {"kind": "multi_joint_arm"},
                },
            },
        }
        result = RobotCapabilityValidator().validate(data)
        assert result.is_valid
        assert len(result.warnings) > 0


class TestValidateErrors:
    """测试非法配置校验。"""

    def test_constraints_invalid_range(self):
        data = {
            "schema_version": "0.1",
            "robot": {
                "name": "test",
                "capabilities": {
                    "head": {
                        "kind": "pan_tilt",
                        "constraints": {
                            "yaw_min": 90,
                            "yaw_max": -90,
                            "pitch_min": -30,
                            "pitch_max": 60,
                        },
                    },
                },
            },
        }
        result = RobotCapabilityValidator().validate(data)
        assert not result.is_valid
        assert any("yaw_max must be greater than yaw_min" in e for e in result.errors)

    def test_duplicate_property_name(self):
        data = {
            "schema_version": "0.1",
            "robot": {
                "name": "test",
                "capabilities": {
                    "camera": {
                        "kind": "rgb_camera",
                        "properties": [
                            {"name": "fps", "value": 30},
                            {"name": "fps", "value": 60},
                        ],
                    },
                },
            },
        }
        result = RobotCapabilityValidator().validate(data)
        assert not result.is_valid
        assert any("重复属性名" in e for e in result.errors)

    def test_empty_action_string(self):
        data = {
            "schema_version": "0.1",
            "robot": {
                "name": "test",
                "capabilities": {
                    "gesture": {
                        "kind": "discrete_action",
                        "actions": ["wave", "", "point"],
                    },
                },
            },
        }
        result = RobotCapabilityValidator().validate(data)
        assert not result.is_valid
        assert any("actions[1]" in e for e in result.errors)

    def test_camera_constraint_invalid(self):
        data = {
            "schema_version": "0.1",
            "robot": {
                "name": "test",
                "capabilities": {
                    "cam": {
                        "kind": "rgb_camera",
                        "constraints": {
                            "width_min": 1920,
                            "width_max": 640,
                            "height_min": 1,
                            "height_max": 1080,
                            "fps_min": 1,
                            "fps_max": 120,
                        },
                    },
                },
            },
        }
        result = RobotCapabilityValidator().validate(data)
        assert not result.is_valid
        assert any("width_max must be greater" in e for e in result.errors)
