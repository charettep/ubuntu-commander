"""
Allow running the desktop server as a module:
    python -m mcp.desktop
"""

from mcp.desktop.server import main

if __name__ == "__main__":
    main()
