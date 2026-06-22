"""Tests for expression parsing: operators, precedence, ternary."""
from openscad_lalr_parser import (
    getASTfromString,
    Assignment,
    AdditionOp,
    SubtractionOp,
    MultiplicationOp,
    DivisionOp,
    ModuloOp,
    ExponentOp,
    UnaryMinusOp,
    LogicalAndOp,
    LogicalOrOp,
    LogicalNotOp,
    BitwiseAndOp,
    BitwiseOrOp,
    BitwiseNotOp,
    BitwiseShiftLeftOp,
    BitwiseShiftRightOp,
    EqualityOp,
    InequalityOp,
    GreaterThanOp,
    GreaterThanOrEqualOp,
    LessThanOp,
    LessThanOrEqualOp,
    TernaryOp,
    NumberLiteral,
    BooleanLiteral,
    Identifier,
    PrimaryCall,
    PrimaryIndex,
    PrimaryMember,
)


class TestArithmeticOps:
    def test_addition(self, parse):
        ast = parse("x = 1 + 2;")
        assert isinstance(ast[0].expr, AdditionOp)
        assert isinstance(ast[0].expr.left, NumberLiteral)
        assert isinstance(ast[0].expr.right, NumberLiteral)

    def test_subtraction(self, parse):
        ast = parse("x = 5 - 3;")
        assert isinstance(ast[0].expr, SubtractionOp)

    def test_multiplication(self, parse):
        ast = parse("x = 2 * 3;")
        assert isinstance(ast[0].expr, MultiplicationOp)

    def test_division(self, parse):
        ast = parse("x = 10 / 2;")
        assert isinstance(ast[0].expr, DivisionOp)

    def test_modulo(self, parse):
        ast = parse("x = 10 % 3;")
        assert isinstance(ast[0].expr, ModuloOp)

    def test_exponent(self, parse):
        ast = parse("x = 2 ^ 3;")
        assert isinstance(ast[0].expr, ExponentOp)

    def test_unary_minus(self, parse):
        ast = parse("x = -5;")
        assert isinstance(ast[0].expr, UnaryMinusOp)

    def test_addition_str(self, parse):
        ast = parse("x = 1 + 2;")
        assert str(ast[0].expr) == "1 + 2"

    def test_subtraction_str(self, parse):
        ast = parse("x = 5 - 3;")
        assert str(ast[0].expr) == "5 - 3"

    def test_chained_operations(self, parse):
        ast = parse("x = 1 + 2 + 3;")
        expr = ast[0].expr
        assert isinstance(expr, AdditionOp)
        assert isinstance(expr.left, AdditionOp)

    def test_mixed_operations(self, parse):
        ast = parse("x = 1 + 2 * 3;")
        expr = ast[0].expr
        assert isinstance(expr, AdditionOp)
        assert isinstance(expr.right, MultiplicationOp)


class TestPrecedence:
    def test_mul_before_add(self, parse):
        ast = parse("x = 1 + 2 * 3;")
        expr = ast[0].expr
        assert isinstance(expr, AdditionOp)
        assert isinstance(expr.right, MultiplicationOp)

    def test_paren_override(self, parse):
        ast = parse("x = (1 + 2) * 3;")
        expr = ast[0].expr
        assert isinstance(expr, MultiplicationOp)
        assert isinstance(expr.left, AdditionOp)

    def test_left_associativity(self, parse):
        ast = parse("x = 1 - 2 - 3;")
        expr = ast[0].expr
        assert isinstance(expr, SubtractionOp)
        assert isinstance(expr.left, SubtractionOp)

    def test_right_associativity_exponent(self, parse):
        ast = parse("x = 2 ^ 3 ^ 4;")
        expr = ast[0].expr
        assert isinstance(expr, ExponentOp)
        assert isinstance(expr.right, ExponentOp)

    def test_exponentiation_before_multiplication(self, parse):
        ast = parse("x = 2 * 3 ^ 2;")
        expr = ast[0].expr
        assert isinstance(expr, MultiplicationOp)
        assert isinstance(expr.right, ExponentOp)

    def test_nested_parentheses(self, parse):
        ast = parse("x = ((1 + 2) * 3) / 4;")
        expr = ast[0].expr
        assert isinstance(expr, DivisionOp)
        assert isinstance(expr.left, MultiplicationOp)

    def test_unary_binds_tighter_than_mul(self, parse):
        ast = parse("x = -2 * 3;")
        expr = ast[0].expr
        assert isinstance(expr, MultiplicationOp)
        assert isinstance(expr.left, UnaryMinusOp)


