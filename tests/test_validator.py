"""Tests for normative-schema and semantic validation."""

from __future__ import annotations

from axiom.validator import AxiomValidator


def contract(capabilities: dict) -> dict:
    return {
        "axiom": "1.0",
        "robot": {"name": "test"},
        "capabilities": capabilities,
    }


def test_valid_canonical_contract() -> None:
    result = AxiomValidator().validate(
        contract({"sensors": {"camera": {"type": "rgb_camera"}}})
    )
    assert result.is_valid


def test_duplicate_property_name_is_rejected() -> None:
    result = AxiomValidator().validate(
        contract(
            {
                "sensors": {
                    "camera": {
                        "type": "rgb_camera",
                        "properties": [
                            {"name": "fps", "value": 30},
                            {"name": "fps", "value": 60},
                        ],
                    }
                }
            }
        )
    )
    assert not result.is_valid
    assert any("duplicate name" in error for error in result.errors)


def test_invalid_range_is_rejected() -> None:
    result = AxiomValidator().validate(
        contract(
            {
                "actuators": {
                    "head": {
                        "constraints": {"yaw_min": 90, "yaw_max": -90}
                    }
                }
            }
        )
    )
    assert not result.is_valid
    assert any("yaw_max must be greater" in error for error in result.errors)


def test_unknown_top_level_field_requires_explicit_extension() -> None:
    document = contract({})
    document["vendor_field"] = True
    strict = AxiomValidator().validate(document)
    relaxed = AxiomValidator(allow_extensions=True).validate(document)
    assert not strict.is_valid
    assert relaxed.is_valid


def test_x_extension_is_allowed() -> None:
    document = contract({})
    document["x-vendor"] = {"firmware": "1.2"}
    assert AxiomValidator().validate(document).is_valid


def test_normative_schema_rejects_unknown_top_level_field() -> None:
    document = contract({})
    document["vendor_field"] = True

    result = AxiomValidator().validate(document)

    assert any("vendor_field" in error for error in result.errors)
