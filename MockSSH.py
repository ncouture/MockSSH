#!/usr/bin/python
#

import sys
import os
import shlex

from twisted.cred import portal, checkers
from twisted.conch import avatar, recvline, interfaces as conchinterfaces
from twisted.conch.ssh import factory, keys, session, userauth, connection
from twisted.conch.insults import insults
from twisted.internet import reactor

from zope.interface import implements

__all__ = ["SSHCommand",
           "PasswordPromptingCommand",
           "ArgumentValidatingCommand",
           "runServer"]


class SSHCommand(object):
    """
    Instance attributes:
      args : the command arguments

    Instance methods:
      write : write to the transport terminal
      writeln : write a new line to the transport terminal

    Misc:
      You can rewrite the shell prompt via protocol.prompt.
    """
    def __init__(self, protocol, *args):
        self.protocol = protocol
        self.args = args
        self.writeln = self.protocol.writeln
        self.write = self.protocol.terminal.write
        self.nextLine = self.protocol.terminal.nextLine

    def start(self):
        self.call()
        self.exit()

    def call(self):
        self.protocol.writeln('Hello World! [%s]' % repr(self.args))

    def exit(self):
        self.protocol.cmdstack.pop()
        self.protocol.cmdstack[-1].resume()

    def ctrl_c(self):
        print 'Received CTRL-C, exiting..'
        self.writeln('^C')
        self.exit()

    def lineReceived(self, line):
        print 'INPUT: %s' % line

    def resume(self):
        pass


class PasswordPromptingCommand(SSHCommand):
    def __init__(self,
                 password,
                 password_prompt,
                 success_callbacks=[],
                 failure_callbacks=[]):
        self.valid_password = password
        self.password_prompt = password_prompt
        self.success_callbacks = success_callbacks
        self.failure_callbacks = failure_callbacks

        self.protocol = None  # protocol is set by __call__

    def __call__(self, protocol, *args):
        SSHCommand.__init__(self, protocol, *args)
        return self

    def start(self):
        self.write(self.password_prompt)
        self.protocol.password_input = True

    def lineReceived(self, line):
        self.validate_password(line.strip())

    def validate_password(self, password):
        if password == self.valid_password:
            [func(self) for func in self.success_callbacks]
        else:
            [func(self) for func in self.failure_callbacks]

        self.protocol.password_input = False
        self.exit()


class ArgumentValidatingCommand(SSHCommand):
    def __init__(self, argument_validator):
        """argument_validator: callback"""
        self.argument_validator = argument_validator
        self.protocol = None  # set in __call__

    def __call__(self, protocol, *args):
        SSHCommand.__init__(self, protocol, *args)
        return self

    def start(self):
        self.argument_validator(self)


class SSHShell(object):
    def __init__(self, protocol, prompt):
        self.protocol = protocol
        self.protocol.prompt = prompt
        self.showPrompt()
        self.cmdpending = []

    def lineReceived(self, line):
        print 'CMD: %s' % line
        for i in [x.strip() for x in line.strip().split(';')]:
            if not len(i):
                continue
            self.cmdpending.append(i)
        if len(self.cmdpending):
            self.runCommand()
        else:
            self.showPrompt()

    def runCommand(self):
        def runOrPrompt():
            if len(self.cmdpending):
                self.runCommand()
            else:
                self.showPrompt()

        if not len(self.cmdpending):
            self.showPrompt()
            return

        line = self.cmdpending.pop(0)
        try:
            cmdAndArgs = shlex.split(line)
        except:
            self.protocol.writeln(
                'MockSSH: syntax error: unexpected end of file')
            self.cmdpending = []
            self.showPrompt()
            return

        cmd = None
        while len(cmdAndArgs):
            piece = cmdAndArgs.pop(0)
            cmd = piece
            break

        args = cmdAndArgs

        if not cmd:
            runOrPrompt()
            return

        rargs = []
        for arg in args:
            rargs.append(arg)

        cmdclass = self.protocol.getCommand(cmd)
        if cmdclass:
            print 'Command found: %s' % (line,)
            self.protocol.call_command(cmdclass, *rargs)
        else:
            print 'Command not found: %s' % (line,)
            if len(line):
                self.protocol.writeln('MockSSH: %s: command not found' % cmd)
                runOrPrompt()

    def resume(self):
        self.runCommand()

    def showPrompt(self):
        self.protocol.terminal.write(self.protocol.prompt)

    def ctrl_c(self):
        self.protocol.lineBuffer = []
        self.protocol.lineBufferIndex = 0
        self.protocol.terminal.nextLine()
        self.showPrompt()


