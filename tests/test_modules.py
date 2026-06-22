"""Tests for module definitions, calls, and modifiers."""
from openscad_lalr_parser import (
    getASTfromString,
    ModuleDeclaration,
    ModularCall,
    ModularModifierShowOnly,
    ModularModifierHighlight,
    ModularModifierBackground,
    ModularModifierDisable,
    PositionalArgument,
    NamedArgument,
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
