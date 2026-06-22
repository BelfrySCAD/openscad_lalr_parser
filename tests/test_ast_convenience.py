"""Tests for AST convenience functions: getASTfromString, getASTfromFile, getASTfromLibraryFile."""

import os
import sys
import time
import tempfile
from io import StringIO
import pytest
from openscad_lalr_parser import (
    getASTfromString,
    getASTfromFile,
    getASTfromLibraryFile,
    findLibraryFile,
    clear_ast_cache,
    Assignment,
    ModuleDeclaration,
    FunctionDeclaration,
    Identifier,
    NumberLiteral,
    AdditionOp,
    LogicalNotOp,
    BitwiseNotOp,
    IncludeStatement,
    Position,
    ModularCall,
    CommentLine,
    CommentSpan,
)


class TestGetASTfromString:
    def test_simple_assignment(self):
        code = "x = 42;"
        ast = getASTfromString(code)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 1
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].name, Identifier)
        assert ast[0].name.name == "x"
        assert isinstance(ast[0].expr, NumberLiteral)
        assert ast[0].expr.val == 42

    def test_complex_expression(self):
        code = "result = 10 + 5;"
        ast = getASTfromString(code)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 1
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, AdditionOp)
        assert isinstance(ast[0].expr.left, NumberLiteral)
        assert ast[0].expr.left.val == 10
        assert isinstance(ast[0].expr.right, NumberLiteral)
        assert ast[0].expr.right.val == 5

    def test_logical_not_expression(self):
        code = "x = !true;"
        ast = getASTfromString(code)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 1
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, LogicalNotOp)

    def test_bitwise_not_expression(self):
        code = "x = ~1;"
        ast = getASTfromString(code)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 1
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, BitwiseNotOp)

    def test_module_declaration(self):
        code = "module test() { cube(10); }"
        ast = getASTfromString(code)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 1
        assert isinstance(ast[0], ModuleDeclaration)
        assert isinstance(ast[0].name, Identifier)
        assert ast[0].name.name == "test"

    def test_function_declaration(self):
        code = "function add(x, y) = x + y;"
        ast = getASTfromString(code)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 1
        assert isinstance(ast[0], FunctionDeclaration)
        assert isinstance(ast[0].name, Identifier)
        assert ast[0].name.name == "add"

    def test_empty_code(self):
        code = ""
        ast = getASTfromString(code)

        assert ast is None or (isinstance(ast, list) and len(ast) == 0)

    def test_multiple_statements(self):
        code = "x = 1; y = 2; z = 3;"
        ast = getASTfromString(code)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 3
        for i, assignment in enumerate(ast):
            assert isinstance(assignment, Assignment)
            assert assignment.name.name == ["x", "y", "z"][i]


