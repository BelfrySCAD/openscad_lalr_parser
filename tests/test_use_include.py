"""Tests for use and include statements."""
from openscad_lalr_parser import (
    getASTfromString,
    UseStatement,
    IncludeStatement,
    Assignment,
)


class TestUseStatement:
    def test_use(self, parse):
        ast = parse("use <library.scad>")
        assert isinstance(ast[0], UseStatement)
        assert ast[0].filepath.val == "library.scad"

    def test_use_path(self, parse):
        ast = parse("use <BOSL2/std.scad>")
        assert isinstance(ast[0], UseStatement)
        assert ast[0].filepath.val == "BOSL2/std.scad"

    def test_use_str(self, parse):
        ast = parse("use <library.scad>")
        assert str(ast[0]) == "use <library.scad>"

    def test_use_multiple(self, parse):
        ast = parse("use <file1.scad>\nuse <file2.scad>")
        assert isinstance(ast[0], UseStatement)
        assert isinstance(ast[1], UseStatement)
        assert ast[0].filepath.val == "file1.scad"
        assert ast[1].filepath.val == "file2.scad"

    def test_use_with_code(self, parse):
        ast = parse("use <file.scad>\nx = 1;")
        assert isinstance(ast[0], UseStatement)
        assert isinstance(ast[1], Assignment)


class TestIncludeStatement:
    def test_include(self, parse):
        ast = parse("include <config.scad>")
        assert isinstance(ast[0], IncludeStatement)
        assert ast[0].filepath.val == "config.scad"

    def test_include_path(self, parse):
        ast = parse("include <utils/math.scad>")
        assert isinstance(ast[0], IncludeStatement)
        assert ast[0].filepath.val == "utils/math.scad"

    def test_include_str(self, parse):
        ast = parse("include <config.scad>")
        assert str(ast[0]) == "include <config.scad>"

    def test_include_multiple(self, parse):
        ast = parse("include <file1.scad>\ninclude <file2.scad>")
        assert isinstance(ast[0], IncludeStatement)
        assert isinstance(ast[1], IncludeStatement)
        assert ast[0].filepath.val == "file1.scad"
        assert ast[1].filepath.val == "file2.scad"

    def test_include_with_code(self, parse):
        ast = parse("include <file.scad>\nx = 1;")
        assert isinstance(ast[0], IncludeStatement)
        assert isinstance(ast[1], Assignment)


class TestMixed:
    def test_use_and_include(self, parse):
        ast = parse("use <lib.scad>\ninclude <config.scad>\ncube(1);")
        assert isinstance(ast[0], UseStatement)
        assert isinstance(ast[1], IncludeStatement)
        assert len(ast) == 3

    def test_use_then_include(self, parse):
        ast = parse("use <file1.scad>\ninclude <file2.scad>")
        assert isinstance(ast[0], UseStatement)
        assert isinstance(ast[1], IncludeStatement)

    def test_include_then_use(self, parse):
        ast = parse("include <file1.scad>\nuse <file2.scad>")
        assert isinstance(ast[0], IncludeStatement)
        assert isinstance(ast[1], UseStatement)

    def test_multiple_mixed(self, parse):
        ast = parse("use <file1.scad>\ninclude <file2.scad>\nuse <file3.scad>")
        assert isinstance(ast[0], UseStatement)
        assert isinstance(ast[1], IncludeStatement)
        assert isinstance(ast[2], UseStatement)
        assert len(ast) == 3
