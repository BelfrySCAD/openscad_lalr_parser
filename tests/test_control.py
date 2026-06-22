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
    ListCompEach,
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


    def test_if_nested(self, parse):
        ast = parse("if (true) if (false) cube(10); else sphere(5);")
        assert isinstance(ast[0], ModularIf)

    def test_if_with_expression(self, parse):
        ast = parse("if (x > 0 && y < 10) cube(10);")
        assert isinstance(ast[0], ModularIf)


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

    def test_for_range_with_step(self, parse):
        ast = parse("for (i=[0:2:10]) translate([i, 0, 0]) cube(1);")
        assert isinstance(ast[0], ModularFor)
        assert len(ast[0].assignments) == 1

    def test_for_vector(self, parse):
        ast = parse("for (i=[1, 2, 3]) translate([i, 0, 0]) cube(1);")
        assert isinstance(ast[0], ModularFor)
        assert len(ast[0].assignments) == 1

    def test_for_with_block(self, parse):
        ast = parse("for (i=[0:5]) { translate([i,0,0]) cube(1); }")
        assert isinstance(ast[0], ModularFor)


class TestModularIntersectionFor:
    def test_intersection_for(self, parse):
        ast = parse("intersection_for (i=[0:3]) rotate([0,0,i*90]) cube(10);")
        assert isinstance(ast[0], ModularIntersectionFor)
        assert len(ast[0].assignments) == 1

    def test_intersection_for_with_block(self, parse):
        ast = parse("intersection_for(i=[0:5]) { translate([i, 0, 0]) cube(1); }")
        assert isinstance(ast[0], ModularIntersectionFor)

    def test_intersection_for_multiple_vars(self, parse):
        ast = parse("intersection_for(i=[0:5], j=[0:3]) translate([i, j, 0]) cube(1);")
        assert isinstance(ast[0], ModularIntersectionFor)
        assert len(ast[0].assignments) == 2


class TestModularLet:
    def test_modular_let(self, parse):
        ast = parse("let (x=10) cube(x);")
        assert isinstance(ast[0], ModularLet)
        assert len(ast[0].assignments) == 1
        assert ast[0].assignments[0].name.name == "x"

    def test_let_multiple(self, parse):
        ast = parse("let(x=10, y=20) cube([x, y, 10]);")
        assert isinstance(ast[0], ModularLet)
        assert len(ast[0].assignments) == 2

    def test_let_with_block(self, parse):
        ast = parse("let(x=10) { cube(x); }")
        assert isinstance(ast[0], ModularLet)

    def test_let_nested(self, parse):
        ast = parse("let(x=10) let(y=x*2) cube(y);")
        assert isinstance(ast[0], ModularLet)
        child = ast[0].children
        assert isinstance(child[0], ModularLet)


class TestModularEcho:
    def test_modular_echo(self, parse):
        ast = parse('echo("hello") cube(1);')
        assert isinstance(ast[0], ModularEcho)
        assert len(ast[0].arguments) == 1

    def test_echo_multiple_args(self, parse):
        ast = parse('echo("Hello", "World") cube(10);')
        assert isinstance(ast[0], ModularEcho)
        assert len(ast[0].arguments) == 2

    def test_echo_with_block(self, parse):
        ast = parse('echo("Hello") { cube(10); }')
        assert isinstance(ast[0], ModularEcho)


class TestModularAssert:
    def test_modular_assert(self, parse):
        ast = parse("assert(x > 0) cube(x);")
        assert isinstance(ast[0], ModularAssert)
        assert len(ast[0].arguments) == 1

    def test_assert_with_message(self, parse):
        ast = parse('assert(true, "Error message") cube(10);')
        assert isinstance(ast[0], ModularAssert)
        assert len(ast[0].arguments) == 2

    def test_assert_with_block(self, parse):
        ast = parse("assert(true) { cube(10); }")
        assert isinstance(ast[0], ModularAssert)


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


class TestModularEchoArgCounts:
    def test_echo_zero_args(self, parse):
        ast = parse("echo();")
        assert isinstance(ast[0], ModularEcho)
        assert len(ast[0].arguments) == 0

    def test_echo_two_args(self, parse):
        ast = parse("echo(1, 2);")
        assert isinstance(ast[0], ModularEcho)
        assert len(ast[0].arguments) == 2

    def test_echo_three_args(self, parse):
        ast = parse("echo(1, 2, 3);")
        assert isinstance(ast[0], ModularEcho)
        assert len(ast[0].arguments) == 3


class TestModularAssertArgCounts:
    def test_assert_two_args(self, parse):
        ast = parse('assert(true, "msg");')
        assert isinstance(ast[0], ModularAssert)
        assert len(ast[0].arguments) == 2


class TestModularLetAssignmentCounts:
    def test_let_zero_assignments(self, parse):
        ast = parse("let() cube(1);")
        assert isinstance(ast[0], ModularLet)
        assert len(ast[0].assignments) == 0

    def test_let_two_assignments(self, parse):
        ast = parse("let(x=1, y=2) cube(x);")
        assert isinstance(ast[0], ModularLet)
        assert len(ast[0].assignments) == 2

    def test_let_three_assignments(self, parse):
        ast = parse("let(x=1, y=2, z=3) cube(x);")
        assert isinstance(ast[0], ModularLet)
        assert len(ast[0].assignments) == 3


class TestModularForAssignmentCounts:
    def test_for_two_assignments(self, parse):
        ast = parse("for (i=[0:3], j=[0:2]) cube(i);")
        assert isinstance(ast[0], ModularFor)
        assert len(ast[0].assignments) == 2

    def test_for_three_assignments(self, parse):
        ast = parse("for (i=[0:3], j=[0:2], k=[0:1]) cube(i);")
        assert isinstance(ast[0], ModularFor)
        assert len(ast[0].assignments) == 3


class TestEach:
    def test_each_in_listcomp(self, parse):
        ast = parse("x = [each [1, 2, 3]];")
        assert ast is not None
        assert isinstance(ast[0], Assignment)

    def test_each_nested(self, parse):
        ast = parse("x = [each [each [1, 2, 3]]];")
        assert ast is not None
        assert isinstance(ast[0], Assignment)


class TestModularIntersectionForCounts:
    def test_intersection_for_two(self, parse):
        ast = parse("intersection_for (i=[0:3], j=[0:2]) cube(i);")
        assert isinstance(ast[0], ModularIntersectionFor)
        assert len(ast[0].assignments) == 2
