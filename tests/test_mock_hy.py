import subprocess
import sys
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


def recv_all(channel):
    while not channel.recv_ready():
        time.sleep(0.1)
    stdout = b""
    while channel.recv_ready():
        stdout += channel.recv(1024)
    return stdout.decode("utf-8")


@pytest.mark.timeout(30)
def test_hy_example():
    # Start hy examples/mock.hy as a subprocess
    env = os.environ.copy()
    env["PYTHONPATH"] = f"src{os.pathsep}."

    # Run the example
    popen_kwargs: dict = {}
    if sys.platform != "win32":
        popen_kwargs["preexec_fn"] = os.setsid

    process = subprocess.Popen(
        [sys.executable, "-m", "hy", "examples/mock.hy"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **popen_kwargs,
    )

    ssh = None
    try:
        # Connect with paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Try to connect multiple times in case it's slow
        connected = False
        for i in range(15):
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
                connected = True
                break
            except Exception:
                time.sleep(1)

        if not connected:
            pytest.fail("Failed to connect to MockSSH subprocess")

        channel = ssh.invoke_shell()

        # Initial recv to clear prompt
        recv_all(channel)

        # Send a command
        channel.send("ls -1\n")
        stdout = recv_all(channel)

        assert "bin\r\nREADME.txt" in stdout

    finally:
        if ssh:
            ssh.close()
        # Terminate the process group (POSIX) or the process (Windows)
        if process.poll() is None:
            if sys.platform != "win32":
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            else:
                process.terminate()
            process.wait()
