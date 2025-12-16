"""
Ubuntu Desktop Commander MCP Server

A FastMCP server providing desktop automation tools for Ubuntu/X11:
- Screenshot capture
- GUI element detection (template matching, OCR)
- Mouse control (move, click, drag)
- Keyboard input
"""

from mcp.desktop.server import mcp, main

__all__ = ["mcp", "main"]
