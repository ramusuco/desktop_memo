from pathlib import Path
from tkinter import Tk, BOTH, TOP, BOTTOM, LEFT, RIGHT, messagebox, simpledialog
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import Tuple
import memo


# Paths and filenames
DATA_DIR = Path.home() / "Documents" / "TaskMemo"
DATA_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR = DATA_DIR / "templates"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
MEMO_FILENAME = "memo.txt"

# Multi-file support
MAX_FILES = 5
DEFAULT_FILE_NAMES = [f"memo_{i+1}.txt" for i in range(MAX_FILES)]

# UI constants
WINDOW_TITLE = "Task Memo"
DEFAULT_FONT = ("Meiryo", 10)
TEXT_BOX_HEIGHT = 18
TEXT_BOX_WIDTH = 50
SAVE_BUTTON_LABEL = "Save File"
APPLY_BUTTON_LABEL = "Apply to Wallpaper"
RESOLUTION_LABEL = "Resolution:"
TEMPLATE_LABEL = "Template:"
SAVE_TEMPLATE_LABEL = "Save as Template"
LOAD_TEMPLATE_LABEL = "Load Template"

# Formatting constants
LINE_LENGTH = 30
FILE_NOT_FOUND_MESSAGE = "File not found."


def get_memo_file_path(filename: str = MEMO_FILENAME) -> Path:
    """Return the path to Documents\\TaskMemo\\{filename}"""
    return DATA_DIR / filename


def read_memo(filename: str = MEMO_FILENAME) -> str:
    file_path = get_memo_file_path(filename)
    if not file_path.exists():
        return ""  # Return empty string for new files
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def save_memo_file(content: str, filename: str) -> None:
    """Save content to specified memo file"""
    formatted_text = format_text_with_newlines(content)
    file_path = get_memo_file_path(filename)
    file_path.write_text(formatted_text, encoding="utf-8")


def get_file_display_name(filename: str) -> str:
    """Get display name for tab (remove .txt extension)"""
    return filename.replace('.txt', '').replace('memo_', 'File ').title()


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


def save_current_memo(text_box_content: str, filename: str) -> None:
    """Save current memo content to file"""
    save_memo_file(text_box_content, filename)


def apply_memo_to_wallpaper(text_box_content: str, selected_resolution: Tuple[int, int], filename: str) -> None:
    """Apply current memo content to wallpaper"""
    # Save the content first
    save_memo_file(text_box_content, filename)
    # Then apply to wallpaper using the saved file
    memo.update_wallpaper_from_memo(selected_resolution, filename)


def on_tab_changed(event, notebook: ttk.Notebook, status_label: ttk.Label):
    """Handle tab change event"""
    try:
        current_tab_index = notebook.index(notebook.select())
        filename = DEFAULT_FILE_NAMES[current_tab_index]
        display_name = get_file_display_name(filename)
        update_status(status_label, f"● Editing {display_name}")
    except:
        pass


def create_notebook_with_files(window: Tk, status_label: ttk.Label) -> Tuple[ttk.Notebook, dict]:
    """Create notebook widget with multiple file tabs"""
    # Create a frame for the notebook
    notebook_frame = ttk.LabelFrame(window, text="Memo Files", padding=10)
    notebook_frame.pack(side=TOP, fill=BOTH, expand=True, padx=15, pady=(15, 5))
    
    # Create the notebook (tab widget)
    notebook = ttk.Notebook(notebook_frame)
    notebook.pack(fill=BOTH, expand=True)
    
    # Dictionary to store text boxes for each file
    text_boxes = {}
    
    # Create tabs for each file
    for i, filename in enumerate(DEFAULT_FILE_NAMES):
        # Create frame for this tab
        tab_frame = ttk.Frame(notebook)
        
        # Create text box for this file
        text_box = ScrolledText(
            tab_frame,
            font=DEFAULT_FONT,
            height=TEXT_BOX_HEIGHT,
            width=TEXT_BOX_WIDTH,
            wrap="char",
            relief="flat",
            borderwidth=1,
            undo=True,
            maxundo=50
        )
        text_box.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Load content for this file
        content = read_memo(filename)
        text_box.insert("1.0", content)
        
        # Store text box reference
        text_boxes[filename] = text_box
        
        # Add tab to notebook
        display_name = get_file_display_name(filename)
        notebook.add(tab_frame, text=display_name)
    
    # Bind tab change event
    notebook.bind("<<NotebookTabChanged>>", lambda event: on_tab_changed(event, notebook, status_label))
    
    # Set initial status for first tab
    if DEFAULT_FILE_NAMES:
        display_name = get_file_display_name(DEFAULT_FILE_NAMES[0])
        update_status(status_label, f"● Editing {display_name}")
    
    return notebook, text_boxes


