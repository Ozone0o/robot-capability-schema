# Axiom

## The capability contract for robots.

Axiom is an open capability specification framework for robots.

> A robot should describe what it can do in a machine-readable way.

```text
robot.yaml
    ↓
validation
    ↓
documentation
    ↓
code generation
    ↓
compatibility checking
```

Axiom is a robot capability contract: a shared language for robot companies,
robot platforms, and AI agents to discover what a robot can do, what it needs,
how it can be invoked, and where it must not operate. It is inspired by the
role OpenAPI plays for Web APIs, with a schema designed around hardware,
skills, interfaces, limitations, and safety.

## A contract in one file

```yaml
axiom: "1.0"

robot:
  name: warehouse-scout
  manufacturer: Axiom Robotics
  model: Scout-1
  description: Autonomous inspection robot for indoor warehouses.

hardware:
  sensors:
    camera:
      type: rgb_camera
      description: Forward-facing RGB camera.
      resolution: 1920x1080
      fps: 30
  actuators:
    arm:
      type: six_dof_arm
      payload_kg: 5

capabilities:
  skills:
    inspect_shelf:
      description: Capture and inspect a shelf image.
      requires: [camera]
      inputs:
        - name: shelf_id
          type: string
      outputs:
        - name: report
          type: object
  limitations:
    - name: indoor_only
      description: Not rated for rain or unstructured outdoor terrain.

interfaces:
  - name: ros2
    protocol: ros2
    namespace: /warehouse_scout
  - name: http
    protocol: http
    endpoint: http://robot.local:8080

constraints:
  safety:
    - Stop the arm when a person enters the operating envelope.
    - Maximum arm payload is 5 kg.

requirements:
  - power: 24V DC
  - network: warehouse VLAN
```

The schema accepts both mapping and list notation. For example, the same
sensor can be written as `camera: {type: rgb_camera}` or as
`- name: camera\n  type: rgb_camera`. Names are stable identifiers; descriptions,
parameters, and vendor extensions are ordinary YAML values. The normative
1.0 envelope is strict about top-level names; use an `x-...` field for a
portable extension. The Python validator's explicit `allow_extensions=True`
option is a migration escape hatch for private fields.

## CLI

Install the published package:

```bash
pip install axiom
```

Install the development checkout:

```bash
pip install -e ".[dev]"
```

Create a contract and run the toolchain:

```bash
axiom init robot.yaml
axiom validate robot.yaml
axiom lint robot.yaml
axiom docs robot.yaml -o robot.md
axiom generate robot.yaml -o robot_protocol.py
axiom diff robot-v1.yaml robot-v2.yaml
axiom match robot.yaml skill-requirements.yaml
```

The command set is intentionally small and composable:

| Command | Purpose |
| --- | --- |
| `axiom init` | Create a starter contract. |
| `axiom validate` | Check the document envelope, types, ranges, and requirements. |
| `axiom lint` | Find portability, documentation, and safety-quality issues. |
| `axiom docs` | Generate Markdown capability documentation. |
| `axiom generate` | Generate Python, TypeScript, or JSON integration artifacts. |
| `axiom diff` | Compare semantic hardware and capability changes. |
| `axiom match` | Check a robot against required capabilities. |

Every command that reports a result can be used in CI. `validate --json`,
`lint --json`, `diff --json`, and `match --json` provide machine-readable
output for platforms and agents.

### Compatibility checking

A skill requirement manifest can be as small as:

```yaml
axiom: "1.0"
skill:
  name: pick_and_place
  requires:
    - camera
    - arm
```

Run it against a robot contract:

```bash
axiom match robot.yaml skill-requirements.yaml
```

The result is explicit:

```text
Incompatible
Required capabilities: camera, arm
Matched: camera
Missing requirements:
  - arm
```

Requirements also support optional capabilities and alternatives:

```yaml
requires:
  all: [camera, arm]
  any: [lidar, depth_camera]
```

## Schema design

The Axiom 1.0 envelope consists of:

| Section | Meaning |
| --- | --- |
| `robot` | Identity and human-facing metadata. `name` is required. |
| `hardware` | Physical sensors, actuators, compute, and platform components. |
| `capabilities` | Machine-usable sensors, actuators, skills, and limitations. |
| `interfaces` | Protocols and endpoints used to invoke or observe capabilities. |
| `constraints` | Operating, environmental, and safety constraints. |
| `requirements` | Dependencies such as power, network, calibration, or permissions. |

The standard categories are `sensors`, `actuators`, `skills`, and
`limitations`. A skill may declare `requires`, `inputs`, `outputs`, `actions`,
and constraints. Implementations may add `x-...` extension fields without
changing the core contract.

The normative JSON Schema is available at
[`schema/axiom-1.0.schema.json`](schema/axiom-1.0.schema.json).

## Architecture

Axiom is split into small layers so a platform can embed only what it needs:

```text
axiom-schema      parse and normalize the contract
       ↓
axiom-core        public document and capability model
       ↓
axiom-validator   validation and lint diagnostics
       ↓
axiom-codegen     Python, TypeScript, and integration artifacts
       ↓
axiom-registry    storage/query boundary for robot catalogs
```

In this reference implementation these layers are exposed as the modules
`axiom.schema`, `axiom.core`, `axiom.validator`, `axiom.codegen`, and
`axiom.registry`. The registry is storage-agnostic so a hosted ecosystem can
add HTTP, database, or signed-artifact adapters later.

## Ecosystem direction

Axiom is intended to become shared infrastructure between:

- robot manufacturers publishing capability contracts;
- robot platforms discovering and scheduling compatible robots;
- AI agents selecting tools based on explicit capabilities and requirements;
- SDKs generating typed interfaces and documentation from the same source;
- CI systems reviewing capability changes with semantic diffs.

The contract is the source of truth. YAML is only the authoring format; the
same document can be validated, indexed, rendered, matched, or transformed
without a human guessing what the robot supports.

## Package naming

The package and executable are both `axiom`. Contracts use `axiom: "1.0"` and
the top-level sections above; all tooling is released through this canonical
surface.

## Development

```bash
pytest tests/ -v
ruff check src/ tests/
python -m axiom --help
```

Axiom is released under the MIT License.
