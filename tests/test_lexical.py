"""Tests for lexical elements: literals, identifiers."""
from openscad_lalr_parser import (
    getASTfromString,
    Assignment,
    NumberLiteral,
    StringLiteral,
    BooleanLiteral,
    UndefinedLiteral,
    Identifier,
)


class TestNumberLiterals:
    def test_integer(self, parse):
        ast = parse("x = 42;")
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, NumberLiteral)
        assert ast[0].expr.val == 42.0

    def test_float(self, parse):
        ast = parse("x = 3.14;")
        assert ast[0].expr.val == 3.14

    def test_scientific_notation(self, parse):
        ast = parse("x = 1e10;")
        assert ast[0].expr.val == 1e10

    def test_scientific_notation_negative_exponent(self, parse):
        ast = parse("x = 1.5e-3;")
        assert ast[0].expr.val == 1.5e-3

    def test_hex(self, parse):
        ast = parse("x = 0xFF;")
        assert ast[0].expr.val == 255.0

    def test_leading_dot(self, parse):
        ast = parse("x = .5;")
        assert ast[0].expr.val == 0.5

    def test_number_str(self, parse):
        ast = parse("x = 42;")
        assert str(ast[0].expr) == "42"

    def test_float_str(self, parse):
        ast = parse("x = 3.14;")
        assert str(ast[0].expr) == "3.14"


class TestStringLiterals:
    def test_simple_string(self, parse):
        ast = parse('x = "hello";')
        assert isinstance(ast[0].expr, StringLiteral)
        assert ast[0].expr.val == "hello"

    def test_empty_string(self, parse):
        ast = parse('x = "";')
        assert ast[0].expr.val == ""

    def test_escaped_quotes(self, parse):
        ast = parse(r'x = "say \"hi\"";')
        assert isinstance(ast[0].expr, StringLiteral)

    def test_string_str(self, parse):
        ast = parse('x = "hello";')
        assert str(ast[0].expr) == '"hello"'


class TestBooleanLiterals:
    def test_true(self, parse):
        ast = parse("x = true;")
        assert isinstance(ast[0].expr, BooleanLiteral)
        assert ast[0].expr.val is True

    def test_false(self, parse):
        ast = parse("x = false;")
        assert isinstance(ast[0].expr, BooleanLiteral)
        assert ast[0].expr.val is False

    def test_true_str(self, parse):
        ast = parse("x = true;")
        assert str(ast[0].expr) == "true"

    def test_false_str(self, parse):
        ast = parse("x = false;")
        assert str(ast[0].expr) == "false"


class TestUndefinedLiteral:
    def test_undef(self, parse):
        ast = parse("x = undef;")
        assert isinstance(ast[0].expr, UndefinedLiteral)

    def test_undef_str(self, parse):
        ast = parse("x = undef;")
        assert str(ast[0].expr) == "undef"


class TestIdentifiers:
    def test_simple(self, parse):
        ast = parse("x = foo;")
        assert isinstance(ast[0].expr, Identifier)
        assert ast[0].expr.name == "foo"

    def test_underscore_prefix(self, parse):
        ast = parse("x = _private;")
        assert ast[0].expr.name == "_private"

    def test_dollar_prefix(self, parse):
        ast = parse("x = $fn;")
        assert ast[0].expr.name == "$fn"

    def test_alphanumeric(self, parse):
        ast = parse("x = myVar123;")
        assert ast[0].expr.name == "myVar123"

    def test_identifier_str(self, parse):
        ast = parse("x = foo;")
        assert str(ast[0].expr) == "foo"
