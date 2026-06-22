"""Tests for module definitions, calls, and modifiers."""
from openscad_lalr_parser import (
    getASTfromString,
    ModuleDeclaration,
    ModularCall,
    ModularFor,
    ModularIf,
    ModularIfElse,
    ModularModifierShowOnly,
    ModularModifierHighlight,
    ModularModifierBackground,
    ModularModifierDisable,
    PositionalArgument,
    NamedArgument,
    Assignment,
    Identifier,
)


class TestModuleDeclaration:
    def test_simple_module(self, parse):
        ast = parse("module foo() { cube(1); }")
        assert isinstance(ast[0], ModuleDeclaration)
        assert ast[0].name.name == "foo"
        assert len(ast[0].parameters) == 0
        assert len(ast[0].children) == 1

    def test_module_with_params(self, parse):
        ast = parse("module box(size, center=true) { cube(size, center=center); }")
        decl = ast[0]
        assert isinstance(decl, ModuleDeclaration)
        assert len(decl.parameters) == 2
        assert decl.parameters[0].name.name == "size"
        assert decl.parameters[1].name.name == "center"
        assert decl.parameters[1].default is not None

    def test_module_empty_body(self, parse):
        ast = parse("module empty() { }")
        assert isinstance(ast[0], ModuleDeclaration)
        assert len(ast[0].children) == 0

    def test_module_single_statement_body(self, parse):
        ast = parse("module foo() cube(1);")
        assert isinstance(ast[0], ModuleDeclaration)

    def test_module_str(self, parse):
        ast = parse("module foo(x) { cube(x); }")
        assert "module" in str(ast[0])
        assert "foo" in str(ast[0])

    def test_module_multiple_parameters_trailing_comma(self, parse):
        """Test parameters with trailing comma."""
        ast = parse("module test(x, y,) {}")
        assert ast is not None
        assert isinstance(ast[0], ModuleDeclaration)
        assert len(ast[0].parameters) == 2

    def test_module_named_parameters(self, parse):
        """Test module with named (default value) parameters."""
        ast = parse("module test(x=1, y=2) {}")
        assert ast is not None
        decl = ast[0]
        assert isinstance(decl, ModuleDeclaration)
        assert len(decl.parameters) == 2
        assert decl.parameters[0].default is not None
        assert decl.parameters[1].default is not None

    def test_module_with_body(self, parse):
        """Test module with body statements."""
        ast = parse("module test() { cube(10); }")
        assert ast is not None
        decl = ast[0]
        assert isinstance(decl, ModuleDeclaration)
        assert len(decl.children) == 1

    def test_module_multiple_statements(self, parse):
        """Test module with multiple statements."""
        ast = parse("module test() { cube(10); sphere(5); }")
        assert ast is not None
        decl = ast[0]
        assert isinstance(decl, ModuleDeclaration)
        assert len(decl.children) == 2

    def test_module_mixed_statements(self, parse):
        """Test module with mixed statements (assignments and calls)."""
        ast = parse("module test(a, b=2) { s = 3 * a + b; cube(s); }")
        assert ast is not None
        decl = ast[0]
        assert isinstance(decl, ModuleDeclaration)
        assert len(decl.children) == 2
        assert isinstance(decl.children[0], Assignment)
        assert isinstance(decl.children[1], ModularCall)

    def test_module_nested(self, parse):
        """Test nested module definitions."""
        ast = parse("module outer() { module inner() {} }")
        assert ast is not None
        outer = ast[0]
        assert isinstance(outer, ModuleDeclaration)
        assert outer.name.name == "outer"
        assert len(outer.children) == 1
        inner = outer.children[0]
        assert isinstance(inner, ModuleDeclaration)
        assert inner.name.name == "inner"

    def test_module_with_comment(self, parse):
        """Test module defined with comments."""
        code = "module test() {\nsphere(5);\n// comment\ncube(10);}"
        ast = getASTfromString(code)
        assert ast is not None
        assert isinstance(ast[0], ModuleDeclaration)
        # Also test with comments included
        ast_comments = getASTfromString(code, include_comments=True)
        assert ast_comments is not None


