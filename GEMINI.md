# MockSSH Project Context

MockSSH is a Python library and DSL (Domain Specific Language) designed to mock an SSH server and its command-line interface. It is primarily used to emulate network devices or other operating systems for testing task automation and performing end-to-end SSH unit tests.

## Project Overview

-   **Purpose:** Emulate SSH-enabled devices to test automation without access to physical hardware.
-   **Core Technologies:**
    -   **Python 3.12+**: The project has been modernized from Python 2 and supports Python 3.12 and 3.13.
    -   **Twisted (Conch):** Used for the underlying SSH transport and protocol implementation.
    -   **Hy (LISP on Python):** Provides a DSL in `mocksshy/` for configuring servers with minimal code.
    -   **Cryptography:** Handles secure host key generation (Ed25519, ECDSA, RSA-SHA2).
    -   **Paramiko:** Used primarily within the test suite for client-side SSH interactions.
    -   **Ruff:** Used for lightning-fast linting and auto-formatting.
    -   **mypy:** Used for static type checking.
    -   **pytest & pytest-twisted:** Used for modern, robust testing with native Twisted integration.
    -   **build:** Used for generating modern source distributions and wheels via `pyproject.toml`.

## Architecture

-   **`src/MockSSH.py`**: The main library containing the SSH realm, avatar, and protocol logic (~650 lines).
    -   `SSHCommand`: Base class for custom commands.
    -   `PromptingCommand`: Handles multi-step interactions (e.g., password prompts).
    -   `ArgumentValidatingCommand`: Validates command arguments before execution.
    -   `SSHShell`: Implements the interactive shell and command matching.
-   **`src/mocksshy/`**: Contains the Hy DSL implementation (`language.hy`).
-   **`examples/`**: Provides reference implementations for emulating Cisco (`mock_cisco.py`) and F5 (`mock_F5.py`) devices.
-   **`tests/`**: Unit tests using **pytest** and a session-wide Twisted reactor managed in `conftest.py`.
-   **`docs/wiki/`**: Comprehensive project documentation (Foundations, Architecture, Testing, DSL).
-   **`pyproject.toml`**: Modern PEP 517/518 compliant configuration for package metadata and dependencies.

## Building and Running

The project includes a `Makefile` that automatically detects the virtual environment (`.venv`).

| Command | Description |
| :--- | :--- |
| `make` | Default target; executes the full test suite. |
| `make test` | Runs unit tests using **pytest**. |
| `make build` | Generates source distribution and wheel packages. |
| `make fix` | Automatically fixes linting errors and formats code using **Ruff**. |
| `make lint` | Checks code formatting and lints the code using **Ruff**. |
| `make typecheck` | Runs static type checking using **mypy**. |
| `make clean` | Removes build artifacts, cached files, and generated host keys. |

### Manual Execution
To start a mock server (e.g., F5):
```bash
PYTHONPATH=src .venv/bin/python examples/mock_F5.py
```

## Development Conventions

-   **Python 3 Compatibility:** Adhere to strict `bytes` and `str` separation. Twisted transport methods expect `bytes`, while command logic typically uses `str`.
-   **Security Defaults:** 
    -   **Supported Host Keys:** `ssh-ed25519`, `ecdsa-sha2-nistp256`, `rsa-sha2-512`, and `rsa-sha2-256`.
    -   **Strong Ciphers:** Only modern ciphers like `aes256-ctr` are enabled.
    -   **Disabled:** Weak protocols like `ssh-rsa` (SHA-1) and `diffie-hellman-group-exchange-sha1` (when moduli are missing).
-   **Host Key Generation:** The server automatically generates missing host keys in the `keypath` directory (default `generated-keys/`).
-   **Coding Style:** Enforced by **Ruff** and **mypy**. Use `make fix` to format and `make typecheck` to verify types.
-   **Testing:** New commands or features should be verified with end-to-end tests in the `tests/` directory.

## Current Roadmap

MockSSH is undergoing a significant modernization phase (v2.0.0+). Key focus areas include:

1.  **Modularization:** Refactoring the monolithic `src/MockSSH.py` into a modern package structure.
2.  **CI/CD:** Implementing robust GitHub Actions workflows for multi-version testing (Python 3.12, 3.13).
3.  **Logging:** Replacing standard `print` statements with structured logging for better production-grade observability.
4.  **Documentation:** Modernizing the wiki (architecture overview created, navigation links fixed).

Refer to **`TODO.md`** for the complete roadmap and granular task tracking.

## Security & Privacy

A security audit (v2.0.0) identified several areas for improvement:
- **Logging:** Avoid using `print()` for logging, as it can leak PII (passwords, commands) to stdout. A migration to structured logging is planned.
- **Host Keys:** Generated host keys in `generated-keys/` must be restricted to owner-only permissions (`0600`).
- **Secrets Management:** **NEVER** commit service account keys or secrets.

## Gemini Automation

This project integrates the **Gemini CLI** via GitHub Actions to automate development workflows.

### Workflows (.github/workflows/)
-   **Gemini Dispatch**: Orchestrates Gemini tasks via comments.
-   **Gemini Review**: Automated PR reviews.
-   **Gemini Triage**: Issue analysis and labeling.
-   **Gemini Plan Execution**: Autonomous implementation of approved plans.

### Command Templates (.github/commands/)
-   `gemini-invoke.toml`: Manual invocations.
-   `gemini-review.toml`: PR reviews.
-   `gemini-triage.toml`: Issue triage.
-   `gemini-plan-execute.toml`: Autonomous task execution.

