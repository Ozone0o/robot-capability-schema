"""An embeddable in-memory registry for Axiom robot contracts.

The registry is intentionally storage-agnostic.  A service can put this
behind SQLite, object storage, or an HTTP API without changing the contract
model or matching semantics.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from .matching import CompatibilityResult, match_requirements
from .schema import AxiomParser
from .validator import AxiomValidator


class AxiomRegistry:
    """Store and query validated robot capability contracts by name."""

    def __init__(self, validator: AxiomValidator | None = None) -> None:
        self._documents: dict[str, dict[str, Any]] = {}
        self._validator = validator or AxiomValidator()

    def register(self, document: Mapping[str, Any], *, name: str | None = None) -> str:
        if not isinstance(document, Mapping):
            raise ValueError("a contract document must be a mapping")
        candidate = deepcopy(dict(document))
        validation = self._validator.validate(candidate)
        if not validation.is_valid:
            details = "; ".join(validation.errors)
            raise ValueError(f"invalid Axiom contract: {details}")

        robot = candidate.get("robot", {})
        robot_name = name or (robot.get("name") if isinstance(robot, Mapping) else None)
        if not isinstance(robot_name, str) or not robot_name.strip():
            raise ValueError("a robot name is required to register a contract")
        key = robot_name.strip()
        # Registry state must not alias either the caller's nested mappings or
        # the mappings returned by get/list.
        self._documents[key] = candidate
        return key

    def register_file(self, path: str | Path) -> str:
        document = AxiomParser().parse(path)
        return self.register(document)

    def get(self, name: str) -> dict[str, Any] | None:
        document = self._documents.get(name)
        return deepcopy(document) if document is not None else None

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._documents))

    def list(self) -> list[dict[str, Any]]:
        return [deepcopy(self._documents[name]) for name in self.names()]

    def match(
        self, requirements: Mapping[str, Any] | Any, *, skill: str | None = None
    ) -> dict[str, CompatibilityResult]:
        return {
            name: match_requirements(document, requirements, skill=skill)
            for name, document in self._documents.items()
        }
