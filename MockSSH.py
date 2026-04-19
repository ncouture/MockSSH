#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
MockSSH: Mock an SSH server and define all commands it supports.
"""

import copy
import os
import shlex
import sys
import warnings
from threading import Thread
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Suppress TripleDES deprecation warnings from cryptography triggered by Twisted's internal imports
try:
    from cryptography.utils import CryptographyDeprecationWarning

    warnings.filterwarnings(
        "ignore", category=CryptographyDeprecationWarning, message=".*TripleDES.*"
    )
except ImportError:
    pass

from twisted.conch import avatar, interfaces as conchinterfaces, recvline
from twisted.conch.insults import insults
from twisted.conch.openssh_compat import primes
from twisted.conch.ssh import connection, factory, keys, session, transport, userauth
from twisted.cred import checkers, portal
from twisted.internet import reactor
from zope.interface import implementer

__all__ = (
    "SSHCommand",
    "PromptingCommand",
    "ArgumentValidatingCommand",
    "runServer",
    "startThreadedServer",
    "stopThreadedServer",
)


class SSHServerError(Exception):
    """Raised when an SSH server error is encountered"""


class MockSSHError(Exception):
    """Raised by MockSSH scripts."""


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

    def __init__(self, protocol: Any, name: str, *args: Any) -> None:
        self.name = name
        self.protocol = protocol
        self.args = args
        self.writeln = self.protocol.writeln
        self.write = self.protocol.terminal.write
        self.nextLine = self.protocol.terminal.nextLine

    def start(self) -> None:
        self.call()
        self.exit()

    def call(self) -> None:
        self.protocol.writeln("Hello World! [%s]" % repr(self.args))

    def exit(self) -> None:
        self.protocol.cmdstack.pop()
        self.protocol.cmdstack[-1].resume()

    def ctrl_c(self) -> None:
        print("Received CTRL-C, exiting..")
        self.writeln("^C")
        self.exit()

    def lineReceived(self, line: str) -> None:
        print("INPUT:", line)

    def resume(self) -> None:
        pass


class PromptingCommand(SSHCommand):
    def __init__(
        self,
        name: str,
        password: str,
        prompt: str,
        success_callbacks: List[Callable[..., Any]] = [],
        failure_callbacks: List[Callable[..., Any]] = [],
    ) -> None:
        self.name = name
        self.valid_password = password
        self.prompt = prompt
        self.success_callbacks = success_callbacks
        self.failure_callbacks = failure_callbacks

        self.protocol: Any = None  # protocol is set by __call__

    def __call__(self, protocol: Any, name: str, *args: Any) -> "PromptingCommand":
        new_instance = copy.copy(self)
        SSHCommand.__init__(new_instance, protocol, name, name, *args)
        return new_instance

    def start(self) -> None:
        self.write(self.prompt)
        self.protocol.password_input = True

    def lineReceived(self, line: str) -> None:
        self.validate_password(line.strip())

    def validate_password(self, password: str) -> None:
        if password == self.valid_password:
            [func(self) for func in self.success_callbacks]
        else:
            [func(self) for func in self.failure_callbacks]

        self.protocol.password_input = False
        self.exit()


class ArgumentValidatingCommand(SSHCommand):
    def __init__(
        self,
        name: str,
        success_callbacks: List[Callable[..., Any]],
        failure_callbacks: List[Callable[..., Any]],
        *args: Any,
    ) -> None:
        self.name = name
        self.success_callbacks = success_callbacks
        self.failure_callbacks = failure_callbacks
        self.required_arguments = [name] + list(args)
        self.protocol: Any = None  # set in __call__

    def __call__(self, protocol: Any, *args: Any) -> "ArgumentValidatingCommand":
        new_instance = copy.copy(self)
        SSHCommand.__init__(new_instance, protocol, self.name, *args)
        return new_instance

    def start(self) -> None:
        if not tuple(self.args) == tuple(self.required_arguments):
            [func(self) for func in self.failure_callbacks]
        else:
            [func(self) for func in self.success_callbacks]
        self.exit()


class SSHShell(object):
    def __init__(self, protocol: Any, prompt: Union[str, bytes]) -> None:
        self.protocol = protocol
        self.protocol.prompt = prompt
        self.showPrompt()
        self.cmdpending: List[str] = []

    def lineReceived(self, line: str) -> None:
        print("CMD:", line)
        for i in [x.strip() for x in line.strip().split(";")]:
            if not len(i):
                continue
            self.cmdpending.append(i)
        if len(self.cmdpending):
            self.runCommand()
        else:
            self.showPrompt()

    def runCommand(self) -> None:
        def runOrPrompt() -> None:
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
        except ValueError:
            self.protocol.writeln("MockSSH: syntax error: unexpected end of file")
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
            print("Command found:", line)
            self.protocol.call_command(cmdclass, *rargs)
        else:
            print("Command not found:", line)
            if len(line):
                self.protocol.writeln("MockSSH: %s: command not found" % cmd)
                runOrPrompt()

    def resume(self) -> None:
        self.runCommand()

    def showPrompt(self) -> None:
        prompt = self.protocol.prompt
        if isinstance(prompt, str):
            prompt = prompt.encode("utf-8")  # type: ignore
        self.protocol.terminal.write(prompt)

    def ctrl_c(self) -> None:
        self.protocol.lineBuffer = []
        self.protocol.lineBufferIndex = 0
        self.protocol.terminal.nextLine()
        self.showPrompt()


class SSHProtocol(recvline.HistoricRecvLine):
    def __init__(self, user: str, prompt: Union[str, bytes], commands: Dict[str, Any]) -> None:
        self.user = user
        self.prompt = prompt
        self.commands = commands
        self.password_input = False
        self.cmdstack: List[Any] = []

    def connectionMade(self) -> None:
        recvline.HistoricRecvLine.connectionMade(self)
        self.cmdstack = [SSHShell(self, self.prompt)]

        transport = self.terminal.transport.session.conn.transport
        transport.factory.sessions[transport.transport.sessionno] = self
        # p = self.terminal.transport.session.conn.transport.transport.getPeer()
        # self.client_ip = p.host

        self.keyHandlers.update(
            {
                b"\x04": self.handle_CTRL_D,
                b"\x15": self.handle_CTRL_U,
                b"\x03": self.handle_CTRL_C,
            }
        )

    def lineReceived(self, line: Union[str, bytes]) -> None:
        if isinstance(line, bytes):
            line_str = line.decode("utf-8")
        else:
            line_str = line
        if len(self.cmdstack):
            self.cmdstack[-1].lineReceived(line_str)

    def connectionLost(self, reason: Any) -> None:
        recvline.HistoricRecvLine.connectionLost(self, reason)
        if hasattr(self, "commands"):
            del self.commands

    # Overriding to prevent terminal.reset() and setInsertMode()
    def initializeScreen(self) -> None:
        pass

    def getCommand(self, name: str) -> Optional[Any]:
        if name in self.commands:
            return self.commands[name]
        return None

    def keystrokeReceived(self, keyID: bytes, modifier: Any) -> None:
        recvline.HistoricRecvLine.keystrokeReceived(self, keyID, modifier)

    # Easier way to implement password input?
    def characterReceived(self, ch: bytes, moreCharactersComing: bool) -> None:
        self.lineBuffer[self.lineBufferIndex : self.lineBufferIndex + 1] = [ch]  # type: ignore
        self.lineBufferIndex += 1

        if not self.password_input:
            data = ch
            if isinstance(data, str):
                data = data.encode("utf-8")  # type: ignore
            self.terminal.write(data)

    def writeln(self, data: Union[str, bytes]) -> None:
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.terminal.write(data)
        self.terminal.nextLine()

    def call_command(self, cmd: Any, *args: Any) -> None:
        obj = cmd(self, cmd.name, *args)
        self.cmdstack.append(obj)
        obj.start()

    def handle_RETURN(self) -> Any:
        if len(self.cmdstack) == 1:
            if self.lineBuffer:
                self.historyLines.append(b"".join(self.lineBuffer))  # type: ignore
            self.historyPosition = len(self.historyLines)
        return recvline.HistoricRecvLine.handle_RETURN(self)

    def handle_CTRL_C(self) -> None:
        self.cmdstack[-1].ctrl_c()

    def handle_CTRL_U(self) -> None:
        for i in range(self.lineBufferIndex):
            self.terminal.cursorBackward()
            self.terminal.deleteCharacter()
        self.lineBuffer = self.lineBuffer[self.lineBufferIndex :]
        self.lineBufferIndex = 0

    def handle_CTRL_D(self) -> None:
        self.call_command(self.commands["_exit"])


@implementer(conchinterfaces.ISession)
class SSHAvatar(avatar.ConchUser):
    def __init__(self, user: str, prompt: Union[str, bytes], commands: Dict[str, Any]) -> None:
        avatar.ConchUser.__init__(self)

        self.user = user
        self.prompt = prompt
        self.commands = commands

        self.channelLookup.update({b"session": session.SSHSession})

    def openShell(self, protocol: Any) -> None:
        serverProtocol = insults.ServerProtocol(SSHProtocol, self, self.prompt, self.commands)

        serverProtocol.makeConnection(protocol)
        protocol.makeConnection(session.wrapProtocol(serverProtocol))

    def getPty(self, terminal: Any, windowSize: Any, attrs: Any) -> bool:
        return True

    def execCommand(self, protocol: Any, cmd: str) -> None:
        raise NotImplementedError

    def closed(self) -> None:
        pass

    def eofReceived(self) -> None:
        pass


@implementer(portal.IRealm)
class SSHRealm:
    def __init__(self, prompt: Union[str, bytes], commands: Dict[str, Any]) -> None:
        self.prompt = prompt
        self.commands = commands

    def requestAvatar(
        self, avatarId: bytes, mind: Any, *interfaces: Any
    ) -> Tuple[Any, Any, Callable[[], None]]:
        if conchinterfaces.IConchUser in interfaces:
            return (
                interfaces[0],
                SSHAvatar(avatarId.decode("utf-8"), self.prompt, self.commands),
                lambda: None,
            )
        else:
            raise Exception("No supported interfaces found.")


class SSHTransport(transport.SSHServerTransport):
    hadVersion = False

    # Explicitly define strong ciphers and MACs, excluding weak ones like TripleDES or MD5
    supportedCiphers = [
        b"aes256-ctr",
        b"aes192-ctr",
        b"aes128-ctr",
        b"aes256-cbc",
        b"aes192-cbc",
        b"aes128-cbc",
    ]
    supportedMACs = [b"hmac-sha2-512", b"hmac-sha2-256", b"hmac-sha1"]

    def connectionMade(self) -> None:
        if self.transport is not None:
            print(
                "New connection: %s:%s (%s:%s) [session: %d]"
                % (
                    self.transport.getPeer().host,  # type: ignore
                    self.transport.getPeer().port,  # type: ignore
                    self.transport.getHost().host,  # type: ignore
                    self.transport.getHost().port,  # type: ignore
                    self.transport.sessionno,  # type: ignore
                )
            )
        self.interactors: List[Any] = []
        self.ttylog_open = False
        transport.SSHServerTransport.connectionMade(self)

    def sendKexInit(self) -> None:
        # Don't send key exchange prematurely
        if not self.gotVersion:
            return
        transport.SSHServerTransport.sendKexInit(self)

    def dataReceived(self, data: bytes) -> None:
        transport.SSHServerTransport.dataReceived(self, data)

    def ssh_KEXINIT(self, packet: bytes) -> Any:
        from twisted.python import log
        from twisted.conch.ssh.common import getNS

        log.msg("Remote SSH version: %r" % self.otherVersionString)

        k = getNS(packet[16:], 10)
        strings = k[:-1]
        kexAlgs, keyAlgs, encCS, encSC, macCS, macSC, compCS, compSC, langCS, langSC = (
            s.split(b",") for s in strings
        )

        log.msg("Client kexAlgs: %s" % kexAlgs)
        log.msg("Client keyAlgs: %s" % keyAlgs)
        log.msg("Client encCS: %s" % encCS)
        log.msg("Client macCS: %s" % macCS)

        # Log what we have
        log.msg("Server supportedKeyExchanges: %s" % self.supportedKeyExchanges)
        log.msg("Server supportedPublicKeys: %s" % self.supportedPublicKeys)
        log.msg("Server supportedCiphers: %s" % self.supportedCiphers)
        log.msg("Server supportedMACs: %s" % self.supportedMACs)

        return transport.SSHServerTransport.ssh_KEXINIT(self, packet)

    # this seems to be the only reliable place of catching lost connection
    def connectionLost(self, reason: Any = None) -> None:  # type: ignore[override]
        for i in self.interactors:
            i.sessionClosed()
        if (
            hasattr(self.factory, "sessions")
            and hasattr(self, "transport")
            and getattr(self.transport, "sessionno", None) in getattr(self.factory, "sessions", {})
        ):
            del self.factory.sessions[self.transport.sessionno]  # type: ignore[union-attr]
        transport.SSHServerTransport.connectionLost(self, reason)


class SSHFactory(factory.SSHFactory):
    def __init__(self) -> None:
        self.sessions: Dict[int, Any] = {}
        self.portal: Any = None
        self.publicKeys: Dict[bytes, Any] = {}
        self.privateKeys: Dict[bytes, Any] = {}
        self.services: Dict[bytes, Any] = {}

    def buildProtocol(self, addr: Any) -> SSHTransport:
        _modulis = "/etc/ssh/moduli", "/private/etc/moduli"

        t = SSHTransport()
        t.ourVersionString = b"SSH-2.0-OpenSSH_Mock MockSSH.py"
        # Support only modern host key algorithms
        t.supportedPublicKeys = [
            b"ssh-ed25519",
            b"ecdsa-sha2-nistp256",
            b"rsa-sha2-256",
            b"rsa-sha2-512",
        ]

        print("DEBUG: buildProtocol supportedPublicKeys:", t.supportedPublicKeys)
        print("DEBUG: buildProtocol supportedKeyExchanges:", t.supportedKeyExchanges)

        for _moduli in _modulis:
            try:
                self.primes = primes.parseModuliFile(_moduli)
                break
            except IOError:
                pass

        if not getattr(self, "primes", None):
            ske = t.supportedKeyExchanges[:]
            for weak_kex in [
                b"diffie-hellman-group-exchange-sha1",
                b"diffie-hellman-group14-sha1",
            ]:
                if weak_kex in ske:
                    ske.remove(weak_kex)
            t.supportedKeyExchanges = ske

        t.factory = self
        return t


class command_exit(SSHCommand):
    name = "exit"

    def call(self) -> None:
        self.protocol.terminal.loseConnection()


# Functions
def getHostKeys(keypath: str = ".") -> Dict[str, Any]:
    if not os.path.exists(keypath):
        print("Could not find specified keypath:", keypath)
        sys.exit(1)

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519, ec
    from cryptography.hazmat.backends import default_backend

    keys_data = {}

    # Define key types we want to generate
    key_types: List[Tuple[str, str, Callable[[], Any]]] = [
        ("ed25519", "ssh-ed25519", lambda: ed25519.Ed25519PrivateKey.generate()),
        (
            "ecdsa",
            "ecdsa-sha2-nistp256",
            lambda: ec.generate_private_key(ec.SECP256R1(), default_backend()),
        ),
    ]

    for key_id, alg, gen_func in key_types:
        priv_file = os.path.join(keypath, "id_%s" % key_id)
        if not os.path.exists(priv_file):
            sys.stdout.write("Generating %s key... " % key_id)
            private_key = gen_func()

            # Export private key in OpenSSH format for best compatibility with Twisted
            private_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.OpenSSH,
                encryption_algorithm=serialization.NoEncryption(),
            )

            with open(priv_file, "wb") as f:
                f.write(private_bytes)
            sys.stdout.write("Done.\n")
        else:
            with open(priv_file, "rb") as f:
                private_bytes = f.read()

        # Load into Twisted Key object
        keys_data[key_id] = keys.Key.fromString(data=private_bytes)

    return keys_data


def getSSHFactory(commands: Any, prompt: str, keypath: str, **users: Any) -> SSHFactory:
    if not users:
        raise SSHServerError(
            "You must provide at least one username/password combination to run this SSH server."
        )

    cmds = {}
    for command in commands:
        cmds[command.name] = command
    commands = cmds

    for exit_cmd in ["_exit", "exit"]:
        if exit_cmd not in commands:
            commands[exit_cmd] = command_exit

    # Use our custom SSHFactory
    sshFactory = SSHFactory()

    from twisted.python import log

    log.msg("Created SSHFactory: %s" % sshFactory)
    sshFactory.portal = portal.Portal(SSHRealm(prompt=prompt, commands=commands))  # type: ignore

    b_users = {u: p.encode("utf-8") if isinstance(p, str) else p for u, p in users.items()}
    sshFactory.portal.registerChecker(checkers.InMemoryUsernamePasswordDatabaseDontUse(**b_users))  # type: ignore[arg-type]

    host_keys_data = getHostKeys(keypath)

    # Map algorithm names to Key objects
    host_keys = {
        b"ssh-ed25519": host_keys_data["ed25519"],
        b"ecdsa-sha2-nistp256": host_keys_data["ecdsa"],
    }

    sshFactory.publicKeys = host_keys
    sshFactory.privateKeys = host_keys

    sshFactory.services = {
        b"ssh-userauth": userauth.SSHUserAuthServer,
        b"ssh-connection": connection.SSHConnection,
    }

    return sshFactory


# TODO: refactor this stuff in a class
def runServer(
    commands: Any,
    prompt: str = "$ ",
    keypath: str = ".",
    interface: str = "",
    port: int = 2222,
    **users: Any,
) -> None:
    sshFactory = getSSHFactory(commands, prompt, keypath, **users)
    reactor.listenTCP(port, sshFactory, interface=interface)  # type: ignore
    reactor.run()  # type: ignore


def startThreadedServer(
    commands: Any,
    prompt: str = "$ ",
    keypath: str = "./generated-keys/",
    interface: str = "",
    port: int = 2222,
    **users: Any,
) -> Any:
    """
    Run a threaded MockSSH Server.
    Returns the IListeningPort object.
    """
    sshFactory = getSSHFactory(commands, prompt, keypath, **users)
    server_port = reactor.listenTCP(port, sshFactory, interface=interface)  # type: ignore
    if not reactor.running:  # type: ignore
        Thread(target=reactor.run, args=(False,)).start()  # type: ignore
    return server_port


def stopThreadedServer(server_port: Optional[Any] = None) -> None:
    if server_port:
        reactor.callFromThread(server_port.stopListening)  # type: ignore
    else:
        reactor.callFromThread(reactor.stop)  # type: ignore


if __name__ == "__main__":
    users = {"root": "x"}
    commands = [command_exit]
    runServer(commands, **users)  # type: ignore[arg-type]
