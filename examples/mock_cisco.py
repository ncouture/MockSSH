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


def en_change_protocol_prompt(instance):
    instance.protocol.prompt = "hostname #"
    instance.protocol.password_input = False


def en_write_password_to_transport(instance):
    instance.writeln("MockSSH: password is %s" % instance.valid_password)


def conf_output_error(instance):
    instance.writeln("MockSSH: supported usage: conf t")


def conf_output_success(instance):
    instance.writeln("Enter configuration commands, one per line. End "
                     "with CNTL/Z")


def conf_change_protocol_prompt(instance):
    instance.protocol.prompt = "hostname(config)#"


command_conf = MockSSH.ArgumentValidatingCommand(
    'conf',
    [conf_output_success, conf_change_protocol_prompt],
    [conf_output_error],
    *["t"])

command_en = MockSSH.PasswordPromptingCommand(
    name='en',
    password='1234',
    password_prompt="Password: ",
    success_callbacks=[en_change_protocol_prompt],
    failure_callbacks=[en_write_password_to_transport])


class command_exit(MockSSH.SSHCommand):
    name = "exit"

    def start(self):
        if 'config' in self.protocol.prompt:
            self.protocol.prompt = "hostname#"
        else:
            self.protocol.call_command(self.protocol.commands['_exit'])

        self.exit()


class command_wr(MockSSH.SSHCommand):
    name = 'wr'

    def start(self):
        if not len(self.args) == 1 or not self.args[0] == 'm':
            self.writeln("MockSSH: Supported usage: wr m")
        else:
            self.writeln("Building configuration...")
            self.writeln("[OK]")

        self.exit()


class command_username(MockSSH.SSHCommand):
    name = 'username'

    def start(self):
        if not 'config' in self.protocol.prompt:
            self.writeln(
                "MockSSH: Please run the username command in `conf t'")

        if (not len(self.args) == 3 or not self.args[1] == 'password'):
            self.writeln("MockSSH: Supported usage: username "
                         "<username> password <password>")

        self.exit()


def main():
    commands = [command_en,
                command_conf,
                command_username,
                command_wr,
                command_exit]

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
