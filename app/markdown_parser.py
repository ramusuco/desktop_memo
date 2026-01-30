"""Markdown parser for DesktopMemo application."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Optional


class TextStyle(Enum):
    NORMAL = "normal"
    BOLD = "bold"
    ITALIC = "italic"
    CODE = "code"
    HEADING1 = "h1"
    HEADING2 = "h2"
    HEADING3 = "h3"
    QUOTE = "quote"


@dataclass
class TextSegment:
    """Represents a segment of text with styling information."""
    text: str
    style: TextStyle = TextStyle.NORMAL
    is_list_item: bool = False
    list_indent: int = 0


@dataclass
class TableRow:
    """Represents a row in a table."""
    cells: List[str]
    is_header: bool = False
    is_separator: bool = False


@dataclass
class ParsedLine:
    """Represents a parsed line with multiple segments."""
    segments: List[TextSegment]
    is_heading: bool = False
    heading_level: int = 0
    is_list_item: bool = False
    list_indent: int = 0
    is_code_block: bool = False
    is_quote: bool = False
    is_table_row: bool = False
    table_row: Optional[TableRow] = None


class MarkdownParser:
    """Parser for basic markdown syntax."""

    # Regex patterns for inline styles
    BOLD_PATTERN = re.compile(r'\*\*(.+?)\*\*')
    ITALIC_PATTERN = re.compile(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)')
    CODE_PATTERN = re.compile(r'`([^`]+)`')

    @classmethod
    def parse_text(cls, text: str) -> List[ParsedLine]:
        """Parse markdown text into a list of parsed lines."""
        lines = text.split('\n')
        parsed_lines = []
        in_code_block = False
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check for code block start/end
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                # Skip the ``` line itself
                i += 1
                continue

            if in_code_block:
                # Inside code block - render as code style
                segments = [TextSegment(text=line, style=TextStyle.CODE)]
                parsed_lines.append(ParsedLine(segments=segments, is_code_block=True))
                i += 1
                continue

            # Check for table row
            if cls._is_table_row(line):
                table_row = cls._parse_table_row(line, i, lines)
                if table_row:
                    segments = [TextSegment(text=line, style=TextStyle.NORMAL)]
                    parsed_lines.append(ParsedLine(
                        segments=segments,
                        is_table_row=True,
                        table_row=table_row
                    ))
                    i += 1
                    continue

            # Check for quote
            if line.strip().startswith('>'):
                content = line.strip()[1:].strip()
                segments = cls._parse_inline_styles(content, base_style=TextStyle.QUOTE)
                parsed_lines.append(ParsedLine(segments=segments, is_quote=True))
                i += 1
                continue

            # Regular line parsing
            parsed_line = cls._parse_line(line)
            parsed_lines.append(parsed_line)
            i += 1

        return parsed_lines

    @classmethod
    def _is_table_row(cls, line: str) -> bool:
        """Check if a line is a table row."""
        stripped = line.strip()
        if not stripped:
            return False
        # Table row starts and ends with | or contains | somewhere
        return '|' in stripped

    @classmethod
    def _parse_table_row(cls, line: str, index: int, all_lines: List[str]) -> Optional[TableRow]:
        """Parse a table row."""
        stripped = line.strip()

        # Remove leading/trailing pipes and split
        if stripped.startswith('|'):
            stripped = stripped[1:]
        if stripped.endswith('|'):
            stripped = stripped[:-1]

        cells = [cell.strip() for cell in stripped.split('|')]

        # Check if this is a separator row (contains only -, :, and spaces)
        is_separator = all(
            re.match(r'^[\-:\s]+$', cell) or cell == ''
            for cell in cells
        )

        if is_separator:
            return TableRow(cells=cells, is_separator=True)

        # Check if this is a header row (first row before separator)
        is_header = False
        if index + 1 < len(all_lines):
            next_line = all_lines[index + 1].strip()
            if cls._is_table_row(next_line):
                # Check if next line is separator
                if next_line.startswith('|'):
                    next_line = next_line[1:]
                if next_line.endswith('|'):
                    next_line = next_line[:-1]
                next_cells = [c.strip() for c in next_line.split('|')]
                is_header = all(
                    re.match(r'^[\-:\s]+$', cell) or cell == ''
                    for cell in next_cells
                )

        return TableRow(cells=cells, is_header=is_header)

    @classmethod
    def _parse_line(cls, line: str) -> ParsedLine:
        """Parse a single line of markdown."""
        original_line = line

        # Check for headings
        heading_match = re.match(r'^(#{1,3})\s+(.*)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            content = heading_match.group(2)
            style = {1: TextStyle.HEADING1, 2: TextStyle.HEADING2, 3: TextStyle.HEADING3}[level]
            segments = cls._parse_inline_styles(content, base_style=style)
            return ParsedLine(
                segments=segments,
                is_heading=True,
                heading_level=level
            )

        # Check for list items
        list_match = re.match(r'^(\s*)([-*])\s+(.*)$', line)
        if list_match:
            indent = len(list_match.group(1))
            content = list_match.group(3)
            bullet = "・"  # Japanese bullet point
            segments = [TextSegment(text=bullet + " ", style=TextStyle.NORMAL)]
            segments.extend(cls._parse_inline_styles(content))
            return ParsedLine(
                segments=segments,
                is_list_item=True,
                list_indent=indent
            )

        # Regular line with inline styles
        segments = cls._parse_inline_styles(line)
        return ParsedLine(segments=segments)

    @classmethod
    def _parse_inline_styles(cls, text: str, base_style: TextStyle = TextStyle.NORMAL) -> List[TextSegment]:
        """Parse inline styles (bold, italic, code) from text."""
        segments = []

        if not text:
            return [TextSegment(text="", style=base_style)]

        # Combined pattern to find all styled text
        combined_pattern = re.compile(
            r'(\*\*(.+?)\*\*)|'  # Bold
            r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)|'  # Italic
            r'`([^`]+)`'  # Code
        )

        last_end = 0
        for match in combined_pattern.finditer(text):
            # Add any text before this match
            if match.start() > last_end:
                before_text = text[last_end:match.start()]
                if before_text:
                    segments.append(TextSegment(text=before_text, style=base_style))

            # Determine which pattern matched
            if match.group(2):  # Bold (**text**)
                style = TextStyle.BOLD if base_style == TextStyle.NORMAL else base_style
                segments.append(TextSegment(text=match.group(2), style=style))
            elif match.group(3):  # Italic (*text*)
                style = TextStyle.ITALIC if base_style == TextStyle.NORMAL else base_style
                segments.append(TextSegment(text=match.group(3), style=style))
            elif match.group(4):  # Code (`text`)
                segments.append(TextSegment(text=match.group(4), style=TextStyle.CODE))

            last_end = match.end()

        # Add any remaining text
        if last_end < len(text):
            remaining = text[last_end:]
            if remaining:
                segments.append(TextSegment(text=remaining, style=base_style))

        # If no segments were added, return the original text
        if not segments:
            segments.append(TextSegment(text=text, style=base_style))

        return segments

    @classmethod
    def strip_markdown(cls, text: str) -> str:
        """Remove markdown syntax and return plain text."""
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)

        # Remove headings markers
        text = re.sub(r'^#{1,3}\s+', '', text, flags=re.MULTILINE)

        # Remove bold
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)

        # Remove italic
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', text)

        # Remove code
        text = re.sub(r'`([^`]+)`', r'\1', text)

        # Convert list markers to bullet points
        text = re.sub(r'^(\s*)[-*]\s+', r'\1・', text, flags=re.MULTILINE)

        # Remove quote markers
        text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)

        return text
