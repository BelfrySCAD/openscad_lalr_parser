"""Comprehensive AST generation tests — ported from openscad_parser's test_ast_generation.py.

Adapted for the openscad_lalr_parser API:
  - Uses getASTfromString() directly (no parser fixture)
  - Uses parse_ast(code, origin=...) where file origin is needed
  - Comment tests (TestCommentASTNodes) are SKIPPED — include_comments not yet supported
"""
import pytest
from openscad_lalr_parser import (
    getASTfromString,
    parse_ast,
    Position,
    ASTNode,
    Expression,
    Primary,
    Identifier,
    StringLiteral,
    NumberLiteral,
    BooleanLiteral,
    UndefinedLiteral,
    ParameterDeclaration,
    Argument,
    PositionalArgument,
    NamedArgument,
    RangeLiteral,
    Assignment,
    LetOp,
    EchoOp,
    AssertOp,
    UnaryMinusOp,
    AdditionOp,
    SubtractionOp,
    MultiplicationOp,
    DivisionOp,
    ModuloOp,
    ExponentOp,
    BitwiseAndOp,
    BitwiseOrOp,
    BitwiseNotOp,
    BitwiseShiftLeftOp,
    BitwiseShiftRightOp,
    LogicalAndOp,
    LogicalOrOp,
    LogicalNotOp,
    TernaryOp,
    EqualityOp,
    InequalityOp,
    GreaterThanOp,
    GreaterThanOrEqualOp,
    LessThanOp,
    LessThanOrEqualOp,
    FunctionLiteral,
    PrimaryCall,
    PrimaryIndex,
    PrimaryMember,
    ListComprehension,
    ListCompFor,
    ListCompIf,
    ListCompIfElse,
    ListCompLet,
    ListCompEach,
    ListCompCFor,
    VectorElement,
    ModuleInstantiation,
    ModularCall,
    ModularFor,
    ModularIntersectionFor,
    ModularLet,
    ModularEcho,
    ModularAssert,
    ModularIf,
    ModularIfElse,
    ModularModifierShowOnly,
    ModularModifierHighlight,
    ModularModifierBackground,
    ModularModifierDisable,
    ModuleDeclaration,
    FunctionDeclaration,
    UseStatement,
    IncludeStatement,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _getast(code: str):
    """Parse OpenSCAD code and return the AST node list."""
    return getASTfromString(code)


def _expr(code: str):
    """Parse an expression by wrapping it in an assignment and returning the expr."""
    ast = getASTfromString(f"x = {code};")
    assert ast is not None and len(ast) > 0
    assert isinstance(ast[0], Assignment)
    return ast[0].expr


# ===========================================================================
# Literal AST Nodes
# ===========================================================================

class TestLiteralASTNodes:
    def test_integer_literal(self):
        expr = _expr("42")
        assert isinstance(expr, NumberLiteral)
        assert expr.val == 42.0

    def test_float_literal(self):
        expr = _expr("3.14")
        assert isinstance(expr, NumberLiteral)
        assert expr.val == 3.14

    def test_scientific_literal(self):
        expr = _expr("1e10")
        assert isinstance(expr, NumberLiteral)
        assert expr.val == 1e10

    def test_hex_literal(self):
        expr = _expr("0xFF")
        assert isinstance(expr, NumberLiteral)
        assert expr.val == 255.0

    def test_string_literal(self):
        expr = _expr('"hello"')
        assert isinstance(expr, StringLiteral)
        assert expr.val == "hello"

    def test_empty_string_literal(self):
        expr = _expr('""')
        assert isinstance(expr, StringLiteral)
        assert expr.val == ""

    def test_true_literal(self):
        expr = _expr("true")
        assert isinstance(expr, BooleanLiteral)
        assert expr.val is True

    def test_false_literal(self):
        expr = _expr("false")
        assert isinstance(expr, BooleanLiteral)
        assert expr.val is False

    def test_undef_literal(self):
        expr = _expr("undef")
        assert isinstance(expr, UndefinedLiteral)

    def test_identifier(self):
        expr = _expr("foo")
        assert isinstance(expr, Identifier)
        assert expr.name == "foo"

    def test_special_variable(self):
        expr = _expr("$fn")
        assert isinstance(expr, Identifier)
        assert expr.name == "$fn"

    def test_number_str(self):
        expr = _expr("42")
        assert str(expr) == "42"

    def test_float_str(self):
        expr = _expr("3.14")
        assert str(expr) == "3.14"

    def test_string_str(self):
        expr = _expr('"hello"')
        assert str(expr) == '"hello"'

    def test_true_str(self):
        expr = _expr("true")
        assert str(expr) == "true"

    def test_false_str(self):
        expr = _expr("false")
        assert str(expr) == "false"

    def test_undef_str(self):
        expr = _expr("undef")
        assert str(expr) == "undef"

    def test_identifier_str(self):
        expr = _expr("foo")
        assert str(expr) == "foo"


# ===========================================================================
# Expression AST Nodes
# ===========================================================================

class TestExpressionASTNodes:
    # --- Arithmetic ---
    def test_addition(self):
        expr = _expr("1 + 2")
        assert isinstance(expr, AdditionOp)
        assert isinstance(expr.left, NumberLiteral)
        assert isinstance(expr.right, NumberLiteral)

    def test_subtraction(self):
        expr = _expr("5 - 3")
        assert isinstance(expr, SubtractionOp)

    def test_multiplication(self):
        expr = _expr("2 * 3")
        assert isinstance(expr, MultiplicationOp)

    def test_division(self):
        expr = _expr("10 / 2")
        assert isinstance(expr, DivisionOp)

    def test_modulo(self):
        expr = _expr("10 % 3")
        assert isinstance(expr, ModuloOp)

    def test_exponent(self):
        expr = _expr("2 ^ 3")
        assert isinstance(expr, ExponentOp)

    def test_unary_minus(self):
        expr = _expr("-x")
        assert isinstance(expr, UnaryMinusOp)
        assert isinstance(expr.expr, Identifier)

    # --- Comparison ---
    def test_equality(self):
        expr = _expr("a == b")
        assert isinstance(expr, EqualityOp)

    def test_inequality(self):
        expr = _expr("a != b")
        assert isinstance(expr, InequalityOp)

    def test_greater_than(self):
        expr = _expr("a > b")
        assert isinstance(expr, GreaterThanOp)

    def test_greater_than_or_equal(self):
        expr = _expr("a >= b")
        assert isinstance(expr, GreaterThanOrEqualOp)

    def test_less_than(self):
        expr = _expr("a < b")
        assert isinstance(expr, LessThanOp)

    def test_less_than_or_equal(self):
        expr = _expr("a <= b")
        assert isinstance(expr, LessThanOrEqualOp)

    def test_comparison_operators_ast(self):
        """All comparison operators produce the correct AST node type."""
        cases = [
            ("a == b", EqualityOp),
            ("a != b", InequalityOp),
            ("a > b", GreaterThanOp),
            ("a >= b", GreaterThanOrEqualOp),
            ("a < b", LessThanOp),
            ("a <= b", LessThanOrEqualOp),
        ]
        for code, expected_type in cases:
            expr = _expr(code)
            assert isinstance(expr, expected_type), f"Expected {expected_type.__name__} for '{code}'"

    # --- Bitwise ---
    def test_bitwise_and(self):
        expr = _expr("a & b")
        assert isinstance(expr, BitwiseAndOp)

    def test_bitwise_or(self):
        expr = _expr("a | b")
        assert isinstance(expr, BitwiseOrOp)

    def test_bitwise_not(self):
        expr = _expr("~a")
        assert isinstance(expr, BitwiseNotOp)

    def test_bitwise_shift_left(self):
        expr = _expr("a << b")
        assert isinstance(expr, BitwiseShiftLeftOp)

    def test_bitwise_shift_right(self):
        expr = _expr("a >> b")
        assert isinstance(expr, BitwiseShiftRightOp)

    def test_bitwise_operators_ast(self):
        """All bitwise operators produce the correct AST node type."""
        cases = [
            ("a & b", BitwiseAndOp),
            ("a | b", BitwiseOrOp),
            ("~a", BitwiseNotOp),
            ("a << b", BitwiseShiftLeftOp),
            ("a >> b", BitwiseShiftRightOp),
        ]
        for code, expected_type in cases:
            expr = _expr(code)
            assert isinstance(expr, expected_type), f"Expected {expected_type.__name__} for '{code}'"

    # --- Logical ---
    def test_logical_and(self):
        expr = _expr("a && b")
        assert isinstance(expr, LogicalAndOp)

    def test_logical_or(self):
        expr = _expr("a || b")
        assert isinstance(expr, LogicalOrOp)

    def test_logical_not(self):
        expr = _expr("!a")
        assert isinstance(expr, LogicalNotOp)

    # --- Ternary ---
    def test_ternary(self):
        expr = _expr("a ? b : c")
        assert isinstance(expr, TernaryOp)
        assert isinstance(expr.condition, Identifier)
        assert isinstance(expr.true_expr, Identifier)
        assert isinstance(expr.false_expr, Identifier)

    def test_nested_ternary(self):
        expr = _expr("a ? b : c ? d : e")
        assert isinstance(expr, TernaryOp)
        assert isinstance(expr.false_expr, TernaryOp)

    # --- Precedence ---
    def test_precedence_mul_over_add(self):
        expr = _expr("a + b * c")
        assert isinstance(expr, AdditionOp)
        assert isinstance(expr.right, MultiplicationOp)

    def test_precedence_add_left_assoc(self):
        expr = _expr("a + b + c")
        assert isinstance(expr, AdditionOp)
        assert isinstance(expr.left, AdditionOp)

    def test_precedence_mul_left_assoc(self):
        expr = _expr("a * b * c")
        assert isinstance(expr, MultiplicationOp)
        assert isinstance(expr.left, MultiplicationOp)

    def test_precedence_exponent_right_assoc(self):
        expr = _expr("a ^ b ^ c")
        assert isinstance(expr, ExponentOp)
        assert isinstance(expr.right, ExponentOp)

    def test_precedence_comparison_lower_than_arithmetic(self):
        expr = _expr("a + b > c")
        assert isinstance(expr, GreaterThanOp)
        assert isinstance(expr.left, AdditionOp)

    def test_precedence_logical_and_lower_than_comparison(self):
        expr = _expr("a > b && c > d")
        assert isinstance(expr, LogicalAndOp)
        assert isinstance(expr.left, GreaterThanOp)
        assert isinstance(expr.right, GreaterThanOp)

    def test_precedence_logical_or_lower_than_and(self):
        expr = _expr("a && b || c && d")
        assert isinstance(expr, LogicalOrOp)
        assert isinstance(expr.left, LogicalAndOp)
        assert isinstance(expr.right, LogicalAndOp)

    def test_precedence_ternary_lowest(self):
        expr = _expr("a || b ? c : d")
        assert isinstance(expr, TernaryOp)
        assert isinstance(expr.condition, LogicalOrOp)

    def test_parenthesized_expression(self):
        expr = _expr("(a + b) * c")
        assert isinstance(expr, MultiplicationOp)
        assert isinstance(expr.left, AdditionOp)

    def test_unary_minus_precedence(self):
        expr = _expr("-a + b")
        assert isinstance(expr, AdditionOp)
        assert isinstance(expr.left, UnaryMinusOp)

    # --- String representation ---
    def test_addition_str(self):
        expr = _expr("1 + 2")
        assert str(expr) == "1 + 2"

    def test_subtraction_str(self):
        expr = _expr("5 - 3")
        assert str(expr) == "5 - 3"

    def test_multiplication_str(self):
        expr = _expr("2 * 3")
        assert str(expr) == "2 * 3"

    def test_division_str(self):
        expr = _expr("10 / 2")
        assert str(expr) == "10 / 2"

    def test_modulo_str(self):
        expr = _expr("10 % 3")
        assert str(expr) == "10 % 3"

    def test_exponent_str(self):
        expr = _expr("2 ^ 3")
        assert str(expr) == "2 ^ 3"

    def test_ternary_str(self):
        expr = _expr("a ? b : c")
        assert str(expr) == "a ? b : c"

    def test_logical_and_str(self):
        expr = _expr("a && b")
        assert str(expr) == "a && b"

    def test_logical_or_str(self):
        expr = _expr("a || b")
        assert str(expr) == "a || b"

    def test_unary_minus_str(self):
        expr = _expr("-x")
        assert str(expr) == "-x"


# ===========================================================================
# Function Call AST Nodes
# ===========================================================================

class TestFunctionCallASTNodes:
    def test_simple_call(self):
        expr = _expr("foo()")
        assert isinstance(expr, PrimaryCall)
        assert isinstance(expr.left, Identifier)
        assert expr.left.name == "foo"
        assert len(expr.arguments) == 0

    def test_call_positional_arg(self):
        expr = _expr("foo(1)")
        assert isinstance(expr, PrimaryCall)
        assert len(expr.arguments) == 1
        assert isinstance(expr.arguments[0], PositionalArgument)

    def test_call_named_arg(self):
        expr = _expr("foo(x=1)")
        assert isinstance(expr, PrimaryCall)
        assert len(expr.arguments) == 1
        assert isinstance(expr.arguments[0], NamedArgument)
        assert expr.arguments[0].name.name == "x"

    def test_call_mixed_args(self):
        expr = _expr("foo(1, x=2)")
        assert isinstance(expr, PrimaryCall)
        assert len(expr.arguments) == 2
        assert isinstance(expr.arguments[0], PositionalArgument)
        assert isinstance(expr.arguments[1], NamedArgument)

    def test_call_multiple_positional(self):
        expr = _expr("foo(1, 2, 3)")
        assert isinstance(expr, PrimaryCall)
        assert len(expr.arguments) == 3
        for arg in expr.arguments:
            assert isinstance(arg, PositionalArgument)

    def test_call_multiple_named(self):
        expr = _expr("foo(x=1, y=2)")
        assert isinstance(expr, PrimaryCall)
        assert len(expr.arguments) == 2
        for arg in expr.arguments:
            assert isinstance(arg, NamedArgument)

    def test_primary_index(self):
        expr = _expr("a[0]")
        assert isinstance(expr, PrimaryIndex)
        assert isinstance(expr.left, Identifier)
        assert isinstance(expr.index, NumberLiteral)

    def test_primary_member(self):
        expr = _expr("a.x")
        assert isinstance(expr, PrimaryMember)
        assert isinstance(expr.left, Identifier)
        assert isinstance(expr.member, Identifier)
        assert expr.member.name == "x"

    def test_chained_calls(self):
        expr = _expr("foo(1)(2)")
        assert isinstance(expr, PrimaryCall)
        assert isinstance(expr.left, PrimaryCall)

    def test_index_on_call(self):
        expr = _expr("foo(1)[0]")
        assert isinstance(expr, PrimaryIndex)
        assert isinstance(expr.left, PrimaryCall)

    def test_member_on_call(self):
        expr = _expr("foo(1).x")
        assert isinstance(expr, PrimaryMember)
        assert isinstance(expr.left, PrimaryCall)

    def test_call_str(self):
        expr = _expr("foo(1, 2)")
        assert str(expr) == "foo(1, 2)"

    def test_index_str(self):
        expr = _expr("a[0]")
        assert str(expr) == "a[0]"

    def test_member_str(self):
        expr = _expr("a.x")
        assert str(expr) == "a.x"


# ===========================================================================
# PrimaryCall Argument counts
# ===========================================================================

class TestPrimaryCallArguments:
    def test_0_positional(self):
        expr = _expr("foo()")
        assert isinstance(expr, PrimaryCall)
        assert len(expr.arguments) == 0

    def test_1_positional(self):
        expr = _expr("foo(1)")
        assert len(expr.arguments) == 1
        assert isinstance(expr.arguments[0], PositionalArgument)

    def test_2_positional(self):
        expr = _expr("foo(1, 2)")
        assert len(expr.arguments) == 2

    def test_3_positional(self):
        expr = _expr("foo(1, 2, 3)")
        assert len(expr.arguments) == 3

    def test_1_named(self):
        expr = _expr("foo(a=1)")
        assert len(expr.arguments) == 1
        assert isinstance(expr.arguments[0], NamedArgument)

    def test_2_named(self):
        expr = _expr("foo(a=1, b=2)")
        assert len(expr.arguments) == 2
        assert isinstance(expr.arguments[0], NamedArgument)
        assert isinstance(expr.arguments[1], NamedArgument)

    def test_mixed_positional_and_named(self):
        expr = _expr("foo(1, a=2)")
        assert len(expr.arguments) == 2
        assert isinstance(expr.arguments[0], PositionalArgument)
        assert isinstance(expr.arguments[1], NamedArgument)


# ===========================================================================
# ListComprehension Elements
# ===========================================================================

class TestListComprehensionElements:
    def test_0_elements(self):
        expr = _expr("[]")
        assert isinstance(expr, ListComprehension)
        assert len(expr.elements) == 0

    def test_1_element(self):
        expr = _expr("[1]")
        assert isinstance(expr, ListComprehension)
        assert len(expr.elements) == 1

    def test_2_elements(self):
        expr = _expr("[1, 2]")
        assert isinstance(expr, ListComprehension)
        assert len(expr.elements) == 2

    def test_3_elements(self):
        expr = _expr("[1, 2, 3]")
        assert isinstance(expr, ListComprehension)
        assert len(expr.elements) == 3

    def test_1_for_element(self):
        expr = _expr("[for (i=[0:5]) i]")
        assert isinstance(expr, ListComprehension)
        assert len(expr.elements) == 1
        assert isinstance(expr.elements[0], ListCompFor)

    def test_2_for_elements(self):
        expr = _expr("[for (i=[0:5]) i, for (j=[0:5]) j]")
        assert isinstance(expr, ListComprehension)
        assert len(expr.elements) == 2
        assert isinstance(expr.elements[0], ListCompFor)
        assert isinstance(expr.elements[1], ListCompFor)

    def test_mixed_elements(self):
        expr = _expr("[1, for (i=[0:5]) i, 2]")
        assert isinstance(expr, ListComprehension)
        assert len(expr.elements) == 3

    def test_if_element(self):
        expr = _expr("[for (i=[0:5]) if (i > 2) i]")
        assert isinstance(expr, ListComprehension)
        elem = expr.elements[0]
        assert isinstance(elem, ListCompFor)
        assert isinstance(elem.body, ListCompIf)

    def test_if_else_element(self):
        expr = _expr("[for (i=[0:5]) if (i > 2) i else 0]")
        assert isinstance(expr, ListComprehension)
        elem = expr.elements[0]
        assert isinstance(elem, ListCompFor)
        assert isinstance(elem.body, ListCompIfElse)

    def test_list_comprehension_str(self):
        expr = _expr("[1, 2, 3]")
        assert str(expr) == "[1, 2, 3]"

    def test_empty_list_str(self):
        expr = _expr("[]")
        assert str(expr) == "[]"


# ===========================================================================
# Control Structure AST Nodes (expression-level)
# ===========================================================================

class TestControlStructureASTNodes:
    def test_let_expression(self):
        expr = _expr("let(a=1) a")
        assert isinstance(expr, LetOp)
        assert len(expr.assignments) == 1
        assert expr.assignments[0].name.name == "a"
        assert isinstance(expr.body, Identifier)

    def test_let_multiple_assignments(self):
        expr = _expr("let(a=1, b=2) a + b")
        assert isinstance(expr, LetOp)
        assert len(expr.assignments) == 2

    def test_nested_let(self):
        expr = _expr("let(a=1) let(b=2) a + b")
        assert isinstance(expr, LetOp)
        assert isinstance(expr.body, LetOp)

    def test_echo_expression(self):
        expr = _expr('echo("val", y) y')
        assert isinstance(expr, EchoOp)
        assert len(expr.arguments) == 2
        assert isinstance(expr.body, Identifier)

    def test_echo_no_body(self):
        ast = _getast('x = echo("val");')
        assert isinstance(ast[0].expr, EchoOp)
        assert isinstance(ast[0].expr.body, UndefinedLiteral)

    def test_assert_expression(self):
        expr = _expr("assert(y > 0) y")
        assert isinstance(expr, AssertOp)
        assert len(expr.arguments) == 1
        assert isinstance(expr.body, Identifier)

    def test_assert_with_message(self):
        expr = _expr('assert(y > 0, "must be positive") y')
        assert isinstance(expr, AssertOp)
        assert len(expr.arguments) == 2

    def test_assert_no_body(self):
        ast = _getast("x = assert(y > 0);")
        assert isinstance(ast[0].expr, AssertOp)
        assert isinstance(ast[0].expr.body, UndefinedLiteral)

    def test_let_str(self):
        expr = _expr("let(a=1) a")
        s = str(expr)
        assert "let" in s

    def test_echo_str(self):
        expr = _expr('echo("x") y')
        s = str(expr)
        assert "echo" in s

    def test_assert_str(self):
        expr = _expr("assert(y > 0) y")
        s = str(expr)
        assert "assert" in s


# ===========================================================================
# Modular Call Arguments
# ===========================================================================

class TestModularCallArguments:
    def test_0_positional(self):
        ast = _getast("foo();")
        assert isinstance(ast[0], ModularCall)
        assert len(ast[0].arguments) == 0

    def test_1_positional(self):
        ast = _getast("foo(1);")
        assert len(ast[0].arguments) == 1
        assert isinstance(ast[0].arguments[0], PositionalArgument)

    def test_2_positional(self):
        ast = _getast("foo(1, 2);")
        assert len(ast[0].arguments) == 2

    def test_3_positional(self):
        ast = _getast("foo(1, 2, 3);")
        assert len(ast[0].arguments) == 3

    def test_1_named(self):
        ast = _getast("foo(a=1);")
        assert len(ast[0].arguments) == 1
        assert isinstance(ast[0].arguments[0], NamedArgument)

    def test_2_named(self):
        ast = _getast("foo(a=1, b=2);")
        assert len(ast[0].arguments) == 2

    def test_mixed_positional_and_named(self):
        ast = _getast("foo(1, a=2);")
        assert len(ast[0].arguments) == 2
        assert isinstance(ast[0].arguments[0], PositionalArgument)
        assert isinstance(ast[0].arguments[1], NamedArgument)


# ===========================================================================
# Module AST Nodes
# ===========================================================================

class TestModuleASTNodes:
    # --- Module declarations ---
    def test_module_declaration_0_params(self):
        ast = _getast("module foo() { cube(1); }")
        assert isinstance(ast[0], ModuleDeclaration)
        assert ast[0].name.name == "foo"
        assert len(ast[0].parameters) == 0

    def test_module_declaration_1_param(self):
        ast = _getast("module foo(x) { cube(x); }")
        assert isinstance(ast[0], ModuleDeclaration)
        assert len(ast[0].parameters) == 1
        assert ast[0].parameters[0].name.name == "x"

    def test_module_declaration_2_params(self):
        ast = _getast("module foo(x, y) { cube([x, y, 1]); }")
        assert len(ast[0].parameters) == 2

    def test_module_declaration_3_params(self):
        ast = _getast("module foo(x, y, z) { cube([x, y, z]); }")
        assert len(ast[0].parameters) == 3

    def test_module_declaration_with_defaults(self):
        ast = _getast("module foo(x=1, y=2) { cube([x, y, 1]); }")
        assert ast[0].parameters[0].default is not None
        assert ast[0].parameters[1].default is not None

    def test_module_declaration_without_defaults(self):
        ast = _getast("module foo(x, y) { cube([x, y, 1]); }")
        assert ast[0].parameters[0].default is None
        assert ast[0].parameters[1].default is None

    def test_module_declaration_mixed_defaults(self):
        ast = _getast("module foo(x, y=10) { cube([x, y, 1]); }")
        assert ast[0].parameters[0].default is None
        assert ast[0].parameters[1].default is not None

    # --- Module children ---
    def test_module_0_children(self):
        ast = _getast("module foo() { }")
        assert len(ast[0].children) == 0

    def test_module_1_child(self):
        ast = _getast("module foo() { cube(1); }")
        assert len(ast[0].children) == 1

    def test_module_2_children(self):
        ast = _getast("module foo() { cube(1); sphere(2); }")
        assert len(ast[0].children) == 2

    def test_module_3_children(self):
        ast = _getast("module foo() { cube(1); sphere(2); cylinder(3); }")
        assert len(ast[0].children) == 3

    def test_module_empty_body(self):
        ast = _getast("module foo() { }")
        assert isinstance(ast[0], ModuleDeclaration)
        assert len(ast[0].children) == 0

    def test_module_single_statement_body(self):
        ast = _getast("module foo() cube(1);")
        assert isinstance(ast[0], ModuleDeclaration)
        assert len(ast[0].children) == 1

    # --- Module calls ---
    def test_module_call_0_args(self):
        ast = _getast("cube();")
        assert isinstance(ast[0], ModularCall)
        assert ast[0].name.name == "cube"
        assert len(ast[0].arguments) == 0

    def test_module_call_1_positional(self):
        ast = _getast("cube(10);")
        assert len(ast[0].arguments) == 1
        assert isinstance(ast[0].arguments[0], PositionalArgument)

    def test_module_call_2_positional(self):
        ast = _getast("cube(10, 20);")
        assert len(ast[0].arguments) == 2

    def test_module_call_3_positional(self):
        ast = _getast("cube(10, 20, 30);")
        assert len(ast[0].arguments) == 3

    def test_module_call_named(self):
        ast = _getast("cube(size=10);")
        assert len(ast[0].arguments) == 1
        assert isinstance(ast[0].arguments[0], NamedArgument)

    def test_module_call_mixed(self):
        ast = _getast("cube(10, center=true);")
        assert len(ast[0].arguments) == 2
        assert isinstance(ast[0].arguments[0], PositionalArgument)
        assert isinstance(ast[0].arguments[1], NamedArgument)

    # --- Children chaining ---
    def test_children_chaining_single(self):
        ast = _getast("translate([1,0,0]) cube(1);")
        assert isinstance(ast[0], ModularCall)
        assert ast[0].name.name == "translate"
        assert len(ast[0].children) == 1
        assert isinstance(ast[0].children[0], ModularCall)

    def test_children_chaining_block(self):
        ast = _getast("translate([1,0,0]) { cube(1); sphere(2); }")
        assert isinstance(ast[0], ModularCall)
        assert len(ast[0].children) == 2

    def test_children_nested(self):
        ast = _getast("translate([1,0,0]) rotate([0,0,45]) cube(1);")
        assert isinstance(ast[0], ModularCall)
        child = ast[0].children[0]
        assert isinstance(child, ModularCall)
        assert child.name.name == "rotate"
        assert len(child.children) == 1

    # --- Modifiers ---
    def test_modifier_show_only(self):
        ast = _getast("!cube(1);")
        assert isinstance(ast[0], ModularModifierShowOnly)
        assert isinstance(ast[0].child, ModularCall)

    def test_modifier_highlight(self):
        ast = _getast("#cube(1);")
        assert isinstance(ast[0], ModularModifierHighlight)
        assert isinstance(ast[0].child, ModularCall)

    def test_modifier_background(self):
        ast = _getast("%cube(1);")
        assert isinstance(ast[0], ModularModifierBackground)
        assert isinstance(ast[0].child, ModularCall)

    def test_modifier_disable(self):
        ast = _getast("*cube(1);")
        assert isinstance(ast[0], ModularModifierDisable)
        assert isinstance(ast[0].child, ModularCall)

    # --- ModularFor ---
    def test_modular_for(self):
        ast = _getast("for (i=[0:5]) cube(i);")
        assert isinstance(ast[0], ModularFor)
        assert len(ast[0].assignments) == 1
        assert ast[0].assignments[0].name.name == "i"

    def test_modular_for_multi_var(self):
        ast = _getast("for (i=[0:2], j=[0:2]) translate([i,j,0]) cube(1);")
        assert isinstance(ast[0], ModularFor)
        assert len(ast[0].assignments) == 2

    # --- ModularIf / ModularIfElse ---
    def test_modular_if(self):
        ast = _getast("if (x > 0) cube(x);")
        assert isinstance(ast[0], ModularIf)

    def test_modular_if_else(self):
        ast = _getast("if (x > 0) cube(x); else sphere(5);")
        assert isinstance(ast[0], ModularIfElse)

    def test_modular_if_with_block(self):
        ast = _getast("if (x > 0) { cube(x); sphere(1); }")
        assert isinstance(ast[0], ModularIf)

    def test_modular_if_else_with_blocks(self):
        ast = _getast("if (x > 0) { cube(x); } else { sphere(5); }")
        assert isinstance(ast[0], ModularIfElse)

    # --- Module str ---
    def test_module_declaration_str(self):
        ast = _getast("module foo(x) { cube(x); }")
        s = str(ast[0])
        assert "module" in s
        assert "foo" in s

    def test_modular_call_str(self):
        ast = _getast("cube(10);")
        s = str(ast[0])
        assert "cube" in s
        assert "10" in s

    def test_modifier_str(self):
        ast = _getast("!cube(1);")
        s = str(ast[0])
        assert "!" in s


# ===========================================================================
# Let Assignments
# ===========================================================================

class TestLetAssignments:
    # --- LetOp ---
    def test_let_op_0(self):
        expr = _expr("let() x")
        assert isinstance(expr, LetOp)
        assert len(expr.assignments) == 0

    def test_let_op_1(self):
        expr = _expr("let(a=1) a")
        assert isinstance(expr, LetOp)
        assert len(expr.assignments) == 1

    def test_let_op_2(self):
        expr = _expr("let(a=1, b=2) a + b")
        assert isinstance(expr, LetOp)
        assert len(expr.assignments) == 2

    def test_let_op_3(self):
        expr = _expr("let(a=1, b=2, c=3) a + b + c")
        assert isinstance(expr, LetOp)
        assert len(expr.assignments) == 3

    # --- ModularLet ---
    def test_modular_let_0(self):
        ast = _getast("let() cube(1);")
        assert isinstance(ast[0], ModularLet)
        assert len(ast[0].assignments) == 0

    def test_modular_let_1(self):
        ast = _getast("let(x=10) cube(x);")
        assert isinstance(ast[0], ModularLet)
        assert len(ast[0].assignments) == 1

    def test_modular_let_2(self):
        ast = _getast("let(x=10, y=20) cube([x,y,1]);")
        assert isinstance(ast[0], ModularLet)
        assert len(ast[0].assignments) == 2

    def test_modular_let_3(self):
        ast = _getast("let(x=10, y=20, z=30) cube([x,y,z]);")
        assert isinstance(ast[0], ModularLet)
        assert len(ast[0].assignments) == 3

    # --- ModularFor ---
    def test_modular_for_1(self):
        ast = _getast("for (i=[0:5]) cube(i);")
        assert isinstance(ast[0], ModularFor)
        assert len(ast[0].assignments) == 1

    def test_modular_for_2(self):
        ast = _getast("for (i=[0:2], j=[0:2]) cube(1);")
        assert isinstance(ast[0], ModularFor)
        assert len(ast[0].assignments) == 2

    def test_modular_for_3(self):
        ast = _getast("for (i=[0:1], j=[0:1], k=[0:1]) cube(1);")
        assert isinstance(ast[0], ModularFor)
        assert len(ast[0].assignments) == 3

    # --- ModularIntersectionFor ---
    def test_modular_intersection_for_1(self):
        ast = _getast("intersection_for (i=[0:3]) cube(i);")
        assert isinstance(ast[0], ModularIntersectionFor)
        assert len(ast[0].assignments) == 1

    def test_modular_intersection_for_2(self):
        ast = _getast("intersection_for (i=[0:2], j=[0:2]) cube(1);")
        assert isinstance(ast[0], ModularIntersectionFor)
        assert len(ast[0].assignments) == 2

    def test_modular_intersection_for_3(self):
        ast = _getast("intersection_for (i=[0:1], j=[0:1], k=[0:1]) cube(1);")
        assert isinstance(ast[0], ModularIntersectionFor)
        assert len(ast[0].assignments) == 3


# ===========================================================================
# Module Declaration Children
# ===========================================================================

class TestModuleDeclarationChildren:
    def test_0_children(self):
        ast = _getast("module foo() { }")
        assert isinstance(ast[0], ModuleDeclaration)
        assert len(ast[0].children) == 0

    def test_1_child(self):
        ast = _getast("module foo() { cube(1); }")
        assert len(ast[0].children) == 1

    def test_2_children(self):
        ast = _getast("module foo() { cube(1); sphere(2); }")
        assert len(ast[0].children) == 2

    def test_3_children(self):
        ast = _getast("module foo() { cube(1); sphere(2); cylinder(3); }")
        assert len(ast[0].children) == 3

    def test_empty_body(self):
        ast = _getast("module foo() { }")
        assert len(ast[0].children) == 0

    def test_single_statement_body(self):
        ast = _getast("module foo() cube(1);")
        assert isinstance(ast[0], ModuleDeclaration)
        assert len(ast[0].children) == 1


# ===========================================================================
# Function AST Nodes
# ===========================================================================

class TestFunctionASTNodes:
    # --- Function declarations ---
    def test_function_declaration_0_params(self):
        ast = _getast("function pi() = 3.14159;")
        assert isinstance(ast[0], FunctionDeclaration)
        assert ast[0].name.name == "pi"
        assert len(ast[0].parameters) == 0

    def test_function_declaration_1_param(self):
        ast = _getast("function double(x) = x * 2;")
        assert isinstance(ast[0], FunctionDeclaration)
        assert len(ast[0].parameters) == 1

    def test_function_declaration_2_params(self):
        ast = _getast("function add(a, b) = a + b;")
        assert len(ast[0].parameters) == 2

    def test_function_declaration_3_params(self):
        ast = _getast("function sum(a, b, c) = a + b + c;")
        assert len(ast[0].parameters) == 3

    def test_function_declaration_with_defaults(self):
        ast = _getast("function foo(x=1, y=2) = x + y;")
        assert ast[0].parameters[0].default is not None
        assert ast[0].parameters[1].default is not None

    def test_function_declaration_without_defaults(self):
        ast = _getast("function foo(x, y) = x + y;")
        assert ast[0].parameters[0].default is None
        assert ast[0].parameters[1].default is None

    def test_function_declaration_mixed_defaults(self):
        ast = _getast("function foo(x, y=10) = x + y;")
        assert ast[0].parameters[0].default is None
        assert ast[0].parameters[1].default is not None

    # --- Function literals ---
    def test_function_literal(self):
        expr = _expr("function(a) a * 2")
        assert isinstance(expr, FunctionLiteral)
        assert len(expr.parameters) == 1

    def test_function_literal_no_params(self):
        expr = _expr("function() 42")
        assert isinstance(expr, FunctionLiteral)
        assert len(expr.parameters) == 0

    def test_function_literal_2_params(self):
        expr = _expr("function(a, b) a + b")
        assert isinstance(expr, FunctionLiteral)
        assert len(expr.parameters) == 2

    def test_function_literal_with_default(self):
        expr = _expr("function(a, b=10) a + b")
        assert isinstance(expr, FunctionLiteral)
        assert expr.parameters[0].default is None
        assert expr.parameters[1].default is not None

    # --- str ---
    def test_function_declaration_str(self):
        ast = _getast("function add(a, b) = a + b;")
        s = str(ast[0])
        assert "function" in s
        assert "add" in s

    def test_function_literal_str(self):
        expr = _expr("function(a) a")
        s = str(expr)
        assert "function" in s


# ===========================================================================
# Declaration Parameters
# ===========================================================================

class TestDeclarationParameters:
    # --- Module ---
    def test_module_0_params(self):
        ast = _getast("module foo() { }")
        assert len(ast[0].parameters) == 0

    def test_module_1_param(self):
        ast = _getast("module foo(x) { }")
        assert len(ast[0].parameters) == 1
        assert ast[0].parameters[0].name.name == "x"

    def test_module_2_params(self):
        ast = _getast("module foo(x, y) { }")
        assert len(ast[0].parameters) == 2

    def test_module_3_params(self):
        ast = _getast("module foo(x, y, z) { }")
        assert len(ast[0].parameters) == 3

    def test_module_param_with_default(self):
        ast = _getast("module foo(x=10) { }")
        assert ast[0].parameters[0].default is not None

    def test_module_param_without_default(self):
        ast = _getast("module foo(x) { }")
        assert ast[0].parameters[0].default is None

    # --- Function ---
    def test_function_0_params(self):
        ast = _getast("function foo() = 1;")
        assert len(ast[0].parameters) == 0

    def test_function_1_param(self):
        ast = _getast("function foo(x) = x;")
        assert len(ast[0].parameters) == 1

    def test_function_2_params(self):
        ast = _getast("function foo(x, y) = x + y;")
        assert len(ast[0].parameters) == 2

    def test_function_3_params(self):
        ast = _getast("function foo(x, y, z) = x + y + z;")
        assert len(ast[0].parameters) == 3

    def test_function_param_with_default(self):
        ast = _getast("function foo(x=10) = x;")
        assert ast[0].parameters[0].default is not None

    def test_function_param_without_default(self):
        ast = _getast("function foo(x) = x;")
        assert ast[0].parameters[0].default is None

    # --- FunctionLiteral ---
    def test_function_literal_0_params(self):
        expr = _expr("function() 1")
        assert len(expr.parameters) == 0

    def test_function_literal_1_param(self):
        expr = _expr("function(x) x")
        assert len(expr.parameters) == 1

    def test_function_literal_2_params(self):
        expr = _expr("function(x, y) x + y")
        assert len(expr.parameters) == 2

    def test_function_literal_3_params(self):
        expr = _expr("function(x, y, z) x + y + z")
        assert len(expr.parameters) == 3

    def test_function_literal_param_with_default(self):
        expr = _expr("function(x=10) x")
        assert expr.parameters[0].default is not None

    def test_function_literal_param_without_default(self):
        expr = _expr("function(x) x")
        assert expr.parameters[0].default is None

    # --- All with/without defaults ---
    def test_module_all_defaults(self):
        ast = _getast("module foo(x=1, y=2, z=3) { }")
        for p in ast[0].parameters:
            assert p.default is not None

    def test_module_no_defaults(self):
        ast = _getast("module foo(x, y, z) { }")
        for p in ast[0].parameters:
            assert p.default is None

    def test_function_all_defaults(self):
        ast = _getast("function foo(x=1, y=2, z=3) = x;")
        for p in ast[0].parameters:
            assert p.default is not None

    def test_function_no_defaults(self):
        ast = _getast("function foo(x, y, z) = x;")
        for p in ast[0].parameters:
            assert p.default is None

    def test_function_literal_all_defaults(self):
        expr = _expr("function(x=1, y=2, z=3) x")
        for p in expr.parameters:
            assert p.default is not None

    def test_function_literal_no_defaults(self):
        expr = _expr("function(x, y, z) x")
        for p in expr.parameters:
            assert p.default is None


# ===========================================================================
# Echo Arguments
# ===========================================================================

class TestEchoArguments:
    # --- EchoOp ---
    def test_echo_op_0(self):
        expr = _expr("echo() x")
        assert isinstance(expr, EchoOp)
        assert len(expr.arguments) == 0

    def test_echo_op_1(self):
        expr = _expr('echo("a") x')
        assert isinstance(expr, EchoOp)
        assert len(expr.arguments) == 1

    def test_echo_op_2(self):
        expr = _expr('echo("a", "b") x')
        assert isinstance(expr, EchoOp)
        assert len(expr.arguments) == 2

    def test_echo_op_3(self):
        expr = _expr('echo("a", "b", "c") x')
        assert isinstance(expr, EchoOp)
        assert len(expr.arguments) == 3

    # --- ModularEcho ---
    def test_modular_echo_0(self):
        ast = _getast("echo() cube(1);")
        assert isinstance(ast[0], ModularEcho)
        assert len(ast[0].arguments) == 0

    def test_modular_echo_1(self):
        ast = _getast('echo("a") cube(1);')
        assert isinstance(ast[0], ModularEcho)
        assert len(ast[0].arguments) == 1

    def test_modular_echo_2(self):
        ast = _getast('echo("a", "b") cube(1);')
        assert isinstance(ast[0], ModularEcho)
        assert len(ast[0].arguments) == 2

    def test_modular_echo_3(self):
        ast = _getast('echo("a", "b", "c") cube(1);')
        assert isinstance(ast[0], ModularEcho)
        assert len(ast[0].arguments) == 3

    # --- ModularAssert ---
    def test_modular_assert_1(self):
        ast = _getast("assert(x > 0) cube(x);")
        assert isinstance(ast[0], ModularAssert)
        assert len(ast[0].arguments) == 1

    def test_modular_assert_2(self):
        ast = _getast('assert(x > 0, "positive") cube(x);')
        assert isinstance(ast[0], ModularAssert)
        assert len(ast[0].arguments) == 2

    def test_modular_assert_3(self):
        ast = _getast('assert(x > 0, "positive", "extra") cube(x);')
        assert isinstance(ast[0], ModularAssert)
        assert len(ast[0].arguments) == 3


# ===========================================================================
# Statement AST Nodes
# ===========================================================================

class TestStatementASTNodes:
    def test_use_statement(self):
        ast = _getast("use <library.scad>")
        assert isinstance(ast[0], UseStatement)
        assert ast[0].filepath.val == "library.scad"

    def test_use_statement_with_path(self):
        ast = _getast("use <BOSL2/std.scad>")
        assert isinstance(ast[0], UseStatement)
        assert ast[0].filepath.val == "BOSL2/std.scad"

    def test_include_statement(self):
        ast = _getast("include <config.scad>")
        assert isinstance(ast[0], IncludeStatement)
        assert ast[0].filepath.val == "config.scad"

    def test_include_statement_with_path(self):
        ast = _getast("include <utils/math.scad>")
        assert ast[0].filepath.val == "utils/math.scad"

    def test_assignment(self):
        ast = _getast("x = 42;")
        assert isinstance(ast[0], Assignment)
        assert ast[0].name.name == "x"
        assert isinstance(ast[0].expr, NumberLiteral)

    def test_assignment_expression(self):
        ast = _getast("x = 1 + 2;")
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, AdditionOp)

    def test_use_str(self):
        ast = _getast("use <library.scad>")
        assert str(ast[0]) == "use <library.scad>"

    def test_include_str(self):
        ast = _getast("include <config.scad>")
        assert str(ast[0]) == "include <config.scad>"

    def test_assignment_str(self):
        ast = _getast("x = 42;")
        s = str(ast[0])
        assert "x" in s
        assert "42" in s


