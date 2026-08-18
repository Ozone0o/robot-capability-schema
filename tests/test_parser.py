"""Tests for the canonical Axiom YAML parser."""

from __future__ import annotations

import pytest

from axiom.schema import AxiomParseError, AxiomParser

VALID = """
axiom: "1.0"
robot:
  name: test_robot
capabilities:
  sensors:
    camera:
      type: rgb_camera
"""


def test_parse_canonical_contract() -> None:
    data = AxiomParser().parse_text(VALID)
    assert data["axiom"] == "1.0"
    assert data["robot"]["name"] == "test_robot"


def test_parse_allows_requirement_document_without_robot() -> None:
    data = AxiomParser().parse_text(
        'axiom: "1.0"\nskill:\n  name: inspect\n  requires: [camera]\n',
        require_robot=False,
    )
    assert data["skill"]["name"] == "inspect"


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("robot: {}\ncapabilities: {}\n", "missing axiom version"),
        ('axiom: "9.9"\nrobot: {}\ncapabilities: {}\n', "unsupported axiom version"),
        ('axiom: "1.0"\ncapabilities: {}\n', "missing robot section"),
        ('axiom: "1.0"\nrobot: {name: test}\n', "missing capabilities section"),
    ],
)
def test_parse_rejects_invalid_envelopes(text: str, message: str) -> None:
    with pytest.raises(AxiomParseError, match=message):
        AxiomParser().parse_text(text)


def test_parse_rejects_invalid_yaml() -> None:
    with pytest.raises(AxiomParseError, match="YAML syntax error"):
        AxiomParser().parse_text("axiom: [\n")
