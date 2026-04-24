MockSSH
=======

Mock SSH servers and all commands they support.


Purpose
-------
This project was developed to emulate operating systems
behind SSH servers in order to test task automation without
having access to the real servers.

Finally Mock SSH has been fully modernized as of **version 2.0.0**,
requiring Python 3.12+ and featuring a robust, type-safe
architecture with modern testing and linting (pytest, Ruff).
It provides a threaded version for performing end-to-end
unit tests against mocked SSH services.

Installation
------------
MockSSH requires Python 3.12+. It uses a modern `pyproject.toml` based build system.

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Development
-----------
The project provides several development commands via `make`:

To install the development dependencies (Ruff, mypy, pytest, pre-commit):
```shell
pip install -e ".[dev]"
```

To run the linters and format the code (using **Ruff**):
```shell
make fix
make lint
```

To run static type checking (using **mypy**):
```shell
make typecheck
```

To run the tests:
```shell
make test
```

To build source and wheel distributions:
```shell
make build
```

To install the pre-commit hooks:
```shell
pre-commit install
```

Mock SSH in Python
-----------------
MockSSH aims to be as easy to use as possible.

Refer to the mock_cisco.py and mock_F5.py in the examples/
directory for an overview on how to use it.


Mock SSH in LISP
---------------
Efforts were invested in simplifying the use of MockSSH
with [HyLang](http://hylang.org/).

As a result a DSL is released with this project and
resides in the *mocksshy/* directory.

Using the DSL will allow you to Mock SSH by writing
something that is closer to a configuration file than
a program.

For comparison, here are two ways to Mock SSH servers
implementations providing the same functionality:


*Python*
```python
import MockSSH

def passwd_change_protocol_prompt(instance):
    instance.protocol.prompt = "hostname #"
    instance.protocol.password_input = False

def passwd_write_password_to_transport(instance):
    instance.writeln("MockSSH: password is %s" % instance.valid_password)

command_passwd = MockSSH.PromptingCommand(
    name='passwd',
    password='1234',
    prompt="Password: ",
    success_callbacks=[passwd_change_protocol_prompt],
    failure_callbacks=[passwd_write_password_to_transport])

users = {'admin': '1234'}

commands = [command_passwd]

MockSSH.runServer(commands,
                  prompt="hostname>",
                  interface='127.0.0.1',
                  port=2222,
                  **users)
```

*HyLang*
```clojure
(import MockSSH)
(require mocksshy.language)


(mock-ssh :users {"testuser" "1234"}
          :host "127.0.0.1"
          :port 2222
          :prompt "hostname>"
          :commands [
  (command :name "passwd"
           :type "prompt"
           :output "Password: "
           :required-input "1234"
           :on-success ["prompt" "hostname#"]
           :on-failure ["write" "Pass is 1234..."]))
```


Unit Testing with MockSSH
-------------------------
As shown from the unit tests in the tests/ directory, it is possible to use
a threaded MockSSH server to perform end-to-end unit tests against mocked
SSH services.

MockSSH now uses **pytest** and **pytest-twisted** to manage the Twisted
reactor lifecycle cleanly. This allows the entire test suite to run in a
single process.

Documentation (Wiki)
--------------------
Comprehensive documentation is available in the `docs/wiki/` directory,
covering foundational concepts, architecture, custom command definition,
and testing strategies.

AI-Powered Automation
---------------------
MockSSH is integrated with the **Gemini CLI** to automate routine development tasks:
*   **Automated Issue Triage**: New issues are automatically analyzed and labeled.
*   **Intelligent Code Review**: Pull requests receive an initial automated review from Gemini.
*   **Autonomous Implementation**: Approved plans can be executed by Gemini to speed up development.

Refer to `GEMINI.md` for more details on the automation workflows.

Security
--------
MockSSH is designed for testing and emulation. When implementing custom commands:
*   **Avoid Sensitive Logging**: Do not use `print()` or `log` to output raw user input or passwords.
*   **Host Key Permissions**: Ensure your host keys (in `generated-keys/`) have restricted permissions (`chmod 600`).
*   **Secret Management**: Do not store sensitive credentials (like Service Account keys) in the repository.

License
-------
MockSSH is released under the **LGPL-3.0-or-later** license.

Credits
-------
MockSSH was inspired by [kippo](https://github.com/desaster/kippo/), an SSH honeypot, and @HyLang

