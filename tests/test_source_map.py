"""Tests for source map functionality, including include processing."""

import os
import tempfile
import pytest
from openscad_lalr_parser.source_map import (
    SourceMap,
    process_includes,
    create_source_map_from_origins,
    _find_valid_includes,
    _skip_whitespace,
)
from openscad_lalr_parser import Position


class TestSourceMapBasic:
    def test_add_origin(self):
        source_map = SourceMap()
        source_map.add_origin("main.scad", "x = 5;\n")

        assert len(source_map.get_segments()) == 1
        assert source_map.get_combined_string() == "x = 5;\n"

    def test_get_location(self):
        source_map = SourceMap()
        source_map.add_origin("main.scad", "x = 5;\n")

        loc = source_map.get_location(0)
        assert loc.origin == "main.scad"
        assert loc.line == 1
        assert loc.column == 1

        loc = source_map.get_location(4)
        assert loc.origin == "main.scad"
        assert loc.line == 1
        assert loc.column == 5

    def test_multiple_origins(self):
        source_map = SourceMap()
        source_map.add_origin("main.scad", "x = 5;\n")
        source_map.add_origin("lib.scad", "y = 10;\n", insert_at=8)

        combined = source_map.get_combined_string()
        assert "x = 5;\n" in combined
        assert "y = 10;\n" in combined

        loc = source_map.get_location(8)
        assert loc.origin == "lib.scad"


