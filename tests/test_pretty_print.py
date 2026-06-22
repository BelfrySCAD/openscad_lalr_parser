"""Tests for the OpenSCAD pretty-printer."""

import pytest
from openscad_lalr_parser import getASTfromString, to_openscad
from openscad_lalr_parser import (
    Assignment, FunctionDeclaration, ModuleDeclaration,
    ModularCall, ModularFor, ModularIf, ModularIfElse,
    ModularIntersectionFor, BlankLine,
)
from openscad_lalr_parser.pretty_print import _as_list, _coalesce_paren_bracket


def _roundtrip(code: str) -> list:
    ast = getASTfromString(code)
    formatted = to_openscad(ast)
    return getASTfromString(formatted)


def _fmt(code: str) -> str:
    return to_openscad(getASTfromString(code))


class TestAssignmentFormatting:
    def test_simple_assignment(self):
        assert _fmt("x=1;") == "x = 1;"

    def test_string_assignment(self):
        assert _fmt('label="hello";') == 'label = "hello";'

    def test_bool_assignment(self):
        assert _fmt("centered=true;") == "centered = true;"

    def test_expression_assignment(self):
        assert _fmt("v=1+2;") == "v = 1 + 2;"


class TestMultilineParamFormatting:
    SHORT_FN = "function f(a, b) = a + b;"
    LONG_FN = "function long_function_name(very_long_param_alpha, very_long_param_beta, very_long_param_gamma, extra) = a;"
    SHORT_MOD = "module m(a, b) { cube(a); }"
    LONG_MOD = "module long_module_name(very_long_param_alpha, very_long_param_beta, very_long_param_gamma, extra_x=0) { cube(a); }"

    def test_short_function_params_inline(self):
        out = _fmt(self.SHORT_FN)
        assert out.startswith("function f(a, b) =")

    def test_long_function_params_multiline(self):
        out = _fmt(self.LONG_FN)
        assert out.startswith("function long_function_name(\n")
        assert ") =\n" in out

    def test_short_module_params_inline(self):
        out = _fmt(self.SHORT_MOD)
        assert out.startswith("module m(a, b)")

    def test_long_module_params_multiline(self):
        out = _fmt(self.LONG_MOD)
        assert out.startswith("module long_module_name(\n")
        assert ") {\n" in out

    def test_long_function_params_roundtrip(self):
        assert len(_roundtrip(self.LONG_FN)) == 1

    def test_long_module_params_roundtrip(self):
        assert len(_roundtrip(self.LONG_MOD)) == 1


class TestFunctionFormatting:
    def test_simple_function(self):
        out = _fmt("function f(x)=x*2;")
        assert out == "function f(x) =\n    x * 2;"

    def test_function_with_default(self):
        out = _fmt("function f(x=1,y=2)=x+y;")
        assert "x=1" in out
        assert "y=2" in out

    def test_function_undef_default_omitted(self):
        out = _fmt("function f(a=undef, b=3) = a + b;")
        assert "a," in out
        assert "undef" not in out
        assert "b=3" in out

    def test_function_roundtrip(self):
        code = "function area(w, h) = w * h;"
        ast2 = _roundtrip(code)
        assert len(ast2) == 1
        assert isinstance(ast2[0], FunctionDeclaration)
        assert ast2[0].name.name == "area"


class TestModuleFormatting:
    def test_empty_module(self):
        out = _fmt("module m(){}")
        assert "module m()" in out
        assert "{}" in out

    def test_module_with_body(self):
        out = _fmt("module box(w,h){cube([w,h,1]);}")
        assert "module box(w, h)" in out
        assert "cube(" in out

    def test_module_indentation(self):
        out = _fmt("module m(){cube(1);sphere(2);}")
        lines = out.split("\n")
        body_lines = [l for l in lines if "cube" in l or "sphere" in l]
        assert all(l.startswith("    ") for l in body_lines)

    def test_module_roundtrip(self):
        code = "module box(w=10, h=5) { cube([w, h, 1]); }"
        ast2 = _roundtrip(code)
        assert len(ast2) == 1
        assert isinstance(ast2[0], ModuleDeclaration)
        assert ast2[0].name.name == "box"
        assert len(ast2[0].parameters) == 2


