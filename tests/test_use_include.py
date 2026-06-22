"""Tests for use and include statements."""
from openscad_lalr_parser import (
    getASTfromString,
    UseStatement,
    IncludeStatement,
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


class TestMixed:
    def test_use_and_include(self, parse):
        ast = parse("use <lib.scad>\ninclude <config.scad>\ncube(1);")
        assert isinstance(ast[0], UseStatement)
        assert isinstance(ast[1], IncludeStatement)
        assert len(ast) == 3
