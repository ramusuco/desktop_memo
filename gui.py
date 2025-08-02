from pathlib import Path
from tkinter import Tk, BOTH, TOP, BOTTOM, LEFT, RIGHT
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import Tuple
import memo


# Paths and filenames
DATA_DIR = Path.home() / "Documents" / "TaskMemo"
DATA_DIR.mkdir(parents=True, exist_ok=True)
MEMO_FILENAME = "memo.txt"

# UI constants
WINDOW_TITLE = "Task Memo"
DEFAULT_FONT = ("Meiryo", 10)
TEXT_BOX_HEIGHT = 20
TEXT_BOX_WIDTH = 50
SAVE_BUTTON_LABEL = "Save"
RESOLUTION_LABEL = "Resolution:"

# Formatting constants
LINE_LENGTH = 30
FILE_NOT_FOUND_MESSAGE = "File not found."


def get_memo_file_path() -> Path:
    """Return the path to Documents\\TaskMemo\\memo.txt"""
    return DATA_DIR / MEMO_FILENAME


def read_memo() -> str:
    file_path = get_memo_file_path()
    if not file_path.exists():
        return FILE_NOT_FOUND_MESSAGE
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return FILE_NOT_FOUND_MESSAGE


def format_text_with_newlines(text: str, line_length: int = LINE_LENGTH) -> str:
    lines = []
    for line in text.split("\n"):
        new_line = ""
        while len(line) > line_length:
            new_line += line[:line_length] + "\n"
            line = line[line_length:]
        new_line += line
        lines.append(new_line)
    return "\n".join(lines)


def save_and_apply_memo(text_box_content: str, selected_resolution: Tuple[int, int]) -> None:
    formatted_text = format_text_with_newlines(text_box_content)
    get_memo_file_path().write_text(formatted_text, encoding="utf-8")
    memo.update_wallpaper_from_memo(selected_resolution)  # Refresh wallpaper with selected resolution


def create_text_box(window: Tk, text: str) -> ScrolledText:
    text_box = ScrolledText(
        window,
        font=DEFAULT_FONT,
        height=TEXT_BOX_HEIGHT,
        width=TEXT_BOX_WIDTH,
        wrap="char",
    )
    text_box.pack(side=TOP, fill=BOTH, expand=True, padx=10, pady=10)
    text_box.insert("1.0", text)
    return text_box


def create_resolution_selector(window: Tk) -> ttk.Combobox:
    """Create resolution selection combobox"""
    resolutions = memo.get_monitor_resolutions()
    resolution_strings = [f"{w}x{h}" for w, h in resolutions]
    
    frame = ttk.Frame(window)
    frame.pack(side=BOTTOM, fill="x", padx=10, pady=5)
    
    label = ttk.Label(frame, text=RESOLUTION_LABEL)
    label.pack(side=LEFT, padx=(0, 5))
    
    combobox = ttk.Combobox(frame, values=resolution_strings, state="readonly", width=15)
    combobox.pack(side=LEFT)
    
    # Set default to first resolution (usually primary monitor)
    if resolution_strings:
        combobox.set(resolution_strings[0])
    
    return combobox


def create_save_button(window: Tk, text_box: ScrolledText, resolution_combobox: ttk.Combobox) -> None:
    button = ttk.Button(
        window,
        text=SAVE_BUTTON_LABEL,
        command=lambda: save_and_apply_memo(
            text_box.get("1.0", "end-1c"),
            get_selected_resolution(resolution_combobox)
        ),
    )
    button.pack(side=BOTTOM, anchor="e", padx=10, pady=5)


def get_selected_resolution(combobox: ttk.Combobox) -> Tuple[int, int]:
    """Parse selected resolution from combobox"""
    selected = combobox.get()
    if selected and "x" in selected:
        try:
            width, height = selected.split("x")
            return (int(width), int(height))
        except ValueError:
            pass
    
    # Fallback to default resolution
    return memo.IMAGE_SIZE


def create_window() -> Tk:
    window = Tk()
    window.title(WINDOW_TITLE)
    window.option_add("*Font", " ".join([DEFAULT_FONT[0], str(DEFAULT_FONT[1])]))
    return window


def main() -> None:
    window = create_window()
    text_box = create_text_box(window, read_memo())
    resolution_combobox = create_resolution_selector(window)
    create_save_button(window, text_box, resolution_combobox)
    window.mainloop()


if __name__ == "__main__":
    main()