class TestModuleCallFormatting:
    def test_leaf_call(self):
        assert _fmt("cube(10);") == "cube(10);"

    def test_call_with_named_args(self):
        out = _fmt("cube(size=10,center=true);")
        assert "size=10" in out
        assert "center=true" in out

    def test_single_child_inline(self):
        out = _fmt("translate([1,2,3]) cube(10);")
        assert "translate(" in out
        assert "cube(10);" in out

    def test_multiple_children_block(self):
        out = _fmt("union() { cube(1); sphere(2); }")
        assert "union()" in out
        assert " {\n" in out
        assert "cube(1);" in out
        assert "sphere(2);" in out

    def test_roundtrip_nested_calls(self):
        code = "translate([1, 0, 0]) rotate([0, 0, 45]) cube(5);"
        ast2 = _roundtrip(code)
        assert len(ast2) == 1


class TestFormatting:
    def test_for_loop(self):
        out = _fmt("for(i=[0:5]) cube(i);")
        assert out.startswith("for (")
        assert "cube(" in out

    def test_for_loop_block(self):
        out = _fmt("for(i=[0:5]){cube(i);sphere(i);}")
        assert "for (" in out
        assert " {\n" in out

    def test_for_roundtrip(self):
        code = "for (i = [0:3]) cube(i);"
        ast2 = _roundtrip(code)
        assert isinstance(ast2[0], ModularFor)


class TestIfFormatting:
    def test_if_simple(self):
        out = _fmt("if(true) cube(1);")
        assert out.startswith("if (")
        assert "cube(1);" in out

    def test_if_else_inline(self):
        out = _fmt("if(x>0) cube(1); else sphere(2);")
        assert "if (" in out
        assert "else" in out

    def test_if_else_block(self):
        out = _fmt("if(x>0){cube(1);sphere(2);}else{cylinder(3);}")
        assert "if (" in out
        assert "else" in out

    def test_if_roundtrip(self):
        code = "if (true) cube(1); else sphere(2);"
        ast2 = _roundtrip(code)
        assert isinstance(ast2[0], ModularIfElse)


class TestModifierFormatting:
    def test_show_only(self):
        assert "!cube(1);" in _fmt("!cube(1);")

    def test_highlight(self):
        assert "#cube(1);" in _fmt("#cube(1);")

    def test_background(self):
        assert "%cube(1);" in _fmt("%cube(1);")

    def test_disable(self):
        assert "*cube(1);" in _fmt("*cube(1);")

    def test_nested_modifiers(self):
        out = _fmt("!#cube(1);")
        assert "!" in out and "#" in out and "cube" in out


class TestUseIncludeFormatting:
    def test_use(self):
        assert _fmt("use <lib.scad>") == "use <lib.scad>"

    def test_include(self):
        assert _fmt("include <lib/utils.scad>") == "include <lib/utils.scad>"


class TestCommentFormatting:
    def test_line_comment(self):
        ast = getASTfromString("// hello\nx=1;", include_comments=True)
        out = to_openscad(ast)
        assert "// hello" in out
        assert "x = 1;" in out

    def test_block_comment(self):
        ast = getASTfromString("/* block */\nx=1;", include_comments=True)
        out = to_openscad(ast)
        assert "/* block */" in out


class TestBlankLineSeparation:
    def test_no_blank_line_before_function(self):
        assert "\n\n" not in _fmt("x=1;\nfunction f(x)=x;")

    def test_no_blank_line_before_module(self):
        assert "\n\n" not in _fmt("x=1;\nmodule m(){}")

    def test_blank_line_between_modules(self):
        assert "\n\n" in _fmt("module a(){}\nmodule b(){}")

    def test_no_blank_line_between_assignments(self):
        assert "\n\n" not in _fmt("x=1;\ny=2;")