# ===========================================================================
# Position AST Nodes
# ===========================================================================

class TestPositionASTNodes:
    def test_position_info_default_origin(self):
        ast = _getast("x = 42;")
        assert ast[0].position is not None
        assert isinstance(ast[0].position, Position)
        assert ast[0].position.origin == "<string>"
        assert ast[0].position.line >= 1
        assert ast[0].position.column >= 1

    def test_position_info_custom_origin(self):
        ast = parse_ast("x = 42;", origin="test.scad")
        assert ast is not None
        assert ast[0].position.origin == "test.scad"

    def test_position_line_column(self):
        ast = _getast("x = 42;")
        pos = ast[0].position
        assert pos.line == 1
        assert pos.column >= 1

    def test_position_multiline(self):
        code = "x = 1;\ny = 2;"
        ast = _getast(code)
        assert ast[0].position.line == 1
        assert ast[1].position.line == 2

    def test_position_preserves_across_expressions(self):
        ast = _getast("x = 1 + 2;")
        assignment = ast[0]
        assert assignment.position is not None
        # The expression inside also has position info
        assert assignment.expr.position is not None

    def test_position_on_module_declaration(self):
        ast = _getast("module foo() { cube(1); }")
        assert ast[0].position is not None
        assert ast[0].position.line == 1

    def test_position_on_function_declaration(self):
        ast = _getast("function add(a, b) = a + b;")
        assert ast[0].position is not None
        assert ast[0].position.line == 1

    def test_position_on_modular_call(self):
        ast = _getast("cube(10);")
        assert ast[0].position is not None

    def test_lazy_evaluation_position(self):
        """Position is set during parsing, not lazily."""
        ast = _getast("x = 42;")
        pos = ast[0].position
        assert pos is not None
        assert pos.line == 1

    def test_position_origin_file(self):
        """When origin is provided, all nodes use that origin."""
        ast = parse_ast("x = 1;\ny = 2;", origin="test.scad")
        assert ast is not None
        for node in ast:
            assert node.position.origin == "test.scad"


