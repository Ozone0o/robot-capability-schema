"""The Axiom document model and YAML loader.

The loader deliberately returns ordinary Python mappings.  Axiom is a
contract format, not a runtime object model: callers should be able to pass
the parsed document to validators, registries, or their own tooling without
having to depend on a large framework.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

AXIOM_VERSION = "1.0"
NORMATIVE_SCHEMA_FILENAME = "axiom-1.0.schema.json"
SUPPORTED_VERSIONS = frozenset({"1.0", "0.1"})
KNOWN_CATEGORIES = frozenset({"sensors", "actuators", "skills", "limitations"})


class AxiomParseError(ValueError):
    """Raised when a file cannot be read or is not an Axiom document."""


@dataclass(frozen=True)
class Capability:
    """A named capability discovered in an Axiom document."""

    name: str
    category: str
    spec: dict[str, Any]
    source: str = "capabilities"

    @property
    def requires(self) -> Any:
        """Return the raw requirement expression for this capability."""

        return self.spec.get("requires", self.spec.get("requirements", []))


@dataclass(frozen=True)
class Interface:
    """A named transport or software interface exposed by a robot."""

    name: str
    spec: dict[str, Any]


@dataclass(frozen=True)
class AxiomDocument:
    """A parsed Axiom document with convenient, derived views."""

    data: dict[str, Any]
    source: Path | None = None

    @property
    def version(self) -> str | None:
        return document_version(self.data)

    @property
    def robot(self) -> dict[str, Any]:
        value = self.data.get("robot", {})
        return dict(value) if isinstance(value, Mapping) else {}

    @property
    def capabilities(self) -> tuple[Capability, ...]:
        return tuple(iter_capabilities(self.data))

    @property
    def hardware(self) -> tuple[Capability, ...]:
        return tuple(iter_hardware(self.data))

    @property
    def interfaces(self) -> tuple[Interface, ...]:
        return tuple(iter_interfaces(self.data))

    @property
    def available_names(self) -> tuple[str, ...]:
        names = available_capabilities(self.data)
        return tuple(sorted(names))


class AxiomParser:
    """Parse and perform structural checks on an Axiom YAML document."""

    SUPPORTED_VERSIONS = SUPPORTED_VERSIONS

    def parse(self, path: str | Path, *, require_robot: bool = True) -> dict[str, Any]:
        """Read *path* and return its YAML mapping.

        ``require_robot=False`` is useful for a standalone skill requirement
        manifest passed to ``axiom match``.  Robot contracts use the default.
        """

        file_path = Path(path)
        try:
            text = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AxiomParseError(f"cannot read {file_path}: {exc}") from exc
        return self.parse_text(text, require_robot=require_robot)

    def parse_text(self, text: str, *, require_robot: bool = True) -> dict[str, Any]:
        """Parse YAML text and run Axiom's structural checks."""

        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise AxiomParseError(f"YAML syntax error: {exc}") from exc
        return self.parse_data(data, require_robot=require_robot)

    def parse_data(
        self, data: Any, *, require_robot: bool = True, copy: bool = True
    ) -> dict[str, Any]:
        """Validate the document envelope and return a plain mapping."""

        if not isinstance(data, Mapping):
            raise AxiomParseError("Axiom document must be a mapping")

        result = deepcopy(dict(data)) if copy else dict(data)
        version = document_version(result)
        if version is None:
            raise AxiomParseError("missing axiom version (expected axiom: '1.0')")
        if version not in self.SUPPORTED_VERSIONS:
            supported = ", ".join(sorted(self.SUPPORTED_VERSIONS))
            raise AxiomParseError(f"unsupported axiom version: {version}; supported: {supported}")

        if require_robot:
            self._check_robot(result)
            self._check_capabilities(result)
        return result

    @staticmethod
    def _check_robot(data: Mapping[str, Any]) -> None:
        if "robot" not in data:
            raise AxiomParseError("missing robot section")
        robot = data["robot"]
        if not isinstance(robot, Mapping):
            raise AxiomParseError("robot must be a mapping")
        name = robot.get("name")
        if not isinstance(name, str) or not name.strip():
            raise AxiomParseError("robot.name must be a non-empty string")

    @staticmethod
    def _check_capabilities(data: Mapping[str, Any]) -> None:
        capabilities = data.get("capabilities")
        if capabilities is None:
            robot = data.get("robot", {})
            if isinstance(robot, Mapping) and "capabilities" in robot:
                capabilities = robot["capabilities"]
            else:
                raise AxiomParseError("missing capabilities section")
        if not isinstance(capabilities, (Mapping, list)):
            raise AxiomParseError("capabilities must be a mapping or a list")


