"""
Vision utilities for desktop automation.

Provides screenshot capture, template matching, and OCR-based element detection.
Includes frame caching and batch OCR for optimized workflow loops.
"""

import io
import os
import shutil
import threading
import time
from dataclasses import dataclass, field
from typing import Literal

import pyautogui
from PIL import Image as PILImage


# =============================================================================
# Frame Cache for Workflow Loop Optimization
# =============================================================================

@dataclass
class CachedFrame:
    """A cached screenshot with metadata for reuse across OCR queries."""
    image: PILImage.Image
    timestamp: float
    width: int
    height: int
    ocr_data: dict | None = None  # Cached pytesseract output
    grayscale: PILImage.Image | None = None  # Cached grayscale for template matching

    def age_ms(self) -> float:
        """Return age in milliseconds."""
        return (time.time() - self.timestamp) * 1000

    def is_stale(self, max_age_ms: float = 500) -> bool:
        """Check if frame is too old."""
        return self.age_ms() > max_age_ms


class FrameCache:
    """Thread-safe frame cache for reusing screenshots within a workflow loop."""

    def __init__(self):
        self._lock = threading.Lock()
        self._frame: CachedFrame | None = None

    def capture(self, region: tuple[int, int, int, int] | None = None, force: bool = False) -> CachedFrame:
        """
        Capture a new frame or return cached one if still fresh.
        
        Args:
            region: Optional (x, y, width, height) for partial capture
            force: If True, always capture fresh frame
            
        Returns:
            CachedFrame with screenshot and metadata
        """
        with self._lock:
            # Return cached frame if fresh and full-screen
            if not force and self._frame and not self._frame.is_stale() and region is None:
                return self._frame

            # Capture new frame
            if region:
                img = pyautogui.screenshot(region=region)
                width, height = region[2], region[3]
            else:
                img = pyautogui.screenshot()
                width, height = img.size

            frame = CachedFrame(
                image=img,
                timestamp=time.time(),
                width=width,
                height=height,
            )

            # Only cache full-screen captures
            if region is None:
                self._frame = frame

            return frame

    def get_cached(self, max_age_ms: float = 500) -> CachedFrame | None:
        """Get cached frame if available and fresh."""
        with self._lock:
            if self._frame and not self._frame.is_stale(max_age_ms):
                return self._frame
            return None

    def invalidate(self):
        """Clear the cache."""
        with self._lock:
            self._frame = None

    def cache_ocr_data(self, ocr_data: dict):
        """Cache OCR data for the current frame."""
        with self._lock:
            if self._frame:
                self._frame.ocr_data = ocr_data

    def get_cached_ocr(self) -> dict | None:
        """Get cached OCR data if frame is still fresh."""
        with self._lock:
            if self._frame and not self._frame.is_stale() and self._frame.ocr_data:
                return self._frame.ocr_data
            return None


# Global frame cache instance
_frame_cache = FrameCache()


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
    use_cache: bool = False,
) -> tuple[bytes, str]:
    """
    Capture a screenshot and return as compressed bytes.

    Args:
        quality: JPEG quality (1-100), lower = smaller file
        format: Output format (jpeg or png)
        region: Optional (x, y, width, height) tuple for partial capture
        use_cache: If True, may return cached frame if fresh

    Returns:
        Tuple of (image_bytes, format_string)
    """
    if use_cache and region is None:
        frame = _frame_cache.capture(region=None, force=False)
        screenshot = frame.image
    elif region:
        screenshot = pyautogui.screenshot(region=region)
    else:
        frame = _frame_cache.capture(region=None, force=True)
        screenshot = frame.image

    buffer = io.BytesIO()

    if format == "jpeg":
        screenshot.convert("RGB").save(buffer, format="JPEG", quality=quality, optimize=True)
    else:
        screenshot.save(buffer, format="PNG", optimize=True)

    return buffer.getvalue(), format


def capture_with_metadata(
    quality: int = 60,
    format: Literal["jpeg", "png"] = "jpeg",
    region: tuple[int, int, int, int] | None = None,
) -> dict:
    """
    Capture a screenshot with display metadata for workflow loops.

    Returns dict with:
        - image_bytes: The compressed image data
        - format: Image format string
        - width: Screen/region width
        - height: Screen/region height
        - timestamp: Capture timestamp
        - mouse_x, mouse_y: Current mouse position
    """
    frame = _frame_cache.capture(region=region, force=True)
    
    buffer = io.BytesIO()
    if format == "jpeg":
        frame.image.convert("RGB").save(buffer, format="JPEG", quality=quality, optimize=True)
    else:
        frame.image.save(buffer, format="PNG", optimize=True)

    mouse_x, mouse_y = pyautogui.position()

    return {
        "image_bytes": buffer.getvalue(),
        "format": format,
        "width": frame.width,
        "height": frame.height,
        "timestamp": frame.timestamp,
        "mouse_x": mouse_x,
        "mouse_y": mouse_y,
    }


def _resolve_tesseract_cmd() -> str | None:
    """Find a usable tesseract binary, honoring TESSERACT_CMD if set."""
    env_cmd = os.environ.get("TESSERACT_CMD")
    if env_cmd and os.path.exists(env_cmd):
        return env_cmd

    # Try PATH and common install locations
    for candidate in (
        "tesseract",
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ):
        if os.path.isabs(candidate):
            if os.path.exists(candidate):
                return candidate
        else:
            resolved = shutil.which(candidate)
            if resolved:
                return resolved
    return None


