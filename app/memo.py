from __future__ import annotations

import ctypes
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .config import (
    DATA_DIR, FONT_PATH, FONT_SIZE, DEFAULT_IMAGE_SIZE,
    FONT_COLOR, BACKGROUND_COLOR, TEXT_MARGIN_LEFT, TEXT_MARGIN_RIGHT,
    TEXT_MARGIN_TOP, SPI_SET_DESKTOP_WALLPAPER, DEFAULT_MEMO_FILENAME,
    OUTPUT_FILENAME, MARKDOWN_SIZE_MULTIPLIERS
)
from .markdown_parser import MarkdownParser, TextStyle, ParsedLine, TableRow

# Ensure directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Font paths for different styles
FONT_PATH_BOLD = Path(r"C:\Windows\Fonts\meiryob.ttc")  # Meiryo Bold
FONT_PATH_REGULAR = Path(r"C:\Windows\Fonts\meiryo.ttc")  # Meiryo Regular
FONT_PATH_CODE = Path(r"C:\Windows\Fonts\consola.ttf")  # Consolas for code


class FontCache:
    """Cache for loaded fonts to avoid reloading."""
    _cache: dict = {}

    @classmethod
    def get_font(cls, style: TextStyle, base_size: int = FONT_SIZE) -> ImageFont.FreeTypeFont:
        """Get font for the given style."""
        # Map TextStyle to config key
        style_to_key = {
            TextStyle.HEADING1: "h1",
            TextStyle.HEADING2: "h2",
            TextStyle.HEADING3: "h3",
            TextStyle.NORMAL: "normal",
            TextStyle.BOLD: "bold",
            TextStyle.ITALIC: "italic",
            TextStyle.CODE: "code",
            TextStyle.QUOTE: "quote",
        }

        key = style_to_key.get(style, "normal")
        multiplier = MARKDOWN_SIZE_MULTIPLIERS.get(key, 1.0)
        size = int(base_size * multiplier)
        cache_key = (style, size)

        if cache_key not in cls._cache:
            if style in (TextStyle.HEADING1, TextStyle.HEADING2, TextStyle.HEADING3, TextStyle.BOLD):
                font_path = FONT_PATH_BOLD
            else:
                # Use regular font for all other styles (including CODE for inline)
                # Code blocks will use CODE font separately
                font_path = FONT_PATH_REGULAR

            # Fallback to bold font if regular not found
            if not font_path.exists():
                font_path = FONT_PATH_BOLD

            cls._cache[cache_key] = ImageFont.truetype(str(font_path), size)

        return cls._cache[cache_key]

    @classmethod
    def clear_cache(cls):
        """Clear the font cache."""
        cls._cache.clear()


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


def calculate_content_height(parsed_lines: list, base_font_size: int) -> int:
    """Calculate the total height needed to render all content."""
    y_position = TEXT_MARGIN_TOP
    line_spacing = int(base_font_size * 0.5)

    for parsed_line in parsed_lines:
        if parsed_line.is_table_row and parsed_line.table_row:
            if parsed_line.table_row.is_separator:
                y_position += line_spacing
            else:
                y_position += base_font_size + line_spacing
            continue

        if parsed_line.is_code_block:
            y_position += int(base_font_size * MARKDOWN_SIZE_MULTIPLIERS.get("code", 0.9)) + line_spacing
            continue

        # Calculate max height for this line
        max_height = base_font_size
        for segment in parsed_line.segments:
            style_to_key = {
                TextStyle.HEADING1: "h1", TextStyle.HEADING2: "h2", TextStyle.HEADING3: "h3",
                TextStyle.NORMAL: "normal", TextStyle.BOLD: "bold", TextStyle.ITALIC: "italic",
                TextStyle.CODE: "code", TextStyle.QUOTE: "quote",
            }
            key = style_to_key.get(segment.style, "normal")
            multiplier = MARKDOWN_SIZE_MULTIPLIERS.get(key, 1.0)
            segment_height = int(base_font_size * multiplier)
            max_height = max(max_height, segment_height)

        if not parsed_line.segments or all(not s.text for s in parsed_line.segments):
            max_height = base_font_size

        y_position += max_height + line_spacing

        if parsed_line.is_heading:
            y_position += int(line_spacing * 0.5)

    return y_position


