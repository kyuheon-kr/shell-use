from __future__ import annotations

import os
import sys

from mcp.server.fastmcp import FastMCP

from .tmux import Runner, TmuxClient, create_local_runner, create_socket_runner
from .tools import register_tools

SERVER_NAME = "shell-use"
INSTRUCTIONS = (
    "Let agents use the shell like a human. View terminal output, type commands, scroll through history, "
    "and interact with any CLI application."
)


def create_runner_from_env() -> Runner:
    """Create a tmux runner based on environment variables.

    Environment variables:
        SHELL_USE_SOCKET: Path to tmux socket file (for Docker with mounted host socket)
    """
    if socket_path := os.environ.get("SHELL_USE_SOCKET"):
        return create_socket_runner(socket_path)

    return create_local_runner()


def get_allowed_sessions() -> list[str]:
    """Get allowed sessions from environment variable.

    Environment variables:
        SHELL_USE_SESSIONS: Comma-separated list of allowed session names (required)
    """
    sessions_str = os.environ.get("SHELL_USE_SESSIONS", "")
    if not sessions_str:
        print("Error: SHELL_USE_SESSIONS environment variable is required.", file=sys.stderr)
        print("Example: SHELL_USE_SESSIONS=dev,work shell-use", file=sys.stderr)
        sys.exit(1)

    return [s.strip() for s in sessions_str.split(",") if s.strip()]


def create_server() -> FastMCP:
    """Create and configure the shell-use FastMCP server."""
    runner = create_runner_from_env()
    allowed_sessions = get_allowed_sessions()
    client = TmuxClient(allowed_sessions=allowed_sessions, runner=runner)
    server = FastMCP(name=SERVER_NAME, instructions=INSTRUCTIONS)
    register_tools(server, client)
    return server


def main() -> None:
    """Start the MCP server using stdio transport."""
    server = create_server()
    server.run()


if __name__ == "__main__":  # pragma: no cover
    main()
