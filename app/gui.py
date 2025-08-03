from __future__ import annotations

from tkinter import Tk, BOTH, TOP, BOTTOM, LEFT, RIGHT, messagebox, simpledialog
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from . import memo
from .config import (
    DATA_DIR, TEMPLATES_DIR, MAX_FILES, DEFAULT_FILE_NAMES,
    WINDOW_TITLE, DEFAULT_FONT, TEXT_BOX_HEIGHT, TEXT_BOX_WIDTH,
    SAVE_BUTTON_LABEL, APPLY_BUTTON_LABEL, RESOLUTION_LABEL, LINE_LENGTH
)
from .templates import DEFAULT_TEMPLATES

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


class TemplateManager:
    @staticmethod
    def create_default_templates():
        """Create default templates if they don't exist"""
        for template_name, content in DEFAULT_TEMPLATES.items():
            template_file = TEMPLATES_DIR / f"{template_name}.txt"
            if not template_file.exists():
                template_file.write_text(content, encoding="utf-8")

    @staticmethod
    def get_available_templates():
        """Get list of available template files"""
        TemplateManager.create_default_templates()
        template_files = list(TEMPLATES_DIR.glob("*.txt"))
        return [f.stem for f in template_files]

    @staticmethod
    def load_template(template_name: str) -> str:
        """Load template content by name"""
        template_file = TEMPLATES_DIR / f"{template_name}.txt"
        if template_file.exists():
            try:
                return template_file.read_text(encoding="utf-8")
            except FileNotFoundError:
                pass
        return ""

    @staticmethod
    def save_template(template_name: str, content: str):
        """Save content as a template"""
        if template_name.strip():
            template_file = TEMPLATES_DIR / f"{template_name.strip()}.txt"
            # Save template as-is without auto-formatting
            template_file.write_text(content, encoding="utf-8")


class FileManager:
    @staticmethod
    def get_memo_file_path(filename: str = "memo.txt") -> Path:
        """Return the path to Documents\\TaskMemo\\{filename}"""
        return DATA_DIR / filename

    @staticmethod
    def read_memo(filename: str = "memo.txt") -> str:
        file_path = FileManager.get_memo_file_path(filename)
        if not file_path.exists():
            return ""  # Return empty string for new files
        try:
            return file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

    @staticmethod
    def save_memo_file(content: str, filename: str) -> None:
        """Save content to specified memo file"""
        # Save content as-is without auto-formatting to preserve user's line breaks
        file_path = FileManager.get_memo_file_path(filename)
        file_path.write_text(content, encoding="utf-8")
    
    @staticmethod
    def save_memo_file_with_wrapping(content: str, filename: str, image_size: tuple[int, int]) -> str:
        """Save content with automatic line wrapping based on image size"""
        # Calculate maximum characters per line for the given resolution
        max_chars = memo.calculate_max_chars_per_line(image_size)
        
        # Apply simple character-based wrapping
        wrapped_content = memo.wrap_text_to_chars(content, max_chars)
        
        # Save the wrapped content
        file_path = FileManager.get_memo_file_path(filename)
        file_path.write_text(wrapped_content, encoding="utf-8")
        
        return wrapped_content

    @staticmethod
    def get_file_display_name(filename: str) -> str:
        """Get display name for tab (remove .txt extension)"""
        return filename.replace('.txt', '').replace('memo_', 'File ').title()

    @staticmethod
    def format_text_with_newlines(text: str, line_length: int = LINE_LENGTH) -> str:
        """Legacy function - now returns text as-is to preserve user formatting"""
        return text