def render_markdown_to_image(
    text: str,
    image_size: tuple[int, int] = DEFAULT_IMAGE_SIZE,
    enable_markdown: bool = True,
    auto_scale: bool = True,
    min_scale: float = 0.5
) -> Image.Image:
    """Render text (optionally with markdown) to an image.

    Args:
        auto_scale: If True, automatically reduce font size to fit content
        min_scale: Minimum scale factor (default 0.5 = 50% of original size)
    """
    image = Image.new("RGB", image_size, BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    if not enable_markdown:
        # Plain text rendering
        font = ImageFont.truetype(str(FONT_PATH), FONT_SIZE)
        draw.multiline_text(
            (TEXT_MARGIN_LEFT, TEXT_MARGIN_TOP),
            text,
            font=font,
            fill=FONT_COLOR
        )
        return image

    # Parse markdown
    parsed_lines = MarkdownParser.parse_text(text)

    # Calculate scale factor if auto_scale is enabled
    scale_factor = 1.0
    if auto_scale:
        available_height = image_size[1] - TEXT_MARGIN_TOP - 50  # 50px bottom margin
        content_height = calculate_content_height(parsed_lines, FONT_SIZE)

        if content_height > available_height:
            scale_factor = available_height / content_height
            scale_factor = max(scale_factor, min_scale)  # Don't go below min_scale
            # Clear font cache when scaling
            FontCache.clear_cache()

    # Calculate actual font size
    actual_font_size = int(FONT_SIZE * scale_factor)

    y_position = TEXT_MARGIN_TOP
    line_spacing = int(actual_font_size * 0.5)  # Space between lines

    # Colors
    quote_color = (100, 100, 100)  # Gray for quotes
    code_bg_color = (240, 240, 240)  # Light gray background for code
    table_border_color = (180, 180, 180)  # Gray for table borders
    inline_code_color = (200, 50, 50)  # Red for inline code (Slack-style)

    # First pass: calculate positions and identify code block regions
    line_positions = []
    temp_y = TEXT_MARGIN_TOP
    temp_line_spacing = int(actual_font_size * 0.5)

    # Pre-load code font for calculations
    code_font_size = int(actual_font_size * MARKDOWN_SIZE_MULTIPLIERS.get("code", 0.9))
    code_font = ImageFont.truetype(str(FONT_PATH_CODE), code_font_size)

    for pl in parsed_lines:
        line_positions.append(temp_y)
        if pl.is_code_block:
            text_to_draw = pl.segments[0].text if pl.segments else ""
            bbox = code_font.getbbox(text_to_draw) if text_to_draw else (0, 0, 0, actual_font_size)
            text_height = bbox[3] - bbox[1] if bbox else actual_font_size
            temp_y += text_height + temp_line_spacing
        elif pl.is_table_row and pl.table_row:
            if pl.table_row.is_separator:
                temp_y += temp_line_spacing
            else:
                temp_y += actual_font_size + temp_line_spacing
        else:
            max_h = actual_font_size
            for seg in pl.segments:
                font = FontCache.get_font(seg.style, actual_font_size)
                if seg.text:
                    bbox = font.getbbox(seg.text)
                    seg_h = bbox[3] - bbox[1] if bbox else actual_font_size
                    max_h = max(max_h, seg_h)
            if not pl.segments or all(not s.text for s in pl.segments):
                max_h = actual_font_size
            temp_y += max_h + temp_line_spacing
            if pl.is_heading:
                temp_y += int(temp_line_spacing * 0.5)

    # Find code block regions
    code_block_regions = []
    i = 0
    while i < len(parsed_lines):
        if parsed_lines[i].is_code_block:
            start_idx = i
            while i < len(parsed_lines) and parsed_lines[i].is_code_block:
                i += 1
            end_idx = i - 1
            start_y = line_positions[start_idx]
            # Calculate end_y from the last code line
            last_text = parsed_lines[end_idx].segments[0].text if parsed_lines[end_idx].segments else ""
            bbox = code_font.getbbox(last_text) if last_text else (0, 0, 0, actual_font_size)
            last_height = bbox[3] - bbox[1] if bbox else actual_font_size
            end_y = line_positions[end_idx] + last_height
            code_block_regions.append((start_y, end_y))
        else:
            i += 1

    # Draw code block backgrounds first
    for start_y, end_y in code_block_regions:
        draw.rectangle(
            [(TEXT_MARGIN_LEFT - 10, start_y + -16),
             (image_size[0] - TEXT_MARGIN_RIGHT, end_y + 7)],
            fill=code_bg_color
        )

    for parsed_line in parsed_lines:
        x_position = TEXT_MARGIN_LEFT

        # Handle table rows
        if parsed_line.is_table_row and parsed_line.table_row:
            table_row = parsed_line.table_row

            # Skip separator rows (just add small spacing)
            if table_row.is_separator:
                # Draw horizontal line
                draw.line(
                    [(x_position, y_position + actual_font_size // 2),
                     (image_size[0] - TEXT_MARGIN_RIGHT, y_position + actual_font_size // 2)],
                    fill=table_border_color,
                    width=1
                )
                y_position += line_spacing
                continue

            # Calculate column width
            num_cols = len(table_row.cells)
            available_width = image_size[0] - TEXT_MARGIN_LEFT - TEXT_MARGIN_RIGHT
            col_width = available_width // max(num_cols, 1)

            # Get font for table
            font = FontCache.get_font(TextStyle.BOLD if table_row.is_header else TextStyle.NORMAL, actual_font_size)

            # Draw each cell
            for i, cell in enumerate(table_row.cells):
                cell_x = x_position + i * col_width
                draw.text((cell_x, y_position), cell, font=font, fill=FONT_COLOR)

            y_position += actual_font_size + line_spacing
            continue

        # Handle code blocks (background already drawn)
        if parsed_line.is_code_block:
            # Use Consolas directly for code blocks
            code_font_size = int(actual_font_size * MARKDOWN_SIZE_MULTIPLIERS.get("code", 0.9))
            code_font = ImageFont.truetype(str(FONT_PATH_CODE), code_font_size)
            text_to_draw = parsed_line.segments[0].text if parsed_line.segments else ""
            bbox = code_font.getbbox(text_to_draw) if text_to_draw else (0, 0, 0, actual_font_size)
            text_height = bbox[3] - bbox[1] if bbox else actual_font_size

            draw.text((x_position, y_position), text_to_draw, font=code_font, fill=FONT_COLOR)
            y_position += text_height + line_spacing
            continue

        # Handle quotes
        if parsed_line.is_quote:
            # Draw quote bar
            draw.rectangle(
                [(x_position - 15, y_position),
                 (x_position - 10, y_position + actual_font_size)],
                fill=quote_color
            )
            x_position += 10  # Indent quote text

        # Add indent for list items
        if parsed_line.is_list_item:
            x_position += parsed_line.list_indent * 20 + 30

        # Calculate max height for this line
        max_height = 0
        for segment in parsed_line.segments:
            font = FontCache.get_font(segment.style, actual_font_size)
            bbox = font.getbbox(segment.text) if segment.text else (0, 0, 0, 0)
            segment_height = bbox[3] - bbox[1] if bbox else actual_font_size
            max_height = max(max_height, segment_height)

        # Handle empty lines
        if not parsed_line.segments or all(not s.text for s in parsed_line.segments):
            max_height = actual_font_size

        # Render each segment
        for segment in parsed_line.segments:
            if not segment.text:
                continue

            font = FontCache.get_font(segment.style, actual_font_size)

            # Choose color based on style
            if segment.style == TextStyle.QUOTE:
                color = quote_color
            elif segment.style == TextStyle.CODE:
                color = inline_code_color
            else:
                color = FONT_COLOR

            # Draw text
            draw.text((x_position, y_position), segment.text, font=font, fill=color)

            # Calculate width for next segment
            bbox = font.getbbox(segment.text)
            text_width = bbox[2] - bbox[0] if bbox else 0
            x_position += text_width

        # Move to next line
        y_position += max_height + line_spacing

        # Add extra spacing after headings
        if parsed_line.is_heading:
            y_position += int(line_spacing * 0.5)

    return image


def update_wallpaper_from_memo(
    image_size: tuple[int, int] = DEFAULT_IMAGE_SIZE,
    memo_filename: str = DEFAULT_MEMO_FILENAME,
    enable_markdown: bool = True
) -> None:
    """Update desktop wallpaper from memo file."""
    output_file = DATA_DIR / OUTPUT_FILENAME

    if output_file.exists():
        output_file.unlink()
        print(f"Deleted existing image '{output_file.name}'.")

    memo_file = DATA_DIR / memo_filename
    if memo_file.exists():
        txt = memo_file.read_text(encoding="utf-8")
    else:
        txt = f"Memo file '{memo_filename}' not found."

    # Render with markdown support
    image = render_markdown_to_image(txt, image_size, enable_markdown)

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