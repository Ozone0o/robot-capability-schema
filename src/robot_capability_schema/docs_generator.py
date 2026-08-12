"""Markdown 文档生成器。

根据解析后的数据生成 Markdown 格式的能力说明文档。
"""

from __future__ import annotations


def generate_markdown(data: dict) -> str:
    """生成 Markdown 能力说明文档。

    Args:
        data: 解析后的 YAML 数据字典

    Returns:
        Markdown 文本
    """
    lines: list[str] = []
    robot = data.get("robot", {})
    capabilities = robot.get("capabilities", {})
    robot_name = robot.get("name", "Unknown Robot")
    robot_desc = robot.get("description", "")
    version = data.get("schema_version", "unknown")

    # 标题
    lines.append(f"# 机器人能力说明: {robot_name}")
    lines.append("")
    lines.append(f"- Schema 版本: {version}")
    if robot_desc:
        lines.append(f"- 描述: {robot_desc}")
    if robot.get("manufacturer"):
        lines.append(f"- 制造商: {robot['manufacturer']}")
    if robot.get("model"):
        lines.append(f"- 型号: {robot['model']}")
    lines.append("")

    # 能力详情
    lines.append("## 能力列表")
    lines.append("")

    for name, cap_data in capabilities.items():
        kind = cap_data.get("kind", "<unknown>")
        desc = cap_data.get("description", "")

        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"- **类型**: {kind}")
        if desc:
            lines.append(f"- **描述**: {desc}")

        # 属性
        properties = cap_data.get("properties", [])
        if properties:
            lines.append("")
            lines.append("**属性:**")
            lines.append("")
            lines.append("| 名称 | 值 | 单位 |")
            lines.append("| --- | --- | --- |")
            for p in properties:
                if isinstance(p, dict):
                    lines.append(
                        f"| {p.get('name', '?')} | {p.get('value', '?')} | {p.get('unit', '')} |"
                    )
            lines.append("")

        # 约束
        constraints = cap_data.get("constraints", {})
        if constraints and isinstance(constraints, dict):
            lines.append("**约束:**")
            lines.append("")
            lines.append("| 约束项 | 值 |")
            lines.append("| --- | --- |")
            for k, v in constraints.items():
                lines.append(f"| {k} | {v} |")
            lines.append("")

        # 动作
        actions = cap_data.get("actions", [])
        if actions:
            lines.append("**可执行动作:**")
            lines.append("")
            for action in actions:
                lines.append(f"- {action}")
            lines.append("")

        # 输入参数
        inputs = cap_data.get("inputs", [])
        if inputs:
            lines.append("**输入参数:**")
            lines.append("")
            lines.append("| 名称 | 类型 | 必填 | 描述 |")
            lines.append("| --- | --- | --- | --- |")
            for inp in inputs:
                if isinstance(inp, dict):
                    req = "是" if inp.get("required", True) else "否"
                    name_s = inp.get('name', '?')
                    type_s = inp.get('type', '?')
                    desc_s = inp.get('description', '')
                    lines.append(f"| {name_s} | {type_s} | {req} | {desc_s} |")
            lines.append("")

        # 输出参数
        outputs = cap_data.get("outputs", [])
        if outputs:
            lines.append("**输出参数:**")
            lines.append("")
            lines.append("| 名称 | 类型 | 描述 |")
            lines.append("| --- | --- | --- |")
            for out in outputs:
                if isinstance(out, dict):
                    name_s = out.get('name', '?')
                    type_s = out.get('type', '?')
                    desc_s = out.get('description', '')
                    lines.append(f"| {name_s} | {type_s} | {desc_s} |")
            lines.append("")

        # 额外元信息
        metadata = cap_data.get("metadata", {})
        if metadata:
            lines.append("**额外元信息:**")
            lines.append("")
            for k, v in metadata.items():
                lines.append(f"- {k}: {v}")
            lines.append("")

    return "\n".join(lines)