# ===========================================================================
# Complex AST Nodes
# ===========================================================================

class TestComplexASTNodes:
    def test_nested_arithmetic(self):
        expr = _expr("(a + b) * (c - d)")
        assert isinstance(expr, MultiplicationOp)
        assert isinstance(expr.left, AdditionOp)
        assert isinstance(expr.right, SubtractionOp)

    def test_deeply_nested_expression(self):
        expr = _expr("a + b * c + d")
        assert isinstance(expr, AdditionOp)
        assert isinstance(expr.left, AdditionOp)
        inner = expr.left
        assert isinstance(inner.right, MultiplicationOp)

    def test_chained_function_calls(self):
        expr = _expr("foo(1)(2)(3)")
        assert isinstance(expr, PrimaryCall)
        assert isinstance(expr.left, PrimaryCall)
        assert isinstance(expr.left.left, PrimaryCall)

    def test_function_call_with_index(self):
        expr = _expr("foo(1)[0]")
        assert isinstance(expr, PrimaryIndex)
        assert isinstance(expr.left, PrimaryCall)

    def test_function_call_with_member(self):
        expr = _expr("foo(1).x")
        assert isinstance(expr, PrimaryMember)
        assert isinstance(expr.left, PrimaryCall)

    def test_complex_module(self):
        code = """
        module box(size, center=true) {
            cube(size, center=center);
            translate([0, 0, size])
                sphere(r=size/2);
        }
        """
        ast = _getast(code)
        assert isinstance(ast[0], ModuleDeclaration)
        assert ast[0].name.name == "box"
        assert len(ast[0].parameters) == 2
        assert len(ast[0].children) == 2

    def test_complex_function(self):
        code = "function dist(a, b) = sqrt((a[0]-b[0])^2 + (a[1]-b[1])^2);"
        ast = _getast(code)
        assert isinstance(ast[0], FunctionDeclaration)
        assert ast[0].name.name == "dist"
        assert len(ast[0].parameters) == 2

    def test_ternary_in_assignment(self):
        ast = _getast("x = a > 0 ? a : -a;")
        assert isinstance(ast[0].expr, TernaryOp)

    def test_let_in_function(self):
        code = "function foo(x) = let(a = x * 2) a + 1;"
        ast = _getast(code)
        assert isinstance(ast[0], FunctionDeclaration)
        assert isinstance(ast[0].expr, LetOp)

    def test_nested_module_calls(self):
        code = "difference() { cube(10); translate([2,2,2]) cube(6); }"
        ast = _getast(code)
        assert isinstance(ast[0], ModularCall)
        assert ast[0].name.name == "difference"
        assert len(ast[0].children) == 2

    def test_for_with_if(self):
        code = "for (i=[0:10]) if (i > 5) cube(i);"
        ast = _getast(code)
        assert isinstance(ast[0], ModularFor)
        # body may be a list or a single node depending on implementation
        body = ast[0].body
        if isinstance(body, list):
            assert len(body) == 1
            assert isinstance(body[0], ModularIf)
        else:
            assert isinstance(body, ModularIf)

    def test_mixed_statements(self):
        code = """
        use <BOSL2/std.scad>
        x = 10;
        module foo() { cube(x); }
        function bar(a) = a * 2;
        foo();
        """
        ast = _getast(code)
        assert isinstance(ast[0], UseStatement)
        assert isinstance(ast[1], Assignment)
        assert isinstance(ast[2], ModuleDeclaration)
        assert isinstance(ast[3], FunctionDeclaration)
        assert isinstance(ast[4], ModularCall)


