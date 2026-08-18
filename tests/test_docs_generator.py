"""Tests for canonical Markdown documentation generation."""

from axiom.docs import generate_markdown


def test_generates_canonical_sections_and_entries() -> None:
    markdown = generate_markdown(
        {
            "axiom": "1.0",
            "robot": {"name": "test_robot", "description": "Test robot"},
            "capabilities": {
                "skills": {
                    "inspect": {
                        "description": "Inspect a shelf",
                        "inputs": [{"name": "shelf_id", "type": "string"}],
                    }
                }
            },
            "constraints": {"safety": ["stop when a person is detected"]},
        }
    )
    assert "# test_robot" in markdown
    assert "Axiom capability contract" in markdown
    assert "## Capabilities" in markdown
    assert "inspect" in markdown
    assert "## Constraints and safety" in markdown