def _configure_tesseract():
    """Ensure pytesseract knows where the tesseract binary is."""
    try:
        import pytesseract
    except ImportError:
        raise ImportError(
            "pytesseract is required for OCR. Install with: pip install pytesseract"
        )

    cmd = _resolve_tesseract_cmd()
    if not cmd:
        raise FileNotFoundError(
            "Tesseract binary not found. Install `tesseract-ocr` or set TESSERACT_CMD to the binary path."
        )
    pytesseract.pytesseract.tesseract_cmd = cmd
    return pytesseract


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
    region: tuple[int, int, int, int] | None = None,
    min_confidence: float = 0.35,
) -> list[ElementMatch]:
    """
    Find text on screen using OCR (requires tesseract).

    Args:
        text: Text to search for (case-insensitive substring match)
        lang: Tesseract language code
        region: Optional (x, y, width, height) crop to speed up/target OCR
        min_confidence: Minimum confidence (0-1) to keep a match

    Returns:
        List of ElementMatch objects for each text match found, sorted by confidence desc
    """
    pytesseract = _configure_tesseract()

    # Capture current screen
    if region:
        screenshot = pyautogui.screenshot(region=region)
        offset_x, offset_y = region[0], region[1]
    else:
        screenshot = pyautogui.screenshot()
        offset_x = offset_y = 0

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
            try:
                conf = float(data["conf"][i]) / 100.0
            except ValueError:
                conf = 0.0

            if conf >= min_confidence:
                bbox = BoundingBox(
                    x=offset_x + data["left"][i],
                    y=offset_y + data["top"][i],
                    width=data["width"][i],
                    height=data["height"][i],
                )
                matches.append(ElementMatch(bbox=bbox, confidence=conf, text=word))

    # Highest confidence first for easy one-shot targeting
    return sorted(matches, key=lambda m: m.confidence, reverse=True)


def find_best_text_match(
    text: str,
    lang: str = "eng",
    region: tuple[int, int, int, int] | None = None,
    min_confidence: float = 0.35,
) -> ElementMatch | None:
    """Get the single best text match by confidence, or None if nothing found."""
    matches = find_text_on_screen(text=text, lang=lang, region=region, min_confidence=min_confidence)
    return matches[0] if matches else None


def ocr_full_screen(
    lang: str = "eng",
    use_cache: bool = True,
    psm: int = 3,
) -> list[dict]:
    """
    Run OCR on the full screen and return all detected text with positions.
    
    Caches OCR result with frame for subsequent find_text queries.
    
    Args:
        lang: Tesseract language code
        use_cache: If True, reuse cached OCR data if frame is still fresh
        psm: Tesseract page segmentation mode (3=auto, 6=uniform block, 11=sparse)
    
    Returns:
        List of dicts with keys: text, confidence, bbox (x, y, width, height, center_x, center_y)
    """
    # Check for cached OCR data
    if use_cache:
        cached = _frame_cache.get_cached_ocr()
        if cached:
            return _ocr_data_to_matches(cached)

    pytesseract = _configure_tesseract()
    
    # Capture fresh frame
    frame = _frame_cache.capture(force=True)
    
    # Run OCR with custom config
    config = f"--psm {psm}"
    data = pytesseract.image_to_data(
        frame.image, 
        lang=lang, 
        output_type=pytesseract.Output.DICT,
        config=config,
    )
    
    # Cache the raw OCR data
    _frame_cache.cache_ocr_data(data)
    
    return _ocr_data_to_matches(data)


def _ocr_data_to_matches(data: dict, min_confidence: float = 0.0) -> list[dict]:
    """Convert pytesseract output dict to list of match dicts."""
    results = []
    n_boxes = len(data["text"])
    
    for i in range(n_boxes):
        word = data["text"][i]
        if not word or not word.strip():
            continue
            
        try:
            conf = float(data["conf"][i]) / 100.0
        except (ValueError, TypeError):
            conf = 0.0
            
        if conf < min_confidence:
            continue
            
        x, y = data["left"][i], data["top"][i]
        w, h = data["width"][i], data["height"][i]
        
        results.append({
            "text": word,
            "confidence": conf,
            "bbox": {
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "center_x": x + w // 2,
                "center_y": y + h // 2,
            },
        })
    
    return results


def find_text_in_ocr_cache(
    text: str,
    min_confidence: float = 0.35,
) -> list[ElementMatch]:
    """
    Search for text in cached OCR data without re-running OCR.
    
    Call ocr_full_screen() first to populate the cache.
    
    Returns:
        List of ElementMatch sorted by confidence desc, or empty if no cache.
    """
    cached = _frame_cache.get_cached_ocr()
    if not cached:
        return []
    
    matches = []
    search_lower = text.lower()
    n_boxes = len(cached["text"])
    
    for i in range(n_boxes):
        word = cached["text"][i]
        if not word:
            continue
            
        if search_lower in word.lower():
            try:
                conf = float(cached["conf"][i]) / 100.0
            except (ValueError, TypeError):
                conf = 0.0
                
            if conf >= min_confidence:
                bbox = BoundingBox(
                    x=cached["left"][i],
                    y=cached["top"][i],
                    width=cached["width"][i],
                    height=cached["height"][i],
                )
                matches.append(ElementMatch(bbox=bbox, confidence=conf, text=word))
    
    return sorted(matches, key=lambda m: m.confidence, reverse=True)


def invalidate_frame_cache():
    """Invalidate the frame cache, forcing fresh capture on next call."""
    _frame_cache.invalidate()


def get_frame_cache_age_ms() -> float | None:
    """Get the age of the cached frame in milliseconds, or None if no cache."""
    frame = _frame_cache.get_cached(max_age_ms=float("inf"))
    return frame.age_ms() if frame else None
