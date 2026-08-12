"""Python 代码生成器。

根据能力定义生成通用的 Python Protocol 接口骨架。
只生成通用接口，不包含任何公司内部驱动或 MCP 代码。
"""

from __future__ import annotations


def generate_python(data: dict) -> str:
    """生成 Python Protocol 骨架代码。

    Args:
        data: 解析后的 YAML 数据字典

    Returns:
        Python 源代码文本
    """
    lines: list[str] = []
    robot = data.get("robot", {})
    robot_name = robot.get("name", "robot")
    capabilities = robot.get("capabilities", {})
    version = data.get("schema_version", "unknown")

    lines.append('"""')
    lines.append(f"机器人能力接口骨架 - {robot_name}")
    lines.append("由 robot-capability-schema 自动生成")
    lines.append(f"Schema 版本: {version}")
    lines.append('"""')
    lines.append("")
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from typing import Any, Protocol")
    lines.append("")
    lines.append("")
    lines.append("class RobotCapabilities(Protocol):")
    lines.append(f'    """{robot_name} 的能力协议。"""')
    lines.append("")

    for name, cap_data in capabilities.items():
        kind = cap_data.get("kind", "unknown")

        # 生成能力方法
        methods = _generate_methods(name, kind, cap_data)
        if methods:
            lines.append(f"    # --- {name} (kind: {kind}) ---")
            lines.append("")
            for method in methods:
                lines.append(method)
                lines.append("")

    lines.append("")
    return "\n".join(lines)


def _generate_methods(name: str, kind: str, cap_data: dict) -> list[str]:
    """根据能力类型生成对应的方法。"""
    methods: list[str] = []
    cap_lower = name.replace(" ", "_")

    if kind == "pan_tilt":
        methods.extend([
            f"    def set_{cap_lower}(self, yaw: float, pitch: float) -> None:",
            '        """设置云台角度。"""',
            "        ...",
        ])

    elif kind == "rgb_camera":
        methods.extend([
            f"    def capture_{cap_lower}(",
            "        self, width: int = 1280, height: int = 720, fps: int = 30",
            "    ) -> bytes:",
            '        """拍摄一张 RGB 图片。"""',
            "        ...",
        ])

    elif kind == "discrete_action":
        actions = cap_data.get("actions", [])
        for action in actions:
            action_method = action.replace(" ", "_").replace("-", "_")
            methods.extend([
                f"    def {action_method}(self) -> bool:",
                f'        """执行动作: {action}。"""',
                "        ...",
            ])

    else:
        # 通用方法
        methods.extend([
            f"    def invoke_{cap_lower}(",
            "        self, params: dict[str, Any] | None = None",
            "    ) -> dict[str, Any] | None:",
            f'        """调用能力: {name}。"""',
            "        ...",
        ])

    return methods
