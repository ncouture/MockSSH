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


#
# command: en
#
def en_change_protocol_prompt(instance):
    instance.protocol.prompt = "hostname #"
    instance.protocol.password_input = False


def en_write_password_to_transport(instance):
    instance.writeln("MockSSH: password is %s" % instance.valid_password)

command_en = MockSSH.PromptingCommand(
    name='en',
    password='1234',
    prompt="Password: ",
    success_callbacks=[en_change_protocol_prompt],
    failure_callbacks=[en_write_password_to_transport])


#
# command: conf
#
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


#
# command: exit
#
def exit_command_success(instance):
    if 'config' in instance.protocol.prompt:
        instance.protocol.prompt = "hostname#"
    else:
        instance.protocol.call_command(
            instance.protocol.commands['_exit'])


def exit_command_failure(instance):
    instance.writeln("MockSSH: supported usage: exit")

command_exit = MockSSH.ArgumentValidatingCommand(
    'exit',
    [exit_command_success],
    [exit_command_failure],
    *[])


#
# command: wr
#
def wr_command_success(instance):
    instance.writeln("Building configuration...")
    instance.writeln("[OK]")


def wr_command_failure(instance):
    instance.writeln("MockSSH: Supported usage: wr m")

command_wr = MockSSH.ArgumentValidatingCommand(
    'wr',
    [wr_command_success],
    [wr_command_failure],
    *["m"])


class command_username(MockSSH.SSHCommand):
    name = 'username'

    def start(self):
        if 'config' not in self.protocol.prompt:
            self.writeln(
                "MockSSH: Please run the username command in `conf t'")

        if (not len(self.args) == 3 or not self.args[1] == 'password'):
            self.writeln("MockSSH: Supported usage: username "
                         "<username> password <password>")

        self.exit()

commands = [command_en,
            command_conf,
            command_username,
            command_wr,
            command_exit]


def main():
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
