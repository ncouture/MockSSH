#!/usr/bin/which python
#

import paramiko
import time
import unittest
import MockSSH

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
        MockSSH.threadedServer(commands,
                               prompt="hostname>",
                               interface="localhost",
                               port=9999,
                               **users)

    @classmethod
    def tearDownClass(cls):
        print "tearDownClass"
        MockSSH.threadedServerStop()

    def test_wr_success(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
        ssh.connect('127.0.0.1',
                    username='testadmin',
                    password='x',
                    port=9999)

        channel = ssh.invoke_shell()
        # read prompt
        recv_all(channel)

        channel.send('wr m\n')
        stdout = recv_all(channel)
        self.assertTrue('[OK]' in stdout)

    def test_wr_failure(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
        ssh.connect('127.0.0.1',
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
