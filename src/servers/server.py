"""
Ubuntu Commander - FastMCP Server for Desktop Automation

Provides 4 atomic tools following the observe-analyze-act pattern for agentic computer use:

1. get_screen    → OBSERVE: Screenshot + display info + mouse position
2. analyze_screen → PERCEIVE: OCR/template detection, element positions, caching
3. use_mouse     → ACT: Move, click, drag, scroll
4. use_keyboard  → ACT: Type, press keys, hotkeys

Design principles:
- Atomic tools that compose well for multi-step workflows
- Separation of observation (get_screen) from perception (analyze_screen)
- Cached analysis results for fast repeated lookups
- Minimal parameters with sensible defaults for common cases
- Rich return values with all info needed for next action

Usage:
    ubuntu-commander --transport stdio
    ubuntu-commander --transport sse --port 8765
"""

import time
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.utilities.types import Image

from .input import (
    fast_click,
    get_action_pause,
    get_mouse_position,
    instant_move,
    keyboard_hotkey,
    keyboard_press,
    keyboard_type,
    mouse_click,
    mouse_drag,
    mouse_move,
    mouse_scroll,
    set_action_pause,
)
from .vision import (
    capture_screenshot,
    capture_with_metadata,
    find_best_text_match,
    find_template_on_screen,
    find_text_in_ocr_cache,
    find_text_on_screen,
    get_frame_cache_age_ms,
    get_screen_size,
    invalidate_frame_cache,
    ocr_full_screen,
)


# =============================================================================
# Server Setup
# =============================================================================

mcp = FastMCP(
    "ubuntu-commander",
    instructions="""Ubuntu/X11 desktop automation server.

Tools:
- get_screen: Capture screenshot (returns image + metadata)
- analyze_screen: Run OCR to find GUI elements and their positions
- use_mouse: Click, move, drag, scroll at coordinates
- use_keyboard: Type text, press keys, hotkey combos

Workflow pattern:
1. get_screen() to see current state
2. analyze_screen() to find element positions via OCR
3. use_mouse()/use_keyboard() to interact with found elements
4. Repeat as needed
""",
    dependencies=["pyautogui", "Pillow", "pytesseract"],
)


# =============================================================================
# TOOL 1: get_screen - Observation (screenshot + metadata)
# =============================================================================


@mcp.tool()
def get_screen(
    region: Annotated[
        dict | None,
        "Capture region only: {x, y, width, height}. Omit for fullscreen.",
    ] = None,
    quality: Annotated[int, "JPEG quality 1-100. Lower=smaller file. Default 50."] = 50,
) -> Image:
    """
    Capture a screenshot of the screen with display metadata.

    Returns the screenshot as an image. Use this to see what's currently displayed.
    For finding clickable elements by text, use analyze_screen() instead.

    The response includes metadata:
    - Screen resolution (width x height)
    - Current mouse position (x, y)

    Args:
        region: Optional {x, y, width, height} to capture only a portion
        quality: JPEG quality 1-100 (50 recommended for balance of size/clarity)

    Returns:
        Screenshot image viewable by the model.

    Example:
        # Full screen capture
        get_screen()

        # Capture specific region
        get_screen(region={"x": 100, "y": 100, "width": 400, "height": 300})
    """
    region_tuple = None
    if region:
        try:
            region_tuple = (
                int(region["x"]),
                int(region["y"]),
                int(region["width"]),
                int(region["height"]),
            )
        except (KeyError, TypeError, ValueError):
            raise ValueError("region must have keys: x, y, width, height")

    # Capture with metadata for cache
    if region_tuple:
        data, fmt = capture_screenshot(quality=quality, format="jpeg", region=region_tuple)
    else:
        meta = capture_with_metadata(quality=quality, format="jpeg")
        data = meta["image_bytes"]
        fmt = meta["format"]

    return Image(data=data, format=fmt)


# =============================================================================
# TOOL 2: analyze_screen - Perception (OCR, element detection, caching)
# =============================================================================


