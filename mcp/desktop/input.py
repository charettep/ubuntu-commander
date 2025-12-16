"""
Input utilities for desktop automation.

Provides mouse and keyboard control functions.
"""

from typing import Literal

import pyautogui

# Configure pyautogui safety features
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.1  # Small pause between actions

MouseButton = Literal["left", "right", "middle"]


def mouse_move(
    x: int,
    y: int,
    duration: float = 0.5,
    relative: bool = False,
) -> tuple[int, int]:
    """
    Move mouse to specified coordinates.

    Args:
        x: X coordinate (absolute or relative)
        y: Y coordinate (absolute or relative)
        duration: Time in seconds for the movement
        relative: If True, move relative to current position

    Returns:
        Final (x, y) position
    """
    if relative:
        pyautogui.moveRel(x, y, duration=duration)
    else:
        pyautogui.moveTo(x, y, duration=duration)

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
