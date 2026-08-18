"""Axiom: the capability contract for robots."""

from __future__ import annotations

from .codegen import generate_python, generate_typescript
from .core import AxiomDocument, AxiomParser, load, match, parse_document, validate
from .docs import generate_markdown
from .matching import CompatibilityResult, RequirementSet, match_requirements
from .registry import AxiomRegistry
from .schema import AXIOM_VERSION, AxiomParseError, Capability
from .validator import AxiomValidator, ValidationResult

__version__ = "0.1.0"

__all__ = [
    "AXIOM_VERSION",
    "AxiomDocument",
    "AxiomParseError",
    "AxiomParser",
    "AxiomValidator",
    "AxiomRegistry",
    "Capability",
    "CompatibilityResult",
    "RequirementSet",
    "ValidationResult",
    "load",
    "match",
    "match_requirements",
    "parse_document",
    "generate_markdown",
    "generate_python",
    "generate_typescript",
    "validate",
]