class TestBlankLineCommentPreservation:
    def _fmt(self, src):
        ast = getASTfromString(src, include_comments=True)
        return to_openscad(ast)

    def test_blank_line_between_toplevel_comment_blocks(self):
        src = "// block 1\n// block 1 cont\n\n// block 2\n// block 2 cont\nx=1;"
        out = self._fmt(src)
        assert "// block 1\n// block 1 cont\n\n// block 2" in out

    def test_no_blank_line_between_adjacent_comment_lines(self):
        src = "// line 1\n// line 2\nx=1;"
        out = self._fmt(src)
        assert "// line 1\n// line 2" in out
        assert "// line 1\n\n// line 2" not in out

    def test_multiple_blank_lines_collapsed_to_one(self):
        # Two blank lines in source -> blank lines preserved in output
        # (LALR parser preserves each BlankLine node from the source)
        src = "// block 1\n\n\n// block 2\nx=1;"
        out = self._fmt(src)
        # At minimum, a blank line separator exists between the two comment blocks
        assert "// block 1\n\n" in out
        assert "// block 2" in out

    def test_blank_line_inside_module_body(self):
        src = "module m() {\n    // group 1\n\n    // group 2\n    cube(1);\n}"
        out = self._fmt(src)
        assert "// group 1" in out
        assert "// group 2" in out

    def test_no_blank_line_leaks_into_module_header(self):
        src = "module m() {\n    // inside\n    cube(1);\n}"
        out = self._fmt(src)
        assert "// inside" in out
        assert "module m() // inside" not in out

    def test_blank_line_not_inserted_without_include_comments(self):
        src = "// block 1\n\n// block 2\nx=1;"
        ast = getASTfromString(src, include_comments=False)
        assert not any(isinstance(n, BlankLine) for n in ast)


class TestIndentWidth:
    def test_custom_indent(self):
        ast = getASTfromString("module m(){cube(1);}")
        out = to_openscad(ast, indent_width=2)
        assert "  cube(1);" in out

    def test_zero_indent(self):
        ast = getASTfromString("module m(){cube(1);}")
        out = to_openscad(ast, indent_width=0)
        assert "cube(1);" in out


class TestRoundTrip:
    def test_complex_model(self):
        code = """
module shelf(width=60, depth=30, thickness=3) {
    cube([width, depth, thickness]);
    translate([0, 0, thickness])
        cube([thickness, depth, 40]);
}

function vol(w, d, t) = w * d * t;

shelf(width=80);
"""
        ast1 = getASTfromString(code.strip())
        formatted = to_openscad(ast1)
        ast2 = getASTfromString(formatted)

        assert len(ast1) == len(ast2)
        for n1, n2 in zip(ast1, ast2):
            assert type(n1) is type(n2)

    def test_for_with_if(self):
        code = "for (i = [0:10]) if (i % 2 == 0) cube(i);"
        ast2 = _roundtrip(code)
        assert isinstance(ast2[0], ModularFor)

    def test_nested_modules(self):
        code = """
module outer(n) {
    for (i = [0:n]) {
        translate([i, 0, 0]) sphere(1);
    }
}
"""
        ast2 = _roundtrip(code.strip())
        assert isinstance(ast2[0], ModuleDeclaration)
        assert ast2[0].name.name == "outer"


class TestIntersectionForFormatting:
    def test_intersection_for(self):
        out = _fmt("intersection_for(i=[0:3]) cube(i);")
        assert "intersection_for (" in out
        assert "cube(" in out

    def test_intersection_for_block(self):
        out = _fmt("intersection_for(i=[0:3]){cube(i);sphere(i);}")
        assert "intersection_for (" in out
        assert " {\n" in out

    def test_intersection_for_roundtrip(self):
        code = "intersection_for (i = [0:3]) cube(i);"
        ast2 = _roundtrip(code)
        assert isinstance(ast2[0], ModularIntersectionFor)


class TestLetEchoAssertFormatting:
    def test_let_statement(self):
        out = _fmt("let(x=1) cube(x);")
        assert "let (x = 1)" in out
        assert "cube(x);" in out

    def test_let_block(self):
        out = _fmt("let(x=1){cube(x);sphere(x);}")
        assert "let (" in out
        assert " {\n" in out

    def test_echo_statement(self):
        out = _fmt('echo("hello") cube(1);')
        assert 'echo("hello")' in out

    def test_echo_no_child(self):
        out = _fmt('echo("debug");')
        assert 'echo("debug")' in out

    def test_assert_statement(self):
        out = _fmt("assert(true) cube(1);")
        assert "assert(true)" in out

    def test_assert_no_child(self):
        out = _fmt("assert(x > 0);")
        assert "assert(x > 0)" in out


