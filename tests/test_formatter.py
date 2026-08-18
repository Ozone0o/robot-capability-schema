"""Tests for the machine-readable Axiom validation result."""

from axiom.validator import ValidationResult


def test_validation_result_is_serializable() -> None:
    result = ValidationResult()
    result.add_warning("missing description")
    assert result.is_valid
    assert result.to_dict() == {
        "valid": True,
        "errors": [],
        "warnings": ["missing description"],
    }


def test_validation_result_error_changes_validity() -> None:
    result = ValidationResult()
    result.add_error("invalid contract")
    assert not result.is_valid
    assert result.to_dict()["errors"] == ["invalid contract"]
