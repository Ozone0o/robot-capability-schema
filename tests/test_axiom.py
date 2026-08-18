"""Reference behavior tests for the Axiom public layer."""

from __future__ import annotations

from pathlib import Path

import pytest

from axiom.codegen import generate_python, generate_typescript
from axiom.diff import diff_documents
from axiom.docs import generate_markdown
from axiom.matching import match_requirements
from axiom.registry import AxiomRegistry
from axiom.schema import AxiomParser, iter_capabilities
from axiom.validator import AxiomValidator

ROOT = Path(__file__).parents[1]


def test_canonical_contract_validates() -> None:
    parser = AxiomParser()
    data = parser.parse(ROOT / "examples" / "robot.yaml")

    result = AxiomValidator().validate(data)

    assert result.is_valid
    assert {"camera", "arm", "pick_and_place"}.issubset(
        {entry.name for entry in iter_capabilities(data)}
    )


def test_match_reports_missing_and_explicit_requirements_can_match() -> None:
    parser = AxiomParser()
    robot = parser.parse(ROOT / "examples" / "robot.yaml")
    skill = parser.parse(ROOT / "examples" / "skill-requirements.yaml", require_robot=False)

    result = match_requirements(robot, skill)
    assert not result.compatible
    assert "one of (lidar, depth_camera)" in result.missing

    compatible = match_requirements(robot, requirements=["camera", "arm"])
    assert compatible.compatible
    assert compatible.missing == ()


def test_docs_codegen_and_diff_are_deterministic() -> None:
    parser = AxiomParser()
    data = parser.parse(ROOT / "examples" / "robot.yaml")
    markdown = generate_markdown(data)
    python = generate_python(data)
    typescript = generate_typescript(data)

    assert "Axiom capability contract" in markdown
    assert "## Constraints and safety" in markdown
    assert "class WarehouseScoutCapabilities" in python
    assert "pick_and_place" in python
    assert "interface WarehouseScoutCapabilities" in typescript
    assert not diff_documents(data, data).has_changes


def test_registry_validates_and_isolates_nested_mutations() -> None:
    document = {
        "axiom": "1.0",
        "robot": {"name": "warehouse-scout"},
        "capabilities": {"sensors": {"camera": {"type": "rgb"}}},
    }
    registry = AxiomRegistry()

    assert registry.register(document) == "warehouse-scout"
    document["robot"]["name"] = "mutated-input"
    stored = registry.get("warehouse-scout")
    assert stored is not None
    stored["capabilities"]["sensors"]["camera"]["type"] = "mutated-result"

    assert registry.get("warehouse-scout")["robot"]["name"] == "warehouse-scout"
    assert (
        registry.get("warehouse-scout")["capabilities"]["sensors"]["camera"]["type"]
        == "rgb"
    )


def test_registry_rejects_invalid_contract() -> None:
    with pytest.raises(ValueError, match="invalid Axiom contract"):
        AxiomRegistry().register({"axiom": "1.0", "robot": {"name": "broken"}})