class TestComparisonOps:
    def test_equality(self, parse):
        ast = parse("x = a == b;")
        assert isinstance(ast[0].expr, EqualityOp)

    def test_inequality(self, parse):
        ast = parse("x = a != b;")
        assert isinstance(ast[0].expr, InequalityOp)

    def test_greater_than(self, parse):
        ast = parse("x = a > b;")
        assert isinstance(ast[0].expr, GreaterThanOp)

    def test_greater_than_or_equal(self, parse):
        ast = parse("x = a >= b;")
        assert isinstance(ast[0].expr, GreaterThanOrEqualOp)

    def test_less_than(self, parse):
        ast = parse("x = a < b;")
        assert isinstance(ast[0].expr, LessThanOp)

    def test_less_than_or_equal(self, parse):
        ast = parse("x = a <= b;")
        assert isinstance(ast[0].expr, LessThanOrEqualOp)

    def test_less_equal(self, parse):
        ast = parse("x = 1 <= 2;")
        assert isinstance(ast[0].expr, LessThanOrEqualOp)

    def test_greater_equal(self, parse):
        ast = parse("x = 2 >= 1;")
        assert isinstance(ast[0].expr, GreaterThanOrEqualOp)

    def test_equal(self, parse):
        ast = parse("x = 1 == 2;")
        assert isinstance(ast[0].expr, EqualityOp)

    def test_not_equal(self, parse):
        ast = parse("x = 1 != 2;")
        assert isinstance(ast[0].expr, InequalityOp)


class TestLogicalOps:
    def test_logical_and(self, parse):
        ast = parse("x = a && b;")
        assert isinstance(ast[0].expr, LogicalAndOp)

    def test_logical_or(self, parse):
        ast = parse("x = a || b;")
        assert isinstance(ast[0].expr, LogicalOrOp)

    def test_logical_not(self, parse):
        ast = parse("x = !a;")
        assert isinstance(ast[0].expr, LogicalNotOp)

    def test_and_or_precedence(self, parse):
        ast = parse("x = a || b && c;")
        expr = ast[0].expr
        assert isinstance(expr, LogicalOrOp)
        assert isinstance(expr.right, LogicalAndOp)

    def test_logical_precedence(self, parse):
        ast = parse("x = true && false || true;")
        expr = ast[0].expr
        assert isinstance(expr, LogicalOrOp)
        assert isinstance(expr.left, LogicalAndOp)


