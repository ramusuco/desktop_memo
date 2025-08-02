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
    # Create a frame for the text area with a label
    text_frame = ttk.LabelFrame(window, text="Memo Content", padding=10)
    text_frame.pack(side=TOP, fill=BOTH, expand=True, padx=15, pady=(15, 5))
    
    text_box = ScrolledText(
        text_frame,
        font=DEFAULT_FONT,
        height=TEXT_BOX_HEIGHT,
        width=TEXT_BOX_WIDTH,
        wrap="char",
        relief="flat",
        borderwidth=1
    )
    text_box.pack(fill=BOTH, expand=True)
    text_box.insert("1.0", text)
    return text_box


def create_control_panel(window: Tk, text_box: ScrolledText) -> None:
    """Create a styled control panel with resolution selector and save button"""
    # Main control frame
    control_frame = ttk.Frame(window)
    control_frame.pack(side=BOTTOM, fill="x", padx=15, pady=10)
    
    # Resolution selection frame (left side)
    resolution_frame = ttk.LabelFrame(control_frame, text="Display Settings", padding=10)
    resolution_frame.pack(side=LEFT, fill="x", expand=True, padx=(0, 10))
    
    # Resolution selector
    resolutions = memo.get_monitor_resolutions()
    resolution_strings = [f"{w}x{h}" for w, h in resolutions]
    
    resolution_label = ttk.Label(resolution_frame, text=RESOLUTION_LABEL)
    resolution_label.pack(side=LEFT, padx=(0, 8))
    
    resolution_combobox = ttk.Combobox(
        resolution_frame, 
        values=resolution_strings, 
        state="readonly", 
        width=12,
        font=DEFAULT_FONT
    )
    resolution_combobox.pack(side=LEFT)
    
    # Set default to first resolution (usually primary monitor)
    if resolution_strings:
        resolution_combobox.set(resolution_strings[0])
    
    # Action frame (right side)
    action_frame = ttk.Frame(control_frame)
    action_frame.pack(side=RIGHT)
    
    # Save button with improved styling
    save_button = ttk.Button(
        action_frame,
        text=SAVE_BUTTON_LABEL,
        command=lambda: save_and_apply_memo(
            text_box.get("1.0", "end-1c"),
            get_selected_resolution(resolution_combobox)
        ),
        width=12
    )
    save_button.pack(pady=5)


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
    
    # Set minimum window size and make it resizable
    window.minsize(600, 500)
    window.geometry("700x600")
    
    # Configure window style
    window.configure(bg='#f0f0f0')
    
    return window


def main() -> None:
    window = create_window()
    text_box = create_text_box(window, read_memo())
    create_control_panel(window, text_box)
    window.mainloop()


if __name__ == "__main__":
    main()
