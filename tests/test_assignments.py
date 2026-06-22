"""Tests for variable assignments."""
from openscad_lalr_parser import (
    getASTfromString,
    Assignment,
    NumberLiteral,
    Identifier,
    AdditionOp,
)


class TestAssignments:
    def test_simple_assignment(self, parse):
        ast = parse("x = 10;")
        assert isinstance(ast[0], Assignment)
        assert ast[0].name.name == "x"
        assert isinstance(ast[0].expr, NumberLiteral)
        assert ast[0].expr.val == 10.0

    def test_expression_assignment(self, parse):
        ast = parse("y = x + 5;")
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, AdditionOp)

    def test_multiple_assignments(self, parse):
        ast = parse("x = 1;\ny = 2;\nz = 3;")
        assert len(ast) == 3
        assert all(isinstance(a, Assignment) for a in ast)

    def test_assignment_str(self, parse):
        ast = parse("x = 10;")
        assert str(ast[0]) == "x = 10"

    def test_dollar_var_assignment(self, parse):
        ast = parse("$fn = 64;")
        assert ast[0].name.name == "$fn"

    def test_assignment_position(self, parse):
        ast = parse("x = 10;")
        assert ast[0].position is not None
        assert ast[0].position.line == 1


class TestScopeAnalysis:
    def test_build_scopes(self):
        from openscad_lalr_parser import getASTfromString, build_scopes
        ast = getASTfromString("x = 10;\ny = 20;")
        scope = build_scopes(ast)
        assert scope.lookup_variable("x") is not None
        assert scope.lookup_variable("y") is not None
        assert scope.lookup_variable("z") is None

    def test_function_scope(self):
        from openscad_lalr_parser import getASTfromString, build_scopes
        ast = getASTfromString("function add(a, b) = a + b;")
        scope = build_scopes(ast)
        assert scope.lookup_function("add") is not None
        assert scope.lookup_variable("add") is None

    def test_module_scope(self):
        from openscad_lalr_parser import getASTfromString, build_scopes
        ast = getASTfromString("module box(size) { cube(size); }")
        scope = build_scopes(ast)
        assert scope.lookup_module("box") is not None
