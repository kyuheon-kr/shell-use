FROM python:3.12-slim

# Label used by MCP clients to discover the server
LABEL io.modelcontextprotocol.server.name="io.github.kyuheon-kr/shell-use"

WORKDIR /app

# Install tmux and ssh client for remote control
RUN apt-get update && apt-get install -y --no-install-recommends \
    tmux \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src ./src
COPY main.py ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Default socket path for mounted host tmux socket
ENV SHELL_USE_SOCKET=/tmux/tmux.sock

# Run the MCP server
CMD ["uv", "run", "python", "main.py"]
