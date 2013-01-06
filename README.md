MockSSH
=======

Mock an SSH server and define all commands it supports (Python, Twisted)

MockSSH is based on [kippo](http://code.google.com/p/kippo/), an SSH honeypot.

Purpose
-------
This was developed to emulate different operating systems running SSH servers
in order to test task automation without having access to the actual servers.

Implementing Commands
---------------------
Since this is heavily based on kippo, you can consult its [source code](http://code.google.com/p/kippo/source/browse/trunk#trunk%2Fkippo%2Fcommands) to 
see how different commands are implemented.

Requirements
------------
* Python >= 2.5
* Twisted >= 8.0
* PyCrypto
* Zope Interface
