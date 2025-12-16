"""Run the Ubuntu Desktop Commander MCP server as a module.

Usage:
    python -m ubuntu_desktop --transport stdio
    python -m ubuntu_desktop --transport sse --port 8765
    python -m ubuntu_desktop --transport streamable-http --port 8765
"""

from ubuntu_desktop.server import main


if __name__ == "__main__":
    main()
