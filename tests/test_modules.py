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