class TestListCompForFormatting:
    def test_short_for_expands(self):
        out = _fmt("x = [for (i = [0:3]) i];")
        assert out == "x = [\n        for (i = [0 : 1 : 3])\n            i\n    ];"

    def test_long_for_body_on_new_line(self):
        out = _fmt("x = [for (long_variable_name = [start_value:step_value:end_value]) long_variable_name * scaling_factor_x];")
        assert "for (long_variable_name = [start_value : step_value : end_value])\n" in out
        assert "            long_variable_name * scaling_factor_x\n" in out

    def test_long_for_assignments_multiline(self):
        out = _fmt("x = [for (very_long_variable_name_alpha = [start_value:end_value], very_long_variable_name_beta = [0:10]) very_long_variable_name_alpha];")
        assert "for (\n" in out
        assert "            very_long_variable_name_alpha = [start_value : 1 : end_value]," in out
        assert ")\n" in out

    def test_nested_for(self):
        out = _fmt("x = [for (long_var_name_i = [start:end]) for (long_var_name_j = [start:end]) long_var_name_i + long_var_name_j];")
        lines = out.split("\n")
        for_i = next(l for l in lines if "long_var_name_i" in l and "for" in l)
        for_j = next(l for l in lines if "long_var_name_j" in l and "for" in l)
        assert for_j.startswith("            for")  # indented one level inside for_i
        assert len(for_j) > len(for_i)

    def test_cfor_body_on_new_line(self):
        out = _fmt("x = [for (i = 0; i < very_long_condition_limit_value_maximum_xx; i = i + step_increment_value) i * scale];")
        assert "for" in out
        assert "i = 0;" in out
        assert ")\n" in out

    def test_for_roundtrip(self):
        code = "x = [for (long_variable_name = [start_value:step_value:end_value]) long_variable_name * scaling_factor_x];"
        assert len(_roundtrip(code)) == 1


class TestListComprehensionFormatting:
    SHORT = "x = [1, 2, 3];"
    LONG_LITERAL = "x = [very_long_element_name_a, very_long_element_name_b, very_long_element_name_c, very_long_element_name_d];"
    LONG_COMP = "x = [for (long_variable_name = [start_value:step_value:end_value]) long_variable_name * scaling_factor_x];"

    def test_short_list_stays_inline(self):
        assert _fmt(self.SHORT) == "x = [1, 2, 3];"

    def test_long_literal_list_multiline(self):
        out = _fmt(self.LONG_LITERAL)
        assert out.startswith("x = [\n")
        assert out.endswith("\n    ];")
        assert "        very_long_element_name_a," in out

    def test_long_comprehension_multiline(self):
        out = _fmt(self.LONG_COMP)
        assert out.startswith("x = [\n")
        assert out.endswith("\n    ];")

    def test_long_list_roundtrip(self):
        assert len(_roundtrip(self.LONG_LITERAL)) == 1

    def test_long_comp_roundtrip(self):
        assert len(_roundtrip(self.LONG_COMP)) == 1


class TestMultilineArgFormatting:
    SHORT = "foo(short_a, short_b, short_c);"
    OVER = "foo(long_arg_a, long_arg_b, long_arg_c, long_arg_d, long_arg_e, long_arg_f, long_arg_g, long_arg_h, long_arg_i);"

    def test_short_call_stays_inline(self):
        assert _fmt(self.SHORT) == self.SHORT

    def test_just_over_limit_goes_multiline(self):
        out = _fmt(self.OVER)
        assert out.startswith("foo(\n")
        assert out.endswith(");")

    def test_long_call_single_child(self):
        src = self.OVER[:-1] + " cube(1);"
        out = _fmt(src)
        assert out.startswith("foo(\n")
        assert out.endswith(")\n    cube(1);")

    def test_long_call_multiple_children(self):
        src = self.OVER[:-1] + " { cube(1); sphere(2); }"
        out = _fmt(src)
        assert out.startswith("foo(\n")
        assert ") {\n" in out

    def test_long_expression_call(self):
        out = _fmt("x = " + self.OVER)
        assert "foo(\n" in out
        assert out.endswith(");")

    def test_indented_long_call(self):
        out = _fmt("module m() { " + self.OVER + " }")
        assert "foo(\n" in out
        assert ");" in out

    def test_long_call_roundtrip(self):
        assert len(_roundtrip(self.OVER)) == 1