class TestModularCall:
    def test_simple_call(self, parse):
        ast = parse("cube(10);")
        assert isinstance(ast[0], ModularCall)
        assert ast[0].name.name == "cube"

    def test_call_with_positional_args(self, parse):
        ast = parse("translate([1, 2, 3]) cube(1);")
        assert isinstance(ast[0], ModularCall)
        assert ast[0].name.name == "translate"
        assert len(ast[0].children) == 1

    def test_call_with_named_args(self, parse):
        ast = parse("cube(size=10, center=true);")
        assert isinstance(ast[0], ModularCall)
        assert len(ast[0].arguments) == 2
        assert isinstance(ast[0].arguments[0], NamedArgument)
        assert isinstance(ast[0].arguments[1], NamedArgument)

    def test_call_with_mixed_args(self, parse):
        ast = parse("foo(1, b=2);")
        assert isinstance(ast[0].arguments[0], PositionalArgument)
        assert isinstance(ast[0].arguments[1], NamedArgument)

    def test_nested_calls(self, parse):
        ast = parse("translate([1,0,0]) rotate([0,0,45]) cube(1);")
        outer = ast[0]
        assert isinstance(outer, ModularCall)
        assert outer.name.name == "translate"
        assert len(outer.children) == 1
        inner = outer.children[0]
        assert isinstance(inner, ModularCall)
        assert inner.name.name == "rotate"

    def test_call_with_block_children(self, parse):
        ast = parse("union() { cube(1); sphere(2); }")
        call = ast[0]
        assert isinstance(call, ModularCall)
        assert len(call.children) == 2

    def test_call_empty_statement(self, parse):
        ast = parse("cube(1);")
        assert isinstance(ast[0], ModularCall)
        assert len(ast[0].children) == 0

    def test_module_call_single_arg(self, parse):
        """Test module call with single argument."""
        ast = parse("cube(10);")
        assert ast is not None
        assert isinstance(ast[0], ModularCall)
        assert len(ast[0].arguments) == 1

    def test_module_call_multiple_args(self, parse):
        """Test module call with multiple arguments (vector)."""
        ast = parse("cube([10, 20, 30]);")
        assert ast is not None
        assert isinstance(ast[0], ModularCall)
        assert len(ast[0].arguments) == 1  # single vector argument


class TestModifiers:
    def test_show_only(self, parse):
        ast = parse("!cube(1);")
        assert isinstance(ast[0], ModularModifierShowOnly)
        assert isinstance(ast[0].child, ModularCall)

    def test_highlight(self, parse):
        ast = parse("#cube(1);")
        assert isinstance(ast[0], ModularModifierHighlight)

    def test_background(self, parse):
        ast = parse("%cube(1);")
        assert isinstance(ast[0], ModularModifierBackground)

    def test_disable(self, parse):
        ast = parse("*cube(1);")
        assert isinstance(ast[0], ModularModifierDisable)

    def test_nested_modifiers(self, parse):
        ast = parse("!#cube(1);")
        assert isinstance(ast[0], ModularModifierShowOnly)
        assert isinstance(ast[0].child, ModularModifierHighlight)

    def test_modifier_str(self, parse):
        ast = parse("!cube(1);")
        assert str(ast[0]) == "!cube(1)"

    def test_modifier_with_transform(self, parse):
        """Test modifier with transform."""
        ast = parse("!translate([1, 2, 3]) cube(10);")
        assert ast is not None
        assert isinstance(ast[0], ModularModifierShowOnly)
        assert isinstance(ast[0].child, ModularCall)
        assert ast[0].child.name.name == "translate"


class TestModuleComplex:
    """Test complex module scenarios."""

    def test_module_with_variables(self, parse):
        """Test module with variable assignments."""
        ast = parse("module test() { x = 10; cube(x); }")
        assert ast is not None
        decl = ast[0]
        assert isinstance(decl, ModuleDeclaration)
        assert len(decl.children) == 2

    def test_module_with_conditionals(self, parse):
        """Test module with conditional statements."""
        ast = parse("module test() { if (true) cube(10); }")
        assert ast is not None
        decl = ast[0]
        assert isinstance(decl, ModuleDeclaration)
        assert len(decl.children) == 1
        assert isinstance(decl.children[0], ModularIf)

    def test_module_with_loops(self, parse):
        """Test module with for loops."""
        ast = parse("module test() { for (i = [0:5]) translate([i, 0, 0]) cube(1); }")
        assert ast is not None
        decl = ast[0]
        assert isinstance(decl, ModuleDeclaration)
        assert len(decl.children) == 1
        assert isinstance(decl.children[0], ModularFor)

    def test_module_instantiation_in_expression(self, parse):
        """Test module instantiation in expression context."""
        ast = parse("x = cube(10);")
        # Note: This may or may not be valid in all contexts,
        # but tests parser behavior
        assert ast is not None


