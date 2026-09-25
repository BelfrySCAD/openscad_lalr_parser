"""Reformatting with comments must give code that parses, and the same program.

Measured on BOSL2 (92 files) before these fixes: 36 reformatted into code that
no longer parsed, 5 more into a different program."""
import pytest

from openscad_lalr_parser import CommentLine, ast_to_dict, getASTfromString
from openscad_lalr_parser.pretty_print import to_openscad


def _program(src):
    return ast_to_dict(getASTfromString(src), include_position=False)


def _reformat(src):
    out = to_openscad(getASTfromString(src, include_comments=True))
    assert getASTfromString(out) is not None, f"reformat does not parse:\n{out}"
    assert _program(out) == _program(src), f"reformat changed the program:\n{out}"
    assert to_openscad(getASTfromString(out, include_comments=True)) == out  # stable
    return out


class TestStatementTrailingComments:
    """A `//` comment ending a statement's line used to be wrapped round the
    statement's last expression and printed before the `;` -- or, with a child
    module, after the child's name (`cube // c(1);`)."""

    @pytest.mark.parametrize("src, expected", [
        ("x = 1; // c\n", "x = 1;  // c"),
        ("x = f(1); // c\n", "x = f(1);  // c"),
        ("cube(1); // c\n", "cube(1);  // c"),
        ('x = "http://a"; // c\n', 'x = "http://a";  // c'),
        ("#cube(1); // c\n", "#cube(1);  // c"),
        ("translate([1,0,0]) cube(1); // c\n", "translate([1, 0, 0])\n    cube(1);  // c"),
        ("if (a) cube(1); // c\n", "if (a)\n    cube(1);  // c"),
        ("for (i=[0:2]) cube(i); // c\n", "for (i = [0 : 2])\n    cube(i);  // c"),
        ("function f() = 1; // c\n", "function f() =\n    1;  // c"),
        ("module m() { cube(1); } // c\n", "module m() {\n    cube(1);\n}  // c"),
        ("module m() {\n  cube(1); // e\n  sphere(2);  // f\n}\n",
         "module m() {\n    cube(1);  // e\n    sphere(2);  // f\n}"),
        ("if (a) { cube(1); // t\n} else { sphere(1); // e\n}\n",
         "if (a) {\n    cube(1);  // t\n} else {\n    sphere(1);  // e\n}"),
        ("module m() { // opening\n  cube(1);\n}\n", "module m() {  // opening\n    cube(1);\n}"),
    ])
    def test_stays_at_the_end_of_its_statement(self, src, expected):
        assert _reformat(src) == expected

    def test_is_a_same_line_comment_after_the_statement(self):
        ast = getASTfromString("x = 1; // c\ny = 2;\n", include_comments=True)
        assert [type(n).__name__ for n in ast] == ["Assignment", "CommentLine", "Assignment"]
        assert ast[1].same_line and ast[1].text == " c"


class TestCommentsInsideExpressions:
    @pytest.mark.parametrize("src", [
        "translate([1, // arg\n  0, 0]) cube(1); // stmt\n",  # landed on `cube`
        "x = [0: // c\n  2];\n",
        "for (i = [0: // c\n  2]) cube(i);\n",
        "x = [0 // a\n  : 1 : // b\n  2 // e\n  ];\n",
        "x = child // why\n  ? a // one\n  : b; // two\n",
        "x = let(\n  a = 1, // one\n  b = 2) a + b;\n",
        "x = f(\n  // lead\n  a, b);\n",
    ])
    def test_reformat_is_the_same_program(self, src):
        out = _reformat(src)
        assert out.count("//") == src.count("//")  # none lost


class TestParentheses:
    """Operands that bind more loosely than their context need parentheses;
    without them `(a + b)[0]` reprinted as `a + b[0]` -- valid, and wrong."""

    @pytest.mark.parametrize("src, expected", [
        ("x = (a+b)[0];", "x = (a + b)[0];"),
        ("x = (a^b).c;", "x = (a ^ b).c;"),
        ("x = (a?b:c)[0];", "x = (a ? b : c)[0];"),
        ("x = (function(y) y)(2);", "x = (function(y) y)(2);"),
        ("x = a && (let(b=1) b);", "x = a && (let(b = 1) b);"),
        ("x = !(let(b=1) b);", "x = !(let(b = 1) b);"),
        ("x = a[0].b(1)[2];", "x = a[0].b(1)[2];"),
    ])
    def test_kept_where_needed(self, src, expected):
        assert _reformat(src) == expected

    def test_ternary_as_condition(self):
        assert _reformat("x = (a?b:c) ? d : e;").startswith("x = (a ? b : c)")


class TestDanglingElse:
    @pytest.mark.parametrize("src", [
        "if (a) { if (b) cube(); } else sphere();",
        "if (a) { for (i = [0:1]) if (b) cube(); } else sphere();",
        "if (a) { if (b) cube(); else if (c) cylinder(); } else sphere();",
    ])
    def test_inner_if_keeps_its_braces(self, src):
        assert "{" in _reformat(src)


def test_top_level_block_is_flattened():
    ast = getASTfromString("x = 1;\n{ cube(1); sphere(1); }\n", include_comments=True)
    assert [type(n).__name__ for n in ast] == ["Assignment", "ModularCall", "ModularCall"]
    assert not any(isinstance(n, list) for n in ast)
