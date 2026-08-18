"""Language-neutral and Python/TypeScript code generation for Axiom."""

from __future__ import annotations

import json
import keyword
import re
from collections.abc import Mapping
from typing import Any

from .schema import iter_capabilities


def generate_python(data: Mapping[str, Any]) -> str:
    """Generate a Python ``Protocol`` representing the robot contract."""

    robot = data.get("robot", {})
    robot = robot if isinstance(robot, Mapping) else {}
    robot_name = str(robot.get("name", "robot"))
    class_name = f"{_pascal(robot_name)}Capabilities"
    lines = [
        "from __future__ import annotations",
        "",
        "from typing import Any, Protocol",
        "",
        "",
        f"class {class_name}(Protocol):",
        f'    """Machine-readable interface generated from the Axiom contract for {robot_name}."""',
    ]

    methods: set[str] = set()
    entries = [entry for entry in iter_capabilities(data) if entry.name]
    for entry in entries:
        for method_name, return_type, description, parameters in _methods_for_entry(entry):
            method_name = _safe_identifier(method_name)
            if method_name in methods:
                continue
            methods.add(method_name)
            signature = _format_signature(parameters)
            method_signature = (
                f"    def {method_name}(self{', ' if signature else ''}"
                f"{signature}) -> {return_type}:"
            )
            method_description = description or f"Invoke {entry.name}."
            lines.extend(
                [
                    "",
                    method_signature,
                    f'        """{method_description}"""',
                    "        ...",
                ]
            )

    if not methods:
        lines.extend(["", "    ..."])
    lines.append("")
    return "\n".join(lines)


def generate_typescript(data: Mapping[str, Any]) -> str:
    """Generate a TypeScript interface from the same normalized contract."""

    robot = data.get("robot", {})
    robot = robot if isinstance(robot, Mapping) else {}
    robot_name = str(robot.get("name", "robot"))
    interface_name = f"{_pascal(robot_name)}Capabilities"
    lines = [
        "/** Generated from an Axiom robot capability contract. */",
        f"export interface {interface_name} {{",
    ]
    methods: set[str] = set()
    for entry in iter_capabilities(data):
        if not entry.name:
            continue
        for method_name, return_type, description, parameters in _methods_for_entry(entry):
            method_name = _safe_identifier(method_name)
            if method_name in methods:
                continue
            methods.add(method_name)
            comment = description or f"Invoke {entry.name}."
            params = ", ".join(
                f"{_safe_identifier(name)}: {_typescript_type(type_name)}"
                for name, type_name, _, _ in parameters
            )
            lines.extend(
                [
                    f"  /** {comment} */",
                    f"  {method_name}({params}): {_typescript_type(return_type)};",
                ]
            )
    if not methods:
        lines.append("  // No callable capabilities declared.")
    lines.extend(["}", ""])
    return "\n".join(lines)


def generate_json(data: Mapping[str, Any]) -> str:
    """Emit a stable JSON representation for downstream tooling."""

    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _methods_for_entry(entry: Any) -> list[tuple[str, str, str, list[tuple[str, str, Any, bool]]]]:
    spec = entry.spec
    name = entry.name
    description = str(spec.get("description", ""))
    parameters = _parameters(spec.get("inputs", []))
    actions = spec.get("actions", [])
    if isinstance(actions, Mapping):
        actions = list(actions)
    methods: list[tuple[str, str, str, list[tuple[str, str, Any, bool]]]] = []

    if entry.category == "skills":
        if actions:
            for action in actions:
                action_name, action_desc, action_params = _action_details(action, parameters)
                methods.append((action_name, "Any", action_desc or description, action_params))
        else:
            methods.append((name, "Any", description, parameters))
        return methods

    kind = str(spec.get("kind", spec.get("type", ""))).lower()
    if kind == "pan_tilt":
        methods.append(
            (
                f"set_{name}",
                "None",
                description,
                [("yaw", "float", None, True), ("pitch", "float", None, True)],
            )
        )
    elif kind in {"rgb_camera", "camera"} or entry.category == "sensors":
        methods.append((f"read_{name}", "Any", description, parameters))
    elif entry.category == "actuators":
        if actions:
            for action in actions:
                action_name, action_desc, action_params = _action_details(action, parameters)
                methods.append((action_name, "None", action_desc or description, action_params))
        else:
            methods.append((f"set_{name}", "None", description, parameters))
    else:
        methods.append((f"invoke_{name}", "Any", description, parameters))
    return methods


def _action_details(
    action: Any, fallback: list[tuple[str, str, Any, bool]]
) -> tuple[str, str, list[tuple[str, str, Any, bool]]]:
    if isinstance(action, Mapping):
        name = str(action.get("name", action.get("id", "action")))
        description = str(action.get("description", ""))
        parameters = _parameters(action.get("parameters", action.get("inputs", fallback)))
        return name, description, parameters
    return str(action), "", fallback


def _parameters(value: Any) -> list[tuple[str, str, Any, bool]]:
    if isinstance(value, Mapping):
        value = [{"name": key, "type": item} for key, item in value.items()]
    if not isinstance(value, list):
        return []
    result: list[tuple[str, str, Any, bool]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        name = str(item.get("name", "arg"))
        type_name = str(item.get("type", "Any"))
        required = bool(item.get("required", "default" not in item))
        default = item.get("default")
        result.append((name, type_name, default, required))
    return result


def _format_signature(parameters: list[tuple[str, str, Any, bool]]) -> str:
    ordered = sorted(parameters, key=lambda item: not item[3])
    values: list[str] = []
    for name, type_name, default, required in ordered:
        annotation = _python_type(type_name)
        safe_name = _safe_identifier(name)
        if required:
            values.append(f"{safe_name}: {annotation}")
        else:
            values.append(f"{safe_name}: {annotation} = {_python_default(default)}")
    return ", ".join(values)


def _python_type(value: str) -> str:
    aliases = {
        "string": "str",
        "str": "str",
        "integer": "int",
        "int": "int",
        "number": "float",
        "float": "float",
        "boolean": "bool",
        "bool": "bool",
        "object": "dict[str, Any]",
        "array": "list[Any]",
    }
    fallback = value if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_\[\], ]*", value) else "Any"
    return aliases.get(value.lower(), fallback)


def _typescript_type(value: str) -> str:
    aliases = {
        "string": "string",
        "str": "string",
        "integer": "number",
        "int": "number",
        "number": "number",
        "float": "number",
        "boolean": "boolean",
        "bool": "boolean",
        "none": "void",
        "object": "Record<string, unknown>",
        "array": "unknown[]",
        "any": "unknown",
    }
    fallback = (
        value
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_<>\[\], ]*", value)
        else "unknown"
    )
    return aliases.get(value.lower(), fallback)


def _python_default(value: Any) -> str:
    if value is None:
        return "None"
    return repr(value)


def _pascal(value: str) -> str:
    parts = re.findall(r"[A-Za-z0-9]+", value) or ["Robot"]
    return "".join(part[:1].upper() + part[1:] for part in parts)


def _safe_identifier(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not result:
        result = "capability"
    if result[0].isdigit() or keyword.iskeyword(result):
        result = f"_{result}"
    return result


generate = generate_python
