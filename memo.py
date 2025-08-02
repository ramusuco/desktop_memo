from pathlib import Path
import ctypes
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple

DATA_DIR = Path.home() / "Documents" / "TaskMemo"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATH = Path(r"C:\Windows\Fonts\meiryob.ttc")
FONT_SIZE = 36
IMAGE_SIZE = (1280, 720)
FONT_COLOR = (0, 0, 0)
BACKGROUND_COLOR = (255, 255, 255)
SPI_SET_DESKTOP_WALLPAPER = 20

MEMO_FILENAME = "memo.txt"
OUTPUT_FILENAME = "memo.bmp"


def get_monitor_resolutions() -> List[Tuple[int, int]]:
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


def update_wallpaper_from_memo(image_size: Tuple[int, int] = IMAGE_SIZE) -> None:
    output_file = DATA_DIR / OUTPUT_FILENAME

    if output_file.exists():
        output_file.unlink()
        print(f"Deleted existing image '{output_file.name}'.")

    memo_file = DATA_DIR / MEMO_FILENAME
    if memo_file.exists():
        txt = memo_file.read_text(encoding="utf-8")
    else:
        txt = "Memo file not found."

    image = Image.new("RGB", image_size, BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(FONT_PATH), FONT_SIZE)
    draw.multiline_text((200, 50), txt, font=font, fill=FONT_COLOR)

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