# ===========================================================================
# Logical NOT AST
# ===========================================================================

class TestLogicalNotAST:
    def test_not_true(self):
        expr = _expr("!true")
        assert isinstance(expr, LogicalNotOp)
        assert isinstance(expr.expr, BooleanLiteral)
        assert expr.expr.val is True

    def test_not_false(self):
        expr = _expr("!false")
        assert isinstance(expr, LogicalNotOp)
        assert isinstance(expr.expr, BooleanLiteral)
        assert expr.expr.val is False

    def test_not_identifier(self):
        expr = _expr("!x")
        assert isinstance(expr, LogicalNotOp)
        assert isinstance(expr.expr, Identifier)
        assert expr.expr.name == "x"

    def test_not_double(self):
        expr = _expr("!!x")
        assert isinstance(expr, LogicalNotOp)
        assert isinstance(expr.expr, LogicalNotOp)
        assert isinstance(expr.expr.expr, Identifier)

    def test_not_equality(self):
        expr = _expr("!(a == b)")
        assert isinstance(expr, LogicalNotOp)
        assert isinstance(expr.expr, EqualityOp)

    def test_not_inequality(self):
        expr = _expr("!(a != b)")
        assert isinstance(expr, LogicalNotOp)
        assert isinstance(expr.expr, InequalityOp)

    def test_not_comparison(self):
        expr = _expr("!(a > b)")
        assert isinstance(expr, LogicalNotOp)
        assert isinstance(expr.expr, GreaterThanOp)

    def test_not_binds_tighter_than_and(self):
        expr = _expr("!a && b")
        assert isinstance(expr, LogicalAndOp)
        assert isinstance(expr.left, LogicalNotOp)
        assert isinstance(expr.right, Identifier)

    def test_not_binds_tighter_than_or(self):
        expr = _expr("!a || b")
        assert isinstance(expr, LogicalOrOp)
        assert isinstance(expr.left, LogicalNotOp)
        assert isinstance(expr.right, Identifier)

    def test_not_both_sides_of_and(self):
        expr = _expr("!a && !b")
        assert isinstance(expr, LogicalAndOp)
        assert isinstance(expr.left, LogicalNotOp)
        assert isinstance(expr.right, LogicalNotOp)

    def test_not_in_ternary_condition(self):
        expr = _expr("!a ? b : c")
        assert isinstance(expr, TernaryOp)
        assert isinstance(expr.condition, LogicalNotOp)

    def test_not_in_ternary_branch(self):
        expr = _expr("a ? !b : !c")
        assert isinstance(expr, TernaryOp)
        assert isinstance(expr.true_expr, LogicalNotOp)
        assert isinstance(expr.false_expr, LogicalNotOp)

    def test_not_in_if_condition(self):
        ast = _getast("if (!x) cube(1);")
        assert isinstance(ast[0], ModularIf)
        assert isinstance(ast[0].condition, LogicalNotOp)

    def test_str_simple(self):
        expr = _expr("!x")
        assert str(expr) == "!x"

    def test_str_double(self):
        expr = _expr("!!x")
        assert str(expr) == "!!x"


