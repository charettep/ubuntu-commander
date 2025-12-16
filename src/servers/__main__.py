"""Run the Ubuntu Commander MCP server as a module.

Usage:
    python -m servers.server --transport stdio
    python -m servers.server --transport sse --port 8765
    python -m servers.server --transport streamable-http --port 8765
"""

from servers.server import main


if __name__ == "__main__":
    main()
