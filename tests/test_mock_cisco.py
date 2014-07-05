#!/usr/bin/which python
#

# this depends on the example mock_cisco.py to be running locally

import paramiko
import time
import unittest


def recv_all(channel):
    while not channel.recv_ready():
        time.sleep(0.1)
    stdout = ''
    while channel.recv_ready():
        stdout += channel.recv(1024)
    return stdout


class MockCiscoTestCase(unittest.TestCase):
    def test_wr_success(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('127.0.0.1',
                    username='testadmin',
                    password='x',
                    port=9999)

        channel = ssh.invoke_shell()
        # read prompt
        recv_all(channel)

        channel.send('wr m\n')
        stdout = recv_all(channel)
        open('/tmp/tmpmtp', 'w').write(stdout)
        self.assertEqual(stdout, ('wr m\r\nBuilding configuration'
                                  '...\r\n[OK]\r\nhostname>'))

    def test_wr_failure(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('127.0.0.1',
                    username='testadmin',
                    password='x',
                    port=9999)

        channel = ssh.invoke_shell()
        # read prompt
        recv_all(channel)

        channel.send('wr\n')
        stdout = recv_all(channel)
        self.assertEqual(stdout, ('wr\r\nMockSSH: Supported '
                                  'usage: wr m\r\nhostname>'))
