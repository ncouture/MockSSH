# MockSSH Roadmap & TODO

This document tracks the progress of MockSSH modernization and future improvements.

## Completed Tasks ✅

- [x] **Python 3 Modernization**: The project now requires Python 3.12+ and has been fully updated to support modern Python patterns.
- [x] **Modern Build System**: Migrated from `setup.py` to `pyproject.toml` (PEP 517/518).
- [x] **Migration to pytest**: Successfully transitioned from `unittest` to `pytest` with `pytest-twisted`.
- [x] **Static Type Checking**: Implemented `mypy` across the codebase with strict type checking enabled.
- [x] **Ruff Integration**: Replaced legacy linters/formatters with `Ruff` for lightning-fast analysis.
- [x] **Pre-commit Hooks**: Set up automated local validation.
- [x] **Gemini Automation**: Integrated Gemini CLI for automated triage, review, and plan execution.
- [x] **Security Hardening**: Explicitly enabled modern host keys (`ed25519`, `ecdsa`) and disabled legacy protocols.
- [x] **Architecture Documentation**: Created core architecture overview in `docs/wiki/core-architecture/Overview.md`.

## High Priority 🚀

- [ ] **Modularize MockSSH.py**: Refactor the monolithic `src/MockSSH.py` into a proper package structure (e.g., `mockssh/server.py`, `mockssh/commands.py`, `mockssh/crypto.py`).
- [ ] **Implement CI/CD Workflows**: Add GitHub Actions for running tests, linters, and type checkers across supported Python versions (3.12, 3.13).
- [/] **Documentation Update**: Wiki navigation fixed and content expanded. Next: Transition into modern Sphinx or MkDocs documentation hosted on GitHub Pages or ReadTheDocs.

## Medium Priority 🛠️

- [ ] **Declarative Configuration**: Evaluate replacing the Hy DSL with a standard format like TOML or YAML for easier configuration without niche dependencies.
- [ ] **Extended Command Library**: Add more pre-built commands for common network devices (e.g., Juniper, Arista).
- [ ] **Improved Logging**: Implement a structured logging system (e.g., `structlog`) to better capture server interactions and errors.

## Low Priority 🧊

- [ ] **Interactive CLI for DSL**: Create a small CLI tool to quickly spin up mock servers from the command line using declarative files.
- [ ] **SSH Proxy Mode**: Implement a mode where MockSSH can act as a proxy, recording interactions with real servers to generate mock configurations automatically.

## Security Audit Items 🔒

- [ ] **Verify `agentic-sa.json` exclusion**: Ensure no real service account keys are committed and add them to `.gitignore`.
- [ ] **Expand SAST**: Integrate `Bandit` or `Safety` into the upcoming CI pipeline.

