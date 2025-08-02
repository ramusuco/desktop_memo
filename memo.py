from __future__ import annotations

from pathlib import Path
import ctypes
from PIL import Image, ImageDraw, ImageFont

DATA_DIR = Path.home() / "Documents" / "TaskMemo"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATH = Path(r"C:\Windows\Fonts\meiryob.ttc")
FONT_SIZE = 36
DEFAULT_IMAGE_SIZE = (1280, 720)
FONT_COLOR = (0, 0, 0)
BACKGROUND_COLOR = (255, 255, 255)
TEXT_MARGIN_LEFT = 200
TEXT_MARGIN_RIGHT = 50
TEXT_MARGIN_TOP = 50
SPI_SET_DESKTOP_WALLPAPER = 20

DEFAULT_MEMO_FILENAME = "memo.txt"
OUTPUT_FILENAME = "memo.bmp"


def get_monitor_resolutions() -> list[tuple[int, int]]:
    """Get resolutions of all connected monitors"""
    import win32api
    import win32con
    
    resolutions = []
    device_num = 0
    
    while True:
        try:
            device = win32api.EnumDisplayDevices(None, device_num)
            if not device.DeviceName:
                break
                
            # Get display settings for this device
            settings = win32api.EnumDisplaySettings(device.DeviceName, win32con.ENUM_CURRENT_SETTINGS)
            if settings:
                width = settings.PelsWidth
                height = settings.PelsHeight
                resolutions.append((width, height))
            
            device_num += 1
        except:
            break
    
    # Fallback to primary monitor if no monitors found
    if not resolutions:
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        resolutions.append((width, height))
    
    # Remove duplicates while preserving order
    unique_resolutions = []
    for res in resolutions:
        if res not in unique_resolutions:
            unique_resolutions.append(res)
    
    return unique_resolutions


def calculate_max_chars_per_line(image_size: tuple[int, int]) -> int:
    """Calculate maximum characters per line with 20-character buffer from right edge"""
    width, height = image_size
    
    # Available width for text = total width - left margin - right margin
    available_width = width - TEXT_MARGIN_LEFT - TEXT_MARGIN_RIGHT
    
    # For Japanese font (Meiryo Bold), approximate character width calculation
    # Empirically tested: full-width characters are roughly 0.7 * font_size
    char_width = FONT_SIZE * 0.7  # Approximate width per character (conservative estimate)
    
    # Calculate how many characters can fit in available width
    theoretical_max_chars = int(available_width / char_width)
    
    # Subtract 20 characters as buffer from right edge
    max_chars_with_buffer = theoretical_max_chars - 20
    
    # Safety bounds: minimum 10 chars, maximum 200 chars
    return max(10, min(max_chars_with_buffer, 200))


def wrap_text_to_chars(text: str, max_chars_per_line: int) -> str:
    """Simple character-based text wrapping"""
    lines = text.split('\n')
    wrapped_lines = []
    
    for line in lines:
        # If line is shorter than max chars, keep as is
        if len(line) <= max_chars_per_line:
            wrapped_lines.append(line)
        else:
            # Split line at max_chars_per_line intervals
            start = 0
            while start < len(line):
                end = start + max_chars_per_line
                wrapped_lines.append(line[start:end])
                start = end
    
    return '\n'.join(wrapped_lines)


def update_wallpaper_from_memo(image_size: tuple[int, int] = DEFAULT_IMAGE_SIZE, memo_filename: str = DEFAULT_MEMO_FILENAME) -> None:
    output_file = DATA_DIR / OUTPUT_FILENAME

    if output_file.exists():
        output_file.unlink()
        print(f"Deleted existing image '{output_file.name}'.")

    memo_file = DATA_DIR / memo_filename
    if memo_file.exists():
        txt = memo_file.read_text(encoding="utf-8")
    else:
        txt = f"Memo file '{memo_filename}' not found."

    image = Image.new("RGB", image_size, BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(FONT_PATH), FONT_SIZE)
    draw.multiline_text((TEXT_MARGIN_LEFT, TEXT_MARGIN_TOP), txt, font=font, fill=FONT_COLOR)

    image.save(output_file, "BMP")
    print(f"Saved image as '{output_file.name}'.")

    abs_path = str(output_file.resolve())
    ctypes.windll.user32.SystemParametersInfoW(
        SPI_SET_DESKTOP_WALLPAPER,
        0,
        abs_path,
        1 | 2,
    )
    print("Wallpaper updated.")


if __name__ == "__main__":
    update_wallpaper_from_memo()