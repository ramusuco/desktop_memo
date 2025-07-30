from pathlib import Path
import ctypes
from PIL import Image, ImageDraw, ImageFont

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


def update_wallpaper_from_memo() -> None:
    output_file = DATA_DIR / OUTPUT_FILENAME

    if output_file.exists():
        output_file.unlink()
        print(f"Deleted existing image '{output_file.name}'.")

    memo_file = DATA_DIR / MEMO_FILENAME
    if memo_file.exists():
        txt = memo_file.read_text(encoding="utf-8")
    else:
        txt = "Memo file not found."

    image = Image.new("RGB", IMAGE_SIZE, BACKGROUND_COLOR)
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