class TestLetExprFormatting:
    def test_let_no_assignments(self):
        out = _fmt("function f() = let() 0;")
        assert out == "function f() =\n    let()\n    0;"

    def test_let_single_assignment(self):
        out = _fmt("function f(x) = let(y = x * 2) y + 1;")
        assert out == "function f(x) =\n    let(y = x * 2)\n    y + 1;"

    def test_let_multi_assignment(self):
        out = _fmt("function f(a, b) = let(x = a * 2, y = b + 1) x + y;")
        assert out == (
            "function f(a, b) =\n"
            "    let(\n"
            "        x = a * 2,\n"
            "        y = b + 1\n"
            "    )\n"
            "    x + y;"
        )

    def test_let_roundtrip(self):
        code = "function f(a, b) = let(x = a * 2, y = b + 1) x + y;"
        assert len(_roundtrip(code)) == 1


class TestAssertEchoExprFormatting:
    def test_assert_expr(self):
        out = _fmt("function f(x) = assert(x > 0) x * 2;")
        assert out == "function f(x) =\n    assert(x > 0)\n    x * 2;"

    def test_echo_expr(self):
        out = _fmt('function f(x) = echo("x=", x) x * 2;')
        assert out == 'function f(x) =\n    echo("x=", x)\n    x * 2;'

    def test_chained_assert_echo(self):
        out = _fmt('function f(x) = assert(x > 0) echo("x=", x) x * 2;')
        assert out == 'function f(x) =\n    assert(x > 0)\n    echo("x=", x)\n    x * 2;'

    def test_assert_with_ternary_body(self):
        out = _fmt("function f(x) = assert(x > 0) x > 5 ? x : 0;")
        assert "assert(x > 0)" in out
        assert "? x" in out
        assert ": 0;" in out

    def test_assert_roundtrip(self):
        code = "function f(x) = assert(x > 0) x * 2;"
        assert len(_roundtrip(code)) == 1

    def test_assert_no_body(self):
        out = _fmt("x = a ? 1 : assert(ok);")
        assert "assert(ok);" in out
        assert "undef" not in out

    def test_echo_no_body(self):
        out = _fmt('x = a ? 1 : echo("hi");')
        assert 'echo("hi");' in out
        assert "undef" not in out

    def test_assert_no_body_in_ternary_false_branch(self):
        # Regression: assert without body in ternary false branch must not be dropped
        out = _fmt('x = a == "X" ? 1 : assert(in_list(a, ["X", "Y"]));')
        assert "assert(in_list(a," in out
        assert "undef" not in out


class TestTernaryFormatting:
    def test_assignment_ternary(self):
        out = _fmt("x = condition ? a : b;")
        assert out == "x = condition\n    ? a\n    : b;"

    def test_function_ternary(self):
        out = _fmt("function f(x) = x > 0 ? x : -x;")
        assert out == "function f(x) =\n    x > 0\n        ? x\n        : -x;"

    def test_nested_ternary(self):
        out = _fmt("x = a ? b : c ? d : e;")
        assert "a ?\n" in out
        assert ": c ?\n" in out
        assert ": e;" in out

    def test_indented_ternary(self):
        out = _fmt("module m() { x = a ? b : c; }")
        lines = out.split("\n")
        q_line = next(l for l in lines if "?" in l)
        assert q_line.startswith("        ? ")

    def test_ternary_roundtrip(self):
        code = "x = condition ? true_val : false_val;"
        ast2 = _roundtrip(code)
        assert len(ast2) == 1
        assert isinstance(ast2[0], Assignment)

    def test_ternary_false_branch_let_block_indent(self):
        src = "function f(u) = is_num(u) ? g(u)[0] : let(d1 = h(u, 1), d2 = h(u, 2)) d1 + d2;"
        out = _fmt(src)
        lines = out.split("\n")
        # ": let(" should appear in the output
        colon_line = next(l for l in lines if l.lstrip().startswith(": let("))
        let_col = colon_line.index("let(")
        # assignment lines should be indented past let(
        assign_line = next(l for l in lines if "d1 = " in l)
        assert assign_line.startswith(" " * (let_col + 4))
        # closing ) should align with let(
        close_line = next(l for l in lines if l.strip() == ")")
        assert close_line == " " * let_col + ")"

    def test_ternary_branch_list_comp_indent(self):
        src = "function f(u) = is_vector(u) ? unit(u) : [for (v = u) unit(v)];"
        out = _fmt(src)
        lines = out.split("\n")
        # ": [" -- find column of "["
        colon_line = next(l for l in lines if l.lstrip().startswith(": ["))
        bracket_col = colon_line.index("[")
        # for loop should be indented past "["
        for_line = next(l for l in lines if "for (" in l)
        assert for_line.startswith(" " * (bracket_col + 4))
        # closing ] should align with "["
        close_line = next(l for l in lines if l.strip() == "];")
        assert close_line == " " * bracket_col + "];"