@mcp.tool()
def analyze_screen(
    find_text: Annotated[
        str | None,
        "Search for specific text. Returns matching elements sorted by confidence.",
    ] = None,
    find_image: Annotated[
        str | None,
        "Path to template image to find on screen.",
    ] = None,
    confidence: Annotated[
        float,
        "Minimum confidence threshold 0.0-1.0. Default 0.4 for text, 0.8 for images.",
    ] = 0.4,
    use_cache: Annotated[
        bool,
        "Reuse cached OCR data if available (faster). Set False to force fresh scan.",
    ] = True,
) -> dict:
    """
    Analyze the screen to find GUI elements and their positions.

    Runs OCR to detect text elements, or template matching to find images.
    Results are cached for fast repeated lookups within the same screen state.

    Use this to:
    - Find clickable buttons, links, labels by their text
    - Get x,y coordinates of elements for use_mouse()
    - Search for specific text on screen
    - Locate icons/images via template matching

    Args:
        find_text: Search for elements containing this text (case-insensitive)
        find_image: Path to template image file to locate on screen
        confidence: Minimum match confidence (0.0-1.0)
        use_cache: Use cached OCR results if fresh (default True)

    Returns:
        Dict with:
        - screen: {width, height}
        - mouse: {x, y} current position
        - elements: List of found elements with {text, x, y, width, height, confidence}
        - cache_age_ms: Age of cached data (if used)

    Example workflow:
        # Find and click a button
        result = analyze_screen(find_text="Submit")
        if result["elements"]:
            elem = result["elements"][0]  # Best match
            use_mouse(action="click", x=elem["x"], y=elem["y"])
    """
    width, height = get_screen_size()
    mouse_x, mouse_y = get_mouse_position()
    cache_age = get_frame_cache_age_ms()

    result = {
        "screen": {"width": width, "height": height},
        "mouse": {"x": mouse_x, "y": mouse_y},
        "elements": [],
        "cache_age_ms": cache_age,
        "timestamp": time.time(),
    }

    # Template matching for images
    if find_image:
        matches = find_template_on_screen(find_image, confidence=confidence or 0.8)
        for m in matches:
            cx, cy = m.bbox.center
            result["elements"].append({
                "type": "image",
                "x": cx,
                "y": cy,
                "bbox": m.bbox.to_dict(),
                "confidence": m.confidence,
            })
        return result

    # OCR for text
    if find_text:
        # Try cache first
        if use_cache:
            cached_matches = find_text_in_ocr_cache(find_text, min_confidence=confidence)
            if cached_matches:
                for m in cached_matches:
                    cx, cy = m.bbox.center
                    result["elements"].append({
                        "type": "text",
                        "text": m.text,
                        "x": cx,
                        "y": cy,
                        "bbox": m.bbox.to_dict(),
                        "confidence": m.confidence,
                    })
                result["from_cache"] = True
                return result

        # Fresh OCR search
        matches = find_text_on_screen(find_text, min_confidence=confidence)
        for m in matches:
            cx, cy = m.bbox.center
            result["elements"].append({
                "type": "text",
                "text": m.text,
                "x": cx,
                "y": cy,
                "bbox": m.bbox.to_dict(),
                "confidence": m.confidence,
            })
        result["from_cache"] = False
        return result

    # Full screen OCR (no specific search)
    if not use_cache:
        invalidate_frame_cache()

    all_text = ocr_full_screen(lang="eng", use_cache=use_cache)

    # Return top elements by confidence
    sorted_elements = sorted(all_text, key=lambda x: x["confidence"], reverse=True)
    for elem in sorted_elements[:50]:  # Limit to top 50
        if elem["confidence"] >= confidence:
            result["elements"].append({
                "type": "text",
                "text": elem["text"],
                "x": elem["bbox"]["center_x"],
                "y": elem["bbox"]["center_y"],
                "bbox": elem["bbox"],
                "confidence": elem["confidence"],
            })

    result["total_detected"] = len(all_text)
    result["from_cache"] = use_cache and cache_age is not None

    return result


# =============================================================================
# TOOL 3: use_mouse - Action (move, click, drag, scroll)
# =============================================================================


