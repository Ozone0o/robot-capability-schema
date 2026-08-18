"""Markdown documentation generation for Axiom contracts."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from typing import Any

from .matching import extract_requirements
from .schema import document_version, iter_capabilities, iter_hardware, iter_interfaces, text_value


def generate_markdown(data: Mapping[str, Any]) -> str:
    """Generate a readable capability catalog from an Axiom document."""

    robot = data.get("robot", {})
    robot = robot if isinstance(robot, Mapping) else {}
    name = str(robot.get("name", "Unnamed robot"))
    description = robot.get("description")
    lines = [
        f"# {name}",
        "",
        "> Axiom capability contract",
        "",
        f"- **Axiom version:** {document_version(data) or 'unknown'}",
    ]
    for key, label in (("manufacturer", "Manufacturer"), ("model", "Model")):
        if robot.get(key):
            lines.append(f"- **{label}:** {_md(robot[key])}")
    if description:
        lines.extend(["", _md(description)])

    hardware = list(iter_hardware(data))
    lines.extend(["", "## Hardware", ""])
    if hardware:
        grouped = _group_by_category(hardware)
        for category, entries in grouped.items():
            lines.extend([f"### {_title(category)}", ""])
            for entry in entries:
                lines.extend(_entry_section(entry.name, entry.spec, level=4))
    else:
        lines.append("No hardware components declared.")

    capabilities = list(iter_capabilities(data))
    lines.extend(["", "## Capabilities", ""])
    if capabilities:
        grouped = _group_by_category(capabilities)
        for category, entries in grouped.items():
            lines.extend([f"### {_title(category)}", ""])
            for entry in entries:
                lines.extend(_entry_section(entry.name, entry.spec, level=4))
    else:
        lines.append("No capabilities declared.")

    interfaces = list(iter_interfaces(data))
    lines.extend(["", "## Interfaces", ""])
    if interfaces:
        lines.extend(["| Name | Protocol | Endpoint |", "| --- | --- | --- |"])
        for interface in interfaces:
            protocol = interface.spec.get("protocol", interface.spec.get("type", ""))
            endpoint = interface.spec.get("endpoint", interface.spec.get("url", ""))
            lines.append(
                f"| {_md(interface.name)} | {_md(protocol)} | {_md(endpoint)} |"
            )
    else:
        lines.append("No interfaces declared.")

    lines.extend(["", "## Constraints and safety", ""])
    constraints = data.get("constraints", {})
    if isinstance(constraints, Mapping) and constraints:
        safety = constraints.get("safety", constraints.get("safety_constraints"))
        if safety:
            lines.extend(["### Safety", ""])
            lines.extend(_bullet_values(safety))
            lines.append("")
        other = {
            key: value
            for key, value in constraints.items()
            if key not in {"safety", "safety_constraints"}
        }
        if other:
            lines.extend(
                [
                    "### Operating constraints",
                    "",
                    "| Constraint | Value |",
                    "| --- | --- |",
                ]
            )
            lines.extend(
                f"| {_md(key)} | {_md(text_value(value))} |"
                for key, value in other.items()
            )
    elif constraints:
        lines.extend(_bullet_values(constraints))
    else:
        lines.append("No constraints declared.")

    lines.extend(["", "## Requirements", ""])
    requirements = data.get("requirements")
    if requirements:
        lines.extend(_bullet_values(requirements))
    else:
        extracted = extract_requirements(data)
        if extracted.required or extracted.optional or extracted.alternatives:
            for item in extracted.required:
                lines.append(f"- `{_md(item)}`")
            for group in extracted.alternatives:
                lines.append(f"- one of: {', '.join(f'`{_md(item)}`' for item in group)}")
            for item in extracted.optional:
                lines.append(f"- optional: `{_md(item)}`")
        else:
            lines.append("No requirements declared.")

    lines.extend(["", "---", "", "Generated from an Axiom contract.", ""])
    return "\n".join(lines)


def _group_by_category(entries: list[Any]) -> dict[str, list[Any]]:
    grouped: dict[str, list[Any]] = defaultdict(list)
    for entry in entries:
        grouped[entry.category].append(entry)
    return dict(grouped)


def _entry_section(name: str, spec: Mapping[str, Any], *, level: int) -> list[str]:
    heading = "#" * level
    lines = [f"{heading} {_md(name or 'unnamed')}", ""]
    description = spec.get("description")
    if description:
        lines.extend([_md(description), ""])

    details = []
    for key in ("type", "kind", "model", "driver", "unit"):
        if spec.get(key) is not None:
            details.append((key.title(), spec[key]))
    if details:
        lines.extend(["| Property | Value |", "| --- | --- |"])
        lines.extend(f"| {_md(key)} | {_md(text_value(value))} |" for key, value in details)
        lines.append("")

    requires = spec.get("requires", spec.get("requirements"))
    if requires:
        lines.append(f"**Requires:** {_md(text_value(requires))}")
        lines.append("")
    for key in ("actions", "inputs", "outputs", "properties", "limitations"):
        value = spec.get(key)
        if value:
            lines.extend([f"**{key.title()}:**", ""])
            lines.extend(_bullet_values(value))
            lines.append("")
    constraints = spec.get("constraints")
    if constraints:
        lines.extend(["**Constraints:**", ""])
        lines.extend(_bullet_values(constraints))
        lines.append("")
    return lines


def _bullet_values(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        return [f"- **{_md(key)}:** {_md(text_value(item))}" for key, item in value.items()]
    if isinstance(value, (list, tuple, set)):
        result: list[str] = []
        for item in value:
            if isinstance(item, Mapping):
                name = item.get("name", item.get("capability", "item"))
                rest = {key: val for key, val in item.items() if key not in {"name", "capability"}}
                detail = _md(text_value(rest)) if rest else ""
                result.append(f"- **{_md(name)}:** {detail}".rstrip())
            else:
                result.append(f"- {_md(text_value(item))}")
        return result
    return [f"- {_md(text_value(value))}"]


def _title(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()


def _md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


generate_docs = generate_markdown
