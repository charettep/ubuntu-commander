# Ubuntu Desktop Commander (FastMCP)

Desktop automation MCP server for Ubuntu/X11 using FastMCP. Provides tools for screenshots, UI element detection (template + OCR), mouse control, and keyboard control.

## Requirements
- Python 3.10+
- Ubuntu/X11 session (pyautogui uses X11)
- System: `sudo apt install tesseract-ocr` (for OCR tools)
- Python deps: `pip install "mcp[fastmcp]" pyautogui pillow pytesseract`

## Run
- StdIO (typical MCP client):
	- `python -m mcp.desktop.server --transport stdio`
- SSE: `python -m mcp.desktop.server --transport sse --port 8765`
- Streamable HTTP: `python -m mcp.desktop.server --transport streamable-http --port 8765`

## Tools
- Screenshot: `screenshot`, `screenshot_region`, `get_screen_info`
- Detection: `find_image_on_screen` (template match), `find_text_on_screen_ocr` (OCR)
- Mouse: `move_mouse`, `click_mouse`, `drag_mouse`, `scroll_mouse`
- Keyboard: `type_text`, `press_key`, `press_hotkey`
- Resource: `screen://info`

Tips:
- Keep screenshots under ~1MB (use lower JPEG quality).
- Ensure the target window is focused before typing/pressing keys.
- OCR requires tesseract and may be slower; prefer template matching when possible.
