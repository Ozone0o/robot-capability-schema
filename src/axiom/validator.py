"""Validation and lint rules for Axiom capability contracts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from numbers import Real
from typing import Any

from .schema import (
    KNOWN_CATEGORIES,
    SUPPORTED_VERSIONS,
    document_version,
    iter_capabilities,
    iter_hardware,
    normative_schema_path,
)


class ValidationResult:
    """Collected validation diagnostics.

    A result is intentionally small and serializable so it can be consumed by
    CI, editor integrations, or an AI agent without parsing terminal output.
    """

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @property
    def is_valid(self) -> bool:
        return not self.errors

    @property
    def ok(self) -> bool:
        return self.is_valid

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def merge(self, other: ValidationResult) -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.is_valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


class AxiomValidator:
    """Validate the shape and semantic invariants of an Axiom document."""

    known_top_level = {
        "axiom",
        "version",
        "schema_version",
        "robot",
        "hardware",
        "capabilities",
        "interfaces",
        "constraints",
        "requirements",
        "metadata",
        "extensions",
        "skill",
        "requires",
    }

    def __init__(self, *, allow_extensions: bool = False) -> None:
        self.allow_extensions = allow_extensions

    def validate(self, data: Mapping[str, Any]) -> ValidationResult:
        result = ValidationResult()
        if not isinstance(data, Mapping):
            result.add_error("document must be a mapping")
            return result

        if document_version(data) == "1.0":
            self._validate_normative_schema(data, result)
        self._validate_envelope(data, result)
        self._validate_robot(data, result)
        self._validate_hardware(data, result)
        self._validate_capabilities(data, result)
        self._validate_interfaces(data, result)
        self._validate_constraints(data, result)
        self._validate_requirements(data, result)
        self._validate_top_level_extensions(data, result)
        return result

    def lint(self, data: Mapping[str, Any]) -> ValidationResult:
        """Run validation plus maintainability and interoperability checks."""

        result = self.validate(data)
        if not isinstance(data, Mapping):
            return result

        for key in data:
            if key not in self.known_top_level and not str(key).startswith("x-"):
                result.add_warning(f"unknown top-level field: {key}")

        version = document_version(data)
        if version == "0.1":
            result.add_warning(
                "legacy schema_version 0.1 is accepted; migrate to axiom: '1.0'"
            )

        entries = [
            entry
            for entry in (*iter_hardware(data), *iter_capabilities(data))
            if entry.name
        ]
        for entry in entries:
            if not _is_identifier(entry.name):
                result.add_warning(
                    f"{entry.source}.name '{entry.name}' is not a portable capability identifier"
                )
            if entry.category in {"sensors", "actuators", "skills"} and not entry.spec.get(
                "description"
            ):
                result.add_warning(f"{entry.source} has no description")

        if any(entry.category == "actuators" for entry in entries):
            constraints = data.get("constraints", {})
            safety = constraints.get("safety") if isinstance(constraints, Mapping) else None
            if not safety:
                result.add_warning("actuators are declared but constraints.safety is empty")

        if not data.get("interfaces"):
            result.add_warning(
                "no interfaces declared; consumers may not know how to invoke skills"
            )
        return result

    def _validate_normative_schema(
        self, data: Mapping[str, Any], result: ValidationResult
    ) -> None:
        """Run the published JSON Schema before semantic validation."""

        try:
            schema = json.loads(normative_schema_path().read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            result.add_error(f"unable to load normative JSON Schema: {exc}")
            return
        if self.allow_extensions:
            # The published schema is strict at the envelope boundary. The
            # explicit CLI/library opt-in keeps arbitrary vendor fields out
            # of the default contract while preserving the legacy escape hatch.
            schema = dict(schema)
            schema["additionalProperties"] = True
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self._fallback_schema_check(data, result)
            return
        validator = Draft202012Validator(schema)
        for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
            path = ".".join(str(part) for part in error.path) or "$"
            result.add_error(f"schema {path}: {error.message}")

    @staticmethod
    def _fallback_schema_check(data: Mapping[str, Any], result: ValidationResult) -> None:
        if data.get("axiom") != "1.0":
            result.add_error("schema $: axiom must be '1.0'")
        robot = data.get("robot")
        if not isinstance(robot, Mapping):
            result.add_error("schema robot: must be an object")
        elif not isinstance(robot.get("name"), str) or not robot["name"].strip():
            result.add_error("schema robot.name: must be a non-empty string")
        if not isinstance(data.get("capabilities"), (Mapping, list)):
            result.add_error("schema capabilities: must be an object or array")

    def _validate_top_level_extensions(
        self, data: Mapping[str, Any], result: ValidationResult
    ) -> None:
        if self.allow_extensions or document_version(data) != "1.0":
            return
        for key in data:
            if key not in self.known_top_level and not str(key).startswith("x-"):
                result.add_error(
                    f"unknown top-level field: {key}; use an x- extension or --allow-extensions"
                )

    def _validate_envelope(self, data: Mapping[str, Any], result: ValidationResult) -> None:
        version = document_version(data)
        if version is None:
            result.add_error("missing axiom version (expected axiom: '1.0')")
        elif version not in SUPPORTED_VERSIONS:
            result.add_error(f"unsupported axiom version: {version}")

        if "capabilities" not in data:
            robot = data.get("robot")
            if isinstance(robot, Mapping) and "capabilities" in robot:
                result.add_warning(
                    "robot.capabilities is legacy; use the top-level capabilities section"
                )
            else:
                result.add_error("missing capabilities section")

        for key in ("hardware", "interfaces", "constraints", "requirements"):
            if key in data and not isinstance(data[key], (Mapping, list, str)):
                result.add_error(f"{key} must be a mapping, list, or string")

    def _validate_robot(self, data: Mapping[str, Any], result: ValidationResult) -> None:
        robot = data.get("robot")
        if robot is None:
            result.add_error("missing robot section")
            return
        if not isinstance(robot, Mapping):
            result.add_error("robot must be a mapping")
            return
        name = robot.get("name")
        if not isinstance(name, str) or not name.strip():
            result.add_error("robot.name must be a non-empty string")
        has = robot.get("has")
        if has is not None and not _valid_string_collection(has):
            result.add_error("robot.has must contain capability names")

    def _validate_hardware(self, data: Mapping[str, Any], result: ValidationResult) -> None:
        hardware = data.get("hardware")
        if hardware is None:
            return
        if not isinstance(hardware, (Mapping, list)):
            result.add_error("hardware must be a mapping or a list")
            return
        if isinstance(hardware, Mapping):
            for key, value in hardware.items():
                if not isinstance(key, str) or not key.strip():
                    result.add_error("hardware names must be non-empty strings")
                if key in KNOWN_CATEGORIES and not isinstance(value, (Mapping, list)):
                    result.add_error(f"hardware.{key} must be a mapping or list")

        for entry in iter_hardware(data):
            self._validate_entry(entry.source, entry.spec, result)

    def _validate_capabilities(self, data: Mapping[str, Any], result: ValidationResult) -> None:
        capabilities = data.get("capabilities")
        if capabilities is None:
            robot = data.get("robot", {})
            capabilities = robot.get("capabilities") if isinstance(robot, Mapping) else None
        if capabilities is None:
            return
        if not isinstance(capabilities, (Mapping, list)):
            result.add_error("capabilities must be a mapping or a list")
            return

        if isinstance(capabilities, Mapping) and not capabilities:
            result.add_warning("capabilities is empty")

        if isinstance(capabilities, Mapping):
            for key, value in capabilities.items():
                if key in KNOWN_CATEGORIES and not isinstance(value, (Mapping, list, str)):
                    result.add_error(f"capabilities.{key} must be a mapping, list, or string")
                elif key not in KNOWN_CATEGORIES and not isinstance(value, (Mapping, list, str)):
                    result.add_error(f"capabilities.{key} must be a mapping, list, or string")

        names: dict[str, str] = {}
        for entry in iter_capabilities(data):
            if not entry.name:
                result.add_error(f"{entry.source} must have a non-empty name")
            elif entry.name in names and names[entry.name] != entry.category:
                result.add_warning(
                    f"capability name '{entry.name}' is used by both "
                    f"{names[entry.name]} and {entry.category}"
                )
            else:
                names[entry.name] = entry.category
            self._validate_entry(entry.source, entry.spec, result)
            if entry.category not in KNOWN_CATEGORIES and entry.category != "capabilities":
                result.add_warning(
                    f"unknown capability category '{entry.category}' at {entry.source}"
                )

    def _validate_interfaces(self, data: Mapping[str, Any], result: ValidationResult) -> None:
        interfaces = data.get("interfaces")
        if interfaces is None:
            return
        if isinstance(interfaces, list):
            for index, item in enumerate(interfaces):
                if not isinstance(item, (Mapping, str)):
                    result.add_error(f"interfaces[{index}] must be a mapping or string")
                elif isinstance(item, Mapping) and not _entry_name(item):
                    result.add_error(f"interfaces[{index}].name must be non-empty")
        elif isinstance(interfaces, Mapping):
            for key, value in interfaces.items():
                if not isinstance(key, str) or not key.strip():
                    result.add_error("interface names must be non-empty strings")
                if not isinstance(value, (Mapping, str, type(None))):
                    result.add_error(f"interfaces.{key} must be a mapping or string")

    def _validate_constraints(self, data: Mapping[str, Any], result: ValidationResult) -> None:
        constraints = data.get("constraints")
        if constraints is None:
            return
        if isinstance(constraints, list):
            for index, item in enumerate(constraints):
                if not isinstance(item, (Mapping, str)):
                    result.add_error(f"constraints[{index}] must be a mapping or string")
            return
        if not isinstance(constraints, Mapping):
            result.add_error("constraints must be a mapping or list")
            return

        for key in ("safety", "safety_constraints"):
            if key in constraints and not isinstance(constraints[key], (Mapping, list, str)):
                result.add_error(f"constraints.{key} must be a mapping, list, or string")

        self._validate_ranges("constraints", constraints, result)

    def _validate_requirements(self, data: Mapping[str, Any], result: ValidationResult) -> None:
        requirements = data.get("requirements")
        if requirements is not None:
            self._validate_requirement_expression("requirements", requirements, result)
        requires = data.get("requires")
        if requires is not None:
            self._validate_requirement_expression("requires", requires, result)

        for entry in iter_capabilities(data):
            if "requires" in entry.spec:
                self._validate_requirement_expression(
                    f"{entry.source}.requires", entry.spec["requires"], result
                )

    def _validate_entry(
        self, path: str, spec: Mapping[str, Any], result: ValidationResult
    ) -> None:
        for key in ("actions", "properties", "inputs", "outputs"):
            value = spec.get(key)
            if value is None:
                continue
            if not isinstance(value, list):
                result.add_error(f"{path}.{key} must be a list")
                continue
            if key == "actions":
                for index, action in enumerate(value):
                    if not isinstance(action, (str, Mapping)):
                        result.add_error(f"{path}.actions[{index}] must be a string or mapping")
                    elif isinstance(action, str) and not action.strip():
                        result.add_error(f"{path}.actions[{index}] must not be empty")
            else:
                for index, item in enumerate(value):
                    if not isinstance(item, Mapping):
                        result.add_error(f"{path}.{key}[{index}] must be a mapping")

            if key == "properties":
                property_names: set[str] = set()
                for index, item in enumerate(value):
                    if isinstance(item, Mapping):
                        name = item.get("name")
                        if not isinstance(name, str) or not name.strip():
                            result.add_error(f"{path}.properties[{index}].name must be non-empty")
                        elif name in property_names:
                            result.add_error(f"{path}.properties contains duplicate name: {name}")
                        property_names.add(str(name))

        constraints = spec.get("constraints")
        if constraints is not None:
            if not isinstance(constraints, Mapping):
                result.add_error(f"{path}.constraints must be a mapping")
            else:
                self._validate_ranges(f"{path}.constraints", constraints, result)

        if "requires" in spec:
            self._validate_requirement_expression(f"{path}.requires", spec["requires"], result)

    def _validate_ranges(
        self, path: str, values: Mapping[str, Any], result: ValidationResult
    ) -> None:
        for key, value in values.items():
            if isinstance(value, Mapping):
                self._validate_ranges(f"{path}.{key}", value, result)

        for key, value in values.items():
            if not isinstance(key, str) or not key.endswith("_min"):
                continue
            maximum_key = f"{key[:-4]}_max"
            maximum = values.get(maximum_key)
            if _is_number(value) and _is_number(maximum) and maximum <= value:
                result.add_error(
                    f"{path}.{maximum_key} must be greater than {key}"
                )
        minimum = values.get("minimum")
        maximum = values.get("maximum")
        if _is_number(minimum) and _is_number(maximum) and maximum <= minimum:
            result.add_error(f"{path}.maximum must be greater than minimum")

    def _validate_requirement_expression(
        self, path: str, value: Any, result: ValidationResult
    ) -> None:
        if isinstance(value, str):
            if not value.strip():
                result.add_error(f"{path} must not contain an empty requirement")
            return
        if isinstance(value, list):
            for index, item in enumerate(value):
                self._validate_requirement_expression(f"{path}[{index}]", item, result)
            return
        if isinstance(value, Mapping):
            if not value:
                result.add_error(f"{path} must not be empty")
                return
            recognized = {"all", "any", "capability", "name", "id", "requires", "optional"}
            if not any(key in value for key in recognized):
                return
            for key in ("all", "any", "requires"):
                if key in value:
                    self._validate_requirement_expression(f"{path}.{key}", value[key], result)
            for key in ("capability", "name", "id"):
                if key in value:
                    self._validate_requirement_expression(f"{path}.{key}", value[key], result)
            return
        result.add_error(f"{path} must be a string, list, or mapping")


def _is_number(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


def _valid_string_collection(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return all(isinstance(item, str) and item.strip() for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and key.strip() for key in value)
    return False


def _entry_name(value: Mapping[str, Any]) -> str:
    for key in ("name", "id", "capability"):
        name = value.get(key)
        if isinstance(name, str) and name.strip():
            return name.strip()
    return ""


def _is_identifier(value: str) -> bool:
    return all(char.isalnum() or char in "._:/-" for char in value) and bool(value)


RobotCapabilityValidator = AxiomValidator
