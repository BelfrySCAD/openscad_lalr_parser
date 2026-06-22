"""Tests for control structures: if/else, for, let, echo, assert."""
from openscad_lalr_parser import (
    getASTfromString,
    ModularIf,
    ModularIfElse,
    ModularFor,
    ModularIntersectionFor,
    ModularLet,
    ModularEcho,
    ModularAssert,
    ModularCall,
    LetOp,
    EchoOp,
    AssertOp,
    Assignment,
    UndefinedLiteral,
)


class TestModularIf:
    def test_if_statement(self, parse):
        ast = parse("if (x > 0) cube(x);")
        assert isinstance(ast[0], ModularIf)

    def test_if_with_block(self, parse):
        ast = parse("if (x > 0) { cube(x); sphere(1); }")
        assert isinstance(ast[0], ModularIf)

    def test_ifelse_statement(self, parse):
        ast = parse("if (x > 0) cube(x); else sphere(5);")
        assert isinstance(ast[0], ModularIfElse)

    def test_ifelse_with_blocks(self, parse):
        ast = parse("if (x > 0) { cube(x); } else { sphere(5); }")
        assert isinstance(ast[0], ModularIfElse)


class TestModularFor:
    def test_simple_for(self, parse):
        ast = parse("for (i=[0:5]) cube(i);")
        assert isinstance(ast[0], ModularFor)
        assert len(ast[0].assignments) == 1
        assert ast[0].assignments[0].name.name == "i"

    def test_multi_variable_for(self, parse):
        ast = parse("for (i=[0:2], j=[0:2]) translate([i,j,0]) cube(1);")
        assert isinstance(ast[0], ModularFor)
        assert len(ast[0].assignments) == 2

    def test_for_with_block(self, parse):
        ast = parse("for (i=[0:5]) { translate([i,0,0]) cube(1); }")
        assert isinstance(ast[0], ModularFor)


class TestModularIntersectionFor:
    def test_intersection_for(self, parse):
        ast = parse("intersection_for (i=[0:3]) rotate([0,0,i*90]) cube(10);")
        assert isinstance(ast[0], ModularIntersectionFor)
        assert len(ast[0].assignments) == 1


class TestModularLet:
    def test_modular_let(self, parse):
        ast = parse("let (x=10) cube(x);")
        assert isinstance(ast[0], ModularLet)
        assert len(ast[0].assignments) == 1
        assert ast[0].assignments[0].name.name == "x"


class TestModularEcho:
    def test_modular_echo(self, parse):
        ast = parse('echo("hello") cube(1);')
        assert isinstance(ast[0], ModularEcho)
        assert len(ast[0].arguments) == 1


class TestModularAssert:
    def test_modular_assert(self, parse):
        ast = parse("assert(x > 0) cube(x);")
        assert isinstance(ast[0], ModularAssert)
        assert len(ast[0].arguments) == 1


class TestLetExpr:
    def test_let_expression(self, parse):
        ast = parse("x = let(a=1, b=2) a + b;")
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, LetOp)
        assert len(ast[0].expr.assignments) == 2

    def test_nested_let(self, parse):
        ast = parse("x = let(a=1) let(b=2) a + b;")
        assert isinstance(ast[0].expr, LetOp)
        assert isinstance(ast[0].expr.body, LetOp)


class TestEchoExpr:
    def test_echo_expression(self, parse):
        ast = parse('x = echo("val", y) y;')
        assert isinstance(ast[0].expr, EchoOp)
        assert len(ast[0].expr.arguments) == 2

    def test_echo_no_body(self, parse):
        ast = parse('x = echo("val");')
        assert isinstance(ast[0].expr, EchoOp)
        assert isinstance(ast[0].expr.body, UndefinedLiteral)


class TestAssertExpr:
    def test_assert_expression(self, parse):
        ast = parse("x = assert(y > 0) y;")
        assert isinstance(ast[0].expr, AssertOp)

    def test_assert_no_body(self, parse):
        ast = parse("x = assert(y > 0);")
        assert isinstance(ast[0].expr, AssertOp)
        assert isinstance(ast[0].expr.body, UndefinedLiteral)
