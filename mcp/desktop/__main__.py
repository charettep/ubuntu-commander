"""Run the Ubuntu Desktop Commander MCP server as a module.

Usage:
    python -m mcp.desktop --transport stdio
    python -m mcp.desktop --transport sse --port 8765
    python -m mcp.desktop --transport streamable-http --port 8765
"""

from mcp.desktop.server import main


if __name__ == "__main__":
    main()