class TestBitwiseOps:
    def test_bitwise_and(self, parse):
        ast = parse("x = 5 & 3;")
        assert isinstance(ast[0].expr, BitwiseAndOp)

    def test_bitwise_or(self, parse):
        ast = parse("x = 5 | 3;")
        assert isinstance(ast[0].expr, BitwiseOrOp)

    def test_bitwise_not(self, parse):
        ast = parse("x = ~5;")
        assert isinstance(ast[0].expr, BitwiseNotOp)

    def test_shift_left(self, parse):
        ast = parse("x = 1 << 3;")
        assert isinstance(ast[0].expr, BitwiseShiftLeftOp)

    def test_shift_right(self, parse):
        ast = parse("x = 8 >> 2;")
        assert isinstance(ast[0].expr, BitwiseShiftRightOp)

    def test_binary_shift_left(self, parse):
        ast = parse("x = 1 << 2;")
        assert isinstance(ast[0].expr, BitwiseShiftLeftOp)

    def test_binary_shift_left_chained(self, parse):
        ast = parse("x = 1 << 2 << 3;")
        expr = ast[0].expr
        assert isinstance(expr, BitwiseShiftLeftOp)
        assert isinstance(expr.left, BitwiseShiftLeftOp)

    def test_binary_shift_right_chained(self, parse):
        ast = parse("x = 64 >> 2 >> 1;")
        expr = ast[0].expr
        assert isinstance(expr, BitwiseShiftRightOp)
        assert isinstance(expr.left, BitwiseShiftRightOp)

    def test_binary_shift_mixed(self, parse):
        ast = parse("x = 1 << 2 >> 1;")
        expr = ast[0].expr
        assert isinstance(expr, BitwiseShiftRightOp)
        assert isinstance(expr.left, BitwiseShiftLeftOp)

    def test_binary_shift_with_arithmetic(self, parse):
        ast = parse("x = (1 << 2) + 3;")
        expr = ast[0].expr
        assert isinstance(expr, AdditionOp)
        assert isinstance(expr.left, BitwiseShiftLeftOp)

    def test_binary_shift_in_expression(self, parse):
        ast = parse("x = a << b >> c;")
        expr = ast[0].expr
        assert isinstance(expr, BitwiseShiftRightOp)
        assert isinstance(expr.left, BitwiseShiftLeftOp)

    def test_binary_not_with_expression(self, parse):
        ast = parse("x = ~(1 + 2);")
        expr = ast[0].expr
        assert isinstance(expr, BitwiseNotOp)
        assert isinstance(expr.expr, AdditionOp)

    def test_binary_not_chained(self, parse):
        ast = parse("x = ~~5;")
        expr = ast[0].expr
        assert isinstance(expr, BitwiseNotOp)
        assert isinstance(expr.expr, BitwiseNotOp)

    def test_binary_not_with_shift(self, parse):
        ast = parse("x = ~(1 << 2);")
        expr = ast[0].expr
        assert isinstance(expr, BitwiseNotOp)
        assert isinstance(expr.expr, BitwiseShiftLeftOp)


class TestTernaryOp:
    def test_ternary(self, parse):
        ast = parse("x = a > 0 ? a : -a;")
        assert isinstance(ast[0].expr, TernaryOp)
        assert isinstance(ast[0].expr.condition, GreaterThanOp)

    def test_ternary_str(self, parse):
        ast = parse("x = a > 0 ? a : b;")
        expr = ast[0].expr
        assert "?" in str(expr)
        assert ":" in str(expr)

    def test_ternary_simple(self, parse):
        ast = parse("x = true ? 1 : 2;")
        expr = ast[0].expr
        assert isinstance(expr, TernaryOp)
        assert isinstance(expr.condition, BooleanLiteral)

    def test_ternary_nested(self, parse):
        ast = parse("x = true ? (false ? 1 : 2) : 3;")
        expr = ast[0].expr
        assert isinstance(expr, TernaryOp)
        assert isinstance(expr.true_expr, TernaryOp)

    def test_ternary_in_expression(self, parse):
        ast = parse("x = (true ? 1 : 2) * 3;")
        expr = ast[0].expr
        assert isinstance(expr, MultiplicationOp)
        assert isinstance(expr.left, TernaryOp)