class TestOperatorPrecedenceParens:
    def test_addition_inside_division(self):
        assert _fmt("x = (3+5)/2;") == "x = (3 + 5) / 2;"

    def test_subtraction_inside_multiplication(self):
        assert _fmt("x = (a-b)*c;") == "x = (a - b) * c;"

    def test_left_assoc_sub_no_extra_parens(self):
        assert _fmt("x = a - b - c;") == "x = a - b - c;"

    def test_right_sub_needs_parens(self):
        assert _fmt("x = a - (b - c);") == "x = a - (b - c);"

    def test_mul_inside_add_no_parens(self):
        assert _fmt("x = a + b * c;") == "x = a + b * c;"

    def test_unary_minus_on_binary_expr(self):
        assert _fmt("x = -(a+b);") == "x = -(a + b);"

    def test_logical_not_on_comparison(self):
        assert _fmt("x = !(a == b);") == "x = !(a == b);"

    def test_logical_and_inside_or(self):
        assert _fmt("x = (a || b) && c;") == "x = (a || b) && c;"

    def test_or_inside_and_no_parens(self):
        assert _fmt("x = a && b || c;") == "x = a && b || c;"

    def test_comparison_inside_logical(self):
        assert _fmt("x = a > 0 && b < 10;") == "x = a > 0 && b < 10;"

    def test_exponent_right_assoc(self):
        assert _fmt("x = a ^ b ^ c;") == "x = a ^ b ^ c;"

    def test_exponent_left_needs_parens(self):
        assert _fmt("x = (a ^ b) ^ c;") == "x = (a ^ b) ^ c;"

    def test_or_inside_bitwise_and_needs_parens(self):
        assert _fmt("x = (a | b) & c;") == "x = (a | b) & c;"

    def test_bitwise_not(self):
        assert _fmt("x = ~(a + b);") == "x = ~(a + b);"

    def test_equality_redundant_parens_in_and(self):
        assert _fmt("x = (a == b) && c;") == "x = a == b && c;"

    def test_modulo_inside_addition(self):
        assert _fmt("x = a + b % c;") == "x = a + b % c;"

    def test_modulo_with_explicit_parens(self):
        assert _fmt("x = (a + b) % c;") == "x = (a + b) % c;"

    def test_roundtrip_preserves_semantics(self):
        code = "x = (3+5)/2;"
        ast2 = _roundtrip(code)
        assert len(ast2) == 1
        assert isinstance(ast2[0], Assignment)


class TestAsListHelper:
    def test_list_passthrough(self):
        lst = [1, 2, 3]
        assert _as_list(lst) is lst

    def test_none_returns_empty(self):
        assert _as_list(None) == []

    def test_single_value_wraps(self):
        assert _as_list("x") == ["x"]
        assert _as_list(42) == [42]


class TestCoalesceParenBracket:
    def test_bare_paren_bracket_joined(self):
        assert _coalesce_paren_bracket("    )\n    [") == "    ) ["

    def test_bracket_content_preserved(self):
        assert _coalesce_paren_bracket("    )\n    [1, 2, 3]") == "    ) [1, 2, 3]"

    def test_indentation_from_paren_line(self):
        assert _coalesce_paren_bracket("        )\n            [x, y]") == "        ) [x, y]"

    def test_no_coalesce_when_paren_has_trailing_content(self):
        inp = "    ) {\n    ["
        assert _coalesce_paren_bracket(inp) == "    ) {\n    ["

    def test_no_coalesce_when_bracket_preceded_by_non_paren(self):
        inp = "    x = 1\n    [1, 2]"
        assert _coalesce_paren_bracket(inp) == "    x = 1\n    [1, 2]"

    def test_multiple_occurrences(self):
        assert _coalesce_paren_bracket(")\n[\n)\n[") == ") [\n) ["

    def test_let_block_with_vector_body(self):
        out = _fmt("x = let(a = 1, b = 2) [a, b];")
        assert ") [a, b];" in out

    def test_let_block_with_list_comp_body(self):
        out = _fmt("x = let(a = 1, b = 2) [for (i = [0:5]) i + a];")
        assert ") [\n" in out
        lines = out.split("\n")
        for i in range(len(lines) - 1):
            assert not (lines[i].strip() == ")" and lines[i + 1].lstrip().startswith("["))