# ===========================================================================
# Bitwise NOT AST
# ===========================================================================

class TestBitwiseNotAST:
    def test_not_number(self):
        expr = _expr("~42")
        assert isinstance(expr, BitwiseNotOp)
        assert isinstance(expr.expr, NumberLiteral)
        assert expr.expr.val == 42.0

    def test_not_identifier(self):
        expr = _expr("~x")
        assert isinstance(expr, BitwiseNotOp)
        assert isinstance(expr.expr, Identifier)
        assert expr.expr.name == "x"

    def test_not_double(self):
        expr = _expr("~~x")
        assert isinstance(expr, BitwiseNotOp)
        assert isinstance(expr.expr, BitwiseNotOp)
        assert isinstance(expr.expr.expr, Identifier)

    def test_not_parenthesized_addition(self):
        expr = _expr("~(a + b)")
        assert isinstance(expr, BitwiseNotOp)
        assert isinstance(expr.expr, AdditionOp)

    def test_not_parenthesized_shift(self):
        expr = _expr("~(a << b)")
        assert isinstance(expr, BitwiseNotOp)
        assert isinstance(expr.expr, BitwiseShiftLeftOp)

    def test_not_binds_tighter_than_bitwise_and(self):
        expr = _expr("~a & b")
        assert isinstance(expr, BitwiseAndOp)
        assert isinstance(expr.left, BitwiseNotOp)
        assert isinstance(expr.right, Identifier)

    def test_not_binds_tighter_than_bitwise_or(self):
        expr = _expr("~a | b")
        assert isinstance(expr, BitwiseOrOp)
        assert isinstance(expr.left, BitwiseNotOp)
        assert isinstance(expr.right, Identifier)

    def test_not_both_sides_of_and(self):
        expr = _expr("~a & ~b")
        assert isinstance(expr, BitwiseAndOp)
        assert isinstance(expr.left, BitwiseNotOp)
        assert isinstance(expr.right, BitwiseNotOp)

    def test_str_simple(self):
        expr = _expr("~x")
        assert str(expr) == "~x"

    def test_str_double(self):
        expr = _expr("~~x")
        assert str(expr) == "~~x"


# ===========================================================================
# Mixed NOT Operators AST
# ===========================================================================

class TestMixedNotOperatorsAST:
    def test_bitwise_not_of_logical_not(self):
        expr = _expr("~!x")
        assert isinstance(expr, BitwiseNotOp)
        assert isinstance(expr.expr, LogicalNotOp)
        assert isinstance(expr.expr.expr, Identifier)

    def test_logical_not_of_bitwise_not(self):
        expr = _expr("!~x")
        assert isinstance(expr, LogicalNotOp)
        assert isinstance(expr.expr, BitwiseNotOp)
        assert isinstance(expr.expr.expr, Identifier)

    def test_three_levels_of_nesting(self):
        expr = _expr("~!~x")
        assert isinstance(expr, BitwiseNotOp)
        assert isinstance(expr.expr, LogicalNotOp)
        assert isinstance(expr.expr.expr, BitwiseNotOp)
        assert isinstance(expr.expr.expr.expr, Identifier)
