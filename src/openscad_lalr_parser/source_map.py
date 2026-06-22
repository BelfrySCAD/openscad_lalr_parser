"""Source map for tracking positions across multiple source origins.

This module provides functionality to combine multiple source origins (files,
editor buffers, etc.) into a single string for parsing while maintaining the
ability to map positions back to their original origin, line, and column locations.
"""

import os
from dataclasses import dataclass
from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .nodes import Position


@dataclass
class SourceSegment:
    origin: str
    start_line: int
    start_column: int
    content: str
    combined_start: int


class SourceMap:
    """Maps positions in a combined source string back to original source locations."""

    def __init__(self):
        self._segments: list[SourceSegment] = []
        self._combined_string: str = ""
        self._combined_string_dirty: bool = True

    def add_origin(self, origin: str, content: str, insert_at: Optional[int] = None,
                   start_line: int = 1, start_column: int = 1, replace_length: int = 0,
                   strip_trailing_newline: bool = False) -> int:
        if insert_at is None:
            if self._segments:
                insert_at = max(seg.combined_start + len(seg.content) for seg in self._segments)
            else:
                insert_at = 0

        if replace_length > 0:
            self._replace_text(insert_at, replace_length, strip_trailing_newline)

        segment = SourceSegment(
            origin=origin,
            start_line=start_line,
            start_column=start_column,
            content=content,
            combined_start=insert_at
        )

        self._insert_segment(segment, insert_at)
        self._combined_string_dirty = True
        return segment.combined_start

    def _replace_text(self, start_pos: int, length: int, strip_trailing_newline: bool = False):
        end_pos = start_pos + length
        segments_to_remove = []
        new_segments = []

        for segment in self._segments:
            segment_start = segment.combined_start
            segment_end = segment_start + len(segment.content)

            if segment_start < end_pos and segment_end > start_pos:
                replace_start_in_segment = max(0, start_pos - segment_start)
                replace_end_in_segment = min(len(segment.content), end_pos - segment_start)

                before_content = segment.content[:replace_start_in_segment]
                after_content = segment.content[replace_end_in_segment:]

                if before_content:
                    segment.content = before_content
                else:
                    segments_to_remove.append(segment)

                if after_content:
                    if strip_trailing_newline and after_content.startswith('\n'):
                        after_content = after_content[1:]
                        line_count_adjustment = 1
                    else:
                        line_count_adjustment = 0

                    if not after_content:
                        continue

                    after_segment = SourceSegment(
                        origin=segment.origin,
                        start_line=segment.start_line,
                        start_column=segment.start_column,
                        content=after_content,
                        combined_start=start_pos
                    )
                    removed_and_before = segment.content[:replace_end_in_segment]
                    line_count = removed_and_before.count('\n') + line_count_adjustment
                    if line_count > 0:
                        if line_count_adjustment and removed_and_before.count('\n') == 0:
                            after_segment.start_line = segment.start_line + line_count
                            after_segment.start_column = 1
                        else:
                            last_newline = removed_and_before.rfind('\n')
                            after_segment.start_line = segment.start_line + line_count
                            after_segment.start_column = len(removed_and_before) - last_newline
                    else:
                        after_segment.start_line = segment.start_line
                        after_segment.start_column = segment.start_column + len(removed_and_before)

                    new_segments.append(after_segment)

        for segment in segments_to_remove:
            if segment in self._segments:
                self._segments.remove(segment)

        self._segments.extend(new_segments)
        self._segments = [seg for seg in self._segments if len(seg.content) > 0]

        for segment in self._segments:
            if segment.combined_start >= end_pos:
                segment.combined_start -= length
            elif segment.combined_start == start_pos and segment in new_segments:
                pass

    def _insert_segment(self, segment: SourceSegment, insert_at: int):
        segment_length = len(segment.content)

        for existing_segment in self._segments:
            if existing_segment.combined_start >= insert_at:
                existing_segment.combined_start += segment_length

        insert_idx = 0
        for i, existing_segment in enumerate(self._segments):
            if existing_segment.combined_start > segment.combined_start:
                insert_idx = i
                break
        else:
            insert_idx = len(self._segments)

        self._segments.insert(insert_idx, segment)

    def get_combined_string(self) -> str:
        if self._combined_string_dirty:
            self._rebuild_combined_string()
        return self._combined_string

    def _rebuild_combined_string(self):
        if not self._segments:
            self._combined_string = ""
            self._combined_string_dirty = False
            return

        sorted_segments = sorted(self._segments, key=lambda s: s.combined_start)
        parts = []
        current_pos = 0

        for segment in sorted_segments:
            if segment.combined_start > current_pos:
                parts.append(' ' * (segment.combined_start - current_pos))
            parts.append(segment.content)
            current_pos = segment.combined_start + len(segment.content)

        self._combined_string = ''.join(parts)
        self._combined_string_dirty = False

    def get_location(self, position: int, end_position: Optional[int] = None):
        from .nodes import Position

        if position < 0:
            position = 0

        segment = self._find_segment(position)

        if segment is None:
            if self._segments:
                last_segment = max(self._segments, key=lambda s: s.combined_start + len(s.content))
                seg_offset = len(last_segment.content)
                end_offset = (
                    (end_position - last_segment.combined_start)
                    if end_position is not None
                    else seg_offset
                )
                return self._calculate_location_in_segment(last_segment, seg_offset, end_offset)
            else:
                return Position(origin="", line=1, column=1)

        segment_offset = position - segment.combined_start
        end_offset = (
            (end_position - segment.combined_start)
            if end_position is not None
            else segment_offset
        )
        return self._calculate_location_in_segment(segment, segment_offset, end_offset)

    def _find_segment(self, position: int) -> Optional[SourceSegment]:
        if not self._segments:
            return None

        left, right = 0, len(self._segments) - 1

        while left <= right:
            mid = (left + right) // 2
            segment = self._segments[mid]
            segment_end = segment.combined_start + len(segment.content)

            if segment.combined_start <= position < segment_end:
                return segment
            elif position < segment.combined_start:
                right = mid - 1
            else:
                left = mid + 1

        return None

    def _calculate_location_in_segment(self, segment: SourceSegment, offset: int,
                                        end_offset: Optional[int] = None):
        from .nodes import Position

        if offset < 0:
            offset = 0
        if offset > len(segment.content):
            offset = len(segment.content)

        content_before = segment.content[:offset]
        line_count = content_before.count('\n')
        line_number = segment.start_line + line_count

        if line_count == 0:
            column_number = segment.start_column + offset
        else:
            last_newline = content_before.rfind('\n')
            column_number = offset - last_newline

        resolved_end = end_offset if end_offset is not None else offset

        return Position(
            origin=segment.origin,
            line=line_number,
            column=column_number,
            start_offset=offset,
            end_offset=resolved_end,
        )

    def get_segments(self) -> list[SourceSegment]:
        return self._segments.copy()