class SSHProtocol(recvline.HistoricRecvLine):
    def __init__(self, user, prompt, commands):
        self.user = user
        self.prompt = prompt
        self.commands = commands
        self.password_input = False
        self.cmdstack = []

    def connectionMade(self):
        recvline.HistoricRecvLine.connectionMade(self)
        self.cmdstack = [SSHShell(self, self.prompt)]

        #p = self.terminal.transport.session.conn.transport.transport.getPeer()
        #self.client_ip = p.host

        self.keyHandlers.update({
            '\x04':     self.handle_CTRL_D,
            '\x15':     self.handle_CTRL_U,
            '\x03':     self.handle_CTRL_C,
            })

    def lineReceived(self, line):
        if len(self.cmdstack):
            self.cmdstack[-1].lineReceived(line)

    def connectionLost(self, reason):
        recvline.HistoricRecvLine.connectionLost(self, reason)
        del self.commands

    # Overriding to prevent terminal.reset() and setInsertMode()
    def initializeScreen(self):
        pass

    def getCommand(self, cmd):
        if cmd in self.commands:
            return self.commands[cmd]

    def keystrokeReceived(self, keyID, modifier):
        recvline.HistoricRecvLine.keystrokeReceived(self, keyID, modifier)

    # Easier way to implement password input?
    def characterReceived(self, ch, moreCharactersComing):
        self.lineBuffer[self.lineBufferIndex:self.lineBufferIndex+1] = [ch]
        self.lineBufferIndex += 1

        if not self.password_input:
            self.terminal.write(ch)

    def writeln(self, data):
        self.terminal.write(data)
        self.terminal.nextLine()

    def call_command(self, cmd, *args):
        obj = cmd(self, *args)
        self.cmdstack.append(obj)
        obj.start()

    def handle_RETURN(self):
        if len(self.cmdstack) == 1:
            if self.lineBuffer:
                self.historyLines.append(''.join(self.lineBuffer))
            self.historyPosition = len(self.historyLines)
        return recvline.HistoricRecvLine.handle_RETURN(self)

    def handle_CTRL_C(self):
        self.cmdstack[-1].ctrl_c()

    def handle_CTRL_U(self):
        for i in range(self.lineBufferIndex):
            self.terminal.cursorBackward()
            self.terminal.deleteCharacter()
        self.lineBuffer = self.lineBuffer[self.lineBufferIndex:]
        self.lineBufferIndex = 0

    def handle_CTRL_D(self):
        self.call_command(self.commands['_exit'])


class SSHAvatar(avatar.ConchUser):
    implements(conchinterfaces.ISession)

    def __init__(self, user, prompt, commands):
        avatar.ConchUser.__init__(self)

        self.user = user
        self.prompt = prompt
        self.commands = commands

        self.channelLookup.update({'session': session.SSHSession})

    def openShell(self, protocol):
        serverProtocol = insults.ServerProtocol(SSHProtocol,
                                                self,
                                                self.prompt,
                                                self.commands)

        serverProtocol.makeConnection(protocol)
        protocol.makeConnection(session.wrapProtocol(serverProtocol))

    def getPty(self, terminal, windowSize, attrs):
        return None

    def execCommand(self, protocol, cmd):
        raise NotImplementedError

    def closed(self):
        pass


class SSHRealm:
    implements(portal.IRealm)

    def __init__(self, prompt, commands):
        self.prompt = prompt
        self.commands = commands

    def requestAvatar(self, avatarId, mind, *interfaces):
        if conchinterfaces.IConchUser in interfaces:
            return interfaces[0], SSHAvatar(
                avatarId, self.prompt, self.commands), lambda: None
        else:
            raise Exception("No supported interfaces found.")


class command_exit(SSHCommand):
    def call(self):
        self.protocol.terminal.loseConnection()


def getRSAKeys(keypath="."):
    if not os.path.exists(keypath):
        print "Could not find specified keypath (%s)" % keypath
        sys.exit(1)

    pubkey = os.path.join(keypath, "public.key")
    privkey = os.path.join(keypath, "private.key")

    if not (os.path.exists(pubkey) and os.path.exists(privkey)):
        sys.stdout.write("Generating RSA keypair... ")

        from Crypto.PublicKey import RSA
        from twisted.python import randbytes

        KEY_LENGTH = 1024

        rsaKey = RSA.generate(KEY_LENGTH, randbytes.secureRandom)

        publicKeyString = keys.Key(rsaKey).public().toString('openssh')
        privateKeyString = keys.Key(rsaKey).toString('openssh')

        file(pubkey, 'w+b').write(publicKeyString)
        file(privkey, 'w+b').write(privateKeyString)

        sys.stdout.write("Done.\n")
    else:
        publicKeyString = file(pubkey).read()
        privateKeyString = file(privkey).read()

    return publicKeyString, privateKeyString


class SSHServerError(Exception):
    pass


def runServer(commands,
              prompt="$ ",
              keypath=".",
              interface='',
              port=2222,
              **users):

    if not users:
        raise SSHServerError("You must provide at least one "
                             "username/password combination "
                             "to run this SSH server.")

    for exit_cmd in ['_exit', 'exit']:
        if not exit_cmd in commands:
            commands[exit_cmd] = command_exit

    sshFactory = factory.SSHFactory()

    sshFactory.portal = portal.Portal(
        SSHRealm(prompt=prompt, commands=commands)
    )
    sshFactory.portal.registerChecker(
        checkers.InMemoryUsernamePasswordDatabaseDontUse(**users)
    )

    pubKeyString, privKeyString = getRSAKeys(keypath)

    sshFactory.publicKeys = {
        'ssh-rsa': keys.Key.fromString(data=pubKeyString)
    }
    sshFactory.privateKeys = {
        'ssh-rsa': keys.Key.fromString(data=privKeyString)
    }
    sshFactory.services = {
        'ssh-userauth': userauth.SSHUserAuthServer,
        'ssh-connection': connection.SSHConnection
    }

    reactor.listenTCP(port,
                      sshFactory,
                      interface=interface)
    reactor.run()

if __name__ == "__main__":
    users = {'root': 'x'}
    commands = {'exit': command_exit}
    runServer(commands, **users)