# --- CommentedExpr / inline block comment tests ---

def _fmt_with_comments(code: str) -> str:
    """Parse with include_comments=True -> pretty-print."""
    return to_openscad(getASTfromString(code, include_comments=True))


class TestInlineBlockComments:
    """Tests for /* */ comments inside expressions (CommentedExpr support)."""

    def test_positional_argument(self):
        out = _fmt_with_comments("x = foo(/* hi */ a, b);")
        assert "/* hi */" in out
        assert "foo(" in out

    def test_named_argument_value(self):
        out = _fmt_with_comments("foo(x = /* val */ 1);")
        assert "/* val */" in out

    def test_vector_element_first(self):
        out = _fmt_with_comments("v = [/* y */ 1, 2, 3];")
        assert "/* y */" in out

    def test_vector_element_middle(self):
        out = _fmt_with_comments("v = [1, /* y */ 2, 3];")
        assert "/* y */" in out

    def test_ternary_true_arm(self):
        out = _fmt_with_comments("x = c ? /* yes */ a : b;")
        assert "/* yes */" in out

    def test_ternary_false_arm(self):
        out = _fmt_with_comments("x = c ? a : /* no */ b;")
        assert "/* no */" in out

    def test_binary_op_comment_does_not_crash(self):
        out = _fmt_with_comments("x = a + /* scale */ b;")
        assert "/* scale */" in out
        assert "a" in out and "b" in out

    def test_without_include_comments_no_commentedexpr(self):
        from openscad_lalr_parser.nodes import CommentedExpr
        nodes = getASTfromString("x = foo(/* hi */ a, b);", include_comments=False)
        def _has_commented_expr(node):
            if isinstance(node, CommentedExpr):
                return True
            for attr in vars(node).values():
                if isinstance(attr, list):
                    for item in attr:
                        if hasattr(item, '__dataclass_fields__') and _has_commented_expr(item):
                            return True
                elif hasattr(attr, '__dataclass_fields__') and _has_commented_expr(attr):
                    return True
            return False
        assert not _has_commented_expr(nodes[0])

    def test_let_expr_body_with_comment(self):
        out = _fmt_with_comments("x = let(a = 1) /* note */ a + 1;")
        assert "/* note */" in out

    def test_parameter_default_with_comment(self):
        out = _fmt_with_comments("function f(x = /* def */ 1) = x;")
        assert "/* def */" in out

    # --- Trailing comments ---

    def test_trailing_after_arg(self):
        out = _fmt_with_comments("x = foo(a /* after */, b);")
        assert "/* after */" in out

    def test_trailing_after_last_arg(self):
        out = _fmt_with_comments("x = foo(a, b /* after */);")
        assert "/* after */" in out

    def test_trailing_after_vector_element(self):
        out = _fmt_with_comments("v = [1 /* after */, 2, 3];")
        assert "/* after */" in out

    def test_trailing_after_last_vector_element(self):
        out = _fmt_with_comments("v = [1, 2, 3 /* after */];")
        assert "/* after */" in out

    def test_trailing_after_whole_vector_arg(self):
        out = _fmt_with_comments("translate([0, 1, 2] /* after */) cube(1);")
        assert "/* after */" in out

    def test_trailing_after_assignment_rhs(self):
        out = _fmt_with_comments("x = 1 /* note */;")
        assert "/* note */" in out

    def test_leading_and_trailing(self):
        out = _fmt_with_comments("x = foo(/* before */ a /* after */, b);")
        assert "/* before */" in out
        assert "/* after */" in out

    def test_trailing_after_function_body(self):
        out = _fmt_with_comments("function f(x) = x + 1 /* end */;")
        assert "/* end */" in out

    def test_between_operand_and_operator_does_not_crash(self):
        out = _fmt_with_comments("x = 3 /* str */ + 4;")
        assert "/* str */" in out
        assert "3" in out and "4" in out
