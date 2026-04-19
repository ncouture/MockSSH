import subprocess
import time
import paramiko
import pytest
import os
import signal


@pytest.fixture(scope="module", autouse=True)
def setup_keys():
    if not os.path.exists("generated-keys"):
        os.makedirs("generated-keys")
    yield


@pytest.mark.timeout(30)
def test_hy_example():
    # Start hy examples/mock.hy as a subprocess
    env = os.environ.copy()
    env["PYTHONPATH"] = "."

    # Run the example
    # Use a different port if possible, but examples/mock.hy is hardcoded to 2222
    process = subprocess.Popen(
        ["./.venv/bin/hy", "examples/mock.hy"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
    )

    ssh = None
    try:
        # Wait for the server to start and generate keys
        # This can take a while on some systems
        time.sleep(5)

        # Connect with paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Try to connect multiple times in case it's slow
        for i in range(5):
            try:
                ssh.connect(
                    "127.0.0.1",
                    username="testuser",
                    password="1234",
                    port=2222,
                    allow_agent=False,
                    look_for_keys=False,
                    timeout=5,
                )
                break
            except Exception:
                if i == 4:
                    raise
                time.sleep(2)

        channel = ssh.invoke_shell()
        time.sleep(1)

        # Initial recv to clear prompt
        channel.recv(1024)

        # Send a command
        channel.send("ls -1\n")
        time.sleep(1)
        stdout = channel.recv(1024).decode("utf-8")

        assert "bin\r\nREADME.txt" in stdout

    finally:
        if ssh:
            ssh.close()
        # Terminate the process group
        if process.poll() is None:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait()
