#!/usr/bin/python
#

"""
This is how it should be used:

hostname>en
Password:
hostname#conf t
Enter configuration commands, one per line. End with CNTL/Z
hostname(config)#username admin password secure
hostname(config)#exit
hostname#wr m
Building configuration...
[OK]
hostname#
"""

import sys
import MockSSH

from twisted.python import log


class command_en(MockSSH.SSHCommand):
    def start(self):
        self.this_password = "1234"
        self.password = ""
        self.write("Password: ")
        self.protocol.password_input = True
        self.callbacks = [self.validatePassword]

    def validatePassword(self):
        if self.password:
            if self.password == self.this_password:
                self.protocol.prompt = "hostname#"
                self.protocol.password_input = False
            else:
                self.writeln("MockSSH: password is %s" %
                             self.this_password)
                self.protocol.password_input = False
            self.exit()

    def lineReceived(self, line):
        self.password = line.strip()
        self.callbacks.pop(0)()


class command_conf(MockSSH.SSHCommand):
    def start(self):
        if (not len(self.args) == 1) or (not self.args[0] == 't'):
            self.writeln("MockSSH: Supported usage: conf t")
        else:
            self.writeln("Enter configuration commands, one per line. End "
                         "with CNTL/Z")
            self.protocol.prompt = "hostname(config)#"
        self.exit()


class command_exit(MockSSH.SSHCommand):
    def start(self):
        if 'config' in self.protocol.prompt:
            self.protocol.prompt = "hostname#"
        else:
            self.protocol.call_command(self.protocol.commands['_exit'])

        self.exit()


class command_wr(MockSSH.SSHCommand):
    def start(self):
        if not len(self.args) == 1 or not self.args[0] == 'm':
            self.writeln("MockSSH: Supported usage: wr m")
        else:
            self.writeln("Building configuration...")
            self.writeln("[OK]")

        self.exit()


class command_username(MockSSH.SSHCommand):
    def start(self):
        if not 'config' in self.protocol.prompt:
            self.writeln(
                "MockSSH: Please run the username command in `conf t'")

        if (not len(self.args) == 3 or not self.args[1] == 'password'):
            self.writeln("MockSSH: Supported usage: username "
                         "<username> password <password>")

        self.exit()


def main():
    commands = {
        'en': command_en,
        'enable': command_en,
        'conf': command_conf,
        'username': command_username,
        'wr': command_wr,
        'exit': command_exit
    }

    users = {'testadmin': 'x'}

    log.startLogging(sys.stderr)

    MockSSH.runServer(commands,
                      prompt="hostname>",
                      interface='127.0.0.1',
                      port=9999,
                      **users)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print "User interrupted"
        sys.exit(1)
