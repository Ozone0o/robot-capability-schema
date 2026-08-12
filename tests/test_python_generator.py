"""Python 代码生成器测试。"""


from robot_capability_schema.python_generator import generate_python


class TestPythonGenerator:
    """测试 Python 代码生成。"""

    def test_generate_pan_tilt(self):
        data = {
            "schema_version": "0.1",
            "robot": {
                "name": "test_robot",
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
        code = generate_python(data)
        assert "class RobotCapabilities" in code
        assert "def set_head" in code
        assert "yaw: float" in code
        assert "pitch: float" in code

    def test_generate_discrete_action(self):
        data = {
            "schema_version": "0.1",
            "robot": {
                "name": "gesture_bot",
                "capabilities": {
                    "hand": {
                        "kind": "discrete_action",
                        "actions": ["wave", "point"],
                    },
                },
            },
        }
        code = generate_python(data)
        assert "def wave" in code
        assert "def point" in code

    def test_generate_unknown_kind(self):
        data = {
            "schema_version": "0.1",
            "robot": {
                "name": "unknown_bot",
                "capabilities": {
                    "sensor": {
                        "kind": "lidar",
                    },
                },
            },
        }
        code = generate_python(data)
        assert "def invoke_sensor" in code