class TestGetASTfromFile:
    def test_parse_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            test_file = f.name
            f.write("x = 42;")

        try:
            ast = getASTfromFile(test_file)

            assert ast is not None
            assert isinstance(ast, list)
            assert len(ast) == 1
            assert isinstance(ast[0], Assignment)
            assert ast[0].name.name == "x"
        finally:
            os.unlink(test_file)

    def test_file_caching(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            test_file = f.name
            f.write("x = 42;")

        try:
            ast1 = getASTfromFile(test_file)
            ast2 = getASTfromFile(test_file)

            assert ast1 is ast2
        finally:
            os.unlink(test_file)

    def test_cache_invalidation_on_modification(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            test_file = f.name
            f.write("x = 42;")

        try:
            ast1 = getASTfromFile(test_file)

            time.sleep(0.1)
            with open(test_file, 'w') as f:
                f.write("y = 100;")

            ast2 = getASTfromFile(test_file)

            assert ast1 is not None
            assert ast2 is not None
            assert ast1 is not ast2
            assert isinstance(ast1[0], Assignment)
            assert ast1[0].name.name == "x"
            assert isinstance(ast2[0], Assignment)
            assert ast2[0].name.name == "y"
        finally:
            os.unlink(test_file)

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            getASTfromFile("nonexistent_file.scad")

    def test_multiple_files_cached_independently(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f1:
            file1 = f1.name
            f1.write("x = 1;")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f2:
            file2 = f2.name
            f2.write("y = 2;")

        try:
            ast1a = getASTfromFile(file1)
            ast2a = getASTfromFile(file2)

            ast1b = getASTfromFile(file1)
            ast2b = getASTfromFile(file2)

            assert ast1a is ast1b
            assert ast2a is ast2b
            assert ast1a is not ast2a
        finally:
            os.unlink(file1)
            os.unlink(file2)

    def test_process_includes_false_keeps_include_nodes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")
            lib_file = os.path.join(temp_dir, "lib.scad")

            with open(lib_file, "w") as f:
                f.write("x = 1;")
            with open(main_file, "w") as f:
                f.write("include <lib.scad>;\n")

            ast = getASTfromFile(main_file, process_includes=False)
            assert ast is not None
            assert any(isinstance(node, IncludeStatement) for node in ast)

    def test_clear_cache(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            test_file = f.name
            f.write("x = 42;")

        try:
            ast1 = getASTfromFile(test_file)
            clear_ast_cache()
            ast2 = getASTfromFile(test_file)

            assert ast1 is not ast2
        finally:
            os.unlink(test_file)


class TestFindLibraryFile:
    def test_find_in_current_file_directory(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            current_file = f.name
            f.write("// main file")

        lib_dir = os.path.dirname(current_file)
        lib_file = os.path.join(lib_dir, "library.scad")
        with open(lib_file, 'w') as f:
            f.write("cube(10);")

        try:
            found = findLibraryFile(current_file, "library.scad")
            assert found == lib_file
        finally:
            os.unlink(current_file)
            os.unlink(lib_file)

    def test_find_with_nested_path(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            current_file = f.name
            f.write("// main file")

        lib_dir = os.path.dirname(current_file)
        utils_dir = os.path.join(lib_dir, "utils")
        os.makedirs(utils_dir, exist_ok=True)
        lib_file = os.path.join(utils_dir, "math.scad")
        with open(lib_file, 'w') as f:
            f.write("function add(x, y) = x + y;")

        try:
            found = findLibraryFile(current_file, "utils/math.scad")
            assert found == lib_file
        finally:
            os.unlink(current_file)
            os.unlink(lib_file)
            os.rmdir(utils_dir)

    def test_not_found_returns_none(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            current_file = f.name
            f.write("// main file")

        try:
            found = findLibraryFile(current_file, "nonexistent.scad")
            assert found is None
        finally:
            os.unlink(current_file)

    def test_empty_current_file(self):
        found = findLibraryFile("", "nonexistent.scad")
        assert found is None

    def test_find_library_file_windows_env_path(self, monkeypatch):
        import platform
        with tempfile.TemporaryDirectory() as temp_dir:
            lib_dir1 = os.path.join(temp_dir, "libs1")
            lib_dir2 = os.path.join(temp_dir, "libs2")
            os.makedirs(lib_dir1)
            os.makedirs(lib_dir2)
            target = os.path.join(lib_dir2, "lib.scad")
            with open(target, "w") as f:
                f.write("x = 1;")

            monkeypatch.setattr(platform, "system", lambda: "Windows")
            monkeypatch.setenv("OPENSCADPATH", f"{lib_dir1};{lib_dir2}")

            found = findLibraryFile("", "lib.scad")
            assert found == target

    def test_find_library_file_darwin_env_path(self, monkeypatch):
        import platform
        with tempfile.TemporaryDirectory() as temp_dir:
            lib_dir = os.path.join(temp_dir, "libraries")
            os.makedirs(lib_dir)
            target = os.path.join(lib_dir, "lib.scad")
            with open(target, "w") as f:
                f.write("x = 1;")

            monkeypatch.setattr(platform, "system", lambda: "Darwin")
            monkeypatch.setenv("OPENSCADPATH", lib_dir)

            found = findLibraryFile("", "lib.scad")
            assert found == target


class TestGetASTfromLibraryFile:
    def test_find_and_parse_library_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            current_file = f.name
            f.write("// main file")

        lib_dir = os.path.dirname(current_file)
        lib_file = os.path.join(lib_dir, "library.scad")
        with open(lib_file, 'w') as f:
            f.write("cube(10);")

        try:
            ast, path = getASTfromLibraryFile(current_file, "library.scad")

            assert ast is not None
            assert isinstance(ast, list)
            assert len(ast) >= 1
            assert isinstance(ast[0], ModularCall)
            assert ast[0].name.name == "cube"
            assert path == os.path.abspath(lib_file)
        finally:
            os.unlink(current_file)
            os.unlink(lib_file)

    def test_find_and_parse_nested_library_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            current_file = f.name
            f.write("// main file")

        lib_dir = os.path.dirname(current_file)
        utils_dir = os.path.join(lib_dir, "utils")
        os.makedirs(utils_dir, exist_ok=True)
        lib_file = os.path.join(utils_dir, "math.scad")
        with open(lib_file, 'w') as f:
            f.write("function add(x, y) = x + y;")

        try:
            ast, path = getASTfromLibraryFile(current_file, "utils/math.scad")

            assert ast is not None
            assert isinstance(ast, list)
            assert len(ast) == 1
            assert isinstance(ast[0], FunctionDeclaration)
            assert ast[0].name.name == "add"
            assert path == os.path.abspath(lib_file)
        finally:
            os.unlink(current_file)
            os.unlink(lib_file)
            os.rmdir(utils_dir)

    def test_library_file_not_found(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            current_file = f.name
            f.write("// main file")

        try:
            with pytest.raises(FileNotFoundError) as exc_info:
                getASTfromLibraryFile(current_file, "nonexistent.scad")

            assert "not found in search paths" in str(exc_info.value)
        finally:
            os.unlink(current_file)

    def test_library_file_caching(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            current_file = f.name
            f.write("// main file")

        lib_dir = os.path.dirname(current_file)
        lib_file = os.path.join(lib_dir, "library.scad")
        with open(lib_file, 'w') as f:
            f.write("cube(10);")

        try:
            ast1, path1 = getASTfromLibraryFile(current_file, "library.scad")
            ast2, path2 = getASTfromLibraryFile(current_file, "library.scad")

            assert ast1 is ast2
            assert path1 == path2
            assert path1 == os.path.abspath(lib_file)
        finally:
            os.unlink(current_file)
            os.unlink(lib_file)

    def test_without_current_file(self):
        with pytest.raises(FileNotFoundError):
            getASTfromLibraryFile("", "nonexistent_library.scad")


class TestIncludeComments:
    def test_getASTfromString_comments_excluded_by_default(self):
        code = "// This is a comment\nx = 5;"
        ast = getASTfromString(code)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 1
        assert isinstance(ast[0], Assignment)
        assert not any(isinstance(node, CommentLine) for node in ast)
        assert not any(isinstance(node, CommentSpan) for node in ast)

    def test_getASTfromString_comments_included_when_requested(self):
        code = "// This is a comment\nx = 5;"
        ast = getASTfromString(code, include_comments=True)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 2
        comment_nodes = [node for node in ast if isinstance(node, CommentLine)]
        assert len(comment_nodes) == 1
        assert comment_nodes[0].text == " This is a comment"
        assignment_nodes = [node for node in ast if isinstance(node, Assignment)]
        assert len(assignment_nodes) == 1

    def test_getASTfromString_multi_line_comment_included(self):
        code = "/* This is a\nmulti-line comment */\nx = 5;"
        ast = getASTfromString(code, include_comments=True)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 2
        comment_nodes = [node for node in ast if isinstance(node, CommentSpan)]
        assert len(comment_nodes) == 1
        assert "This is a\nmulti-line comment" in comment_nodes[0].text
        assignment_nodes = [node for node in ast if isinstance(node, Assignment)]
        assert len(assignment_nodes) == 1

    def test_getASTfromString_comments_excluded_when_false(self):
        code = "// This is a comment\nx = 5;"
        ast = getASTfromString(code, include_comments=False)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 1
        assert isinstance(ast[0], Assignment)
        assert not any(isinstance(node, CommentLine) for node in ast)

    def test_getASTfromFile_comments_excluded_by_default(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            f.write("// This is a comment\nx = 5;")
            temp_file = f.name

        try:
            ast = getASTfromFile(temp_file)

            assert ast is not None
            assert isinstance(ast, list)
            assert len(ast) == 1
            assert isinstance(ast[0], Assignment)
            assert not any(isinstance(node, CommentLine) for node in ast)
        finally:
            os.unlink(temp_file)

    def test_getASTfromFile_comments_included_when_requested(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            f.write("// This is a comment\nx = 5;")
            temp_file = f.name

        try:
            ast = getASTfromFile(temp_file, include_comments=True)

            assert ast is not None
            assert isinstance(ast, list)
            assert len(ast) == 2
            comment_nodes = [node for node in ast if isinstance(node, CommentLine)]
            assert len(comment_nodes) == 1
            assignment_nodes = [node for node in ast if isinstance(node, Assignment)]
            assert len(assignment_nodes) == 1
        finally:
            os.unlink(temp_file)

    def test_getASTfromFile_cache_separate_for_comments(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            f.write("// This is a comment\nx = 5;")
            temp_file = f.name

        try:
            clear_ast_cache()

            ast1 = getASTfromFile(temp_file, include_comments=False)
            assert ast1 is not None
            assert len(ast1) == 1
            assert not any(isinstance(node, CommentLine) for node in ast1)

            ast2 = getASTfromFile(temp_file, include_comments=True)
            assert ast2 is not None
            assert len(ast2) == 2
            assert any(isinstance(node, CommentLine) for node in ast2)

            ast3 = getASTfromFile(temp_file, include_comments=False)
            assert ast3 is not None
            assert len(ast3) == 1
            assert not any(isinstance(node, CommentLine) for node in ast3)
        finally:
            os.unlink(temp_file)

    def test_getASTfromLibraryFile_comments_parameter(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            lib_file = os.path.join(temp_dir, "test_lib.scad")
            with open(lib_file, 'w') as f:
                f.write("// Library comment\nx = 5;")

            ast1, path1 = getASTfromLibraryFile("", lib_file, include_comments=False)
            assert ast1 is not None
            assert len(ast1) == 1
            assert not any(isinstance(node, CommentLine) for node in ast1)

            ast2, path2 = getASTfromLibraryFile("", lib_file, include_comments=True)
            assert ast2 is not None
            assert len(ast2) == 2
            assert any(isinstance(node, CommentLine) for node in ast2)


class TestErrorReporting:
    def test_error_shows_line_and_caret(self):
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            result = getASTfromString('x = ')
            output = buffer.getvalue()

            assert "Syntax error" in output
            assert "line 1" in output
            assert "column" in output
            assert "^" in output
        finally:
            sys.stdout = old_stdout

    def test_error_caret_position_single_line(self):
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            result = getASTfromString('x = 5 +')
            output = buffer.getvalue()

            assert "x = 5 +" in output
            assert "^" in output
        finally:
            sys.stdout = old_stdout

    def test_error_caret_position_multi_line(self):
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            result = getASTfromString('x = 5;\ny = 10 +')
            output = buffer.getvalue()

            assert "y = 10 +" in output
            assert "^" in output
            assert "line 2" in output
        finally:
            sys.stdout = old_stdout

    def test_error_with_origin(self):
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            result = getASTfromString('x = ', origin='test.scad')
            output = buffer.getvalue()

            assert "test.scad" in output or "<string>" in output
        finally:
            sys.stdout = old_stdout

    def test_error_format_components(self):
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            result = getASTfromString('x = ')
            output = buffer.getvalue()

            assert "Syntax error" in output
            assert "line" in output
            assert "column" in output
            assert "^" in output
        finally:
            sys.stdout = old_stdout

    def test_error_with_tabs(self):
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            result = getASTfromString('x\t= ')
            output = buffer.getvalue()

            assert "Syntax error" in output
            assert "^" in output
        finally:
            sys.stdout = old_stdout

    def test_error_with_source_map(self):
        from openscad_lalr_parser.source_map import SourceMap
        from openscad_lalr_parser import parse_ast

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            source_map = SourceMap()
            source_map.add_origin("test.scad", "x = ")
            combined_code = source_map.get_combined_string()

            result = parse_ast(combined_code, source_map=source_map)
            output = buffer.getvalue()

            assert "Syntax error" in output
            assert "^" in output
        finally:
            sys.stdout = old_stdout

    def test_error_reporting_without_source_map(self):
        from openscad_lalr_parser import parse_ast

        old_stdout = sys.stdout
        try:
            buffer = StringIO()
            sys.stdout = buffer

            result = parse_ast("x = ;", origin="test.scad", source_map=None)
            output = buffer.getvalue()

            assert "Syntax error" in output
            assert "test.scad" in output
            assert "^" in output
        finally:
            sys.stdout = old_stdout

    def test_get_ast_from_file_error_handling(self):
        with pytest.raises(FileNotFoundError):
            getASTfromFile("nonexistent_file_that_does_not_exist.scad")

        with tempfile.TemporaryDirectory() as temp_dir:
            fake_file = os.path.join(temp_dir, "fake.scad")
            os.makedirs(fake_file, exist_ok=True)

            with pytest.raises(Exception):
                getASTfromFile(fake_file)

    def test_get_ast_from_file_process_includes_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")

            with open(main_file, 'w') as f:
                f.write("x = 5;\ninclude <nonexistent.scad>\n")

            with pytest.raises(Exception):
                getASTfromFile(main_file, process_includes=True)
