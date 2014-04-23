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


def conf_argument_validator(instance):
    if (not len(instance.args) == 1) or (not instance.args[0] == 't'):
        instance.writeln("MockSSH: Supported usage: conf t")
    else:
        instance.writeln("Enter configuration commands, one per line. End "
                         "with CNTL/Z")
        instance.protocol.prompt = "hostname(config)#"
    instance.exit()


def en_change_protocol_prompt(instance):
    instance.protocol.prompt = "hostname #"
    instance.protocol.password_input = False


def en_write_password_to_transport(instance):
    instance.writeln("MockSSH: password is %s" % instance.valid_password)


command_conf = MockSSH.ArgumentValidatingCommand(conf_argument_validator)
command_en = MockSSH.PasswordPromptingCommand(
    password='1234',
    password_prompt="Password: ",
    success_callbacks=[en_change_protocol_prompt],
    failure_callbacks=[en_write_password_to_transport])


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
