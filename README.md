MockSSH
=======

Mock an SSH server and all commands it supports.


Purpose
-------
This project was developed to emulate operating systems
behind SSH servers in order to test task automation without
having access to the real servers.

There has been user interest in using MockSSH to perform
end-to-end unit tests against SSH servers and as such a
threaded version of MockSSH server is available as of
version 1.4 (thanks to Claudio Mignanti).


MockSSH in Python
-----------------
MockSSH aims to be as easy to use as possible.

Refer to the mock_cisco.py and mock_F5.py in the examples/
directory for an overview on how to use it.


MockSSH in LISP
---------------
Efforts were invested in simplifying the use of MockSSH
with [HyLang](http://hylang.org/).

As a result a DSL is released with this project and
resides in the *mocksshy/* directory.

Using the DSL will allow you to use MockSSH by writing
something that is closer to a configuration file than
a program.

For comparison, here are two MockSSH servers
implementations providing the same functionality:


*Python*
```python
import MockSSH

def passwd_change_protocol_prompt(instance):
    instance.protocol.prompt = "hostname #"
    instance.protocol.password_input = False

def passwd_write_password_to_transport(instance):
    instance.writeln("MockSSH: password is %s" % instance.valid_password)

command_passwd = MockSSH.PromptingCommand(
    name='passwd',
    password='1234',
    password_prompt="Password: ",
    success_callbacks=[passwd_change_protocol_prompt],
    failure_callbacks=[passwd_write_password_to_transport])

users = {'admin': '1234'}

commands = [command_passwd]

MockSSH.runServer(commands,
                  prompt="hostname>",
                  interface='127.0.0.1',
                  port=2222,
                  **users)
```

*HyLang*
```clojure
(import MockSSH)
(require mocksshy.language)


(mock-ssh :users {"testuser" "1234"}
          :host "127.0.0.1"
          :port 2222
          :prompt "hostname>"
          :commands [
  (command :name "passwd"
           :type "prompt"
           :output "Password: "
           :required-input "1234"
           :on-success ["prompt" "hostname#"]
           :on-failure ["write" "Pass is 1234..."]))
```


Unit Testing with MockSSH
-------------------------
As shown from the unit tests in the tests/ directory, it is possible to use
a threaded MockSSH server to perform end-to-end unit tests against mocked
SSH services.

Note that this is a hack and may not be the right approach depending on your
use case as only one Twisted reactor can run at the same time and reactors
cannot be restarted.

Source
------
MockSSH is derived from [kippo](https://github.com/desaster/kippo/), an SSH honeypot.