class TestPostfixOps:
    def test_function_call(self, parse):
        ast = parse("x = foo(1, 2);")
        assert isinstance(ast[0].expr, PrimaryCall)
        assert ast[0].expr.left.name == "foo"
        assert len(ast[0].expr.arguments) == 2

    def test_index_access(self, parse):
        ast = parse("x = arr[0];")
        assert isinstance(ast[0].expr, PrimaryIndex)
        assert ast[0].expr.left.name == "arr"

    def test_member_access(self, parse):
        ast = parse("x = obj.member;")
        assert isinstance(ast[0].expr, PrimaryMember)
        assert ast[0].expr.member.name == "member"

    def test_chained_calls(self, parse):
        ast = parse("x = foo(1)(2);")
        assert isinstance(ast[0].expr, PrimaryCall)
        assert isinstance(ast[0].expr.left, PrimaryCall)

    def test_chained_index(self, parse):
        ast = parse("x = arr[0][1];")
        assert isinstance(ast[0].expr, PrimaryIndex)
        assert isinstance(ast[0].expr.left, PrimaryIndex)

    def test_member_chained(self, parse):
        ast = parse("x = obj.member.submember;")
        assert isinstance(ast[0].expr, PrimaryMember)
        assert isinstance(ast[0].expr.left, PrimaryMember)

    def test_function_call_no_args(self, parse):
        ast = parse("x = foo();")
        assert isinstance(ast[0].expr, PrimaryCall)
        assert len(ast[0].expr.arguments) == 0

    def test_nested_function_calls(self, parse):
        ast = parse("x = sin(cos(0));")
        assert isinstance(ast[0].expr, PrimaryCall)
        assert isinstance(ast[0].expr.arguments[0].expr, PrimaryCall)

    def test_function_call_in_expression(self, parse):
        ast = parse("x = sin(0) + cos(0);")
        assert isinstance(ast[0].expr, AdditionOp)

    def test_member_access_in_expression(self, parse):
        ast = parse("x = obj.member + 1;")
        expr = ast[0].expr
        assert isinstance(expr, AdditionOp)
        assert isinstance(expr.left, PrimaryMember)

    def test_array_access_expression(self, parse):
        ast = parse("x = arr[i + 1];")
        expr = ast[0].expr
        assert isinstance(expr, PrimaryIndex)
        assert isinstance(expr.index, AdditionOp)

    def test_function_call_with_member(self, parse):
        ast = parse("x = obj.func(1, 2);")
        expr = ast[0].expr
        assert isinstance(expr, PrimaryCall)
        assert isinstance(expr.left, PrimaryMember)


class TestUnaryOps:
    def test_unary_plus(self, parse):
        ast = parse("x = +5;")
        assert ast is not None
        # Unary plus is a pass-through; the expression is the number itself
        assert isinstance(ast[0].expr, NumberLiteral)

    def test_unary_not(self, parse):
        ast = parse("x = !true;")
        assert isinstance(ast[0].expr, LogicalNotOp)


class TestComplexExpressions:
    def test_complex_1(self, parse):
        ast = parse("x = (a + b) * (c - d) / (e % f);")
        assert isinstance(ast[0].expr, DivisionOp)

    def test_complex_2(self, parse):
        ast = parse("x = a > b && c < d || e == f;")
        assert isinstance(ast[0].expr, LogicalOrOp)

    def test_complex_3(self, parse):
        ast = parse("x = sin(a) * cos(b) + tan(c);")
        assert isinstance(ast[0].expr, AdditionOp)

    def test_complex_4(self, parse):
        ast = parse("x = arr[i] + arr[j] * arr[k];")
        assert isinstance(ast[0].expr, AdditionOp)

    def test_complex_5(self, parse):
        ast = parse("x = a > b ? c + d : e - f;")
        assert isinstance(ast[0].expr, TernaryOp)

    def test_multiple_unary(self, parse):
        from openscad_lalr_parser import UnaryMinusOp
        ast = parse("x = --5;")
        assert isinstance(ast[0].expr, UnaryMinusOp)
        assert isinstance(ast[0].expr.expr, UnaryMinusOp)

    def test_unary_with_expression(self, parse):
        from openscad_lalr_parser import UnaryMinusOp
        ast = parse("x = -(1 + 2);")
        assert isinstance(ast[0].expr, UnaryMinusOp)
        assert isinstance(ast[0].expr.expr, AdditionOp)
