"""Compatibility imports for applications that call the loader a parser."""

from .schema import (
    AXIOM_VERSION,
    SUPPORTED_VERSIONS,
    AxiomDocument,
    AxiomParseError,
    AxiomParser,
    Capability,
    document_version,
    parse_document,
)

ParseError = AxiomParseError
Parser = AxiomParser

__all__ = [
    "AXIOM_VERSION",
    "SUPPORTED_VERSIONS",
    "AxiomDocument",
    "AxiomParseError",
    "AxiomParser",
    "Capability",
    "ParseError",
    "Parser",
    "document_version",
    "parse_document",
]