@mcp.tool()
def use_mouse(
    action: Annotated[
        Literal["click", "move", "drag", "scroll"],
        "Mouse action: click, move, drag, or scroll",
    ],
    x: Annotated[int | None, "Target X coordinate"] = None,
    y: Annotated[int | None, "Target Y coordinate"] = None,
    button: Annotated[
        Literal["left", "right", "middle"],
        "Mouse button for click/drag",
    ] = "left",
    clicks: Annotated[int, "Number of clicks (2 for double-click)"] = 1,
    # Drag endpoints
    end_x: Annotated[int | None, "Drag end X (drag action only)"] = None,
    end_y: Annotated[int | None, "Drag end Y (drag action only)"] = None,
    # Scroll
    amount: Annotated[int | None, "Scroll amount: positive=up, negative=down"] = None,
    # Timing
    duration: Annotated[float, "Animation duration in seconds (0=instant)"] = 0.0,
) -> dict:
    """
    Perform mouse actions at specified coordinates.

    Actions:
    - click: Click at (x, y) or current position if omitted
    - move: Move cursor to (x, y)
    - drag: Click at (x, y), drag to (end_x, end_y), release
    - scroll: Scroll wheel at (x, y) or current position

    Args:
        action: One of "click", "move", "drag", "scroll"
        x, y: Target coordinates (required for move/drag, optional for click/scroll)
        button: Mouse button - "left", "right", "middle"
        clicks: Number of clicks (use 2 for double-click)
        end_x, end_y: Drag destination (required for drag action)
        amount: Scroll amount (required for scroll, positive=up, negative=down)
        duration: Movement duration in seconds (0=instant)

    Returns:
        Dict with action result and final mouse position.

    Examples:
        # Click at coordinates
        use_mouse(action="click", x=500, y=300)

        # Double-click
        use_mouse(action="click", x=500, y=300, clicks=2)

        # Right-click
        use_mouse(action="click", x=500, y=300, button="right")

        # Move cursor
        use_mouse(action="move", x=100, y=200)

        # Drag from (100,100) to (300,300)
        use_mouse(action="drag", x=100, y=100, end_x=300, end_y=300)

        # Scroll down 3 clicks
        use_mouse(action="scroll", amount=-3)

        # Scroll at specific position
        use_mouse(action="scroll", x=500, y=400, amount=5)
    """
    result = {
        "action": action,
        "success": True,
        "timestamp": time.time(),
    }

    if action == "click":
        if x is not None and y is not None:
            if duration > 0:
                mouse_move(x, y, duration=duration)
                mouse_click(button=button, clicks=clicks)
            else:
                fast_click(x, y, button=button, clicks=clicks)
            result["x"] = x
            result["y"] = y
        else:
            # Click at current position
            pos = mouse_click(button=button, clicks=clicks)
            result["x"] = pos[0]
            result["y"] = pos[1]
        result["button"] = button
        result["clicks"] = clicks

    elif action == "move":
        if x is None or y is None:
            raise ValueError("move action requires x and y coordinates")
        if duration > 0:
            mouse_move(x, y, duration=duration)
        else:
            instant_move(x, y)
        result["x"] = x
        result["y"] = y

    elif action == "drag":
        if x is None or y is None:
            raise ValueError("drag action requires x and y (start position)")
        if end_x is None or end_y is None:
            raise ValueError("drag action requires end_x and end_y (end position)")
        drag_result = mouse_drag(
            start_x=x, start_y=y,
            end_x=end_x, end_y=end_y,
            duration=duration or 0.3,
            button=button,
        )
        result["start"] = {"x": x, "y": y}
        result["end"] = {"x": end_x, "y": end_y}
        result["button"] = button

    elif action == "scroll":
        if amount is None:
            raise ValueError("scroll action requires amount parameter")
        pos = mouse_scroll(amount, x, y)
        result["x"] = pos[0]
        result["y"] = pos[1]
        result["amount"] = amount

    else:
        raise ValueError(f"Unknown action: {action}")

    # Always include final position
    final = get_mouse_position()
    result["mouse"] = {"x": final[0], "y": final[1]}

    return result


# =============================================================================
# TOOL 4: use_keyboard - Action (type, press, hotkey)
# =============================================================================