def create_control_panel(window: Tk, notebook: ttk.Notebook, text_boxes: dict, status_label: ttk.Label) -> None:
    """Create a styled control panel with resolution selector and separated save/apply buttons"""
    # Main control frame
    control_frame = ttk.Frame(window)
    control_frame.pack(side=BOTTOM, fill="x", padx=15, pady=(10, 5))
    
    # Template selection frame (left side)
    template_frame = ttk.LabelFrame(control_frame, text="Templates", padding=10)
    template_frame.pack(side=LEFT, fill="x", expand=True, padx=(0, 5))
    
    # Template selector
    available_templates = get_available_templates()
    template_combobox = ttk.Combobox(
        template_frame,
        values=available_templates,
        state="readonly",
        width=15,
        font=DEFAULT_FONT
    )
    template_combobox.pack(side=LEFT, padx=(0, 5))
    
    # Template load button
    load_template_button = ttk.Button(
        template_frame,
        text="Load",
        command=lambda: load_selected_template_to_current_tab(template_combobox, notebook, text_boxes, status_label),
        width=8
    )
    load_template_button.pack(side=LEFT, padx=(0, 5))
    
    # Save template button
    save_template_button = ttk.Button(
        template_frame,
        text="Save Template",
        command=lambda: save_current_tab_as_template(notebook, text_boxes, status_label),
        width=12
    )
    save_template_button.pack(side=LEFT)
    
    # Resolution selection frame (center)
    resolution_frame = ttk.LabelFrame(control_frame, text="Display Settings", padding=10)
    resolution_frame.pack(side=LEFT, fill="x", expand=True, padx=(5, 5))
    
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
    
    # Action frame (right side) - Now with two separate buttons
    action_frame = ttk.LabelFrame(control_frame, text="Actions", padding=12)
    action_frame.pack(side=RIGHT, padx=(5, 0))
    
    # Save file button
    save_button = ttk.Button(
        action_frame,
        text=SAVE_BUTTON_LABEL,
        command=lambda: save_current_tab(notebook, text_boxes, status_label),
        width=16
    )
    save_button.pack(pady=(0, 4))
    
    # Apply to wallpaper button
    apply_button = ttk.Button(
        action_frame,
        text=APPLY_BUTTON_LABEL,
        command=lambda: apply_current_tab_to_wallpaper(notebook, text_boxes, get_selected_resolution(resolution_combobox), status_label),
        width=16
    )
    apply_button.pack(pady=(0, 0))


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


def create_default_templates():
    """Create default templates if they don't exist"""
    default_templates = {
        "Daily ToDo": """Today's Tasks:
□ 
□ 
□ 


Tomorrow:
□ 
□ """,
        
        "Meeting Notes": """Meeting: 
Date: 
Attendees: 

Agenda:
1. 
2. 
3. 

Action Items:
□ 
□ 
□ """,
        
        "Weekly Report": """Week of: 

Completed:
• 
• 
• 

In Progress:
• 
• 

Next Week:
• 
• 
 """
    }
    
    for template_name, content in default_templates.items():
        template_file = TEMPLATES_DIR / f"{template_name}.txt"
        if not template_file.exists():
            template_file.write_text(content, encoding="utf-8")


def get_available_templates():
    """Get list of available template files"""
    create_default_templates()
    template_files = list(TEMPLATES_DIR.glob("*.txt"))
    return [f.stem for f in template_files]


def load_template(template_name: str) -> str:
    """Load template content by name"""
    template_file = TEMPLATES_DIR / f"{template_name}.txt"
    if template_file.exists():
        try:
            return template_file.read_text(encoding="utf-8")
        except FileNotFoundError:
            pass
    return ""


def save_template(template_name: str, content: str):
    """Save content as a template"""
    if template_name.strip():
        template_file = TEMPLATES_DIR / f"{template_name.strip()}.txt"
        formatted_content = format_text_with_newlines(content)
        template_file.write_text(formatted_content, encoding="utf-8")




