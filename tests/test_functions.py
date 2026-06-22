"""Tests for function definitions and function literals."""
from openscad_lalr_parser import (
    getASTfromString,
    FunctionDeclaration,
    FunctionLiteral,
    Assignment,
    AdditionOp,
    MultiplicationOp,
    Identifier,
    PrimaryCall,
)


class TestFunctionDeclaration:
    def test_simple_function(self, parse):
        ast = parse("function add(a, b) = a + b;")
        assert isinstance(ast[0], FunctionDeclaration)
        assert ast[0].name.name == "add"
        assert len(ast[0].parameters) == 2
        assert isinstance(ast[0].expr, AdditionOp)

    def test_function_with_defaults(self, parse):
        ast = parse("function foo(x, y=10) = x + y;")
        assert ast[0].parameters[0].default is None
        assert ast[0].parameters[1].default is not None

    def test_function_no_params(self, parse):
        ast = parse("function pi() = 3.14159;")
        assert isinstance(ast[0], FunctionDeclaration)
        assert len(ast[0].parameters) == 0

    def test_function_str(self, parse):
        ast = parse("function add(a, b) = a + b;")
        s = str(ast[0])
        assert "function" in s
        assert "add" in s


class TestFunctionLiteral:
    def test_function_literal(self, parse):
        ast = parse("x = function(a) a * 2;")
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, FunctionLiteral)
        assert len(ast[0].expr.parameters) == 1
        assert isinstance(ast[0].expr.body, MultiplicationOp)

    def test_function_literal_no_params(self, parse):
        ast = parse("x = function() 42;")
        assert isinstance(ast[0].expr, FunctionLiteral)
        assert len(ast[0].expr.parameters) == 0

    def test_function_literal_str(self, parse):
        ast = parse("x = function(a) a;")
        s = str(ast[0].expr)
        assert "function" in s

    def test_function_call_on_literal(self, parse):
        ast = parse("x = (function(a) a * 2)(5);")
        assert isinstance(ast[0].expr, PrimaryCall)
