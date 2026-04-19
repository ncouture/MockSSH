import shutil
import tempfile
import time

import MockSSH
import paramiko
import pytest
from examples.mock_cisco import commands


def recv_all(channel):
    while not channel.recv_ready():
        time.sleep(0.1)
    stdout = b""
    while channel.recv_ready():
        stdout += channel.recv(1024)
    return stdout.decode("utf-8")


@pytest.fixture(scope="module")
def cisco_server():
    users = {"testadmin": "x"}
    keypath = tempfile.mkdtemp()
    server_port = MockSSH.startThreadedServer(
        commands,
        prompt="hostname>",
        keypath=keypath,
        interface="127.0.0.1",
        port=9999,
        **users,
    )
    yield server_port
    MockSSH.stopThreadedServer(server_port)
    shutil.rmtree(keypath)


@pytest.fixture
def ssh_client(cisco_server):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        "127.0.0.1",
        username="testadmin",
        password="x",
        port=9999,
        allow_agent=False,
        look_for_keys=False,
    )
    yield ssh
    ssh.close()


def test_wr_success(ssh_client):
    channel = ssh_client.invoke_shell()
    recv_all(channel)

    channel.send("wr m\n")
    stdout = recv_all(channel)
    assert "[OK]" in stdout


def test_wr_failure(ssh_client):
    channel = ssh_client.invoke_shell()
    recv_all(channel)

    channel.send("wr\n")
    stdout = recv_all(channel)
    assert stdout == "wr\r\nMockSSH: Supported usage: wr m\r\nhostname>"


def test_password_reset_success(ssh_client):
    channel = ssh_client.invoke_shell()
    recv_all(channel)

    channel.send("en\n")
    stdout = recv_all(channel)
    assert "Password:" in stdout

    channel.send("1234\n")
    stdout = recv_all(channel)
    assert stdout == "\r\nhostname #"

    channel.send("conf t\n")
    stdout = recv_all(channel)
    assert (
        "conf t\r\nEnter configuration commands, one per line. End with CNTL/Z\r\nhostname(config)#"
        in stdout
    )

    channel.send("username remote password 1234\n")
    stdout = recv_all(channel)
    assert stdout == "username remote password 1234\r\nhostname(config)#"

    channel.send("exit\n")
    stdout = recv_all(channel)
    assert stdout == "exit\r\nhostname#"

    channel.send("wr m\n")
    stdout = recv_all(channel)
    assert "wr m\r\nBuilding configuration...\r\n[OK]\r\nhostname#" in stdout

    channel.send("exit\n")
    stdout = recv_all(channel)
    assert stdout == "exit\r\n\x1bc"
