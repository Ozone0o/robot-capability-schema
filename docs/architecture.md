# Axiom architecture

Axiom keeps the contract boundary independent from the transport or runtime
used by a robot. The reference implementation follows five logical layers.

| Layer | Responsibility | Reference module |
| --- | --- | --- |
| `axiom-schema` | YAML loading, version envelopes, canonical views | `axiom.schema` |
| `axiom-core` | Document, capability, and interface model | `axiom.core` |
| `axiom-validator` | Structural, semantic, safety, and lint diagnostics | `axiom.validator` |
| `axiom-codegen` | Typed integration interfaces and JSON artifacts | `axiom.codegen` |
| `axiom-registry` | Register, discover, and match robot contracts | `axiom.registry` |

The layers communicate through ordinary mappings and small result objects.
That keeps the format usable from Python, a CLI, an HTTP registry, or an AI
agent tool without requiring a robot runtime.

## Data flow

```text
YAML / JSON
    │
    ▼
axiom-schema ──► normalized capability view
    │                         │
    ├──► axiom-validator      ├──► axiom-codegen
    ├──► axiom-registry       ├──► Markdown docs
    └──► compatibility        └──► typed SDK interface
```

Validation is intentionally separate from parsing. Parsing answers “can this
be read as an Axiom document?”; validation answers “is the contract complete
and internally consistent?”. Compatibility is a query over a validated (or
intentionally partially validated) robot document, so a platform can explain
missing requirements instead of returning a boolean with no context.