def get_current_tab_info(notebook: ttk.Notebook, text_boxes: dict) -> Tuple[str, ScrolledText]:
    """Get current tab's filename and text box"""
    current_tab_index = notebook.index(notebook.select())
    filename = DEFAULT_FILE_NAMES[current_tab_index]
    text_box = text_boxes[filename]
    return filename, text_box


def save_current_tab(notebook: ttk.Notebook, text_boxes: dict, status_label: ttk.Label):
    """Save current tab's content to file"""
    filename, text_box = get_current_tab_info(notebook, text_boxes)
    content = text_box.get("1.0", "end-1c")
    save_current_memo(content, filename)
    update_status(status_label, f"✓ Saved {get_file_display_name(filename)}")


def apply_current_tab_to_wallpaper(notebook: ttk.Notebook, text_boxes: dict, resolution: Tuple[int, int], status_label: ttk.Label):
    """Apply current tab's content to wallpaper"""
    filename, text_box = get_current_tab_info(notebook, text_boxes)
    content = text_box.get("1.0", "end-1c")
    apply_memo_to_wallpaper(content, resolution, filename)
    update_status(status_label, f"✓ Applied {get_file_display_name(filename)} to wallpaper ({resolution[0]}x{resolution[1]})")


def load_selected_template_to_current_tab(template_combobox: ttk.Combobox, notebook: ttk.Notebook, text_boxes: dict, status_label: ttk.Label):
    """Load selected template into current tab"""
    selected_template = template_combobox.get()
    if not selected_template:
        update_status(status_label, "⚠ Please select a template first")
        return
        
    filename, text_box = get_current_tab_info(notebook, text_boxes)
    template_content = load_template(selected_template)
    if template_content:
        # Ask for confirmation before replacing current content
        if text_box.get("1.0", "end-1c").strip():
            result = messagebox.askyesno(
                "Load Template", 
                "This will replace the current content. Continue?"
            )
            if not result:
                return
        
        # Clear current content and load template
        text_box.delete("1.0", "end")
        text_box.insert("1.0", template_content)
        update_status(status_label, f"✓ Loaded template '{selected_template}' to {get_file_display_name(filename)}")
    else:
        update_status(status_label, f"✗ Could not load template '{selected_template}'")


def save_current_tab_as_template(notebook: ttk.Notebook, text_boxes: dict, status_label: ttk.Label):
    """Save current tab's content as a new template"""
    filename, text_box = get_current_tab_info(notebook, text_boxes)
    current_content = text_box.get("1.0", "end-1c").strip()
    if not current_content:
        update_status(status_label, "⚠ Cannot save empty content as template")
        return
    
    template_name = simpledialog.askstring(
        "Save Template", 
        "Enter template name:",
        initialvalue="My Template"
    )
    
    if template_name:
        try:
            save_template(template_name, current_content)
            update_status(status_label, f"✓ Template '{template_name}' saved successfully!")
        except Exception as e:
            update_status(status_label, f"✗ Failed to save template: {str(e)}")


def create_status_bar(window: Tk) -> ttk.Label:
    """Create status bar at the bottom of the window"""
    status_frame = ttk.Frame(window)
    status_frame.pack(side=BOTTOM, fill="x", padx=10, pady=(5, 10))
    
    status_label = ttk.Label(
        status_frame, 
        text="● Ready - Select a tab and start editing", 
        relief="sunken", 
        anchor="w",
        padding=(8, 4)
    )
    status_label.pack(fill="x")
    
    return status_label


def update_status(status_label: ttk.Label, message: str):
    """Update status message (no auto-clear, only changes on user action)"""
    status_label.config(text=message)


def create_window() -> Tk:
    window = Tk()
    window.title(WINDOW_TITLE)
    window.option_add("*Font", " ".join([DEFAULT_FONT[0], str(DEFAULT_FONT[1])]))
    
    # Set minimum window size and make it resizable
    window.minsize(650, 550)
    window.geometry("750x650")
    
    # Configure window style
    window.configure(bg='#f0f0f0')
    
    return window


def main() -> None:
    window = create_window()
    
    # Create status bar first (at the bottom)
    status_label = create_status_bar(window)
    
    # Create notebook with status integration
    notebook, text_boxes = create_notebook_with_files(window, status_label)
    create_control_panel(window, notebook, text_boxes, status_label)
    
    window.mainloop()


if __name__ == "__main__":
    main()
