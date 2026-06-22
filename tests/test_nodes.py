"""Tests for AST node __str__ representations by constructing nodes directly."""
import pytest
from openscad_lalr_parser import (
    ASTNode,
    Position,
    CommentLine,
    CommentSpan,
    Identifier,
    StringLiteral,
    NumberLiteral,
    BooleanLiteral,
    UndefinedLiteral,
    ParameterDeclaration,
    PositionalArgument,
    NamedArgument,
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
    RangeLiteral,
    VectorElement,
    ListCompLet,
    ListCompEach,
    ListCompFor,
    ListCompCFor,
    ListCompIf,
    ListCompIfElse,
    ListComprehension,
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


def _pos():
    return Position(origin="<test>", line=1, column=1)


def _ident(name):
    return Identifier(name=name, position=_pos())


def _num(val):
    return NumberLiteral(val=val, position=_pos())


def test_basic_literals_str():
    # CommentLine
    assert str(CommentLine(text=" hello", position=_pos())) == "// hello"

    # CommentSpan
    assert str(CommentSpan(text=" block ", position=_pos())) == "/* block */"

    # Identifier
    assert str(_ident("foo")) == "foo"

    # repr(Identifier)
    assert repr(_ident("foo")) == "Identifier('foo')"

    # StringLiteral
    assert str(StringLiteral(val="bar", position=_pos())) == '"bar"'

    # NumberLiteral
    assert str(_num(1.5)) == "1.5"
    assert str(_num(1.0)) == "1"
    assert str(_num(0.0)) == "0"

    # BooleanLiteral
    assert str(BooleanLiteral(val=True, position=_pos())) == "true"
    assert str(BooleanLiteral(val=False, position=_pos())) == "false"

    # UndefinedLiteral
    assert str(UndefinedLiteral(position=_pos())) == "undef"


def test_params_args_assignments_str():
    # ParameterDeclaration with default
    pd_with = ParameterDeclaration(
        name=_ident("x"), default=_num(1.0), position=_pos()
    )
    assert str(pd_with) == "x=1"

    # ParameterDeclaration without default
    pd_without = ParameterDeclaration(
        name=_ident("y"), default=None, position=_pos()
    )
    assert str(pd_without).strip() == "y"

    # PositionalArgument
    pa = PositionalArgument(expr=_num(3.0), position=_pos())
    assert str(pa) == "3"

    # NamedArgument
    na = NamedArgument(name=_ident("r"), expr=_num(5.0), position=_pos())
    assert str(na) == "r=5"

    # Assignment
    assign = Assignment(name=_ident("a"), expr=_num(10.0), position=_pos())
    assert str(assign) == "a = 10"

    # LetOp
    let_assign = Assignment(name=_ident("x"), expr=_num(1.0), position=_pos())
    let_op = LetOp(
        assignments=[let_assign], body=_ident("x"), position=_pos()
    )
    assert str(let_op) == "let(x = 1) x"

    # EchoOp
    echo_op = EchoOp(
        arguments=[PositionalArgument(expr=_num(1.0), position=_pos())],
        body=_num(2.0),
        position=_pos(),
    )
    assert str(echo_op) == "echo(1) 2"

    # AssertOp
    assert_op = AssertOp(
        arguments=[PositionalArgument(expr=BooleanLiteral(val=True, position=_pos()), position=_pos())],
        body=_num(3.0),
        position=_pos(),
    )
    assert str(assert_op) == "assert(true) 3"


def test_operator_str():
    left = _num(1.0)
    right = _num(2.0)

    # Unary
    assert str(UnaryMinusOp(expr=left, position=_pos())) == "-1"

    # Binary operators
    assert str(AdditionOp(left=left, right=right, position=_pos())) == "1 + 2"
    assert str(SubtractionOp(left=left, right=right, position=_pos())) == "1 - 2"
    assert str(MultiplicationOp(left=left, right=right, position=_pos())) == "1 * 2"
    assert str(DivisionOp(left=left, right=right, position=_pos())) == "1 / 2"
    assert str(ModuloOp(left=left, right=right, position=_pos())) == "1 % 2"
    assert str(ExponentOp(left=left, right=right, position=_pos())) == "1 ^ 2"

    # Bitwise operators
    assert str(BitwiseAndOp(left=left, right=right, position=_pos())) == "1 & 2"
    assert str(BitwiseOrOp(left=left, right=right, position=_pos())) == "1 | 2"
    assert str(BitwiseNotOp(expr=left, position=_pos())) == "~1"
    assert str(BitwiseShiftLeftOp(left=left, right=right, position=_pos())) == "1 << 2"
    assert str(BitwiseShiftRightOp(left=left, right=right, position=_pos())) == "1 >> 2"

    # Logical operators
    assert str(LogicalAndOp(left=left, right=right, position=_pos())) == "1 && 2"
    assert str(LogicalOrOp(left=left, right=right, position=_pos())) == "1 || 2"
    assert str(LogicalNotOp(expr=left, position=_pos())) == "!1"

    # Ternary
    cond = _num(1.0)
    t = _num(2.0)
    f = _num(3.0)
    assert str(TernaryOp(condition=cond, true_expr=t, false_expr=f, position=_pos())) == "1 ? 2 : 3"

    # Comparison operators
    assert str(EqualityOp(left=left, right=right, position=_pos())) == "1 == 2"
    assert str(InequalityOp(left=left, right=right, position=_pos())) == "1 != 2"
    assert str(GreaterThanOp(left=left, right=right, position=_pos())) == "1 > 2"
    assert str(GreaterThanOrEqualOp(left=left, right=right, position=_pos())) == "1 >= 2"
    assert str(LessThanOp(left=left, right=right, position=_pos())) == "1 < 2"
    assert str(LessThanOrEqualOp(left=left, right=right, position=_pos())) == "1 <= 2"


def test_primary_and_range_str():
    # FunctionLiteral
    param = ParameterDeclaration(name=_ident("x"), default=None, position=_pos())
    func_lit = FunctionLiteral(parameters=[param], body=_num(4.0), position=_pos())
    assert str(func_lit) == "function(x) 4"

    # PrimaryCall
    pc = PrimaryCall(
        left=_ident("foo"),
        arguments=[PositionalArgument(expr=_num(3.0), position=_pos())],
        position=_pos(),
    )
    assert str(pc) == "foo(3)"

    # PrimaryIndex
    pi = PrimaryIndex(left=_ident("arr"), index=_num(1.0), position=_pos())
    assert str(pi) == "arr[1]"

    # PrimaryMember
    pm = PrimaryMember(left=_ident("obj"), member=_ident("x"), position=_pos())
    assert str(pm) == "obj.x"

    # RangeLiteral
    rl = RangeLiteral(
        start=_num(0.0), end=_num(5.0), step=_num(1.0), position=_pos()
    )
    assert str(rl) == "[0 : 1 : 5]"


def test_list_comprehension_str():
    # ListCompLet
    lc_let = ListCompLet(
        assignments=[Assignment(name=_ident("x"), expr=_num(1.0), position=_pos())],
        body=ListCompIf(
            condition=_ident("x"),
            true_expr=ListCompIf(condition=_ident("x"), true_expr=ListCompEach(body=ListCompFor(
                assignments=[Assignment(name=_ident("i"), expr=_ident("x"), position=_pos())],
                body=ListCompIf(condition=_ident("i"), true_expr=ListCompEach(body=ListCompFor(
                    assignments=[], body=ListCompIf(condition=_num(1.0), true_expr=ListCompEach(body=ListCompFor(
                        assignments=[], body=ListCompIf(condition=_num(1.0), true_expr=_num(0.0), position=_pos()),
                        position=_pos()
                    ), position=_pos()), position=_pos()),
                    position=_pos()
                ), position=_pos()), position=_pos()),
                position=_pos()
            ), position=_pos()), position=_pos()),
            position=_pos()
        ),
        position=_pos(),
    )
    assert "let" in str(lc_let)

    # ListCompEach
    lc_each = ListCompEach(body=_num(1.0), position=_pos())
    assert str(lc_each) == "each 1"

    # ListCompFor
    lc_for = ListCompFor(
        assignments=[Assignment(name=_ident("i"), expr=_ident("list"), position=_pos())],
        body=_ident("i"),
        position=_pos(),
    )
    assert str(lc_for) == "for (i = list) i"

    # ListCompCFor
    lc_cfor = ListCompCFor(
        inits=[Assignment(name=_ident("i"), expr=_num(0.0), position=_pos())],
        condition=LessThanOp(left=_ident("i"), right=_num(10.0), position=_pos()),
        incrs=[Assignment(name=_ident("i"), expr=AdditionOp(left=_ident("i"), right=_num(1.0), position=_pos()), position=_pos())],
        body=_ident("i"),
        position=_pos(),
    )
    assert str(lc_cfor) == "for (i = 0; i < 10; i = i + 1) i"

    # ListCompIf
    lc_if = ListCompIf(
        condition=_num(1.0), true_expr=_num(5.0), position=_pos()
    )
    assert str(lc_if) == "if (1) 5"

    # ListCompIfElse
    lc_ifelse = ListCompIfElse(
        condition=_num(1.0),
        true_expr=_num(6.0),
        false_expr=_num(7.0),
        position=_pos(),
    )
    assert str(lc_ifelse) == "if (1) 6 else 7"

    # ListComprehension wrapping ListCompIf
    lc = ListComprehension(
        elements=[ListCompIf(condition=_num(1.0), true_expr=_num(5.0), position=_pos())],
        position=_pos(),
    )
    assert str(lc) == "[if (1) 5]"


def _cube_call():
    """Helper to create a simple cube(1) ModularCall."""
    return ModularCall(
        name=_ident("cube"),
        arguments=[PositionalArgument(expr=_num(1.0), position=_pos())],
        children=[],
        position=_pos(),
    )


def test_modular_and_declaration_str():
    cube = _cube_call()

    # ModularCall
    assert str(cube) == "cube(1)"

    # ModularFor
    mfor = ModularFor(
        assignments=[Assignment(name=_ident("i"), expr=_ident("list"), position=_pos())],
        body=cube,
        position=_pos(),
    )
    assert str(mfor) == "for (i = list) cube(1)"

    # ModularIntersectionFor
    mifor = ModularIntersectionFor(
        assignments=[Assignment(name=_ident("i"), expr=_ident("list"), position=_pos())],
        body=cube,
        position=_pos(),
    )
    assert str(mifor) == "intersection_for (i = list) cube(1)"

    # ModularLet
    mlet = ModularLet(
        assignments=[Assignment(name=_ident("x"), expr=_num(1.0), position=_pos())],
        children=[cube],
        position=_pos(),
    )
    assert str(mlet) == "let (x = 1) cube(1)"

    # ModularEcho
    mecho = ModularEcho(
        arguments=[PositionalArgument(expr=_num(1.0), position=_pos())],
        children=[cube],
        position=_pos(),
    )
    assert str(mecho) == "echo(1) cube(1)"

    # ModularAssert
    massert = ModularAssert(
        arguments=[PositionalArgument(expr=BooleanLiteral(val=True, position=_pos()), position=_pos())],
        children=[cube],
        position=_pos(),
    )
    assert str(massert) == "assert(true) cube(1)"

    # ModularIf
    mif = ModularIf(condition=_num(1.0), true_branch=cube, position=_pos())
    assert str(mif) == "if (1) cube(1)"

    # ModularIfElse
    mifelse = ModularIfElse(
        condition=_num(1.0),
        true_branch=cube,
        false_branch=_cube_call(),
        position=_pos(),
    )
    assert str(mifelse) == "if (1) cube(1) else cube(1)"

    # Modifiers
    assert str(ModularModifierShowOnly(child=cube, position=_pos())) == "!cube(1)"
    assert str(ModularModifierHighlight(child=cube, position=_pos())) == "#cube(1)"
    assert str(ModularModifierBackground(child=cube, position=_pos())) == "%cube(1)"
    assert str(ModularModifierDisable(child=cube, position=_pos())) == "*cube(1)"

    # ModuleDeclaration
    mod_decl = ModuleDeclaration(
        name=_ident("m"),
        parameters=[],
        children=[cube],
        position=_pos(),
    )
    assert str(mod_decl) == "module m() { cube(1) }"

    # FunctionDeclaration
    func_decl = FunctionDeclaration(
        name=_ident("f"),
        parameters=[],
        expr=_num(2.0),
        position=_pos(),
    )
    assert str(func_decl) == "function f() = 2;"

    # UseStatement
    use = UseStatement(
        filepath=StringLiteral(val="lib.scad", position=_pos()),
        position=_pos(),
    )
    assert str(use) == "use <lib.scad>"

    # IncludeStatement
    inc = IncludeStatement(
        filepath=StringLiteral(val="lib.scad", position=_pos()),
        position=_pos(),
    )
    assert str(inc) == "include <lib.scad>"


def test_astnode_str_raises_not_implemented():
    node = ASTNode(position=_pos())
    with pytest.raises(NotImplementedError):
        str(node)


def test_vector_element_str_raises_not_implemented():
    ve = VectorElement(position=_pos())
    with pytest.raises(NotImplementedError):
        str(ve)