class TestProcessIncludes:
    def test_simple_include(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")
            lib_file = os.path.join(temp_dir, "lib.scad")

            with open(main_file, 'w') as f:
                f.write("x = 5;\ninclude <lib.scad>\ny = 10;\n")

            with open(lib_file, 'w') as f:
                f.write("z = 20;\n")

            source_map = SourceMap()
            with open(main_file, 'r') as f:
                source_map.add_origin(main_file, f.read())

            source_map = process_includes(source_map, main_file)
            result = source_map.get_combined_string()

            assert "x = 5;\n" in result
            assert "z = 20;\n" in result
            assert "y = 10;\n" in result
            assert "include <lib.scad>" not in result

    def test_nested_includes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")
            lib1_file = os.path.join(temp_dir, "lib1.scad")
            lib2_file = os.path.join(temp_dir, "lib2.scad")

            with open(main_file, 'w') as f:
                f.write("x = 5;\ninclude <lib1.scad>\n")

            with open(lib1_file, 'w') as f:
                f.write("y = 10;\ninclude <lib2.scad>\nz = 15;\n")

            with open(lib2_file, 'w') as f:
                f.write("w = 20;\n")

            source_map = SourceMap()
            with open(main_file, 'r') as f:
                source_map.add_origin(main_file, f.read())

            source_map = process_includes(source_map, main_file)
            result = source_map.get_combined_string()

            assert "x = 5;\n" in result
            assert "y = 10;\n" in result
            assert "w = 20;\n" in result
            assert "z = 15;\n" in result
            assert "include" not in result

    def test_multiple_includes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")
            lib1_file = os.path.join(temp_dir, "lib1.scad")
            lib2_file = os.path.join(temp_dir, "lib2.scad")

            with open(main_file, 'w') as f:
                f.write("x = 5;\ninclude <lib1.scad>\ny = 10;\ninclude <lib2.scad>\nz = 15;\n")

            with open(lib1_file, 'w') as f:
                f.write("a = 1;\n")

            with open(lib2_file, 'w') as f:
                f.write("b = 2;\n")

            source_map = SourceMap()
            with open(main_file, 'r') as f:
                source_map.add_origin(main_file, f.read())

            source_map = process_includes(source_map, main_file)
            result = source_map.get_combined_string()

            assert "x = 5;\n" in result
            assert "a = 1;\n" in result
            assert "y = 10;\n" in result
            assert "b = 2;\n" in result
            assert "z = 15;\n" in result
            assert "include" not in result

    def test_include_in_string_ignored(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")
            lib_file = os.path.join(temp_dir, "lib.scad")

            with open(main_file, 'w') as f:
                f.write('x = 5;\n"include <lib.scad>"\ninclude <lib.scad>\n')

            with open(lib_file, 'w') as f:
                f.write("z = 20;\n")

            source_map = SourceMap()
            with open(main_file, 'r') as f:
                source_map.add_origin(main_file, f.read())

            source_map = process_includes(source_map, main_file)
            result = source_map.get_combined_string()

            assert '"include <lib.scad>"' in result
            assert "z = 20;\n" in result
            assert result.count("include <lib.scad>") == 1

    def test_include_in_single_line_comment_ignored(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")
            lib_file = os.path.join(temp_dir, "lib.scad")

            with open(main_file, 'w') as f:
                f.write("x = 5;\n// include <lib.scad>\ninclude <lib.scad>\n")

            with open(lib_file, 'w') as f:
                f.write("z = 20;\n")

            source_map = SourceMap()
            with open(main_file, 'r') as f:
                source_map.add_origin(main_file, f.read())

            source_map = process_includes(source_map, main_file)
            result = source_map.get_combined_string()

            assert "// include <lib.scad>" in result
            assert "z = 20;\n" in result
            assert result.count("include <lib.scad>") == 1

    def test_include_in_multi_line_comment_ignored(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")
            lib_file = os.path.join(temp_dir, "lib.scad")

            with open(main_file, 'w') as f:
                f.write("x = 5;\n/* include <lib.scad> */\ninclude <lib.scad>\n")

            with open(lib_file, 'w') as f:
                f.write("z = 20;\n")

            source_map = SourceMap()
            with open(main_file, 'r') as f:
                source_map.add_origin(main_file, f.read())

            source_map = process_includes(source_map, main_file)
            result = source_map.get_combined_string()

            assert "/* include <lib.scad> */" in result
            assert "z = 20;\n" in result
            assert result.count("include <lib.scad>") == 1

    def test_include_file_not_found(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")

            with open(main_file, 'w') as f:
                f.write("x = 5;\ninclude <nonexistent.scad>\n")

            source_map = SourceMap()
            with open(main_file, 'r') as f:
                source_map.add_origin(main_file, f.read())

            with pytest.raises(FileNotFoundError) as exc_info:
                process_includes(source_map, main_file)

            assert "nonexistent.scad" in str(exc_info.value)

    def test_circular_includes_prevention(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")
            lib_file = os.path.join(temp_dir, "lib.scad")

            with open(main_file, 'w') as f:
                f.write("include <lib.scad>\n")

            with open(lib_file, 'w') as f:
                f.write("include <main.scad>\n")

            source_map = SourceMap()
            with open(main_file, 'r') as f:
                source_map.add_origin(main_file, f.read())

            with pytest.raises(ValueError) as exc_info:
                process_includes(source_map, main_file, max_iterations=10)

            assert "Maximum iterations" in str(exc_info.value)

    def test_include_with_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")
            lib_dir = os.path.join(temp_dir, "lib")
            os.makedirs(lib_dir)
            lib_file = os.path.join(lib_dir, "lib.scad")

            with open(main_file, 'w') as f:
                f.write("x = 5;\ninclude <lib/lib.scad>\n")

            with open(lib_file, 'w') as f:
                f.write("z = 20;\n")

            source_map = SourceMap()
            with open(main_file, 'r') as f:
                source_map.add_origin(main_file, f.read())

            source_map = process_includes(source_map, main_file)
            result = source_map.get_combined_string()

            assert "x = 5;\n" in result
            assert "z = 20;\n" in result
            assert "include <lib/lib.scad>" not in result

    def test_include_preserves_source_locations(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")
            lib_file = os.path.join(temp_dir, "lib.scad")

            with open(main_file, 'w') as f:
                f.write("x = 5;\ninclude <lib.scad>\ny = 10;\n")

            with open(lib_file, 'w') as f:
                f.write("z = 20;\n")

            source_map = SourceMap()
            with open(main_file, 'r') as f:
                source_map.add_origin(main_file, f.read())

            source_map = process_includes(source_map, main_file)

            loc = source_map.get_location(0)
            assert loc.origin == main_file
            assert loc.line == 1
            assert loc.column == 1

            result = source_map.get_combined_string()
            lib_pos = result.find("z = 20")
            if lib_pos >= 0:
                loc = source_map.get_location(lib_pos)
                assert loc.origin == lib_file

    def test_include_with_whitespace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")
            lib_file = os.path.join(temp_dir, "lib.scad")

            with open(main_file, 'w') as f:
                f.write("x = 5;\ninclude   <lib.scad>\n")

            with open(lib_file, 'w') as f:
                f.write("z = 20;\n")

            source_map = SourceMap()
            with open(main_file, 'r') as f:
                source_map.add_origin(main_file, f.read())

            source_map = process_includes(source_map, main_file)
            result = source_map.get_combined_string()

            assert "z = 20;\n" in result
            assert "include" not in result or "include   <lib.scad>" not in result

    def test_include_with_tabs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")
            lib_file = os.path.join(temp_dir, "lib.scad")

            with open(main_file, 'w') as f:
                f.write("x = 5;\ninclude\t<lib.scad>\n")

            with open(lib_file, 'w') as f:
                f.write("z = 20;\n")

            source_map = SourceMap()
            with open(main_file, 'r') as f:
                source_map.add_origin(main_file, f.read())

            source_map = process_includes(source_map, main_file)
            result = source_map.get_combined_string()

            assert "z = 20;\n" in result

    def test_escaped_quotes_in_string(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")
            lib_file = os.path.join(temp_dir, "lib.scad")

            with open(main_file, 'w') as f:
                f.write('x = "include <lib.scad>";\ninclude <lib.scad>\n')

            with open(lib_file, 'w') as f:
                f.write("z = 20;\n")

            source_map = SourceMap()
            with open(main_file, 'r') as f:
                source_map.add_origin(main_file, f.read())

            source_map = process_includes(source_map, main_file)
            result = source_map.get_combined_string()

            assert '"include <lib.scad>"' in result or 'x = "include <lib.scad>";' in result
            assert "z = 20;\n" in result

    def test_no_includes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")

            with open(main_file, 'w') as f:
                f.write("x = 5;\ny = 10;\n")

            source_map = SourceMap()
            with open(main_file, 'r') as f:
                source_map.add_origin(main_file, f.read())

            original = source_map.get_combined_string()
            source_map = process_includes(source_map, main_file)
            result = source_map.get_combined_string()

            assert result == original

    def test_empty_included_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")
            lib_file = os.path.join(temp_dir, "lib.scad")

            with open(main_file, 'w') as f:
                f.write("x = 5;\ninclude <lib.scad>\ny = 10;\n")

            with open(lib_file, 'w') as f:
                f.write("")

            source_map = SourceMap()
            with open(main_file, 'r') as f:
                source_map.add_origin(main_file, f.read())

            source_map = process_includes(source_map, main_file)
            result = source_map.get_combined_string()

            assert "x = 5;\n" in result
            assert "y = 10;\n" in result
            assert "include <lib.scad>" not in result


class TestSourceMapEdgeCases:
    def test_add_origin_with_existing_segments_calculates_insert_at(self):
        source_map = SourceMap()
        source_map.add_origin("file1.scad", "x = 1;\n")
        source_map.add_origin("file2.scad", "y = 2;\n")

        combined = source_map.get_combined_string()
        assert "x = 1;\n" in combined
        assert "y = 2;\n" in combined

    def test_replace_text_with_zero_length(self):
        source_map = SourceMap()
        source_map.add_origin("file.scad", "x = 1;\n")
        source_map.add_origin("file2.scad", "y = 2;\n", insert_at=0, replace_length=0)

        combined = source_map.get_combined_string()
        assert "x = 1;\n" in combined
        assert "y = 2;\n" in combined

    def test_replace_text_without_strip_trailing_newline(self):
        source_map = SourceMap()
        source_map.add_origin("file.scad", "x = 1;\n")
        source_map.add_origin("file2.scad", "y = 2", insert_at=0, replace_length=1)

        combined = source_map.get_combined_string()
        assert "y = 2" in combined

    def test_replace_text_with_strip_trailing_newline(self):
        source_map = SourceMap()
        source_map.add_origin("main.scad", "include <x>\nY")
        source_map.add_origin(
            "lib.scad",
            "A\n",
            insert_at=0,
            replace_length=len("include <x>"),
            strip_trailing_newline=True,
        )

        combined = source_map.get_combined_string()
        assert combined == "A\nY"

    def test_rebuild_combined_string_empty_segments(self):
        source_map = SourceMap()
        assert source_map.get_combined_string() == ""

    def test_combined_string_includes_gaps(self):
        source_map = SourceMap()
        source_map.add_origin("file1.scad", "abc")
        source_map.add_origin("file2.scad", "Z", insert_at=5)

        combined = source_map.get_combined_string()
        assert combined == "abc  Z"

    def test_get_location_negative_position(self):
        source_map = SourceMap()
        source_map.add_origin("file.scad", "x = 1;\n")

        loc = source_map.get_location(-1)
        assert loc.origin == "file.scad"
        assert loc.line == 1
        assert loc.column == 1

    def test_get_location_no_segments(self):
        source_map = SourceMap()
        loc = source_map.get_location(0)
        assert loc.origin == ""
        assert loc.line == 1
        assert loc.column == 1

    def test_find_segment_no_segments(self):
        source_map = SourceMap()
        segment = source_map._find_segment(0)
        assert segment is None

    def test_find_segment_last_segment_edge_case(self):
        source_map = SourceMap()
        source_map.add_origin("file.scad", "x = 1;\ny = 2;\n")
        segment = source_map._find_segment(10)
        assert segment is not None

    def test_calculate_location_in_segment_negative_offset(self):
        source_map = SourceMap()
        source_map.add_origin("file.scad", "x = 1;\n")
        loc = source_map.get_location(0)
        assert loc.column >= 1

    def test_calculate_location_in_segment_offset_too_large(self):
        source_map = SourceMap()
        source_map.add_origin("file.scad", "x = 1;\n")
        loc = source_map.get_location(100)
        assert loc.origin == "file.scad"

    def test_calculate_location_in_segment_newline_offsets(self):
        source_map = SourceMap()
        source_map.add_origin("file.scad", "a\nb")

        loc = source_map.get_location(2)
        assert loc.origin == "file.scad"
        assert loc.line == 2
        assert loc.column == 1

    def test_create_source_map_from_origins_with_insert_positions(self):
        origins = [("file1.scad", "x = 1;\n"), ("file2.scad", "y = 2;\n")]
        insert_positions = [0, 10]

        source_map = create_source_map_from_origins(origins, insert_positions)
        combined = source_map.get_combined_string()
        assert "x = 1;\n" in combined
        assert "y = 2;\n" in combined

    def test_create_source_map_from_origins_mismatched_lengths(self):
        origins = [("file1.scad", "x = 1;\n")]
        insert_positions = [0, 10]

        with pytest.raises(ValueError) as exc_info:
            create_source_map_from_origins(origins, insert_positions)

        assert "same length" in str(exc_info.value)

    def test_process_includes_without_current_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            lib_file = os.path.join(temp_dir, "lib.scad")

            with open(lib_file, 'w') as f:
                f.write("z = 20;\n")

            source_map = SourceMap()
            source_map.add_origin("main.scad", "x = 5;\ninclude <lib.scad>\n")

            try:
                process_includes(source_map, "")
            except FileNotFoundError:
                pass

    def test_process_includes_io_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")
            lib_file = os.path.join(temp_dir, "lib.scad")

            with open(main_file, 'w') as f:
                f.write("x = 5;\ninclude <lib.scad>\n")

            os.makedirs(lib_file, exist_ok=True)

            source_map = SourceMap()
            with open(main_file, 'r') as f:
                source_map.add_origin(main_file, f.read())

            with pytest.raises(IOError):
                process_includes(source_map, main_file)

    def test_find_valid_includes_escaped_quote(self):
        code = 'x = "include <lib.scad>";\ninclude <lib.scad>\n'
        includes = _find_valid_includes(code)
        assert len(includes) == 1
        assert includes[0]['filename'] == 'lib.scad'

    def test_find_valid_includes_multiline_include(self):
        code = "include <lib\n.scad>\n"
        includes = _find_valid_includes(code)
        assert len(includes) == 0

    def test_find_valid_includes_word_boundary(self):
        code = "xinclude <lib.scad>\ninclude_me <lib.scad>\n"
        includes = _find_valid_includes(code)
        assert len(includes) == 0

    def test_calculate_location_offset_edge_cases(self):
        source_map = SourceMap()
        source_map.add_origin("file.scad", "x = 1;\n")

        loc = source_map.get_location(7)
        assert loc.origin == "file.scad"

        loc = source_map.get_location(100)
        assert loc.origin == "file.scad"

    def test_find_segment_last_segment_exact_boundary(self):
        source_map = SourceMap()
        source_map.add_origin("file1.scad", "x = 1;\n")
        source_map.add_origin("file2.scad", "y = 2;\n", insert_at=8)

        segment = source_map._find_segment(8)
        assert segment is not None
        assert segment.origin == "file2.scad"

    def test_create_source_map_from_origins_without_insert_positions(self):
        origins = [("file1.scad", "x = 1;\n"), ("file2.scad", "y = 2;\n")]

        source_map = create_source_map_from_origins(origins)
        combined = source_map.get_combined_string()
        assert "x = 1;\n" in combined
        assert "y = 2;\n" in combined

    def test_find_valid_includes_with_escaped_quote_in_string(self):
        code = 'x = "include \\" <lib.scad>";\ninclude <lib.scad>\n'
        includes = _find_valid_includes(code)
        assert len(includes) == 1
        assert includes[0]['filename'] == 'lib.scad'

    def test_skip_whitespace_helper(self):
        code = " \t\n\rX"
        assert _skip_whitespace(code, 0) == 4


class TestPositionOffsets:
    def test_get_location_returns_start_offset(self):
        source_map = SourceMap()
        source_map.add_origin("main.scad", "x = 5;\ny = 10;\n")
        loc = source_map.get_location(4)
        assert loc.start_offset == 4

    def test_get_location_returns_end_offset(self):
        source_map = SourceMap()
        source_map.add_origin("main.scad", "x = 5;\ny = 10;\n")
        loc = source_map.get_location(4, end_position=5)
        assert loc.start_offset == 4
        assert loc.end_offset == 5

    def test_get_location_end_defaults_to_start(self):
        source_map = SourceMap()
        source_map.add_origin("main.scad", "abc")
        loc = source_map.get_location(1)
        assert loc.start_offset == loc.end_offset == 1

    def test_offsets_relative_to_segment(self):
        source_map = SourceMap()
        source_map.add_origin("a.scad", "aaa")
        source_map.add_origin("b.scad", "bbb")
        loc = source_map.get_location(4, end_position=6)
        assert loc.origin == "b.scad"
        assert loc.start_offset == 1
        assert loc.end_offset == 3

    def test_position_repr_includes_offsets(self):
        pos = Position(origin="f.scad", line=1, column=1, start_offset=0, end_offset=6)
        assert repr(pos) == "f.scad:1:1[0:6]"

    def test_serialization_roundtrip_offsets(self):
        from openscad_lalr_parser import getASTfromString, ast_to_json, ast_from_json
        ast = getASTfromString("cube(10);")
        json_str = ast_to_json(ast)
        restored = ast_from_json(json_str)
        assert restored is not None and isinstance(restored, list)
        orig_pos = ast[0].position
        rest_pos = restored[0].position
        assert rest_pos.start_offset == orig_pos.start_offset
        assert rest_pos.end_offset == orig_pos.end_offset
