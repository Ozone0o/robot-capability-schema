"""Python 接口骨架生成器。

根据解析后的 YAML 数据生成 Python Protocol 类代码。
"""

from __future__ import annotations


def generate_python(data: dict) -> str:
    """生成 Python Protocol 接口骨架。

    Args:
        data: 解析后的 YAML 数据字典

    Returns:
        Python 源码文本
    """
    lines: list[str] = []
    robot = data.get("robot", {})
    capabilities = robot.get("capabilities", {})
    robot_name = robot.get("name", "UnknownRobot")

    lines.append("from __future__ import annotations")
    lines.append("from typing import Protocol")
    lines.append("")
    lines.append("")

    # 类头
    class_name = f"{robot_name.replace('-', '_').title().replace('_', '')}Capabilities"
    lines.append(f"class {class_name}(Protocol):")
    lines.append(f'    """{robot_name} 的能力协议。"""')
    lines.append("")

    for name, cap_data in capabilities.items():
        kind = cap_data.get("kind", "")
        desc = cap_data.get("description", "")
        method_name = f"{kind}_{name}" if kind else name

        if kind == "pan_tilt":
            lines.append(f"    def set_{name}(self, yaw: float, pitch: float) -> None:")
            lines.append(f'        """{desc or f"设置{name}云台角度"}。"""')
            lines.append("        ...")
            lines.append("")

        elif kind == "rgb_camera":
            props = {p["name"]: p for p in cap_data.get("properties", []) if isinstance(p, dict)}
            args_parts, defaults_parts = [], []
            for prop_name in ("width", "height", "fps"):
                if prop_name in props:
                    p = props[prop_name]
                    val = p.get("value", 0)
                    args_parts.append(f"{prop_name}: int = {val}")
                    defaults_parts.append(f"{prop_name}={val}")
            args_str = ", ".join(args_parts) if args_parts else ""
            lines.append(f"    def capture_{name}(self, {args_str}) -> bytes:")
            lines.append(f'        """{desc or f"拍摄{name} RGB图片"}。"""')
            lines.append("        ...")
            lines.append("")

        elif kind == "discrete_action":
            actions = cap_data.get("actions", [])
            inputs = cap_data.get("inputs", [])
            for action in actions if actions else inputs:
                if isinstance(action, dict):
                    act_name = action.get("name", action if isinstance(action, str) else "?")
                    safe_name = act_name.replace("-", "_").replace(" ", "_")
                    sig_parts = ["self"]
                    for inp in action.get("parameters", []):
                        if isinstance(inp, dict):
                            p_name = inp.get("name", "?")
                            p_type = inp.get("type", "Any")
                            req = inp.get("required", True)
                            if req:
                                sig_parts.append(f"{p_name}: {p_type}")
                            else:
                                default = inp.get("default", "None")
                                sig_parts.append(f"{p_name}: {p_type} = {default}")
                    sig = ", ".join(sig_parts)
                    lines.append(f"    def {safe_name}(self, {sig}) -> Any:")
                    lines.append(f'        """{action.get("description", f"执行{act_name}")}。"""')
                    lines.append("        ...")
                    lines.append("")
                elif isinstance(action, str):
                    safe_name = action.replace("-", "_").replace(" ", "_")
                    lines.append(f"    def {safe_name}(self) -> Any:")
                    lines.append(f'        """执行{action}。"""')
                    lines.append("        ...")
                    lines.append("")
        else:
            # 通用回退：基于 inputs 生成方法
            inputs = cap_data.get("inputs", [])
            if inputs:
                for inp in inputs:
                    if isinstance(inp, dict):
                        inp_name = inp.get("name", "?")
                        safe_name = inp_name.replace("-", "_").replace(" ", "_")
                        sig_parts = ["self"]
                        for param in inp.get("parameters", []):
                            if isinstance(param, dict):
                                p_name = param.get("name", "?")
                                p_type = param.get("type", "Any")
                                sig_parts.append(f"{p_name}: {p_type}")
                        sig = ", ".join(sig_parts)
                        lines.append(f"    def {safe_name}(self, {sig}) -> Any:")
                        lines.append(f'        """{inp.get("description", f"{inp_name}")}。"""')
                        lines.append("        ...")
                        lines.append("")
            else:
                props = cap_data.get("properties", [])
                if props:
                    args_parts = []
                    for p in props:
                        if isinstance(p, dict):
                            p_name = p.get("name", "?")
                            val = p.get("value", None)
                            args_parts.append(f"{p_name}: int = {val}" if isinstance(val, (int, float)) else f"{p_name}: str = '{val}'")
                    args_str = ", ".join(args_parts)
                    lines.append(f"    def configure_{name}(self, {args_str}) -> None:")
                    lines.append(f'        """配置{name}。"""')
                    lines.append("        ...")
                    lines.append("")

    return "\n".join(lines)
