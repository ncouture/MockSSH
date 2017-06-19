#!/usr/bin/which python
#

import time
import unittest

import MockSSH
import paramiko


def exec_successful(instance):
    instance.writeln("ok")

def exec_failure(instance):
    instance.writeln("failure")

def recv_all(channel):
    while not channel.recv_ready():
        time.sleep(0.1)
    stdout = ''
    while channel.recv_ready():
        stdout += channel.recv(1024)
    return stdout

class TestParamikoExecCommand(unittest.TestCase):

    def setUp(self):
        users = {'admin': 'x'}
        command = MockSSH.ArgumentValidatingCommand(
                'ls',
                [exec_successful],
                [exec_failure],
                *['123'])
        MockSSH.startThreadedServer(
            [command],
            prompt="hostname>",
            interface="localhost",
            port=9999,
            **users)

    def tearDown(self):
        MockSSH.stopThreadedServer()

    def test_exec_command(self):
        """test paramiko exec_commanbd
        """
        ssh = paramiko.Transport(('127.0.0.1', 9999))
        ssh.connect(username='admin', password='x')
        ch=ssh.open_session()
        ch.exec_command('ls')
        stdout = recv_all(ch)
        self.assertEqual(stdout.strip(), 'failure')
        ch=ssh.open_session()
        ch.exec_command('ls 123')
        stdout = recv_all(ch)
        self.assertEqual(stdout.strip(), 'ok')
        ch.close()
        ssh.close()

if __name__ == "__main__":
    unittest.main()
