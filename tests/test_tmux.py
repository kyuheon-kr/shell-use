import subprocess

import pytest

from shell_use.tmux import TmuxClient, TmuxError


def completed(stdout: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")


def runner_with(responses):
    calls: list[tuple[list[str], str | None]] = []
    iterator = iter(responses)

    def _runner(args: list[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
        calls.append((args, input_text))
        result = next(iterator)
        if isinstance(result, Exception):
            raise result
        return result

    _runner.calls = calls  # type: ignore[attr-defined]
    return _runner


def test_list_sessions_returns_allowed_sessions():
    runner = runner_with([])
    client = TmuxClient(allowed_sessions=["dev", "work"], runner=runner)

    assert client.list_sessions() == ["dev", "work"]


def test_capture_includes_scrollback():
    runner = runner_with([completed("screen")])
    client = TmuxClient(allowed_sessions=["dev"], runner=runner)

    assert client.capture("dev", scroll_back=50) == "screen"
    assert runner.calls[0] == (["capture-pane", "-t", "dev", "-p", "-S", "-50"], None)  # type: ignore[index]


def test_send_keys_and_text_commands():
    runner = runner_with([completed(), completed(), completed()])
    client = TmuxClient(allowed_sessions=["dev"], runner=runner)

    client.send_keys("dev", "Enter")
    client.send_text("dev", "echo hi")

    assert runner.calls[0] == (["send-keys", "-t", "dev", "Enter"], None)  # type: ignore[index]
    assert runner.calls[1] == (["load-buffer", "-"], "echo hi")  # type: ignore[index]
    assert runner.calls[2] == (["paste-buffer", "-d", "-p", "-t", "dev"], None)  # type: ignore[index]


def test_send_text_without_bracketed_paste():
    runner = runner_with([completed(), completed()])
    client = TmuxClient(allowed_sessions=["dev"], runner=runner)

    client.send_text("dev", "echo hi\n", bracketed=False)

    assert runner.calls[0] == (["load-buffer", "-"], "echo hi\n")  # type: ignore[index]
    assert runner.calls[1] == (["paste-buffer", "-d", "-t", "dev"], None)  # type: ignore[index]


def test_scroll_uses_copy_mode_and_repeats():
    runner = runner_with([completed(), completed(), completed()])
    client = TmuxClient(allowed_sessions=["dev"], runner=runner)

    client.scroll("dev", direction="up", amount=2)

    assert runner.calls[0] == (["copy-mode", "-t", "dev"], None)  # type: ignore[index]
    assert runner.calls[1] == (["send-keys", "-t", "dev", "-X", "halfpage-up"], None)  # type: ignore[index]
    assert runner.calls[2] == (["send-keys", "-t", "dev", "-X", "halfpage-up"], None)  # type: ignore[index]


def test_exit_scroll_mode_sends_cancel():
    runner = runner_with([completed()])
    client = TmuxClient(allowed_sessions=["dev"], runner=runner)

    client.exit_scroll_mode("dev")

    assert runner.calls[0] == (["send-keys", "-t", "dev", "-X", "cancel"], None)  # type: ignore[index]


def test_invalid_inputs_raise_errors():
    client = TmuxClient(allowed_sessions=["dev"], runner=runner_with([completed()]))

    with pytest.raises(ValueError):
        client.capture("dev", scroll_back=-1)

    with pytest.raises(ValueError):
        client.scroll("dev", direction="down", amount=0)

    with pytest.raises(ValueError):
        client.scroll("dev", direction="left", amount=1)


def test_called_process_error_translates_to_tmux_error():
    error = subprocess.CalledProcessError(returncode=1, cmd="tmux", stderr="no server running")
    client = TmuxClient(allowed_sessions=["dev"], runner=runner_with([error]))

    with pytest.raises(TmuxError, match="no server running"):
        client.capture("dev")


def test_session_not_in_allowed_list_raises_error():
    client = TmuxClient(allowed_sessions=["dev"], runner=runner_with([]))

    with pytest.raises(TmuxError, match="not in allowed list"):
        client.capture("other")


def test_empty_allowed_sessions_raises_error():
    with pytest.raises(ValueError, match="must not be empty"):
        TmuxClient(allowed_sessions=[], runner=runner_with([]))