@mcp.tool()
def use_keyboard(
    action: Annotated[
        Literal["type", "press", "hotkey"],
        "Keyboard action: type text, press key, or hotkey combo",
    ],
    text: Annotated[str | None, "Text to type (for action='type')"] = None,
    key: Annotated[
        str | None,
        "Key to press: enter, tab, escape, backspace, delete, up, down, left, right, home, end, pageup, pagedown, f1-f12, etc.",
    ] = None,
    keys: Annotated[
        list[str] | None,
        "Key combination for hotkey: ['ctrl', 'c'], ['alt', 'tab'], etc.",
    ] = None,
    presses: Annotated[int, "Times to press key (for action='press')"] = 1,
    interval: Annotated[float, "Delay between keystrokes in seconds"] = 0.05,
) -> dict:
    """
    Perform keyboard actions.

    Actions:
    - type: Type text string character by character
    - press: Press a single key (with optional repeat)
    - hotkey: Press a key combination simultaneously

    Args:
        action: One of "type", "press", "hotkey"
        text: Text string to type (required for type action)
        key: Key name to press (required for press action)
        keys: List of keys for hotkey (required for hotkey action)
        presses: Number of times to press key
        interval: Delay between keystrokes

    Returns:
        Dict with action details.

    Common keys:
        enter, tab, escape, space, backspace, delete,
        up, down, left, right, home, end, pageup, pagedown,
        f1, f2, ..., f12, ctrl, alt, shift, win, capslock

    Common hotkeys:
        ['ctrl', 'c'] - Copy
        ['ctrl', 'v'] - Paste
        ['ctrl', 'x'] - Cut
        ['ctrl', 'z'] - Undo
        ['ctrl', 's'] - Save
        ['ctrl', 'a'] - Select all
        ['alt', 'tab'] - Switch window
        ['alt', 'f4'] - Close window
        ['ctrl', 'shift', 'esc'] - Task manager

    Examples:
        # Type text
        use_keyboard(action="type", text="Hello World")

        # Press Enter
        use_keyboard(action="press", key="enter")

        # Press Tab 3 times
        use_keyboard(action="press", key="tab", presses=3)

        # Copy (Ctrl+C)
        use_keyboard(action="hotkey", keys=["ctrl", "c"])

        # Paste (Ctrl+V)
        use_keyboard(action="hotkey", keys=["ctrl", "v"])
    """
    result = {
        "action": action,
        "success": True,
        "timestamp": time.time(),
    }

    if action == "type":
        if not text:
            raise ValueError("type action requires text parameter")
        chars = keyboard_type(text, interval=interval)
        result["text"] = text
        result["characters"] = chars

    elif action == "press":
        if not key:
            raise ValueError("press action requires key parameter")
        keyboard_press(key, presses=presses, interval=interval)
        result["key"] = key
        result["presses"] = presses

    elif action == "hotkey":
        if not keys:
            raise ValueError("hotkey action requires keys parameter")
        keyboard_hotkey(*keys)
        result["keys"] = keys
        result["combo"] = "+".join(keys)

    else:
        raise ValueError(f"Unknown action: {action}")

    return result


# =============================================================================
# Utility Tools
# =============================================================================


@mcp.tool()
def get_screen_info() -> dict:
    """
    Get current screen information without taking a screenshot.

    Returns display resolution and current mouse position.
    Useful for quick position checks without the overhead of a screenshot.

    Returns:
        Dict with:
        - screen: {width, height}
        - mouse: {x, y}
        - cache_age_ms: Age of any cached frame data
    """
    width, height = get_screen_size()
    mx, my = get_mouse_position()
    cache_age = get_frame_cache_age_ms()

    return {
        "screen": {"width": width, "height": height},
        "mouse": {"x": mx, "y": my},
        "cache_age_ms": cache_age,
    }


@mcp.tool()
def set_speed(
    pause_ms: Annotated[int, "Pause between actions in milliseconds (10-500)"] = 50,
) -> dict:
    """
    Configure automation speed.

    Lower values = faster but may miss UI updates.
    Higher values = more reliable but slower.

    Recommended:
    - Fast/modern apps: 20-50ms
    - Standard apps: 50-100ms
    - Slow/remote apps: 100-200ms

    Args:
        pause_ms: Milliseconds to pause between actions (10-500)

    Returns:
        Dict with old and new pause values.
    """
    old = get_action_pause()
    new = max(0.01, min(0.5, pause_ms / 1000.0))
    set_action_pause(new)
    return {
        "old_pause_ms": int(old * 1000),
        "new_pause_ms": int(new * 1000),
    }


# =============================================================================
# Resources
# =============================================================================


@mcp.resource("screen://info")
def screen_info_resource() -> str:
    """Current screen info as a resource."""
    width, height = get_screen_size()
    mx, my = get_mouse_position()
    return f"Screen: {width}x{height}, Mouse: ({mx}, {my})"


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
        help="Host for HTTP transports (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port for HTTP transports (default: 8765)",
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
