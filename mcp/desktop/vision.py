"""
Vision utilities for desktop automation.

Provides screenshot capture, template matching, and OCR-based element detection.
"""

import io
from dataclasses import dataclass
from typing import Literal

import pyautogui
from PIL import Image as PILImage


@dataclass
class BoundingBox:
    """A bounding box with x, y coordinates and dimensions."""

    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> tuple[int, int]:
        """Return the center point of the bounding box."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "center_x": self.center[0],
            "center_y": self.center[1],
        }


@dataclass
class ElementMatch:
    """A detected element on screen."""

    bbox: BoundingBox
    confidence: float
    text: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "bbox": self.bbox.to_dict(),
            "confidence": self.confidence,
            "text": self.text,
        }


def capture_screenshot(
    quality: int = 60,
    format: Literal["jpeg", "png"] = "jpeg",
    region: tuple[int, int, int, int] | None = None,
) -> tuple[bytes, str]:
    """
    Capture a screenshot and return as compressed bytes.

    Args:
        quality: JPEG quality (1-100), lower = smaller file
        format: Output format (jpeg or png)
        region: Optional (x, y, width, height) tuple for partial capture

    Returns:
        Tuple of (image_bytes, format_string)
    """
    if region:
        screenshot = pyautogui.screenshot(region=region)
    else:
        screenshot = pyautogui.screenshot()

    buffer = io.BytesIO()

    if format == "jpeg":
        screenshot.convert("RGB").save(buffer, format="JPEG", quality=quality, optimize=True)
    else:
        screenshot.save(buffer, format="PNG", optimize=True)

    return buffer.getvalue(), format


def get_screen_size() -> tuple[int, int]:
    """Return the screen size as (width, height)."""
    return pyautogui.size()


def find_template_on_screen(
    template_path: str,
    confidence: float = 0.8,
    grayscale: bool = True,
) -> list[ElementMatch]:
    """
    Find all occurrences of a template image on screen.

    Args:
        template_path: Path to the template image file
        confidence: Minimum confidence threshold (0.0-1.0)
        grayscale: Whether to use grayscale matching (faster)

    Returns:
        List of ElementMatch objects for each match found
    """
    try:
        locations = pyautogui.locateAllOnScreen(
            template_path,
            confidence=confidence,
            grayscale=grayscale,
        )

        matches = []
        for loc in locations:
            bbox = BoundingBox(x=loc.left, y=loc.top, width=loc.width, height=loc.height)
            matches.append(ElementMatch(bbox=bbox, confidence=confidence))

        return matches
    except pyautogui.ImageNotFoundException:
        return []


def find_text_on_screen(
    text: str,
    lang: str = "eng",
) -> list[ElementMatch]:
    """
    Find text on screen using OCR (requires tesseract).

    Args:
        text: Text to search for (case-insensitive substring match)
        lang: Tesseract language code

    Returns:
        List of ElementMatch objects for each text match found
    """
    try:
        import pytesseract
    except ImportError:
        raise ImportError("pytesseract is required for OCR. Install with: pip install pytesseract")

    # Capture current screen
    screenshot = pyautogui.screenshot()

    # Run OCR with bounding box data
    data = pytesseract.image_to_data(screenshot, lang=lang, output_type=pytesseract.Output.DICT)

    matches = []
    search_lower = text.lower()

    n_boxes = len(data["text"])
    for i in range(n_boxes):
        word = data["text"][i]
        if not word:
            continue

        if search_lower in word.lower():
            conf = float(data["conf"][i]) / 100.0
            if conf > 0:
                bbox = BoundingBox(
                    x=data["left"][i],
                    y=data["top"][i],
                    width=data["width"][i],
                    height=data["height"][i],
                )
                matches.append(ElementMatch(bbox=bbox, confidence=conf, text=word))

    return matches
