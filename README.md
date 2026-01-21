## shell-use

Let agents use the shell like a human.

---

### Features

- Interact with any CLI application (vim, htop, gdb, etc.)
- Send special keys (Ctrl+C, Enter, arrow keys, etc.)
- Dockerized for easy deployment

### Available Tools

| Tool | Description |
|------|-------------|
| `list_sessions()` | Returns allowed session names |
| `capture(session, scroll_back?)` | Captures terminal screen text |
| `send_keys(session, keys)` | Sends key input (e.g., `Enter`, `C-c`) |
| `send_text(session, text, enter?)` | Sends literal text (`enter=True` to press Enter) |
| `scroll(session, direction, amount?)` | Scrolls through history |
| `exit_scroll_mode(session)` | Exits copy-mode |

---

### Setup

#### 1. Build the Docker image

```bash
docker build -t shell-use:latest .
```

#### 2. Create a tmux session

```bash
tmux new-session -s dev
```

#### 2.1. Get the tmux socket path

```bash
SOCK="$(tmux display-message -p -F '#{socket_path}')"
[ -S "$SOCK" ] || { echo "tmux socket not found: $SOCK"; exit 1; }
```

#### 3. Configure your MCP client

**Claude Code**:

```bash
claude mcp add shell-use \
  -e SHELL_USE_SESSIONS=dev \
  -- docker run -i --rm \
  -v "$SOCK":/tmux/tmux.sock \
  -e SHELL_USE_SOCKET=/tmux/tmux.sock \
  -e SHELL_USE_SESSIONS \
  shell-use:latest
```

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "shell-use": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/tmp/tmux-1000/default:/tmux/tmux.sock",
        "-e", "SHELL_USE_SOCKET=/tmux/tmux.sock",
        "-e", "SHELL_USE_SESSIONS",
        "shell-use:latest"
      ],
      "env": {
        "SHELL_USE_SESSIONS": "dev"
      }
    }
  }
}
```

> Replace `/tmp/tmux-1000/default` with the path from
> `tmux display-message -p -F '#{socket_path}'`.

---

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SHELL_USE_SESSIONS` | Comma-separated list of allowed session names | Yes |
| `SHELL_USE_SOCKET` | Path to tmux socket (default: `/tmux/tmux.sock` in Docker) | No |

---

### Acknowledgments

Inspired by [browser-use](https://github.com/browser-use/browser-use).
