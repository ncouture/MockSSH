# MockSSH Project Context

MockSSH is a Python library and DSL (Domain Specific Language) designed to mock an SSH server and its command-line interface. It is primarily used to emulate network devices or other operating systems for testing task automation and performing end-to-end SSH unit tests.

## Project Overview

-   **Purpose:** Emulate SSH-enabled devices to test automation without access to physical hardware.
-   **Core Technologies:**
    -   **Python 3.12.12:** The project has been modernized from Python 2.
    -   **Twisted (Conch):** Used for the underlying SSH transport and protocol implementation.
    -   **Hy (LISP on Python):** Provides a DSL in `mocksshy/` for configuring servers with minimal code.
    -   **Cryptography:** Handles secure host key generation (Ed25519, ECDSA, RSA-SHA2).
    -   **Paramiko:** Used primarily within the test suite for client-side SSH interactions.
    -   **Ruff:** Used for lightning-fast linting and auto-formatting.
    -   **mypy:** Used for static type checking.
    -   **pytest & pytest-twisted:** Used for modern, robust testing with native Twisted integration.
    -   **build:** Used for generating modern source distributions and wheels via `pyproject.toml`.

## Architecture

-   **`MockSSH.py`:** The main library containing the SSH realm, avatar, and protocol logic.
    -   `SSHCommand`: Base class for custom commands.
    -   `PromptingCommand`: Handles multi-step interactions (e.g., password prompts).
    -   `ArgumentValidatingCommand`: Validates command arguments before execution.
    -   `SSHShell`: Implements the interactive shell and command matching.
-   **`mocksshy/`**: Contains the Hy DSL implementation (`language.hy`).
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
.venv/bin/python examples/mock_F5.py
```

## Development Conventions

-   **Python 3 Compatibility:** Adhere to strict `bytes` and `str` separation. Twisted transport methods expect `bytes`, while command logic typically uses `str`.
-   **Security Defaults:** 
    -   **Supported Host Keys:** `ssh-ed25519`, `ecdsa-sha2-nistp256`, `rsa-sha2-512`, and `rsa-sha2-256`.
    -   **Disabled:** Weak protocols like `ssh-rsa` (SHA-1) and `diffie-hellman-group-exchange-sha1`.
-   **Host Key Generation:** The server automatically generates missing host keys in the `keypath` directory using the `getHostKeys` function.
-   **Coding Style:** Enforced by **Ruff** and **mypy**. Use `make fix` to format and `make typecheck` to verify types. Pre-commit hooks should be installed for continuous validation.
-   **Testing:** New commands or features should be verified with end-to-end tests in the `tests/` directory. The test suite is fully optimized and runs with **zero warnings**. Ensure `tests/__init__.py` exists for package discovery.

## Gemini Automation

This project integrates the **Gemini CLI** via GitHub Actions to automate common development workflows.

### Workflows (.github/workflows/)
-   **Gemini Dispatch**: Orchestrates the execution of Gemini tasks based on issue or pull request comments.
-   **Gemini Review**: Performs automated code reviews on pull requests using the Interaction API.
-   **Gemini Triage**: Automatically analyzes and labels new issues based on their content.
-   **Gemini Scheduled Triage**: Periodically scans for untriaged issues to ensure they are properly labeled.
-   **Gemini Plan Execution**: Executes approved implementation plans for feature requests or bug fixes.

### Command Templates (.github/commands/)
-   **gemini-invoke.toml**: General-purpose prompt for manual Gemini CLI invocations.
-   **gemini-review.toml**: Specialized prompt for performing high-quality code reviews.
-   **gemini-triage.toml**: Configuration for the issue triage and labeling logic.
-   **gemini-plan-execute.toml**: Orchestration logic for autonomous task execution.

