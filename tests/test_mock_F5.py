import shutil
import tempfile
import time

import MockSSH
import paramiko
import pytest
from examples.mock_F5 import commands


def recv_all(channel):
    while not channel.recv_ready():
        time.sleep(0.1)
    stdout = b""
    while channel.recv_ready():
        stdout += channel.recv(1024)
    return stdout.decode("utf-8")


@pytest.fixture(scope="module")
def f5_server():
    users = {"testadmin": "x"}
    keypath = tempfile.mkdtemp()
    server_port = MockSSH.startThreadedServer(
        commands,
        prompt="[root@hostname:Active] testadmin # ",
        keypath=keypath,
        interface="127.0.0.1",
        port=1025,
        **users,
    )
    yield server_port
    MockSSH.stopThreadedServer(server_port)
    shutil.rmtree(keypath)


@pytest.fixture
def ssh_client(f5_server):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        "127.0.0.1",
        username="testadmin",
        password="x",
        port=1025,
        allow_agent=False,
        look_for_keys=False,
    )
    yield ssh
    ssh.close()


def test_passwd_success(ssh_client):
    channel = ssh_client.invoke_shell()
    recv_all(channel)

    channel.send("passwd remotex\n")
    stdout = recv_all(channel)
    assert (
        stdout == "passwd remotex\r\nChanging password for user remotex.\r\nNew BIG-IP password: "
    )

    channel.send("1234\n")
    stdout = recv_all(channel)
    assert stdout == "\r\nRetype new BIG-IP password: "

    channel.send("1234\n")
    stdout = recv_all(channel)
    assert "passwd: all authentication tokens updated successfully." in stdout
    assert "[root@hostname:Active] testadmin # " in stdout


def test_invalid_passwd_failure(ssh_client):
    channel = ssh_client.invoke_shell()
    recv_all(channel)

    channel.send("passwd remotey\n")
    stdout = recv_all(channel)
    assert (
        stdout == "passwd remotey\r\nChanging password for user remotey.\r\nNew BIG-IP password: "
    )

    channel.send("1234\n")
    stdout = recv_all(channel)
    assert stdout == "\r\nRetype new BIG-IP password: "

    channel.send("12345\n")
    stdout = recv_all(channel)
    assert "Sorry, passwords do not match" in stdout
    assert "passwd: password unchanged" in stdout


def test_passwd_usage_failure(ssh_client):
    channel = ssh_client.invoke_shell()
    recv_all(channel)

    channel.send("passwd\n")
    stdout = recv_all(channel)
    assert "MockSSH: Supported usage: passwd <username>" in stdout
