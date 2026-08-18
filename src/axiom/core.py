"""Small public facade for applications embedding Axiom."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .matching import CompatibilityResult, match_requirements
from .schema import AxiomDocument, AxiomParser, parse_document
from .validator import AxiomValidator, ValidationResult


def load(path: str | Path, *, validate: bool = False) -> AxiomDocument:
    """Load an Axiom document, optionally failing on validation errors."""

    document = parse_document(path)
    if validate:
        result = AxiomValidator().validate(document.data)
        if not result.is_valid:
            raise ValueError("invalid Axiom document: " + "; ".join(result.errors))
    return document


def validate(data: Mapping[str, Any]) -> ValidationResult:
    """Validate an in-memory contract."""

    return AxiomValidator().validate(data)


def match(
    robot: Mapping[str, Any],
    requirements: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> CompatibilityResult:
    """Check a robot against another document or an explicit requirement set."""

    return match_requirements(robot, requirements, **kwargs)


__all__ = ["AxiomDocument", "AxiomParser", "load", "match", "parse_document", "validate"]
