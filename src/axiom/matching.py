"""Capability requirement extraction and compatibility checking."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .schema import available_capabilities, iter_capabilities


@dataclass
class RequirementSet:
    """A normalized capability requirement expression."""

    required: list[str] = field(default_factory=list)
    alternatives: list[list[str]] = field(default_factory=list)
    optional: list[str] = field(default_factory=list)

    @property
    def requirements(self) -> list[str]:
        """Compatibility alias for callers that prefer this name."""

        return self.required

    def add(self, name: str, *, is_optional: bool = False) -> None:
        name = name.strip()
        if not name:
            return
        target = self.optional if is_optional else self.required
        if name not in target:
            target.append(name)


@dataclass(frozen=True)
class CompatibilityResult:
    """Result returned by :func:`match_requirements`."""

    compatible: bool
    required: tuple[str, ...]
    available: tuple[str, ...]
    matched: tuple[str, ...]
    missing: tuple[str, ...]
    optional_missing: tuple[str, ...] = ()
    alternatives: tuple[tuple[str, ...], ...] = ()

    @property
    def is_compatible(self) -> bool:
        return self.compatible

    @property
    def missing_requirements(self) -> tuple[str, ...]:
        return self.missing

    def to_dict(self) -> dict[str, Any]:
        return {
            "compatible": self.compatible,
            "required": list(self.required),
            "available": list(self.available),
            "matched": list(self.matched),
            "missing": list(self.missing),
            "optional_missing": list(self.optional_missing),
            "alternatives": [list(group) for group in self.alternatives],
        }


def requirements_from(value: Any) -> RequirementSet:
    """Normalize strings, lists, and ``all``/``any`` requirement mappings."""

    result = RequirementSet()
    _collect_requirements(value, result)
    return result


def extract_requirements(data: Mapping[str, Any], skill: str | None = None) -> RequirementSet:
    """Extract a requirement set from a skill manifest or robot contract."""

    if skill:
        for entry in iter_capabilities(data):
            if entry.name == skill and entry.category == "skills":
                return requirements_from(entry.requires)
        singular = data.get("skill")
        if isinstance(singular, Mapping) and singular.get("name") == skill:
            return requirements_from(singular.get("requires", singular.get("requirements", [])))
        raise ValueError(f"skill not found: {skill}")

    singular = data.get("skill")
    if isinstance(singular, Mapping):
        return requirements_from(singular.get("requires", singular.get("requirements", [])))

    if "requires" in data:
        return requirements_from(data["requires"])

    if "requirements" in data:
        return requirements_from(data["requirements"])

    skills = [entry for entry in iter_capabilities(data) if entry.category == "skills"]
    if len(skills) == 1:
        return requirements_from(skills[0].requires)
    result = RequirementSet()
    for entry in skills:
        _collect_requirements(entry.requires, result)
    return result


def match_requirements(
    robot: Mapping[str, Any],
    requirement_document: Mapping[str, Any] | None = None,
    *,
    requirements: Any = None,
    skill: str | None = None,
) -> CompatibilityResult:
    """Check whether *robot* satisfies a capability requirement set."""

    if requirements is not None:
        required_set = (
            requirements
            if isinstance(requirements, RequirementSet)
            else requirements_from(requirements)
        )
    elif requirement_document is not None:
        required_set = extract_requirements(requirement_document, skill=skill)
    else:
        required_set = extract_requirements(robot, skill=skill)

    available = available_capabilities(robot)
    matched = [name for name in required_set.required if name in available]
    missing = [name for name in required_set.required if name not in available]
    optional_missing = [name for name in required_set.optional if name not in available]
    failed_alternatives: list[str] = []
    for group in required_set.alternatives:
        if not any(name in available for name in group):
            failed_alternatives.append(f"one of ({', '.join(group)})")

    missing.extend(failed_alternatives)
    return CompatibilityResult(
        compatible=not missing,
        required=tuple(required_set.required),
        available=tuple(sorted(available)),
        matched=tuple(matched),
        missing=tuple(missing),
        optional_missing=tuple(optional_missing),
        alternatives=tuple(tuple(group) for group in required_set.alternatives),
    )


def _collect_requirements(value: Any, result: RequirementSet, *, optional: bool = False) -> None:
    if isinstance(value, str):
        result.add(value, is_optional=optional)
        return
    if isinstance(value, (tuple, list, set)):
        for item in value:
            _collect_requirements(item, result, optional=optional)
        return
    if not isinstance(value, Mapping):
        return

    is_optional = optional or bool(value.get("optional", False))
    if "all" in value:
        _collect_requirements(value["all"], result, optional=is_optional)
    if "requires" in value:
        _collect_requirements(value["requires"], result, optional=is_optional)
    if "any" in value:
        group = _requirement_names(value["any"])
        if group:
            result.alternatives.append(group)

    for key in ("capability", "name", "id"):
        if key in value:
            _collect_requirements(value[key], result, optional=is_optional)

    # A concise mapping such as ``{camera: {optional: true}}`` is useful in
    # hand-written manifests and costs little to support.
    known = {"all", "any", "requires", "capability", "name", "id", "optional"}
    for key, nested in value.items():
        if key not in known and isinstance(key, str):
            _collect_requirements(key, result, optional=is_optional)
            if isinstance(nested, Mapping) and nested.get("optional"):
                if key in result.required:
                    result.required.remove(key)
                result.add(key, is_optional=True)


def _requirement_names(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (tuple, list, set)):
        names: list[str] = []
        for item in value:
            names.extend(_requirement_names(item))
        return list(dict.fromkeys(names))
    if isinstance(value, Mapping):
        for key in ("capability", "name", "id"):
            if key in value:
                return _requirement_names(value[key])
        return [key for key in value if isinstance(key, str) and key.strip()]
    return []


def format_compatibility(result: CompatibilityResult) -> str:
    """Format a match result for humans and shell transcripts."""

    lines = ["Compatible" if result.compatible else "Incompatible"]
    if result.required:
        lines.append(f"Required capabilities: {', '.join(result.required)}")
    if result.matched:
        lines.append(f"Matched: {', '.join(result.matched)}")
    if result.missing:
        lines.append("Missing requirements:")
        lines.extend(f"  - {item}" for item in result.missing)
    if result.optional_missing:
        lines.append(f"Optional requirements not present: {', '.join(result.optional_missing)}")
    return "\n".join(lines)


check_compatibility = match_requirements
