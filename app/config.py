"""Configuration constants for DesktopMemo application."""

from pathlib import Path

# Directory paths
DATA_DIR = Path.home() / "Documents" / "TaskMemo"
TEMPLATES_DIR = DATA_DIR / "templates"

# Multi-file support
MAX_FILES = 5
DEFAULT_FILE_NAMES = [f"memo_{i+1}.txt" for i in range(MAX_FILES)]

# UI constants
WINDOW_TITLE = "Task Memo"
DEFAULT_FONT = ("Meiryo", 10)
TEXT_BOX_HEIGHT = 18
TEXT_BOX_WIDTH = 60
SAVE_BUTTON_LABEL = "Save File"
APPLY_BUTTON_LABEL = "Apply to Wallpaper"
RESOLUTION_LABEL = "Resolution:"

# Formatting constants
LINE_LENGTH = 30

# Memo output constants
DEFAULT_MEMO_FILENAME = "memo.txt"
OUTPUT_FILENAME = "memo.bmp"

# Font and display settings
FONT_PATH = Path(r"C:\Windows\Fonts\meiryob.ttc")
FONT_SIZE = 36
DEFAULT_IMAGE_SIZE = (1280, 720)
FONT_COLOR = (0, 0, 0)
BACKGROUND_COLOR = (255, 255, 255)
TEXT_MARGIN_LEFT = 200
TEXT_MARGIN_RIGHT = 50
TEXT_MARGIN_TOP = 50

# Windows API constants
SPI_SET_DESKTOP_WALLPAPER = 20

# Markdown style size multipliers (relative to FONT_SIZE)
# Adjust these values to change the size of each style
MARKDOWN_SIZE_MULTIPLIERS = {
    "h1": 1.8,      # Heading 1 (largest)
    "h2": 1.5,      # Heading 2
    "h3": 1.2,      # Heading 3
    "normal": 1.0,  # Normal text
    "bold": 1.0,    # Bold text
    "italic": 1.0,  # Italic text
    "code": 0.9,    # Code (inline and block)
    "quote": 1.0,   # Quote text
}