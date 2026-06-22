"""Tests for lexical elements: comments, strings, numbers, identifiers."""
from openscad_lalr_parser import (
    getASTfromString,
    Assignment,
    NumberLiteral,
    StringLiteral,
    BooleanLiteral,
    UndefinedLiteral,
    Identifier,
    CommentLine,
    CommentSpan,
    FunctionDeclaration,
    ModuleDeclaration,
)


class TestComments:
    """Test comment parsing."""

    def test_single_line_comment(self, parse):
        """Test single-line comments parse without error."""
        ast = parse("// This is a comment")
        assert ast is not None

    def test_single_line_comment_with_code(self, parse):
        """Test single-line comment after code."""
        ast = parse("x = 5; // comment")
        assert ast is not None
        assert isinstance(ast[0], Assignment)

    def test_multi_line_comment(self, parse):
        """Test multi-line comments."""
        ast = parse("/* This is a\nmulti-line comment */")
        assert ast is not None

    def test_multi_line_comment_single_line(self, parse):
        """Test multi-line comment on single line."""
        ast = parse("/* comment */")
        assert ast is not None

    def test_comments_in_expressions(self, parse):
        """Test comments within expressions."""
        ast = parse("x = 1 + /* comment */ 2;")
        assert ast is not None
        assert isinstance(ast[0], Assignment)

    def test_block_comment_followed_by_block_comment(self, parse):
        """Test block comment followed by another block comment."""
        ast = parse("/* comment *//* another comment */")
        assert ast is not None

    def test_block_comment_followed_by_inline_comment(self, parse):
        """Test block comment followed by an inline comment."""
        ast = parse("/* comment */// another comment")
        assert ast is not None

    def test_inline_comment_with_nested_inline(self, parse):
        """Test an inline comment with a nested inline is parsed as one comment."""
        ast = parse("// comment // the same comment")
        assert ast is not None

    def test_inline_comment_with_nested_block_comment(self, parse):
        """Test an inline comment with a nested block comment is parsed as one comment."""
        ast = parse("// comment /* the same comment */")
        assert ast is not None

    def test_inline_comment_with_nested_unclosed_block_comment(self, parse):
        """Test an inline comment with a nested unclosed block comment is parsed as one comment."""
        ast = parse("// comment /* the same comment")
        assert ast is not None

    def test_block_comment_with_unclosed_nested_block_comment(self, parse):
        """Test that a block comment with a nested unclosed block comment parses."""
        ast = parse("/* comment /* the same comment */")
        assert ast is not None

    def test_block_comment_with_nested_block_comment(self, parse):
        """Test that an invalid nested block comment with two close tokens fails."""
        ast = parse("/* comment /* the same comment */*/")
        assert ast is None

    def test_single_line_comment_with_include_comments(self):
        """Test single-line comments are captured with include_comments=True."""
        ast = getASTfromString("// This is a comment", include_comments=True)
        assert ast is not None
        comments = [n for n in ast if isinstance(n, CommentLine)]
        assert len(comments) >= 1

    def test_multi_line_comment_with_include_comments(self):
        """Test multi-line comments are captured with include_comments=True."""
        ast = getASTfromString("/* block comment */", include_comments=True)
        assert ast is not None
        comments = [n for n in ast if isinstance(n, CommentSpan)]
        assert len(comments) >= 1

    def test_comments_at_various_positions(self, parse):
        """Test that comments at various positions in code parse correctly."""
        # Comment before code
        assert parse("// leading comment\nx = 1;") is not None
        # Comment after code
        assert parse("x = 1; // trailing comment") is not None
        # Block comment between statements
        assert parse("x = 1; /* between */ y = 2;") is not None
        # Comment inside module body
        assert parse("module test() { // inside\n  cube(1); }") is not None
        # Comment between function arguments
        assert parse("cube(/* size */ 10);") is not None
        # Comment before closing brace
        assert parse("module test() { cube(1); // end\n}") is not None


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

    def test_scientific_positive_exponent(self, parse):
        ast = parse("x = 1e+10;")
        assert ast[0].expr.val == 1e10

    def test_hex(self, parse):
        ast = parse("x = 0xFF;")
        assert ast[0].expr.val == 255.0

    def test_hex_lowercase(self, parse):
        ast = parse("x = 0xff;")
        assert ast[0].expr.val == 255.0

    def test_leading_dot(self, parse):
        ast = parse("x = .5;")
        assert ast[0].expr.val == 0.5

    def test_negative_integer(self, parse):
        from openscad_lalr_parser import UnaryMinusOp
        ast = parse("x = -42;")
        assert isinstance(ast[0].expr, UnaryMinusOp)

    def test_positive_integer(self, parse):
        ast = parse("x = +42;")
        assert isinstance(ast[0].expr, NumberLiteral)
        assert ast[0].expr.val == 42.0

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

    def test_string_with_escapes(self, parse):
        ast = parse('x = "hello\\nworld";')
        assert isinstance(ast[0].expr, StringLiteral)

    def test_string_with_leading_spaces(self, parse):
        ast = parse('x = "  foo";')
        assert isinstance(ast[0].expr, StringLiteral)
        assert ast[0].expr.val == "  foo"

    def test_string_with_only_spaces(self, parse):
        ast = parse('x = "   ";')
        assert isinstance(ast[0].expr, StringLiteral)
        assert ast[0].expr.val == "   "

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

    def test_double_underscore(self, parse):
        ast = parse("x = __internal;")
        assert ast[0].expr.name == "__internal"

    def test_dollar_underscore(self, parse):
        ast = parse("x = $_special;")
        assert ast[0].expr.name == "$_special"

    def test_underscore_in_function_name(self, parse):
        ast = parse("function _helper(x) = x + 1;")
        assert ast[0].name.name == "_helper"

    def test_underscore_in_module_name(self, parse):
        ast = parse("module _internal() { cube(1); }")
        assert ast[0].name.name == "_internal"

    def test_simple_identifier_as_target(self, parse):
        """Test simple identifier as assignment target."""
        ast = parse("x = 1;")
        assert ast is not None
        assert isinstance(ast[0], Assignment)

    def test_identifier_with_underscore(self, parse):
        """Test identifiers with underscores in the middle."""
        ast = parse("my_var = 1;")
        assert ast is not None
        assert isinstance(ast[0], Assignment)
        assert ast[0].name.name == "my_var"

    def test_identifier_with_numbers(self, parse):
        """Test identifiers with numbers."""
        ast = parse("var1 = 1;")
        assert ast is not None
        assert isinstance(ast[0], Assignment)
        assert ast[0].name.name == "var1"

    def test_identifier_dollar_sign_as_target(self, parse):
        """Test identifiers starting with dollar sign as assignment target."""
        ast = parse("$var = 1;")
        assert ast is not None
        assert isinstance(ast[0], Assignment)
        assert ast[0].name.name == "$var"

    def test_identifier_mixed_case(self, parse):
        """Test mixed case identifiers."""
        ast = parse("myVariable = 1;")
        assert ast is not None
        assert isinstance(ast[0], Assignment)
        assert ast[0].name.name == "myVariable"

    def test_identifier_leading_underscore_as_target(self, parse):
        """Test identifiers starting with underscore as assignment target."""
        ast = parse("_private_var = 1;")
        assert ast is not None
        assert isinstance(ast[0], Assignment)
        assert ast[0].name.name == "_private_var"

    def test_identifier_leading_underscore_uppercase(self, parse):
        """Test uppercase identifiers starting with underscore."""
        ast = parse("_UNDEF = 1;")
        assert ast is not None
        assert isinstance(ast[0], Assignment)
        assert ast[0].name.name == "_UNDEF"

    def test_identifier_str(self, parse):
        ast = parse("x = foo;")
        assert str(ast[0].expr) == "foo"

    def test_identifier_repr(self, parse):
        ast = parse("x = foo;")
        assert repr(ast[0].expr) == "Identifier('foo')"
