# Security policy

Please report vulnerabilities privately through a GitHub Security Advisory for
this repository, or contact the project maintainers privately through the
repository owner. Do not publish a malicious contract or parser exploit in a
public issue.

Include the affected version, a minimal reproduction, the expected impact, and
safe mitigation details. Remove credentials, robot addresses, logs containing
personal data, and private capability contracts before sharing artifacts.

Axiom parses YAML and can generate source code. Treat contracts and generated
artifacts as untrusted input, validate them before use, and review generated
code before compiling or deploying it.
