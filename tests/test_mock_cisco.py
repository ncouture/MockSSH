#!/usr/bin/which python
#

import time
import unittest
import tempfile
import shutil

import MockSSH
import paramiko
from examples.mock_cisco import commands


def recv_all(channel):
    while not channel.recv_ready():
        time.sleep(0.1)
    stdout = ''
    while channel.recv_ready():
        stdout += channel.recv(1024)
    return stdout


class MockCiscoTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        users = {'testadmin': 'x'}
        cls.keypath = tempfile.mkdtemp()
        MockSSH.startThreadedServer(
            commands,
            prompt="hostname>",
            keypath=cls.keypath,
            interface="localhost",
            port=9999,
            **users)

    @classmethod
    def tearDownClass(cls):
        print "tearDownClass"
        MockSSH.stopThreadedServer()
        shutil.rmtree(cls.keypath)

    def test_wr_success(self):  # also tested by test_password_reset_success
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
        ssh.connect('127.0.0.1', username='testadmin', password='x', port=9999)

        channel = ssh.invoke_shell()
        # read prompt
        recv_all(channel)

        channel.send('wr m\n')
        stdout = recv_all(channel)
        self.assertTrue('[OK]' in stdout)

    def test_wr_failure(self):  # also tested by test_password_reset_success
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
        ssh.connect(
            '127.0.0.1',
            username='testadmin',
            password='x',
            port=9999,
            look_for_keys=False)

        channel = ssh.invoke_shell()
        # read prompt
        recv_all(channel)

        channel.send('wr\n')
        stdout = recv_all(channel)
        self.assertEqual(stdout, ('wr\r\nMockSSH: Supported '
                                  'usage: wr m\r\nhostname>'))

    def test_password_reset_success(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
        ssh.connect('127.0.0.1', username='testadmin', password='x', port=9999)

        channel = ssh.invoke_shell()
        # read prompt
        recv_all(channel)

        channel.send('en\n')
        stdout = recv_all(channel)
        self.assertTrue('Password:' in stdout)

        channel.send('1234\n')
        stdout = recv_all(channel)
        self.assertEqual(stdout, '\r\nhostname #')

        channel.send('conf t\n')
        stdout = recv_all(channel)
        self.assertEqual(stdout, ('conf t\r\nEnter configuration commands, '
                                  'one per line. End with CNTL/Z\r\nhostname'
                                  '(config)#'))

        channel.send('username remote password 1234\n')
        stdout = recv_all(channel)
        self.assertEqual(stdout,
                         'username remote password 1234\r\nhostname(config)#')

        channel.send('exit\n')
        stdout = recv_all(channel)
        self.assertEqual(stdout, 'exit\r\nhostname#')

        channel.send('wr m\n')
        stdout = recv_all(channel)
        self.assertEqual(stdout, ('wr m\r\nBuilding configuration...\r\n[OK]'
                                  '\r\nhostname#'))

        channel.send('exit\n')
        stdout = recv_all(channel)
        self.assertEqual(stdout, 'exit\r\n\x1bc')


if __name__ == "__main__":
    unittest.main()
