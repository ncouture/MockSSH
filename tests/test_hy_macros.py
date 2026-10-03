import hy
import pytest

import MockSSH


@pytest.fixture
def ev():
    ns = {"MockSSH": MockSSH}
    hy.eval(hy.read("(require mocksshy.language *)"), ns)

    def _ev(source):
        return hy.eval(hy.read(source), ns)

    return _ev


class FakeInstance:
    def __init__(self):
        self.written = []
        self.protocol = type("P", (), {"prompt": None})()

    def writeln(self, text):
        self.written.append(text)


def test_output_command_expansion(ev):
    cmd = ev(
        '(command :name "ls" :type "output" :args ["-1"]'
        ' :on-success ["write" "ok"] :on-failure ["write" "bad"])'
    )
    assert isinstance(cmd, MockSSH.ArgumentValidatingCommand)
    assert cmd.name == "ls"
    assert cmd.required_arguments == ["-1"]
    inst = FakeInstance()
    cmd.success_callbacks[0](inst)
    cmd.failure_callbacks[0](inst)
    assert inst.written == ["ok", "bad"]


def test_output_command_without_args(ev):
    cmd = ev('(output-command :name "x" :on-success [] :on-failure [])')
    assert cmd.required_arguments == []
    assert cmd.success_callbacks == []


def test_prompt_command_expansion(ev):
    cmd = ev(
        '(command :name "en" :type "prompt" :output "Password: "'
        ' :required-input "1234" :on-success ["prompt" "host#"]'
        ' :on-failure ["write" "denied"])'
    )
    assert isinstance(cmd, MockSSH.PromptingCommand)
    assert cmd.name == "en"
    assert cmd.prompt == "Password: "
    assert cmd.valid_password == "1234"
    inst = FakeInstance()
    cmd.success_callbacks[0](inst)
    cmd.failure_callbacks[0](inst)
    assert inst.protocol.prompt == "host#"
    assert inst.written == ["denied"]


def test_type_given_as_symbol(ev):
    cmd = ev(
        '(command :name "en" :type prompt :output "P" :required-input "1"'
        ' :on-success ["prompt" "h#"] :on-failure ["write" "no"])'
    )
    assert isinstance(cmd, MockSSH.PromptingCommand)


def test_unsupported_type(ev):
    with pytest.raises(Exception, match=r"command 'x'.*unsupported :type 'bogus'"):
        ev('(command :name "x" :type "bogus")')


def test_missing_type(ev):
    with pytest.raises(Exception, match=r"command 'x'.*missing required :type"):
        ev('(command :name "x")')


def test_missing_name(ev):
    with pytest.raises(Exception, match="missing required :name"):
        ev('(command :type "output")')
    with pytest.raises(Exception, match="missing required :name"):
        ev('(prompting-command :output "p")')


def test_unknown_and_duplicate_keys(ev):
    with pytest.raises(Exception, match="unknown or misplaced argument"):
        ev('(output-command :name "x" :bogus 1)')
    with pytest.raises(Exception, match="more than once"):
        ev('(output-command :name "x" :name "y")')


@pytest.mark.parametrize(
    "source, message",
    [
        ('(output-command :name "x" :on-success "write" :on-failure [])', "must be a list"),
        ('(output-command :name "x" :on-success ["write"] :on-failure [])', "even list"),
        ('(output-command :name "x" :on-success [] :on-failure None)', "must be a list"),
        (
            '(output-command :name "x" :on-success ["nope" "a"] :on-failure [])',
            "unsupported :on-success action 'nope'",
        ),
        (
            '(prompting-command :name "x" :on-success ["prompt"] :on-failure ["write" "a"])',
            "exactly two",
        ),
        (
            '(prompting-command :name "x" :on-success ["write" "a"] :on-failure ["write" "a"])',
            "unsupported :on-success action 'write'",
        ),
        (
            '(prompting-command :name "x" :on-success ["prompt" "a"] :on-failure ["prompt" "a"])',
            "unsupported :on-failure action 'prompt'",
        ),
        ('(prompting-command :name "x" :on-success ["prompt" "a"])', "must be a list"),
        ("(output-command :name 5 :on-success [] :on-failure [])", "name must be a string"),
    ],
)
def test_malformed_callbacks(ev, source, message):
    with pytest.raises(MockSSH.MockSSHError, match=message):
        ev(source)
