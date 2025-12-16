"""
Ubuntu Desktop Commander - FastMCP Server

A FastMCP server providing desktop automation tools for Ubuntu/X11:
- Screenshot capture
- GUI element detection (template matching, OCR)
- Mouse control (move, click, drag)
- Keyboard input

Usage:
    # Run with stdio transport (default for MCP clients)
    python -m mcp.desktop.server

    # Run with SSE transport
    python -m mcp.desktop.server --transport sse --port 8000

    # Run with streamable HTTP
    python -m mcp.desktop.server --transport streamable-http --port 8000
"""

from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.utilities.types import Image

from mcp.desktop.input import (
    get_mouse_position,
    keyboard_hotkey,
    keyboard_press,
    keyboard_type,
    mouse_click,
    mouse_drag,
    mouse_move,
    mouse_scroll,
)
from mcp.desktop.vision import (
    capture_screenshot,
    find_template_on_screen,
    find_text_on_screen,
    get_screen_size,
)


# Create the FastMCP server
mcp = FastMCP(
    "Ubuntu Desktop Commander",
    dependencies=["pyautogui", "Pillow", "pytesseract"],
)


# =============================================================================
# Screenshot Tools
# =============================================================================


@mcp.tool()
def screenshot(
    quality: Annotated[int, "JPEG quality 1-100, lower=smaller"] = 60,
    format: Annotated[Literal["jpeg", "png"], "Image format"] = "jpeg",
) -> Image:
    """
    Capture a screenshot of the entire screen.

    Returns the screenshot as an image that can be viewed directly.
    Use this tool to see what's currently displayed on the user's screen.

    Note: For Claude, images should be under ~1MB. Lower quality for smaller files.
    """
    data, fmt = capture_screenshot(quality=quality, format=format)
    return Image(data=data, format=fmt)


@mcp.tool()
def screenshot_region(
    x: Annotated[int, "Left X coordinate"],
    y: Annotated[int, "Top Y coordinate"],
    width: Annotated[int, "Width of region"],
    height: Annotated[int, "Height of region"],
    quality: Annotated[int, "JPEG quality 1-100"] = 60,
) -> Image:
    """
    Capture a screenshot of a specific screen region.

    Args:
        x: Left edge X coordinate
        y: Top edge Y coordinate
        width: Width of the region to capture
        height: Height of the region to capture
        quality: JPEG quality (1-100), lower = smaller file

    Returns the cropped screenshot as an image.
    """
    data, fmt = capture_screenshot(quality=quality, format="jpeg", region=(x, y, width, height))
    return Image(data=data, format=fmt)


@mcp.tool()
def get_screen_info() -> dict:
    """
    Get information about the screen.

    Returns:
        Dictionary with screen width, height, and current mouse position.
    """
    width, height = get_screen_size()
    mouse_x, mouse_y = get_mouse_position()
    return {
        "screen_width": width,
        "screen_height": height,
        "mouse_x": mouse_x,
        "mouse_y": mouse_y,
    }


# =============================================================================
# Element Detection Tools
# =============================================================================


@mcp.tool()
def find_image_on_screen(
    template_path: Annotated[str, "Path to template image file to search for"],
    confidence: Annotated[float, "Minimum match confidence 0.0-1.0"] = 0.8,
) -> list[dict]:
    """
    Find all occurrences of a template image on the screen.

    Uses template matching to locate UI elements. Provide a screenshot/image
    of the element you want to find.

    Args:
        template_path: Path to the template image file
        confidence: Minimum confidence threshold (0.8 recommended)

    Returns:
        List of matches with bounding boxes and center coordinates.
        Empty list if no matches found.
    """
    matches = find_template_on_screen(template_path, confidence=confidence)
    return [m.to_dict() for m in matches]


@mcp.tool()
def find_text_on_screen_ocr(
    text: Annotated[str, "Text to search for (case-insensitive)"],
    lang: Annotated[str, "Tesseract language code"] = "eng",
) -> list[dict]:
    """
    Find text on the screen using OCR.

    Searches the entire screen for text matching the query.
    Requires tesseract-ocr to be installed on the system.

    Args:
        text: Text to search for (case-insensitive substring match)
        lang: Tesseract language code (default: 'eng')

    Returns:
        List of matches with bounding boxes, confidence scores, and matched text.
        Empty list if no matches found.
    """
    matches = find_text_on_screen(text, lang=lang)
    return [m.to_dict() for m in matches]


# =============================================================================
# Mouse Control Tools
# =============================================================================


@mcp.tool()
def move_mouse(
    x: Annotated[int, "Target X coordinate"],
    y: Annotated[int, "Target Y coordinate"],
    duration: Annotated[float, "Movement duration in seconds"] = 0.5,
) -> dict:
    """
    Move the mouse cursor to specified screen coordinates.

    Args:
        x: Target X coordinate
        y: Target Y coordinate
        duration: How long the movement should take (for smooth motion)

    Returns:
        Dictionary with the final mouse position.
    """
    final_x, final_y = mouse_move(x, y, duration=duration)
    return {"x": final_x, "y": final_y}


