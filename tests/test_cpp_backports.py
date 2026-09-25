"""Fixes backported from openscad_cpp_parser, the C++ port of this parser."""
import os
import platform

import pytest

from openscad_lalr_parser import (
    RangeLiteral, RenderExpression, ModularCall, ast_from_json, ast_to_json, build_scopes,
    findLibraryFile, getASTfromLibraryFile, getASTfromString, librarySearchDirs,
)
from openscad_lalr_parser.pretty_print import to_openscad


def _roundtrip(src: str) -> str:
    """Pretty-print with comments, and check the result re-parses to itself."""
    out = to_openscad(getASTfromString(src, include_comments=True))
    again = getASTfromString(out, include_comments=True)
    assert again is not None, f"printed source does not parse:\n{out}"
    assert to_openscad(again) == out
    return out


class TestLineCommentsInArgumentLists:
    """A `//` comment after an argument attaches to the next one, and used to
    be printed inline -- commenting out the rest of the call."""

    @pytest.mark.parametrize("src, expected", [
        ("foo(a // one\n, b // two\n, c);\n", "foo(\n    a,  // one\n    b,  // two\n    c\n);"),
        ("x = f(a, // one\n  b);\n", "x = f(\n    a,  // one\n    b\n);"),
        ("echo(a, // one\n  b);\n", "echo(\n    a,  // one\n    b\n);"),
        ("x = echo(a, // one\n  b) 1;\n", "x = echo(\n    a,  // one\n    b\n)\n1;"),
        ("function f(a, // one\n  b) = a;\n", "function f(\n    a,  // one\n    b\n) =\n    a;"),
        ("module m(a, // one\n  b) {}\n", "module m(\n    a,  // one\n    b\n) {}"),
        ("foo(a, b=1, // one\n  c=2);\n", "foo(\n    a,\n    b=1,  // one\n    c=2\n);"),
    ])
    def test_comment_stays_after_its_comma(self, src, expected):
        assert _roundtrip(src) == expected

    def test_string_with_slashes_stays_inline(self):
        assert _roundtrip('foo("http://x", b);\n') == 'foo("http://x", b);'


class TestBackslashNewlineInString:
    def test_parses_and_is_kept_verbatim(self):
        ast = getASTfromString('x = "a\\\nb";\n')
        assert ast[0].expr.val == "a\\\nb"  # the evaluator resolves escapes
        assert _roundtrip('x = "a\\\nb";\n') == 'x = "a\\\nb";'

    def test_slashes_after_it_are_not_a_comment(self):
        ast = getASTfromString('x = "a\\\n// not a comment\nb";\ny = 2;\n', include_comments=True)
        assert [type(n).__name__ for n in ast] == ["Assignment", "Assignment"]


class TestLibrarySearch:
    @pytest.fixture
    def home(self, tmp_path, monkeypatch):
        monkeypatch.setattr(platform, "system", lambda: "Darwin")
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.delenv("OPENSCADPATH", raising=False)
        default = tmp_path / "Documents" / "OpenSCAD" / "libraries"
        default.mkdir(parents=True)
        return tmp_path

    def test_openscadpath_comes_first_and_keeps_the_default(self, home, monkeypatch):
        env_dir = home / "extra"
        env_dir.mkdir()
        monkeypatch.setenv("OPENSCADPATH", str(env_dir))
        default = home / "Documents" / "OpenSCAD" / "libraries"
        (default / "BOSL2.scad").write_text("x = 1;")
        (env_dir / "mine.scad").write_text("x = 1;")
        (default / "both.scad").write_text("x = 1;")
        (env_dir / "both.scad").write_text("x = 2;")
        main = home / "main.scad"
        assert librarySearchDirs(str(main)) == [str(home), str(env_dir), str(default)]
        assert findLibraryFile(str(main), "BOSL2.scad") == str(default / "BOSL2.scad")  # was hidden
        assert findLibraryFile(str(main), "both.scad") == str(env_dir / "both.scad")

    def test_windows_asks_for_documents(self, monkeypatch):
        import openscad_lalr_parser as p
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        monkeypatch.setattr(p, "_windows_documents_dir", lambda: "D:\\OneDrive\\Documents")
        monkeypatch.delenv("OPENSCADPATH", raising=False)
        assert librarySearchDirs("") == [os.path.join("D:\\OneDrive\\Documents", "OpenSCAD", "libraries")]

    def test_not_found_lists_every_directory(self, home):
        main = home / "main.scad"
        main.write_text("")
        with pytest.raises(FileNotFoundError) as e:
            getASTfromLibraryFile(str(main), "nope.scad")
        assert str(e.value) == ("Library file 'nope.scad' not found. Searched:\n"
                                f"  {home}\n  {home / 'Documents' / 'OpenSCAD' / 'libraries'}")


class TestRangeStepWritten:
    def test_flag_and_printing(self):
        implicit = getASTfromString("x = [5:0];")[0].expr
        explicit = getASTfromString("x = [5:1:0];")[0].expr
        assert isinstance(implicit, RangeLiteral)
        assert implicit.implicit_step and not explicit.implicit_step
        assert implicit.step.val == 1.0  # still there for anyone who just wants the value
        assert str(implicit) == "[5 : 0]" and str(explicit) == "[5 : 1 : 0]"

    def test_survives_serialization(self):
        ast = ast_from_json(ast_to_json(getASTfromString("x = [5:0];")))
        assert ast[0].expr.implicit_step


class TestRenderExpression:
    def test_expression_form(self):
        ast = getASTfromString("obj = render() { x = 2; cube(x); };")
        expr = ast[0].expr
        assert isinstance(expr, RenderExpression) and len(expr.children) == 2
        build_scopes(ast)
        assert expr.children[1].arguments[0].expr.scope.lookup_variable("x") is not None

    def test_statement_form_is_still_a_modular_call(self):
        (node,) = getASTfromString("render(convexity=2) cube(1);")
        assert isinstance(node, ModularCall) and node.name.name == "render"

    @pytest.mark.parametrize("src", [
        "obj = render() { cube(1); };",
        "v = render() { cube(1); }.volume;",
        "e = render() {};",
    ])
    def test_round_trips(self, src):
        _roundtrip(src)
        _roundtrip(f"x = {getASTfromString(src)[0].expr};")  # str() re-parses too
        assert to_openscad(ast_from_json(ast_to_json(getASTfromString(src)))) == to_openscad(getASTfromString(src))

    @pytest.mark.parametrize("src", [
        "obj = render() cube(1);",  # unbraced: the child swallows the `;`
        "render = 3;",
        "f(render=1);",
    ])
    def test_rejected(self, src):
        assert getASTfromString(src) is None

    @pytest.mark.parametrize("src", ["$render = 1;", "x = a.render;", "module render() {}", "renderx = 1;"])
    def test_still_a_name_where_no_keyword_fits(self, src):
        assert getASTfromString(src) is not None