class TaskMemoApp:
    def __init__(self):
        self.window = None
        self.notebook = None
        self.text_boxes = {}
        self.status_label = None
        self.template_combobox = None
        self.resolution_combobox = None

    def run(self):
        self.window = self._create_window()
        self.status_label = self._create_status_bar()
        self.notebook, self.text_boxes = self._create_notebook_with_files()
        self._create_control_panel()
        self.window.mainloop()

    def _create_window(self):
        window = Tk()
        window.title(WINDOW_TITLE)
        window.option_add("*Font", " ".join([DEFAULT_FONT[0], str(DEFAULT_FONT[1])]))
        
        # Set minimum window size and make it resizable
        window.minsize(650, 550)
        window.geometry("750x650")
        
        # Configure window style
        window.configure(bg='#f0f0f0')
        
        return window

    def _create_status_bar(self):
        """Create status bar at the bottom of the window"""
        status_frame = ttk.Frame(self.window)
        status_frame.pack(side=BOTTOM, fill="x", padx=10, pady=(5, 10))
        
        status_label = ttk.Label(
            status_frame,
            text="",
            relief="sunken",
            anchor="w",
            padding=(8, 4)
        )
        status_label.pack(fill="x")
        
        return status_label

    def _update_status(self, message: str):
        """Update status message (no auto-clear, only changes on user action)"""
        self.status_label.config(text=message)

    def _update_editing_status(self):
        """Update status to show editing state"""
        try:
            filename, _ = self._get_current_tab_info()
            display_name = FileManager.get_file_display_name(filename)
            self._update_status(f"● Editing {display_name}")
        except:
            pass

    def _create_notebook_with_files(self):
        """Create notebook widget with multiple file tabs"""
        # Create a frame for the notebook
        notebook_frame = ttk.LabelFrame(self.window, text="Memo Files", padding=10)
        notebook_frame.pack(side=TOP, fill=BOTH, expand=True, padx=15, pady=(15, 5))
        
        # Create the notebook (tab widget)
        notebook = ttk.Notebook(notebook_frame)
        notebook.pack(fill=BOTH, expand=True)
        
        # Dictionary to store text boxes for each file
        text_boxes = {}
        
        # Create tabs for each file
        for filename in DEFAULT_FILE_NAMES:
            # Create frame for this tab
            tab_frame = ttk.Frame(notebook)
            
            # Create text box for this file
            text_box = ScrolledText(
                tab_frame,
                font=DEFAULT_FONT,
                height=TEXT_BOX_HEIGHT,
                width=TEXT_BOX_WIDTH,
                wrap="none",  # Disable auto-wrap to match image output
                relief="flat",
                borderwidth=1,
                undo=True,
                maxundo=50
            )
            text_box.pack(fill=BOTH, expand=True, padx=5, pady=5)
            
            # Load content for this file
            content = FileManager.read_memo(filename)
            text_box.insert("1.0", content)
            
            # Create text change detection for status updates only
            def on_key_press(event):
                # Schedule status update for after the key event is processed
                text_box.after_idle(lambda: self._update_editing_status())
            
            def on_paste(event):
                # Schedule status update for after paste is processed
                text_box.after_idle(lambda: self._update_editing_status())
            
            # Bind multiple events for comprehensive detection
            text_box.bind("<KeyPress>", on_key_press)
            text_box.bind("<Control-v>", on_paste)
            text_box.bind("<Button-2>", on_paste)  # Middle mouse paste
            text_box.bind("<BackSpace>", on_key_press)
            text_box.bind("<Delete>", on_key_press)
            
            # Store text box reference
            text_boxes[filename] = text_box
            
            # Add tab to notebook
            display_name = FileManager.get_file_display_name(filename)
            notebook.add(tab_frame, text=display_name)
        
        return notebook, text_boxes

    def _create_control_panel(self):
        """Create a styled control panel with resolution selector and separated save/apply buttons"""
        # Main control frame
        control_frame = ttk.Frame(self.window)
        control_frame.pack(side=BOTTOM, fill="x", padx=15, pady=(10, 5))
        
        # Template selection frame (left side)
        template_frame = ttk.LabelFrame(control_frame, text="Templates", padding=10)
        template_frame.pack(side=LEFT, fill="x", expand=True, padx=(0, 5))
        
        # Template selector
        available_templates = TemplateManager.get_available_templates()
        self.template_combobox = ttk.Combobox(
            template_frame,
            values=available_templates,
            state="readonly",
            width=15,
            font=DEFAULT_FONT
        )
        self.template_combobox.pack(side=LEFT, padx=(0, 5))
        
        # Template load button
        ttk.Button(
            template_frame,
            text="Load",
            command=self._load_selected_template,
            width=8
        ).pack(side=LEFT, padx=(0, 5))
        
        # Save template button
        ttk.Button(
            template_frame,
            text="Save Template",
            command=self._save_current_as_template,
            width=14
        ).pack(side=LEFT)
        
        # Resolution selection frame (center)
        resolution_frame = ttk.LabelFrame(control_frame, text="Display Settings", padding=10)
        resolution_frame.pack(side=LEFT, fill="x", expand=True, padx=(5, 5))
        
        # Resolution selector
        resolutions = memo.get_monitor_resolutions()
        resolution_strings = [f"{w}x{h}" for w, h in resolutions]
        
        resolution_label = ttk.Label(resolution_frame, text=RESOLUTION_LABEL)
        resolution_label.pack(side=LEFT, padx=(0, 8))
        
        self.resolution_combobox = ttk.Combobox(
            resolution_frame,
            values=resolution_strings,
            state="readonly",
            width=12,
            font=DEFAULT_FONT
        )
        self.resolution_combobox.pack(side=LEFT)
        
        # Set default to first resolution (usually primary monitor)
        if resolution_strings:
            self.resolution_combobox.set(resolution_strings[0])
        
        # Action frame (right side) - Now with two separate buttons
        action_frame = ttk.LabelFrame(control_frame, text="Actions", padding=12)
        action_frame.pack(side=RIGHT, padx=(5, 0))
        
        # Save file button
        ttk.Button(
            action_frame,
            text=SAVE_BUTTON_LABEL,
            command=self._save_current_tab,
            width=16
        ).pack(pady=(0, 4))
        
        # Apply to wallpaper button
        ttk.Button(
            action_frame,
            text=APPLY_BUTTON_LABEL,
            command=self._apply_current_tab_to_wallpaper,
            width=19
        ).pack(pady=(0, 0))

    def _get_selected_resolution(self) -> tuple[int, int]:
        """Parse selected resolution from combobox"""
        selected = self.resolution_combobox.get()
        if selected and "x" in selected:
            try:
                width, height = selected.split("x")
                return (int(width), int(height))
            except ValueError:
                pass
        
        # Fallback to default resolution
        return memo.DEFAULT_IMAGE_SIZE

    def _get_current_tab_info(self) -> tuple[str, ScrolledText]:
        """Get current tab's filename and text box"""
        current_tab_index = self.notebook.index(self.notebook.select())
        filename = DEFAULT_FILE_NAMES[current_tab_index]
        text_box = self.text_boxes[filename]
        return filename, text_box

    def _save_current_tab(self):
        """Save current tab's content to file with automatic line wrapping"""
        filename, text_box = self._get_current_tab_info()
        content = text_box.get("1.0", "end-1c")
        resolution = self._get_selected_resolution()
        
        # Apply line wrapping before saving
        wrapped_content = FileManager.save_memo_file_with_wrapping(content, filename, resolution)
        
        # Update the text box to show the wrapped content
        text_box.delete("1.0", "end")
        text_box.insert("1.0", wrapped_content)
        
        self._update_status(f"✓ Saved {FileManager.get_file_display_name(filename)} with auto-wrap")

    def _apply_current_tab_to_wallpaper(self):
        """Apply current tab's content to wallpaper with intelligent wrapping"""
        filename, text_box = self._get_current_tab_info()
        content = text_box.get("1.0", "end-1c")
        resolution = self._get_selected_resolution()
        
        # Apply intelligent wrapping and save
        wrapped_content = FileManager.save_memo_file_with_wrapping(content, filename, resolution)
        
        # Update the text box to show the wrapped content
        text_box.delete("1.0", "end")
        text_box.insert("1.0", wrapped_content)
        
        # Generate wallpaper
        memo.update_wallpaper_from_memo(resolution, filename)
        self._update_status(f"✓ Applied {FileManager.get_file_display_name(filename)} to wallpaper ({resolution[0]}x{resolution[1]}) with auto-wrap")

    def _load_selected_template(self):
        """Load selected template into current tab"""
        selected_template = self.template_combobox.get()
        if not selected_template:
            self._update_status("⚠ Please select a template first")
            return
            
        filename, text_box = self._get_current_tab_info()
        template_content = TemplateManager.load_template(selected_template)
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
            self._update_status(f"✓ Loaded template '{selected_template}' to {FileManager.get_file_display_name(filename)}")
        else:
            self._update_status(f"✗ Could not load template '{selected_template}'")

    def _save_current_as_template(self):
        """Save current tab's content as a new template"""
        filename, text_box = self._get_current_tab_info()
        current_content = text_box.get("1.0", "end-1c").strip()
        if not current_content:
            self._update_status("⚠ Cannot save empty content as template")
            return
        
        template_name = simpledialog.askstring(
            "Save Template",
            "Enter template name:",
            initialvalue="My Template"
        )
        
        if template_name:
            try:
                TemplateManager.save_template(template_name, current_content)
                self._update_status(f"✓ Template '{template_name}' saved successfully!")
            except Exception as e:
                self._update_status(f"✗ Failed to save template: {str(e)}")



def main():
    app = TaskMemoApp()
    app.run()


if __name__ == "__main__":
    main()