def create_source_map_from_origins(origins: list[Tuple[str, str]],
                                    insert_positions: Optional[list[int]] = None) -> SourceMap:
    source_map = SourceMap()

    if insert_positions is None:
        for origin, content in origins:
            source_map.add_origin(origin, content)
    else:
        if len(insert_positions) != len(origins):
            raise ValueError("insert_positions must have same length as origins")
        for (origin, content), insert_at in zip(origins, insert_positions):
            source_map.add_origin(origin, content, insert_at=insert_at)

    return source_map


def process_includes(source_map: SourceMap, current_file: str = "",
                     max_iterations: int = 100) -> SourceMap:
    from . import findLibraryFile

    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        combined = source_map.get_combined_string()
        includes = _find_valid_includes(combined)

        if not includes:
            break

        includes.sort(key=lambda x: x['position'], reverse=True)

        for include_info in includes:
            filename = include_info['filename']
            position = include_info['position']
            length = include_info['length']

            if current_file:
                lib_file = findLibraryFile(current_file, filename)
            else:
                lib_file = findLibraryFile("", filename)

            if lib_file is None:
                raise FileNotFoundError(
                    f"Included file '{filename}' not found. "
                    f"Searched relative to: {current_file if current_file else 'current directory'}"
                )

            try:
                with open(lib_file, 'r', encoding='utf-8') as f:
                    included_content = f.read()
            except Exception as e:
                raise IOError(f"Error reading included file '{lib_file}': {e}")

            location = source_map.get_location(position)

            source_map.add_origin(
                origin=lib_file,
                content=included_content,
                insert_at=position,
                replace_length=length,
                strip_trailing_newline=True
            )

            current_file = lib_file
    else:
        raise ValueError(
            f"Maximum iterations ({max_iterations}) exceeded while processing includes. "
            "This may indicate circular includes or a very deep include chain."
        )

    return source_map


def _find_valid_includes(code: str) -> list[dict]:
    includes = []
    i = 0
    in_string = False
    string_char = None
    in_single_line_comment = False
    in_multi_line_comment = False

    while i < len(code):
        char = code[i]
        next_char = code[i + 1] if i + 1 < len(code) else None

        if not in_single_line_comment and not in_multi_line_comment:
            if char == '"' or char == "'":
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    if i > 0 and code[i - 1] != '\\':
                        in_string = False
                        string_char = None
            elif in_string and char == '\\' and next_char == string_char:
                i += 1

        if not in_string and not in_multi_line_comment:
            if char == '/' and next_char == '/':
                in_single_line_comment = True
                i += 1
            elif in_single_line_comment and char == '\n':
                in_single_line_comment = False

        if not in_string and not in_single_line_comment:
            if char == '/' and next_char == '*':
                in_multi_line_comment = True
                i += 1
            elif in_multi_line_comment and char == '*' and next_char == '/':
                in_multi_line_comment = False
                i += 1

        if not in_string and not in_single_line_comment and not in_multi_line_comment:
            if (char == 'i' and
                i + 7 < len(code) and
                code[i:i+7] == 'include' and
                (i == 0 or not (code[i-1].isalnum() or code[i-1] == '_')) and
                i + 8 < len(code)):

                after_include = _skip_whitespace(code, i + 7)
                if after_include < len(code) and code[after_include] == '<':
                    start_pos = i
                    filename_start = after_include + 1
                    filename_end = filename_start

                    while filename_end < len(code) and code[filename_end] != '>':
                        if code[filename_end] == '\n':
                            break
                        filename_end += 1
                    else:
                        if filename_end < len(code):
                            filename = code[filename_start:filename_end].strip()
                            if filename:
                                end_pos = filename_end + 1
                                includes.append({
                                    'position': start_pos,
                                    'length': end_pos - start_pos,
                                    'filename': filename
                                })
                                i = end_pos
                                continue

        i += 1

    return includes


def _skip_whitespace(code: str, start: int) -> int:
    i = start
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    return i
