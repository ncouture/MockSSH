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

from mockSSH import SSHCommand, commands, runServer

class command_en(SSHCommand):
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
                self.writeln("mockSSH: password is %s" %
                             self.this_password)
                self.protocol.password_input = False
            self.exit()

    def lineReceived(self, line):
        self.password = line.strip()
        self.callbacks.pop(0)()

class command_conf(SSHCommand):
    def start(self):
        if (not len(self.args) == 1) or (not self.args[0] == 't'):
            self.writeln("mockSSH: Supported usage: conf t")
        else:
            self.writeln("Enter configuration commands, one per line. End "
                         "with CNTL/Z")
            self.protocol.prompt = "hostname(config)#"
        self.exit()

class command_exit(SSHCommand):
    def start(self):
        if 'config' in self.protocol.prompt:
            self.protocol.prompt = "hostname#"
        else:
            self.protocol.commands['_exit']()

        self.exit()

class command_wr(SSHCommand):
    def start(self):
        if not len(self.args) == 1 or not self.args[0] == 'm':
            self.writeln("mockSSH: Supported usage: wr m")
        else:
            self.writeln("Building configuration...")
            self.writeln("[OK]")

        self.exit()

class command_username(SSHCommand):
    def start(self):
        if not 'config' in self.protocol.prompt:
            self.writeln("mockSSH: Please run the username command in `conf t'")

        if (not len(self.args) == 3 or
            not self.args[1] == 'password'):
            self.writeln("mockSSH: Supported usage: username "
                         "<username> password <password>")

        self.exit()

def main():
    commands['en'] = command_en
    commands['conf'] = command_conf
    commands['exit'] = command_exit
    commands['wr'] = command_wr
    commands['username'] = command_username
    users = {'testadmin': 'x'}
    runServer(prompt="hostname>", **users)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print "User interrupted"
        sys.exit(1)
