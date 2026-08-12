"""格式化输出。

将校验结果和能力列表格式化为可读文本。
"""

from __future__ import annotations

from .validator import ValidationResult


def format_validation(result: ValidationResult) -> str:
    """格式化校验结果为文本。

    Args:
        result: 校验结果

    Returns:
        可读的文本
    """
    lines: list[str] = []

    if result.is_valid:
        lines.append("校验通过: 配置合法")
    else:
        lines.append(f"校验失败: 发现 {len(result.errors)} 个错误")
        lines.append("")
        for i, err in enumerate(result.errors, 1):
            lines.append(f"  {i}. {err}")

    if result.warnings:
        lines.append("")
        lines.append(f"警告 ({len(result.warnings)}):")
        for warn in result.warnings:
            lines.append(f"  - {warn}")

    return "\n".join(lines)


def format_list(capabilities: dict) -> str:
    """格式化能力列表为文本。

    Args:
        capabilities: capabilities 字典

    Returns:
        可读的列表文本
    """
    lines: list[str] = []
    lines.append(f"能力列表 (共 {len(capabilities)} 个):")
    lines.append("")

    for name, data in capabilities.items():
        kind = data.get("kind", "<unknown>")
        desc = data.get("description", "")
        lines.append(f"  {name}")
        lines.append(f"    kind: {kind}")
        if desc:
            lines.append(f"    描述: {desc}")

        actions = data.get("actions", [])
        if actions:
            lines.append(f"    动作: {', '.join(str(a) for a in actions)}")

        props = data.get("properties", [])
        if props:
            prop_strs = []
            for p in props:
                if isinstance(p, dict):
                    prop_strs.append(f"{p.get('name', '?')}={p.get('value', '?')}")
                else:
                    prop_strs.append(str(p))
            lines.append(f"    属性: {', '.join(prop_strs)}")

        constraints = data.get("constraints", {})
        if constraints and isinstance(constraints, dict):
            constraint_strs = [f"{k}={v}" for k, v in constraints.items()]
            lines.append(f"    约束: {', '.join(constraint_strs)}")

        lines.append("")

    return "\n".join(lines)
