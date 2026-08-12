"""文档生成器测试。"""


from robot_capability_schema.docs_generator import generate_markdown


class TestDocsGenerator:
    """测试 Markdown 文档生成。"""

    def test_basic_generation(self):
        data = {
            "schema_version": "0.1",
            "robot": {
                "name": "test_robot",
                "description": "测试机器人",
                "capabilities": {
                    "head": {
                        "kind": "pan_tilt",
                        "description": "头部云台",
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
        md = generate_markdown(data)
        assert "# 机器人能力说明: test_robot" in md
        assert "## 能力列表" in md
        assert "### head" in md
        assert "**类型**: pan_tilt" in md
        assert "| yaw_min | -90 |" in md

    def test_with_actions(self):
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
        md = generate_markdown(data)
        assert "- wave" in md
        assert "- point" in md

    def test_with_properties(self):
        data = {
            "schema_version": "0.1",
            "robot": {
                "name": "camera_bot",
                "capabilities": {
                    "cam": {
                        "kind": "rgb_camera",
                        "properties": [
                            {"name": "width", "value": 1280, "unit": "px"},
                            {"name": "fps", "value": 30, "unit": "Hz"},
                        ],
                    },
                },
            },
        }
        md = generate_markdown(data)
        assert "| width | 1280 | px |" in md
        assert "| fps | 30 | Hz |" in md

    def test_with_metadata(self):
        data = {
            "schema_version": "0.1",
            "robot": {
                "name": "meta_bot",
                "capabilities": {
                    "sensor": {
                        "kind": "lidar",
                        "metadata": {"firmware": "1.2.3", "serial": "ABC123"},
                    },
                },
            },
        }
        md = generate_markdown(data)
        assert "- firmware: 1.2.3" in md
        assert "- serial: ABC123" in md
