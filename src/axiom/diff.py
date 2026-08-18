"""Semantic compatibility diffs between two Axiom contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .schema import capability_map, document_version


@dataclass(frozen=True)
class DiffResult:
    """Added, removed, and changed capability paths."""

    added: tuple[str, ...]
    removed: tuple[str, ...]
    changed: tuple[str, ...]
    old_version: str | None = None
    new_version: str | None = None

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "added": list(self.added),
            "removed": list(self.removed),
            "changed": list(self.changed),
            "old_version": self.old_version,
            "new_version": self.new_version,
            "has_changes": self.has_changes,
        }


def diff_documents(old: Mapping[str, Any], new: Mapping[str, Any]) -> DiffResult:
    """Compare hardware and capability contracts, ignoring YAML ordering."""

    old_map = capability_map(old)
    new_map = capability_map(new)
    old_keys = set(old_map)
    new_keys = set(new_map)
    added = tuple(sorted(new_keys - old_keys))
    removed = tuple(sorted(old_keys - new_keys))
    changed = tuple(sorted(key for key in old_keys & new_keys if old_map[key] != new_map[key]))
    return DiffResult(added, removed, changed, document_version(old), document_version(new))


def format_diff(result: DiffResult) -> str:
    """Format a diff in a review-friendly form."""

    lines = ["Axiom contract diff"]
    if result.old_version != result.new_version:
        old_version = result.old_version or "unknown"
        new_version = result.new_version or "unknown"
        lines.append(f"Version: {old_version} -> {new_version}")
    for title, values, marker in (
        ("Added capabilities", result.added, "+"),
        ("Removed capabilities", result.removed, "-"),
        ("Changed capabilities", result.changed, "~"),
    ):
        if values:
            lines.extend([f"\n{title}:", *(f"  {marker} {value}" for value in values)])
    if not result.has_changes:
        lines.append("\nNo capability changes.")
    return "\n".join(lines)


diff = diff_documents
