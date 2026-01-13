import os
from unittest import mock

from shell_use.server import create_runner_from_env, get_allowed_sessions, create_server


def test_create_runner_from_env_uses_local_runner_by_default():
    """When no env vars set, uses local runner."""
    with mock.patch.dict(os.environ, {}, clear=True):
        runner = create_runner_from_env()
        assert runner is not None


def test_create_runner_from_env_uses_socket_runner_when_socket_set():
    """When SHELL_USE_SOCKET is set, uses socket runner."""
    with mock.patch.dict(os.environ, {"SHELL_USE_SOCKET": "/tmp/test.sock"}, clear=True):
        runner = create_runner_from_env()
        assert runner is not None


def test_get_allowed_sessions_parses_comma_separated():
    """SHELL_USE_SESSIONS is parsed as comma-separated list."""
    with mock.patch.dict(os.environ, {"SHELL_USE_SESSIONS": "dev, work, test"}, clear=True):
        sessions = get_allowed_sessions()
        assert sessions == ["dev", "work", "test"]


def test_get_allowed_sessions_exits_when_not_set(capsys):
    """When SHELL_USE_SESSIONS is not set, exits with error."""
    import pytest
    with mock.patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SystemExit) as exc_info:
            get_allowed_sessions()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "SHELL_USE_SESSIONS" in captured.err


def test_create_server_returns_fastmcp_instance():
    """create_server returns a configured FastMCP server."""
    with mock.patch.dict(os.environ, {"SHELL_USE_SESSIONS": "dev"}, clear=True):
        server = create_server()
        assert server.name == "shell-use"
