# Ubuntu Commander (FastMCP)

Desktop automation MCP server for Ubuntu/X11 using FastMCP. Provides 4 comprehensive tools for screenshots, UI analysis (OCR), mouse control, and keyboard control.

## Requirements
- Python 3.10+
- Ubuntu/X11 session (pyautogui uses X11)
- System: `sudo apt install tesseract-ocr` (for OCR tools)
- Python deps (package install handles this): `pip install "mcp[fastmcp]" pyautogui pillow pytesseract`

## Install (editable for local dev)
```bash
# From repo root
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Run
```bash
# StdIO (typical MCP client)
ubuntu-commander --transport stdio

# Or via module
python -m servers.server --transport stdio

# SSE transport
python -m servers.server --transport sse --port 8765

# Streamable HTTP
python -m servers.server --transport streamable-http --port 8765
```

## Tools (4 Comprehensive)

### 1. `take_screenshot`
Capture a screenshot of the screen or a region.

```python
# Full screen
take_screenshot(quality=50)

# Region only
take_screenshot(quality=60, region={"x": 0, "y": 0, "width": 800, "height": 600})
```

**Returns:** Image viewable by the model.

---

### 2. `take_snapshot`
Analyze screen via OCR without returning the image. Results cached for `use_mouse(action="click_text")`.

```python
# Summary only
take_snapshot()

# With full element positions
take_snapshot(verbose=True)

# Save to file
take_snapshot(filePath="/tmp/snapshot.json")
```

**Returns:**
- `screen_width`, `screen_height`: Display dimensions
- `mouse_x`, `mouse_y`: Current mouse position
- `text_summary`: Top 30 detected text items
- `text_elements`: Full positions (if verbose=True)
- `element_count`: Total detected elements

---

### 3. `use_mouse`
All mouse operations in one tool.

**Actions:**
- `click` - Click at coordinates or current position
- `move` / `hover` - Move mouse to coordinates
- `drag` - Click and drag from start to end
- `scroll` - Scroll wheel
- `click_text` - Find text via OCR and click it

```python
# Click at coordinates
use_mouse(action="click", x=100, y=200)

# Double-click
use_mouse(action="click", x=100, y=200, clicks=2)
use_mouse(action="click", x=100, y=200, dblClick=True)

# Right-click
use_mouse(action="click", x=100, y=200, button="right")

# Move mouse
use_mouse(action="move", x=500, y=300)

# Drag
use_mouse(action="drag", start_x=100, start_y=100, end_x=300, end_y=300)

# Scroll down
use_mouse(action="scroll", scroll_amount=-3)

# Click on text (uses OCR)
use_mouse(action="click_text", text="Submit")
use_mouse(action="click_text", text="OK", button="left", clicks=2)
```

**Returns:** Dict with action result, position, and metadata.

---

### 4. `use_keyboard`
All keyboard operations in one tool.

**Actions:**
- `type` - Type text character by character
- `press` - Press a single key (with repeat)
- `hotkey` - Press a key combination

```python
# Type text
use_keyboard(action="type", text="Hello World")

# Press Enter
use_keyboard(action="press", key="enter")

# Press Tab 3 times
use_keyboard(action="press", key="tab", presses=3)

# Ctrl+C (copy)
use_keyboard(action="hotkey", keys=["ctrl", "c"])

# Ctrl+Shift+S (save as)
use_keyboard(action="hotkey", keys=["ctrl", "shift", "s"])
```

**Common keys:** enter, tab, escape, space, backspace, delete, up, down, left, right, home, end, pageup, pagedown, f1-f12

**Common hotkeys:**
- `['ctrl', 'c']` - Copy
- `['ctrl', 'v']` - Paste
- `['ctrl', 'z']` - Undo
- `['ctrl', 's']` - Save
- `['ctrl', 'a']` - Select all
- `['alt', 'tab']` - Switch window
- `['alt', 'f4']` - Close window

---

## Utility Tools

### `gui_action_loop`
Automated loop: screenshot → OCR → find target → click → repeat until goal reached.

```python
gui_action_loop(
    goal_text="Success",
    click_targets=["Next", "Continue", "OK"],
    max_iterations=10,
    step_delay_ms=100
)
```

### `set_automation_speed`
Configure action timing (10-500ms pause between actions).

```python
set_automation_speed(pause_ms=30)  # Faster
set_automation_speed(pause_ms=100)  # More reliable
```

---

## Resource

- `screen://info` - Get screen dimensions and mouse position

---

## Tips

- Keep screenshots under ~1MB (use quality 40-60)
- Use `take_snapshot` before `use_mouse(action="click_text")` for cached OCR
- Ensure target window is focused before keyboard actions
- OCR requires tesseract; prefer lower-level coordinates when possible for speed