def document_version(data: Mapping[str, Any]) -> str | None:
    """Return the version from any accepted envelope spelling."""

    for key in ("axiom", "schema_version", "version"):
        value = data.get(key)
        if value is not None:
            return str(value)
    return None


def parse_document(path: str | Path, *, require_robot: bool = True) -> AxiomDocument:
    """Parse *path* and return an :class:`AxiomDocument`."""

    parser = AxiomParser()
    return AxiomDocument(parser.parse(path, require_robot=require_robot), Path(path))


def _canonical_category(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip().lower().replace("-", "_")
    aliases = {
        "sensor": "sensors",
        "sensors": "sensors",
        "actuator": "actuators",
        "actuators": "actuators",
        "action": "actuators",
        "actions": "actuators",
        "skill": "skills",
        "skills": "skills",
        "behavior": "skills",
        "behaviors": "skills",
        "limitation": "limitations",
        "limitations": "limitations",
    }
    if text in aliases:
        return aliases[text]
    if text.endswith("_sensor") or text in {"camera", "rgb_camera", "lidar", "imu"}:
        return "sensors"
    if text.endswith("_actuator") or text in {"arm", "gripper", "pan_tilt", "mobile_base"}:
        return "actuators"
    return None


def _entry_name(value: Mapping[str, Any], fallback: str = "") -> str:
    for key in ("name", "id", "capability"):
        name = value.get(key)
        if isinstance(name, str) and name.strip():
            return name.strip()
    return fallback


def _entry_spec(value: Mapping[str, Any], name: str) -> dict[str, Any]:
    spec = dict(value)
    if name and not spec.get("name"):
        spec["name"] = name
    return spec


def _iter_named_entries(
    value: Any, category: str, source: str
) -> Iterator[Capability]:
    """Yield entries from either a list or a name-to-spec mapping."""

    if isinstance(value, str):
        yield Capability(value.strip(), category, {"name": value.strip()}, source)
        return

    if isinstance(value, list):
        for index, item in enumerate(value):
            if isinstance(item, str):
                name = item.strip()
                yield Capability(name, category, {"name": name}, f"{source}[{index}]")
            elif isinstance(item, Mapping):
                name = _entry_name(item)
                yield Capability(name, category, _entry_spec(item, name), f"{source}[{index}]")
        return

    if not isinstance(value, Mapping):
        return

    # A mapping with a name is a single entry.  Otherwise it is a registry of
    # named entries, e.g. ``sensors: {camera: {type: rgb}}``.
    if any(key in value for key in ("name", "id", "capability")):
        name = _entry_name(value)
        yield Capability(name, category, _entry_spec(value, name), source)
        return

    for name_key, item in value.items():
        name = str(name_key)
        if isinstance(item, Mapping):
            spec = _entry_spec(item, name)
        elif item is None:
            spec = {"name": name}
        else:
            spec = {"name": name, "type": item}
        yield Capability(name, category, spec, f"{source}.{name}")


def _infer_category(spec: Mapping[str, Any], default: str = "capabilities") -> str:
    for key in ("category", "type", "kind"):
        category = _canonical_category(spec.get(key))
        if category:
            return category
    return default


def _looks_like_entry(value: Any) -> bool:
    """Return whether a mapping is a capability spec, not a category registry.

    Legacy Axiom documents commonly use names such as ``camera`` as keys and
    put fields like ``kind`` and ``properties`` below them.  Those names also
    happen to be accepted category aliases, so the shape of the value must
    take precedence over the key spelling.
    """

    return isinstance(value, Mapping) and any(
        key in value
        for key in (
            "name",
            "id",
            "capability",
            "kind",
            "type",
            "description",
            "properties",
            "constraints",
            "actions",
            "requires",
            "inputs",
            "outputs",
        )
    )


def iter_capabilities(data: Mapping[str, Any]) -> Iterator[Capability]:
    """Yield normalized capabilities from canonical and legacy layouts."""

    raw = data.get("capabilities")
    if raw is None:
        robot = data.get("robot", {})
        raw = robot.get("capabilities", {}) if isinstance(robot, Mapping) else {}

    if isinstance(raw, list):
        for index, item in enumerate(raw):
            if isinstance(item, Mapping):
                name = _entry_name(item)
                category = _infer_category(item)
                yield Capability(name, category, _entry_spec(item, name), f"capabilities[{index}]")
        return

    if not isinstance(raw, Mapping):
        return

    for key, value in raw.items():
        category = _canonical_category(key)
        if category and not _looks_like_entry(value):
            yield from _iter_named_entries(value, category, f"capabilities.{key}")
            continue

        if isinstance(value, Mapping):
            inferred = _infer_category(value)
            name = _entry_name(value, str(key))
            yield Capability(name, inferred, _entry_spec(value, name), f"capabilities.{key}")
        elif isinstance(value, list):
            yield from _iter_named_entries(value, "capabilities", f"capabilities.{key}")
        else:
            yield Capability(str(key), "capabilities", {"name": str(key), "type": value})


def iter_hardware(data: Mapping[str, Any]) -> Iterator[Capability]:
    """Yield named hardware components, including sensors and actuators."""

    raw = data.get("hardware", {})
    if not isinstance(raw, Mapping):
        return

    for key, value in raw.items():
        category = _canonical_category(key)
        if category and not _looks_like_entry(value):
            yield from _iter_named_entries(value, category, f"hardware.{key}")
        elif isinstance(value, Mapping):
            inferred = _infer_category(value, "hardware")
            name = _entry_name(value, str(key))
            yield Capability(name, inferred, _entry_spec(value, name), f"hardware.{key}")
        elif isinstance(value, list):
            yield from _iter_named_entries(value, "hardware", f"hardware.{key}")
        else:
            yield Capability(str(key), "hardware", {"name": str(key), "type": value})


def iter_interfaces(data: Mapping[str, Any]) -> Iterator[Interface]:
    """Yield interfaces from list or mapping notation."""

    raw = data.get("interfaces", [])
    if isinstance(raw, list):
        for index, item in enumerate(raw):
            if isinstance(item, Mapping):
                name = _entry_name(item, f"interface-{index + 1}")
                yield Interface(name, _entry_spec(item, name))
            elif isinstance(item, str):
                yield Interface(item, {"name": item})
        return
    if not isinstance(raw, Mapping):
        return
    if any(key in raw for key in ("name", "id", "protocol", "type")):
        name = _entry_name(raw, str(raw.get("protocol", "interface")))
        yield Interface(name, _entry_spec(raw, name))
        return
    for key, value in raw.items():
        spec = dict(value) if isinstance(value, Mapping) else {"protocol": value}
        yield Interface(str(key), _entry_spec(spec, str(key)))


def available_capabilities(data: Mapping[str, Any]) -> set[str]:
    """Return the names a robot can provide for compatibility matching."""

    names: set[str] = set()
    robot = data.get("robot", {})
    if isinstance(robot, Mapping):
        has = robot.get("has", [])
        if isinstance(has, str):
            names.add(has)
        elif isinstance(has, list):
            names.update(item for item in has if isinstance(item, str))
        elif isinstance(has, Mapping):
            names.update(str(key) for key in has)

    for entry in iter_hardware(data):
        if entry.name:
            names.add(entry.name)
    for entry in iter_capabilities(data):
        if entry.name and entry.category != "limitations":
            names.add(entry.name)
    return names


def capability_map(data: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Build a deterministic semantic map used by ``axiom diff``."""

    result: dict[str, dict[str, Any]] = {}
    for entry in iter_hardware(data):
        if entry.name:
            result[f"hardware.{entry.category}.{entry.name}"] = dict(entry.spec)
    for entry in iter_capabilities(data):
        if entry.name:
            result[f"capabilities.{entry.category}.{entry.name}"] = dict(entry.spec)
    return result


def text_value(value: Any) -> str:
    """Format a YAML value for human-readable generated documentation."""

    if isinstance(value, (dict, list)):
        return yaml.safe_dump(value, allow_unicode=True, default_flow_style=True).strip()
    if value is None:
        return ""
    return str(value)


def normative_schema_path() -> Path:
    """Locate the repository or installed copy of the normative schema."""

    import sys

    candidates = (
        Path(__file__).resolve().parents[2] / "schema" / NORMATIVE_SCHEMA_FILENAME,
        Path(__file__).resolve().parents[3] / "schema" / NORMATIVE_SCHEMA_FILENAME,
        Path(sys.prefix) / "share" / "axiom" / "schema" / NORMATIVE_SCHEMA_FILENAME,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise AxiomParseError(
        f"normative schema is not installed ({NORMATIVE_SCHEMA_FILENAME})"
    )