@mcp.tool()
def click_mouse(
    x: Annotated[int | None, "X coordinate (None=current position)"] = None,
    y: Annotated[int | None, "Y coordinate (None=current position)"] = None,
    button: Annotated[Literal["left", "right", "middle"], "Mouse button"] = "left",
    clicks: Annotated[int, "Number of clicks"] = 1,
) -> dict:
    """
    Click the mouse at specified coordinates or current position.

    Args:
        x: X coordinate (None = click at current position)
        y: Y coordinate (None = click at current position)
        button: Which mouse button to click
        clicks: Number of clicks (2 for double-click)

    Returns:
        Dictionary with the click position.
    """
    click_x, click_y = mouse_click(x, y, button=button, clicks=clicks)
    return {"x": click_x, "y": click_y, "button": button, "clicks": clicks}


@mcp.tool()
def drag_mouse(
    start_x: Annotated[int, "Starting X coordinate"],
    start_y: Annotated[int, "Starting Y coordinate"],
    end_x: Annotated[int, "Ending X coordinate"],
    end_y: Annotated[int, "Ending Y coordinate"],
    duration: Annotated[float, "Drag duration in seconds"] = 0.5,
    button: Annotated[Literal["left", "right", "middle"], "Mouse button to hold"] = "left",
) -> dict:
    """
    Drag the mouse from one position to another.

    Performs a click-and-drag operation, useful for:
    - Moving windows
    - Selecting text
    - Dragging files
    - Drawing

    Args:
        start_x: Starting X coordinate
        start_y: Starting Y coordinate
        end_x: Ending X coordinate
        end_y: Ending Y coordinate
        duration: How long the drag should take
        button: Which mouse button to hold during drag

    Returns:
        Dictionary with start and end positions.
    """
    return mouse_drag(start_x, start_y, end_x, end_y, duration=duration, button=button)


@mcp.tool()
def scroll_mouse(
    clicks: Annotated[int, "Scroll amount (positive=up, negative=down)"],
    x: Annotated[int | None, "X coordinate (None=current position)"] = None,
    y: Annotated[int | None, "Y coordinate (None=current position)"] = None,
) -> dict:
    """
    Scroll the mouse wheel.

    Args:
        clicks: Number of scroll clicks (positive = scroll up, negative = scroll down)
        x: X coordinate to scroll at (None = current position)
        y: Y coordinate to scroll at (None = current position)

    Returns:
        Dictionary with the scroll position.
    """
    pos_x, pos_y = mouse_scroll(clicks, x, y)
    return {"x": pos_x, "y": pos_y, "scroll_clicks": clicks}


# =============================================================================
# Keyboard Control Tools
# =============================================================================


@mcp.tool()
def type_text(
    text: Annotated[str, "Text to type"],
    interval: Annotated[float, "Delay between keystrokes in seconds"] = 0.05,
) -> dict:
    """
    Type text using the keyboard.

    Types the specified text character by character.
    Note: This uses the keyboard, so the appropriate window must be focused.

    Args:
        text: The text to type
        interval: Delay between each keystroke

    Returns:
        Dictionary with the number of characters typed.
    """
    count = keyboard_type(text, interval=interval)
    return {"characters_typed": count, "text": text}


@mcp.tool()
def press_key(
    key: Annotated[str, "Key to press (e.g., 'enter', 'tab', 'escape', 'f1')"],
    presses: Annotated[int, "Number of times to press"] = 1,
) -> dict:
    """
    Press a keyboard key.

    Common keys: enter, tab, escape, space, backspace, delete,
    up, down, left, right, home, end, pageup, pagedown,
    f1-f12, ctrl, alt, shift, win

    Args:
        key: The key to press
        presses: How many times to press it

    Returns:
        Dictionary with the key pressed.
    """
    keyboard_press(key, presses=presses)
    return {"key": key, "presses": presses}


@mcp.tool()
def press_hotkey(
    keys: Annotated[list[str], "List of keys to press together (e.g., ['ctrl', 'c'])"],
) -> dict:
    """
    Press a keyboard hotkey combination.

    Examples:
    - Copy: ['ctrl', 'c']
    - Paste: ['ctrl', 'v']
    - Undo: ['ctrl', 'z']
    - Save: ['ctrl', 's']
    - Select all: ['ctrl', 'a']
    - Alt-Tab: ['alt', 'tab']
    - Screenshot: ['print']

    Args:
        keys: List of keys to press together

    Returns:
        Dictionary with the keys pressed.
    """
    pressed = keyboard_hotkey(*keys)
    return {"keys": pressed, "hotkey": "+".join(pressed)}


# =============================================================================
# Resources
# =============================================================================


@mcp.resource("screen://info")
def screen_info_resource() -> str:
    """Get current screen information as a resource."""
    width, height = get_screen_size()
    mouse_x, mouse_y = get_mouse_position()
    return f"Screen: {width}x{height}, Mouse: ({mouse_x}, {mouse_y})"


# =============================================================================
# Main Entry Point
# =============================================================================


def main():
    """Run the Ubuntu Desktop Commander MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="Ubuntu Desktop Commander MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport type (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to for HTTP transports (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port to bind to for HTTP transports (default: 8765)",
    )

    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run(transport="streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
