#!/usr/bin/which python
#

import paramiko
import time
import unittest
import MockSSH

from examples.mock_F5 import commands


def recv_all(channel):
    while not channel.recv_ready():
        time.sleep(0.1)
    stdout = ''
    while channel.recv_ready():
        stdout += channel.recv(1024)
    return stdout


class MockF5TestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        users = {'testadmin': 'x'}
        MockSSH.startThreadedServer(
            commands,
            prompt="[root@hostname:Active] testadmin # ",
            interface="localhost",
            port=1025,
            **users)

    @classmethod
    def tearDownClass(cls):
        print "tearDownClass"
        MockSSH.stopThreadedServer()

    def test_passwd_success(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
        ssh.connect('127.0.0.1',
                    username='testadmin',
                    password='x',
                    port=1025)

        channel = ssh.invoke_shell()
        # read prompt
        recv_all(channel)

        channel.send('passwd remotex\n')
        stdout = recv_all(channel)
        open('stdout', 'w').write(stdout)
        self.assertEqual(stdout, ('passwd remotex\r\nChanging password for user'
                                  ' remotex.\r\nNew BIG-IP password: '))

        channel.send('1234\n')
        stdout = recv_all(channel)
        self.assertEqual(stdout, '\r\nRetype new BIG-IP password: ')

        channel.send('1234\n')
        stdout = recv_all(channel)
        self.assertEqual(stdout, ('\r\nChanging password for user remotex.\r'
                                  '\npasswd: all authentication tokens updated'
                                  ' successfully.\r\n[root@hostname:Active] '
                                  'testadmin # '))

    def test_invalid_passwd_failure(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
        ssh.connect('127.0.0.1',
                    username='testadmin',
                    password='x',
                    port=1025)

        channel = ssh.invoke_shell()
        # read prompt
        recv_all(channel)

        channel.send('passwd remotey\n')
        stdout = recv_all(channel)
        open('stdout', 'w').write(stdout)
        self.assertEqual(stdout, ('passwd remotey\r\nChanging password for '
                                  'user remotey.\r\nNew BIG-IP password: '))

        channel.send('1234\n')
        stdout = recv_all(channel)
        self.assertEqual(stdout, '\r\nRetype new BIG-IP password: ')

        channel.send('12345\n')
        stdout = recv_all(channel)
        self.assertEqual(stdout, ('\r\nSorry, passwords do not match\r\npasswd'
                                  ': Authentication token manipulation error\r'
                                  '\npasswd: password unchanged\r\n[root@hostn'
                                  'ame:Active] testadmin # '))

    def test_passwd_usage_failure(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
        ssh.connect('127.0.0.1',
                    username='testadmin',
                    password='x',
                    port=1025)

        channel = ssh.invoke_shell()
        # read prompt
        recv_all(channel)

        channel.send('passwd\n')
        stdout = recv_all(channel)
        open('stdout', 'w').write(stdout)
        self.assertEqual(stdout, ('passwd\r\nMockSSH: Supported usage: passwd '
                                  '<username>\r\n[root@hostname:Active] testad'
                                  'min # '))