class TestChildStatementMultipleChildren:
    """Regression tests: child_statement with blocks should return all children."""

    def test_modular_call_block_all_children_returned(self):
        """translate() with a block of three cubes should yield all three children."""
        code = """
translate([1, 2, 3])
    rotate([4, 5, 6]) {
        cube([7, 7, 7]);
        cube([8, 8, 8]);
        cube([9, 9, 9]);
    }
"""
        ast = getASTfromString(code)
        assert ast is not None and isinstance(ast, list)
        translate = ast[0]
        assert isinstance(translate, ModularCall)
        assert translate.name.name == "translate"

        rotate = translate.children[0]
        assert isinstance(rotate, ModularCall)
        assert rotate.name.name == "rotate"
        assert len(rotate.children) == 3, (
            f"Expected 3 children, got {len(rotate.children)}: {rotate.children}"
        )
        names = [c.name.name for c in rotate.children]
        assert names == ["cube", "cube", "cube"]

    def test_for_block_all_children_returned(self):
        """for loop with a block body should capture all child instantiations."""
        code = "for (i = [0:2]) { cube(i); sphere(i); }"
        ast = getASTfromString(code)
        assert ast is not None and isinstance(ast, list)
        for_node = ast[0]
        assert isinstance(for_node, ModularFor)
        body = for_node.body
        if not isinstance(body, list):
            body = [body]
        assert len(body) == 2
        assert body[0].name.name == "cube"
        assert body[1].name.name == "sphere"

    def test_if_block_all_children_returned(self):
        """if statement with a block body should capture all child instantiations."""
        code = "if (true) { cube(1); sphere(2); cylinder(3); }"
        ast = getASTfromString(code)
        assert ast is not None and isinstance(ast, list)
        if_node = ast[0]
        assert isinstance(if_node, ModularIf)
        branch = if_node.true_branch
        if not isinstance(branch, list):
            branch = [branch]
        assert len(branch) == 3

    def test_ifelse_block_both_branches_complete(self):
        """if/else with blocks should capture all children in each branch."""
        code = "if (true) { cube(1); sphere(2); } else { cylinder(3); cube(4); }"
        ast = getASTfromString(code)
        assert ast is not None and isinstance(ast, list)
        if_node = ast[0]
        assert isinstance(if_node, ModularIfElse)
        true_branch = if_node.true_branch
        if not isinstance(true_branch, list):
            true_branch = [true_branch]
        false_branch = if_node.false_branch
        if not isinstance(false_branch, list):
            false_branch = [false_branch]
        assert len(true_branch) == 2
        assert len(false_branch) == 2

    def test_single_child_statement_still_works(self):
        """Single child (no block) should still work and return a one-element list."""
        code = "translate([1, 0, 0]) cube(5);"
        ast = getASTfromString(code)
        assert ast is not None and isinstance(ast, list)
        translate = ast[0]
        assert isinstance(translate, ModularCall)
        assert len(translate.children) == 1
        assert translate.children[0].name.name == "cube"


class TestModuleDeclarationDetailed:
    def test_no_params(self, parse):
        ast = parse("module foo() {}")
        assert isinstance(ast[0], ModuleDeclaration)
        assert len(ast[0].parameters) == 0
        assert len(ast[0].children) == 0

    def test_one_param_no_default(self, parse):
        from openscad_lalr_parser import ParameterDeclaration
        ast = parse("module foo(x) { cube(x); }")
        params = ast[0].parameters
        assert len(params) == 1
        assert isinstance(params[0], ParameterDeclaration)
        assert params[0].name.name == "x"
        assert params[0].default is None

    def test_one_param_with_default(self, parse):
        from openscad_lalr_parser import ParameterDeclaration, NumberLiteral
        ast = parse("module foo(x=10) { cube(x); }")
        params = ast[0].parameters
        assert len(params) == 1
        assert isinstance(params[0].default, NumberLiteral)
        assert params[0].default.val == 10

    def test_three_params_no_defaults(self, parse):
        ast = parse("module foo(x, y, z) { cube([x, y, z]); }")
        assert len(ast[0].parameters) == 3
        names = [p.name.name for p in ast[0].parameters]
        assert names == ["x", "y", "z"]

    def test_three_params_with_defaults(self, parse):
        from openscad_lalr_parser import NumberLiteral
        ast = parse("module foo(x=1, y=2, z=3) { cube([x, y, z]); }")
        assert len(ast[0].parameters) == 3
        defaults = [p.default.val for p in ast[0].parameters]
        assert defaults == [1.0, 2.0, 3.0]

    def test_mixed_params(self, parse):
        ast = parse("module foo(x, y=2, z) { cube([x, y, z]); }")
        params = ast[0].parameters
        assert len(params) == 3
        assert params[0].default is None
        assert params[1].default is not None
        assert params[2].default is None

    def test_multiple_children(self, parse):
        ast = parse("module foo() { cube(10); sphere(5); translate([1,2,3]) cylinder(1, 2); }")
        assert len(ast[0].children) == 3
        assert ast[0].children[0].name.name == "cube"
        assert ast[0].children[1].name.name == "sphere"
        assert ast[0].children[2].name.name == "translate"
        assert len(ast[0].children[2].children) == 1

    def test_module_no_args_call(self, parse):
        ast = parse("cube();")
        assert isinstance(ast[0], ModularCall)
        assert len(ast[0].arguments) == 0

    def test_module_chained_calls(self, parse):
        ast = parse("translate([1, 2, 3]) rotate([0, 0, 45]) cube(10);")
        outer = ast[0]
        assert outer.name.name == "translate"
        assert len(outer.children) == 1
        mid = outer.children[0]
        assert mid.name.name == "rotate"
        assert len(mid.children) == 1
        inner = mid.children[0]
        assert inner.name.name == "cube"
