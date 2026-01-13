from __future__ import annotations

import subprocess
from typing import Callable, Literal


class TmuxError(RuntimeError):
    """Raised when a tmux command fails."""


Runner = Callable[[list[str], str | None], subprocess.CompletedProcess[str]]


def create_local_runner(tmux_bin: str = "tmux") -> Runner:
    """Create a runner for local tmux execution."""
    def runner(args: list[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [tmux_bin, *args],
            input=input_text,
            check=True,
            capture_output=True,
            text=True,
        )
    return runner


def create_socket_runner(socket_path: str, tmux_bin: str = "tmux") -> Runner:
    """Create a runner that connects via tmux socket."""
    def runner(args: list[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [tmux_bin, "-S", socket_path, *args],
            input=input_text,
            check=True,
            capture_output=True,
            text=True,
        )
    return runner


class TmuxClient:
    """Lightweight wrapper around the tmux CLI with session allowlist."""

    def __init__(
        self,
        allowed_sessions: list[str],
        tmux_bin: str = "tmux",
        runner: Runner | None = None,
    ) -> None:
        if not allowed_sessions:
            raise ValueError("allowed_sessions must not be empty")
        self.allowed_sessions = allowed_sessions
        self.tmux_bin = tmux_bin
        self._runner: Runner = runner or create_local_runner(tmux_bin)

    def _validate_session(self, session: str) -> None:
        if session not in self.allowed_sessions:
            raise TmuxError(f"Session '{session}' is not in allowed list: {self.allowed_sessions}")

    def _execute(self, args: list[str], input_text: str | None = None) -> str:
        try:
            result = self._runner(args, input_text)
        except FileNotFoundError as exc:  # pragma: no cover - environment specific
            raise TmuxError(f"tmux binary not found at {self.tmux_bin}") from exc
        except subprocess.CalledProcessError as exc:
            message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
            raise TmuxError(message) from exc

        return result.stdout or ""

    def list_sessions(self) -> list[str]:
        """Return allowed tmux session names."""
        return list(self.allowed_sessions)

    def capture(self, session: str, scroll_back: int = 0) -> str:
        """Capture text from a tmux session."""
        self._validate_session(session)
        if scroll_back < 0:
            raise ValueError("scroll_back must be >= 0")
        args = ["capture-pane", "-t", session, "-p", "-S", f"-{scroll_back}"]
        return self._execute(args)

    def send_keys(self, session: str, keys: str) -> None:
        """Send key input (Enter, C-c, etc.)."""
        self._validate_session(session)
        self._execute(["send-keys", "-t", session, keys])

    def send_text(self, session: str, text: str, bracketed: bool = True) -> None:
        """Send literal text via tmux buffer (supports newlines and special characters).

        Args:
            session: Target tmux session name.
            text: Text to send.
            bracketed: If True, use bracketed paste mode (editors handle newlines correctly).
                      If False, newlines trigger command execution in shells.
        """
        self._validate_session(session)
        self._execute(["load-buffer", "-"], input_text=text)
        paste_args = ["paste-buffer", "-d", "-t", session]
        if bracketed:
            paste_args.insert(2, "-p")
        self._execute(paste_args)

    def scroll(self, session: str, direction: Literal["up", "down"], amount: int = 1) -> None:
        """Scroll a session's history using tmux copy-mode."""
        self._validate_session(session)
        if amount < 1:
            raise ValueError("amount must be >= 1")
        if direction not in ("up", "down"):
            raise ValueError("direction must be 'up' or 'down'")
        self._execute(["copy-mode", "-t", session])
        key = "halfpage-up" if direction == "up" else "halfpage-down"
        for _ in range(amount):
            self._execute(["send-keys", "-t", session, "-X", key])

    def exit_scroll_mode(self, session: str) -> None:
        """Exit tmux copy-mode."""
        self._validate_session(session)
        self._execute(["send-keys", "-t", session, "-X", "cancel"])
