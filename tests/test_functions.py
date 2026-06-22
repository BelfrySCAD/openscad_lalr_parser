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
    TernaryOp,
    LetOp,
    NamedArgument,
    PositionalArgument,
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

    def test_function_complex_expression(self, parse):
        ast = parse("function complex(x) = x * 2 + sin(x) * cos(x);")
        assert isinstance(ast[0], FunctionDeclaration)
        assert ast[0].name.name == "complex"

    def test_function_ternary(self, parse):
        ast = parse("function abs(x) = x >= 0 ? x : -x;")
        assert isinstance(ast[0], FunctionDeclaration)
        assert isinstance(ast[0].expr, TernaryOp)

    def test_function_with_let(self, parse):
        ast = parse("function test(x) = let(y = x * 2) y + 1;")
        assert isinstance(ast[0], FunctionDeclaration)
        assert isinstance(ast[0].expr, LetOp)


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

    def test_function_literal_two_params(self, parse):
        ast = parse("x = function(a, b) a + b;")
        assert isinstance(ast[0].expr, FunctionLiteral)
        assert len(ast[0].expr.parameters) == 2

    def test_function_literal_three_params(self, parse):
        ast = parse("x = function(a, b, c) a + b + c;")
        assert isinstance(ast[0].expr, FunctionLiteral)
        assert len(ast[0].expr.parameters) == 3

    def test_function_literal_params_with_defaults(self, parse):
        ast = parse("x = function(a, b=2, c=3) a + b + c;")
        fl = ast[0].expr
        assert isinstance(fl, FunctionLiteral)
        assert len(fl.parameters) == 3
        assert fl.parameters[0].default is None
        assert fl.parameters[1].default is not None
        assert fl.parameters[2].default is not None

    def test_function_literal_str(self, parse):
        ast = parse("x = function(a) a;")
        s = str(ast[0].expr)
        assert "function" in s

    def test_function_call_on_literal(self, parse):
        ast = parse("x = (function(a) a * 2)(5);")
        assert isinstance(ast[0].expr, PrimaryCall)


class TestFunctionCall:
    def test_function_call_no_args(self, parse):
        ast = parse("x = test();")
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, PrimaryCall)

    def test_function_call_single_arg(self, parse):
        ast = parse("x = test(5);")
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, PrimaryCall)

    def test_function_call_multiple_args(self, parse):
        ast = parse("x = add(1, 2);")
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, PrimaryCall)

    def test_function_call_named_args(self, parse):
        ast = parse("x = test(x=1, y=2);")
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, PrimaryCall)

    def test_function_call_mixed_args(self, parse):
        ast = parse("x = test(1, y=2);")
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, PrimaryCall)

    def test_function_call_nested(self, parse):
        ast = parse("x = add(multiply(2, 3), 4);")
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, PrimaryCall)

    def test_function_call_in_expression(self, parse):
        ast = parse("x = add(1, 2) * 3;")
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, MultiplicationOp)


class TestFunctionDeclarationDetailed:
    def test_one_param_no_default(self, parse):
        from openscad_lalr_parser import ParameterDeclaration, NumberLiteral
        ast = parse("function foo(x) = x;")
        func = ast[0]
        assert isinstance(func, FunctionDeclaration)
        assert len(func.parameters) == 1
        assert func.parameters[0].name.name == "x"
        assert func.parameters[0].default is None
        assert isinstance(func.expr, Identifier)

    def test_one_param_with_default(self, parse):
        from openscad_lalr_parser import NumberLiteral
        ast = parse("function foo(x=10) = x;")
        assert ast[0].parameters[0].default.val == 10

    def test_two_params_no_defaults(self, parse):
        ast = parse("function foo(x, y) = x + y;")
        assert len(ast[0].parameters) == 2
        assert ast[0].parameters[0].default is None
        assert ast[0].parameters[1].default is None

    def test_two_params_with_defaults(self, parse):
        from openscad_lalr_parser import NumberLiteral
        ast = parse("function foo(x=1, y=2) = x + y;")
        assert len(ast[0].parameters) == 2
        assert ast[0].parameters[0].default.val == 1
        assert ast[0].parameters[1].default.val == 2

    def test_mixed_params(self, parse):
        ast = parse("function foo(x, y=2, z) = x + y + z;")
        assert len(ast[0].parameters) == 3
        assert ast[0].parameters[0].default is None
        assert ast[0].parameters[1].default is not None
        assert ast[0].parameters[2].default is None
