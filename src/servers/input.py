"""
Input utilities for desktop automation.

Provides mouse and keyboard control functions with configurable speed.
"""

from typing import Literal

import pyautogui

# Configure pyautogui safety features
pyautogui.FAILSAFE = True  # Move mouse to corner to abort

# Default pause - can be reduced for faster loops
_DEFAULT_PAUSE = 0.05  # 50ms between actions (was 0.1)
pyautogui.PAUSE = _DEFAULT_PAUSE

MouseButton = Literal["left", "right", "middle"]


def set_action_pause(pause: float):
    """Set the pause between pyautogui actions (in seconds)."""
    global _DEFAULT_PAUSE
    _DEFAULT_PAUSE = pause
    pyautogui.PAUSE = pause


def get_action_pause() -> float:
    """Get current pause between actions."""
    return pyautogui.PAUSE


def mouse_move(
    x: int,
    y: int,
    duration: float = 0.0,
    relative: bool = False,
) -> tuple[int, int]:
    """
    Move mouse to specified coordinates.

    Args:
        x: X coordinate (absolute or relative)
        y: Y coordinate (absolute or relative)
        duration: Time in seconds for the movement (0=instant)
        relative: If True, move relative to current position

    Returns:
        Final (x, y) position
    """
    if relative:
        pyautogui.moveRel(x, y, duration=duration)
    else:
        pyautogui.moveTo(x, y, duration=duration)

    return pyautogui.position()


def instant_move(x: int, y: int) -> tuple[int, int]:
    """Move mouse instantly to coordinates (no duration, no tween)."""
    pyautogui.moveTo(x, y, duration=0, _pause=False)
    return pyautogui.position()


def mouse_click(
    x: int | None = None,
    y: int | None = None,
    button: MouseButton = "left",
    clicks: int = 1,
    interval: float = 0.1,
) -> tuple[int, int]:
    """
    Click mouse at specified coordinates or current position.

    Args:
        x: X coordinate (None = current position)
        y: Y coordinate (None = current position)
        button: Mouse button to click
        clicks: Number of clicks
        interval: Time between clicks

    Returns:
        Click position (x, y)
    """
    if x is not None and y is not None:
        pyautogui.click(x, y, clicks=clicks, interval=interval, button=button)
        return (x, y)
    else:
        pos = pyautogui.position()
        pyautogui.click(clicks=clicks, interval=interval, button=button)
        return pos


def mouse_drag(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration: float = 0.5,
    button: MouseButton = "left",
) -> dict:
    """
    Drag mouse from start to end position.

    Args:
        start_x: Starting X coordinate
        start_y: Starting Y coordinate
        end_x: Ending X coordinate
        end_y: Ending Y coordinate
        duration: Time in seconds for the drag
        button: Mouse button to hold during drag

    Returns:
        Dict with start and end positions
    """
    pyautogui.moveTo(start_x, start_y)
    pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration, button=button)

    return {
        "start": {"x": start_x, "y": start_y},
        "end": {"x": end_x, "y": end_y},
    }


def mouse_scroll(
    clicks: int,
    x: int | None = None,
    y: int | None = None,
) -> tuple[int, int]:
    """
    Scroll mouse wheel.

    Args:
        clicks: Number of scroll clicks (positive = up, negative = down)
        x: X coordinate (None = current position)
        y: Y coordinate (None = current position)

    Returns:
        Current mouse position
    """
    if x is not None and y is not None:
        pyautogui.scroll(clicks, x, y)
    else:
        pyautogui.scroll(clicks)

    return pyautogui.position()


def keyboard_type(
    text: str,
    interval: float = 0.05,
) -> int:
    """
    Type text using the keyboard.

    Args:
        text: Text to type
        interval: Time between keystrokes

    Returns:
        Number of characters typed
    """
    pyautogui.typewrite(text, interval=interval)
    return len(text)


def keyboard_press(
    key: str,
    presses: int = 1,
    interval: float = 0.1,
) -> str:
    """
    Press a keyboard key.

    Args:
        key: Key to press (e.g., 'enter', 'tab', 'escape', 'f1', etc.)
        presses: Number of times to press
        interval: Time between presses

    Returns:
        The key that was pressed
    """
    pyautogui.press(key, presses=presses, interval=interval)
    return key


def keyboard_hotkey(*keys: str) -> list[str]:
    """
    Press a keyboard hotkey combination.

    Args:
        *keys: Keys to press together (e.g., 'ctrl', 'c' for Ctrl+C)

    Returns:
        List of keys pressed
    """
    pyautogui.hotkey(*keys)
    return list(keys)


def get_mouse_position() -> tuple[int, int]:
    """Return current mouse position as (x, y)."""
    return pyautogui.position()


def fast_click(
    x: int,
    y: int,
    button: MouseButton = "left",
    clicks: int = 1,
) -> tuple[int, int]:
    """
    Move and click in one fast operation with minimal delays.
    
    Args:
        x: X coordinate
        y: Y coordinate  
        button: Mouse button
        clicks: Number of clicks
    
    Returns:
        Click position (x, y)
    """
    # Use _pause=False for the move to avoid extra delay
    pyautogui.moveTo(x, y, duration=0, _pause=False)
    pyautogui.click(clicks=clicks, interval=0.02, button=button)
    return (x, y)


def move_and_click(
    x: int,
    y: int,
    button: MouseButton = "left",
    clicks: int = 1,
    move_duration: float = 0.0,
    click_interval: float = 0.05,
) -> dict:
    """
    Combined move and click with configurable timing.
    
    Args:
        x: Target X coordinate
        y: Target Y coordinate
        button: Mouse button
        clicks: Number of clicks
        move_duration: Duration for mouse movement (0=instant)
        click_interval: Interval between multiple clicks
        
    Returns:
        Dict with final position and action details
    """
    if move_duration > 0:
        pyautogui.moveTo(x, y, duration=move_duration)
    else:
        pyautogui.moveTo(x, y, duration=0, _pause=False)
    
    pyautogui.click(clicks=clicks, interval=click_interval, button=button)
    
    final_pos = pyautogui.position()
    return {
        "x": final_pos[0],
        "y": final_pos[1],
        "button": button,
        "clicks": clicks,
    }
