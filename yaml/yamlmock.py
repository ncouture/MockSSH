#!/usr/bin/python
#

import sys
import yaml
import MockSSH


def get_prompt_command(name, config):
    output = config['output']
    expected_input = config['input']

    success_callbacks = []
    failure_callbacks = []

    for event in ('on-success', 'on-failure'):
        for kwdict in config[event]:
            for action in kwdict:
                if action in ['write', 'set-prompt', 'call-command']:
                    if 'success' in event:
                        func = success_callbacks.append
                    elif 'failure' in event:
                        func = failure_callbacks.append
                    func((action, kwdict[action]))

    return MockSSH.PasswordPromptingCommand(
        name,
        password=expected_input,
        password_prompt=output,
        success_callbacks=success_callbacks,
        failure_callbacks=failure_callbacks)


def get_standard_commmand(name, config):
    success_callbacks = []
    failure_callbacks = []

    callback = ('on-success', 'on-failure')
    events = [event for event in callback if event in config]
    for event in events:
        for kwdict in config[event]:
            for action in kwdict:
                if action in ['write', 'set-prompt', 'call-command']:
                    if 'success' in event:
                        func = success_callbacks.append
                    elif 'failure' in event:
                        func = failure_callbacks.append
                    func((action, kwdict[action]))

    complexes = ['prompt-match', 
                 'else']
    events = [event for event in complexes if event in config]
    for event in events:
        test = config[event][0]
        actions = config[event][1::]
        cond_action = None
        for action in actions:
            for key in ['write', 'set-prompt', 'call-command']:
                if key in action:
                    r_action = action
            if 'else' in action:
                cond_action = action

        success_callbacks.append((event,
                                  test,
                                  r_action,
                                  cond_action))

    args = config.get('args') or []
    return MockSSH.ArgumentValidatingCommand(
        name,
        success_callbacks,
        failure_callbacks,
        *args)


def start_mockssh(commands, **kwargs):
    interface = kwargs.get('host') or '127.0.0.1'
    keypath = kwargs.get('keypath') or '.'
    prompt = kwargs.get('prompt') or 'mockssh$'
    users = kwargs.get('users') or {'testadmin': "x"}
    port = kwargs.get('port') or 2222

    MockSSH.runServer(commands,
                      prompt=prompt,
                      keypath=keypath,
                      interface=interface,
                      port=port,
                      **users)


def get_commands(commands):
    cmds = []
    for cmd in commands:
        if commands[cmd]['type'] == 'prompt':
            cmds.append(get_prompt_command(cmd, commands[cmd]))
        if commands[cmd]['type'] == 'command':
                cmds.append(get_standard_commmand(cmd, commands[cmd]))
    return cmds


def main():
    conf = yaml.load(open('example.yaml').read())
    commands = get_commands(conf['commands'])
    start_mockssh(commands, **conf['ssh-server'])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print "User interrupted"
        sys.exit(1)
