from __future__ import annotations

from typing import Literal

from mcp.server.fastmcp import FastMCP

from .tmux import TmuxClient


def register_tools(server: FastMCP, client: TmuxClient) -> None:
    """Register shell control tools on a FastMCP server."""

    @server.tool()
    def list_sessions() -> list[str]:
        """Returns list of available tmux sessions."""
        return client.list_sessions()

    @server.tool()
    def capture(session: str, scroll_back: int = 0) -> str:
        """Captures current terminal screen text."""
        return client.capture(session=session, scroll_back=scroll_back)

    @server.tool()
    def send_keys(session: str, keys: str) -> None:
        """Sends key input. Supports tmux key notation (Enter, C-c, etc.)."""
        client.send_keys(session=session, keys=keys)

    @server.tool()
    def send_text(session: str, text: str, enter: bool = False) -> None:
        """Sends literal text via tmux buffer. Supports multiline text with \\n and \\t.

        Use enter=True for shell commands - automatically presses Enter after sending.
        Use enter=False (default) for editors - newlines are preserved as text.

        Examples:
            - Shell: send_text(session, "ls -la", enter=True) -> executes command
            - Editor: send_text(session, "line1\\nline2") -> pastes two lines
        """
        bracketed = not enter
        client.send_text(session=session, text=text, bracketed=bracketed)
        if enter:
            client.send_keys(session=session, keys="Enter")

    @server.tool()
    def scroll(session: str, direction: Literal["up", "down"], amount: int | None = 1) -> None:
        """Navigates the scrollback buffer (half-pages by default)."""
        client.scroll(session=session, direction=direction, amount=amount or 1)

    @server.tool()
    def exit_scroll_mode(session: str) -> None:
        """Exits tmux copy-mode and returns to normal mode."""
        client.exit_scroll_mode(session=session)
