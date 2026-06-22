"""Lark Transformer that converts parse trees into AST nodes."""
from __future__ import annotations

from lark import Transformer, v_args, Token, Tree

from .nodes import (
    Position,
    ASTNode,
    Identifier,
    StringLiteral,
    NumberLiteral,
    BooleanLiteral,
    UndefinedLiteral,
    ParameterDeclaration,
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
    Expression,
    Argument,
)


def _pos(meta, origin: str = "<string>") -> Position:
    """Create a Position from Lark's tree meta info."""
    line = getattr(meta, 'line', 1) or 1
    column = getattr(meta, 'column', 1) or 1
    start = getattr(meta, 'start_pos', 0) or 0
    end = getattr(meta, 'end_pos', 0) or 0
    return Position(
        origin=origin,
        line=line,
        column=column,
        start_offset=start,
        end_offset=end,
    )


def _token_pos(token: Token, origin: str = "<string>") -> Position:
    """Create a Position from a Lark Token."""
    return Position(
        origin=origin,
        line=token.line or 1,
        column=token.column or 1,
        start_offset=token.start_pos or 0,
        end_offset=token.end_pos or 0,
    )


@v_args(meta=True)
class OpenSCADTransformer(Transformer):
    """Transforms a Lark parse tree into OpenSCAD AST nodes."""

    def __init__(self, origin: str = "<string>"):
        super().__init__()
        self.origin = origin

    def _pos(self, meta) -> Position:
        return _pos(meta, self.origin)

    def _tpos(self, token: Token) -> Position:
        return _token_pos(token, self.origin)

    # --- Terminals ---

    def NAME(self, token: Token) -> Identifier:
        return Identifier(name=str(token), position=self._tpos(token))

    def NUMBER(self, token: Token) -> NumberLiteral:
        text = str(token)
        if text.startswith('0x') or text.startswith('0X'):
            val = float(int(text, 16))
        else:
            val = float(text)
        return NumberLiteral(val=val, position=self._tpos(token))

    def STRING(self, token: Token) -> StringLiteral:
        raw = str(token)
        val = raw[1:-1] if raw.startswith('"') and raw.endswith('"') else raw
        return StringLiteral(val=val, position=self._tpos(token))

    def USE_INCLUDE_FILE(self, token: Token) -> str:
        raw = str(token)
        return raw[1:-1] if raw.startswith('<') and raw.endswith('>') else raw

    # --- Literals ---

    def true_literal(self, meta, children):
        return BooleanLiteral(val=True, position=self._pos(meta))

    def false_literal(self, meta, children):
        return BooleanLiteral(val=False, position=self._pos(meta))

    def undef_literal(self, meta, children):
        return UndefinedLiteral(position=self._pos(meta))

    # --- Use / Include ---

    def use_statement(self, meta, children):
        filepath = children[0]
        if isinstance(filepath, str):
            filepath = StringLiteral(val=filepath, position=self._pos(meta))
        return UseStatement(filepath=filepath, position=self._pos(meta))

    def include_statement(self, meta, children):
        filepath = children[0]
        if isinstance(filepath, str):
            filepath = StringLiteral(val=filepath, position=self._pos(meta))
        return IncludeStatement(filepath=filepath, position=self._pos(meta))

    # --- Top-level ---

    def start(self, meta, children):
        return [c for c in children if c is not None]

    def toplevel_statement(self, meta, children):
        return children[0]

    # --- Statements ---

    def statement(self, meta, children):
        if not children:
            return None
        result = children[0]
        if isinstance(result, list):
            return result
        return result

    def empty_statement(self, meta, children):
        return []

    def statement_block(self, meta, children):
        result = []
        for c in children:
            if isinstance(c, list):
                result.extend(c)
            elif c is not None:
                result.append(c)
        return result

    # --- Parameters ---

    def parameter_block(self, meta, children):
        return children[0] if children else []

    def parameters(self, meta, children):
        return [c for c in children if isinstance(c, ParameterDeclaration)]

    def parameter(self, meta, children):
        return children[0]

    def parameter_with_default(self, meta, children):
        name = children[0]
        default = children[1] if len(children) > 1 else None
        return ParameterDeclaration(name=name, default=default, position=self._pos(meta))

    def parameter_without_default(self, meta, children):
        name = children[0]
        return ParameterDeclaration(name=name, default=None, position=self._pos(meta))

    # --- Arguments ---

    def argument_block(self, meta, children):
        return children[0] if children else []

    def arguments(self, meta, children):
        return [c for c in children if isinstance(c, Argument)]

    def argument(self, meta, children):
        return children[0]

    def positional_argument(self, meta, children):
        return PositionalArgument(expr=children[0], position=self._pos(meta))

    def named_argument(self, meta, children):
        name = children[0]
        expr = children[1]
        return NamedArgument(name=name, expr=expr, position=self._pos(meta))

    # --- Module / Function Definitions ---

    def module_definition(self, meta, children):
        name = children[0]
        parameters = children[1] if len(children) > 1 and isinstance(children[1], list) else []
        body = children[2] if len(children) > 2 else children[-1]
        if not isinstance(body, list):
            body = [body] if body is not None else []
        flattened = []
        for item in body:
            if isinstance(item, list):
                flattened.extend(item)
            elif item is not None:
                flattened.append(item)
        return ModuleDeclaration(
            name=name,
            parameters=parameters,
            children=flattened,
            position=self._pos(meta),
        )

    def function_definition(self, meta, children):
        name = children[0]
        parameters = children[1] if len(children) > 1 and isinstance(children[1], list) else []
        expr = children[-1]
        return FunctionDeclaration(
            name=name,
            parameters=parameters,
            expr=expr,
            position=self._pos(meta),
        )

    # --- Assignments ---

    def assignment(self, meta, children):
        return Assignment(name=children[0], expr=children[1], position=self._pos(meta))

    def assignment_expr(self, meta, children):
        return Assignment(name=children[0], expr=children[1], position=self._pos(meta))

    def assignments_expr(self, meta, children):
        return [c for c in children if isinstance(c, Assignment)]

    # --- Module Instantiation ---

    def module_instantiation(self, meta, children):
        return children[0]

    def single_module_instantiation(self, meta, children):
        return children[0]

    def child_statement(self, meta, children):
        result = []
        for c in children:
            if isinstance(c, list):
                result.extend(c)
            elif c is not None:
                result.append(c)
        return result

    def modifier_show_only(self, meta, children):
        return ModularModifierShowOnly(child=children[0], position=self._pos(meta))

    def modifier_highlight(self, meta, children):
        return ModularModifierHighlight(child=children[0], position=self._pos(meta))

    def modifier_background(self, meta, children):
        return ModularModifierBackground(child=children[0], position=self._pos(meta))

    def modifier_disable(self, meta, children):
        return ModularModifierDisable(child=children[0], position=self._pos(meta))

    def if_statement(self, meta, children):
        condition = children[0]
        true_branch = children[1]
        return ModularIf(condition=condition, true_branch=true_branch, position=self._pos(meta))

    def ifelse_statement(self, meta, children):
        condition = children[0]
        true_branch = children[1]
        false_branch = children[2]
        return ModularIfElse(
            condition=condition,
            true_branch=true_branch,
            false_branch=false_branch,
            position=self._pos(meta),
        )

    def modular_for(self, meta, children):
        assignments = children[0] if isinstance(children[0], list) else [children[0]]
        assignments = [a for a in assignments if isinstance(a, Assignment)]
        body = children[1]
        return ModularFor(assignments=assignments, body=body, position=self._pos(meta))

    def modular_intersection_for(self, meta, children):
        assignments = children[0] if isinstance(children[0], list) else [children[0]]
        assignments = [a for a in assignments if isinstance(a, Assignment)]
        body = children[1]
        return ModularIntersectionFor(assignments=assignments, body=body, position=self._pos(meta))

    def modular_let(self, meta, children):
        assignments = children[0] if isinstance(children[0], list) else [children[0]]
        assignments = [a for a in assignments if isinstance(a, Assignment)]
        body = children[1]
        if not isinstance(body, list):
            body = [body] if body is not None else []
        return ModularLet(assignments=assignments, children=body, position=self._pos(meta))

    def modular_assert(self, meta, children):
        arguments = children[0] if isinstance(children[0], list) else [children[0]]
        arguments = [a for a in arguments if isinstance(a, Argument)]
        body = children[1]
        if not isinstance(body, list):
            body = [body] if body is not None else []
        return ModularAssert(arguments=arguments, children=body, position=self._pos(meta))

    def modular_echo(self, meta, children):
        arguments = children[0] if isinstance(children[0], list) else [children[0]]
        arguments = [a for a in arguments if isinstance(a, Argument)]
        body = children[1]
        if not isinstance(body, list):
            body = [body] if body is not None else []
        return ModularEcho(arguments=arguments, children=body, position=self._pos(meta))

    def modular_call(self, meta, children):
        name = children[0]
        arguments = children[1] if len(children) > 1 and isinstance(children[1], list) else []
        arguments = [a for a in arguments if isinstance(a, Argument)]
        body = children[2] if len(children) > 2 else []
        if not isinstance(body, list):
            body = [body] if body is not None else []
        return ModularCall(
            name=name,
            arguments=arguments,
            children=body,
            position=self._pos(meta),
        )

    # --- Expressions ---

    def let_expr(self, meta, children):
        assignments = children[0] if isinstance(children[0], list) else [children[0]]
        assignments = [a for a in assignments if isinstance(a, Assignment)]
        body = children[1] if len(children) > 1 else UndefinedLiteral(position=self._pos(meta))
        return LetOp(assignments=assignments, body=body, position=self._pos(meta))

    def assert_expr(self, meta, children):
        arguments = children[0] if isinstance(children[0], list) else [children[0]]
        arguments = [a for a in arguments if isinstance(a, Argument)]
        body = children[1] if len(children) > 1 and isinstance(children[1], Expression) else UndefinedLiteral(position=self._pos(meta))
        return AssertOp(arguments=arguments, body=body, position=self._pos(meta))

    def echo_expr(self, meta, children):
        arguments = children[0] if isinstance(children[0], list) else [children[0]]
        arguments = [a for a in arguments if isinstance(a, Argument)]
        body = children[1] if len(children) > 1 and isinstance(children[1], Expression) else UndefinedLiteral(position=self._pos(meta))
        return EchoOp(arguments=arguments, body=body, position=self._pos(meta))

    def funclit_def(self, meta, children):
        parameters = children[0] if isinstance(children[0], list) else []
        parameters = [p for p in parameters if isinstance(p, ParameterDeclaration)]
        body = children[-1]
        return FunctionLiteral(parameters=parameters, body=body, position=self._pos(meta))

    def ternary_expr(self, meta, children):
        return TernaryOp(
            condition=children[0],
            true_expr=children[1],
            false_expr=children[2],
            position=self._pos(meta),
        )

    # --- Binary Operators ---

    def logical_or_op(self, meta, children):
        return LogicalOrOp(left=children[0], right=children[1], position=self._pos(meta))

    def logical_and_op(self, meta, children):
        return LogicalAndOp(left=children[0], right=children[1], position=self._pos(meta))

    def equality_op(self, meta, children):
        return EqualityOp(left=children[0], right=children[1], position=self._pos(meta))

    def inequality_op(self, meta, children):
        return InequalityOp(left=children[0], right=children[1], position=self._pos(meta))

    def less_than_op(self, meta, children):
        return LessThanOp(left=children[0], right=children[1], position=self._pos(meta))

    def greater_than_op(self, meta, children):
        return GreaterThanOp(left=children[0], right=children[1], position=self._pos(meta))

    def less_than_or_equal_op(self, meta, children):
        return LessThanOrEqualOp(left=children[0], right=children[1], position=self._pos(meta))

    def greater_than_or_equal_op(self, meta, children):
        return GreaterThanOrEqualOp(left=children[0], right=children[1], position=self._pos(meta))

    def bitwise_or_op(self, meta, children):
        return BitwiseOrOp(left=children[0], right=children[1], position=self._pos(meta))

    def bitwise_and_op(self, meta, children):
        return BitwiseAndOp(left=children[0], right=children[1], position=self._pos(meta))

    def bitwise_shift_left_op(self, meta, children):
        return BitwiseShiftLeftOp(left=children[0], right=children[1], position=self._pos(meta))

    def bitwise_shift_right_op(self, meta, children):
        return BitwiseShiftRightOp(left=children[0], right=children[1], position=self._pos(meta))

    def addition_op(self, meta, children):
        return AdditionOp(left=children[0], right=children[1], position=self._pos(meta))

    def subtraction_op(self, meta, children):
        return SubtractionOp(left=children[0], right=children[1], position=self._pos(meta))

    def multiplication_op(self, meta, children):
        return MultiplicationOp(left=children[0], right=children[1], position=self._pos(meta))

    def division_op(self, meta, children):
        return DivisionOp(left=children[0], right=children[1], position=self._pos(meta))

    def modulo_op(self, meta, children):
        return ModuloOp(left=children[0], right=children[1], position=self._pos(meta))

    # --- Unary Operators ---

    def unary_minus_op(self, meta, children):
        return UnaryMinusOp(expr=children[0], position=self._pos(meta))

    def logical_not_op(self, meta, children):
        return LogicalNotOp(expr=children[0], position=self._pos(meta))

    def bitwise_not_op(self, meta, children):
        return BitwiseNotOp(expr=children[0], position=self._pos(meta))

    def unary_plus_op(self, meta, children):
        return children[0]

    def exponent_op(self, meta, children):
        return ExponentOp(left=children[0], right=children[1], position=self._pos(meta))

    # --- Postfix ---

    def call_expr(self, meta, children):
        left = children[0]
        arguments = children[1] if len(children) > 1 and isinstance(children[1], list) else []
        arguments = [a for a in arguments if isinstance(a, Argument)]
        return PrimaryCall(left=left, arguments=arguments, position=self._pos(meta))

    def index_expr(self, meta, children):
        return PrimaryIndex(left=children[0], index=children[1], position=self._pos(meta))

    def member_expr(self, meta, children):
        return PrimaryMember(left=children[0], member=children[1], position=self._pos(meta))

    def paren_expr(self, meta, children):
        return children[0]

    # --- Range and Vector ---

    def range_expr(self, meta, children):
        start = children[0]
        if len(children) == 3:
            step = children[1]
            end = children[2]
        else:
            end = children[1]
            step = NumberLiteral(val=1.0, position=self._pos(meta))
        return RangeLiteral(start=start, end=end, step=step, position=self._pos(meta))

    def vector_expr(self, meta, children):
        if children and isinstance(children[0], list):
            elements = children[0]
        else:
            elements = []
        return ListComprehension(elements=elements, position=self._pos(meta))

    def vector_elements(self, meta, children):
        return list(children)

    # --- List Comprehensions ---

    def listcomp_paren_expr(self, meta, children):
        return children[0]

    def listcomp_let(self, meta, children):
        assignments = children[0] if isinstance(children[0], list) else [children[0]]
        assignments = [a for a in assignments if isinstance(a, Assignment)]
        body = children[-1]
        return ListCompLet(assignments=assignments, body=body, position=self._pos(meta))

    def listcomp_each(self, meta, children):
        return ListCompEach(body=children[0], position=self._pos(meta))

    def listcomp_for(self, meta, children):
        assignments = children[0] if isinstance(children[0], list) else [children[0]]
        assignments = [a for a in assignments if isinstance(a, Assignment)]
        body = children[-1]
        return ListCompFor(assignments=assignments, body=body, position=self._pos(meta))

    def listcomp_c_for(self, meta, children):
        inits = children[0] if isinstance(children[0], list) else [children[0]]
        inits = [a for a in inits if isinstance(a, Assignment)]
        condition = children[1]
        incrs = children[2] if isinstance(children[2], list) else [children[2]]
        incrs = [a for a in incrs if isinstance(a, Assignment)]
        body = children[-1]
        return ListCompCFor(
            inits=inits,
            condition=condition,
            incrs=incrs,
            body=body,
            position=self._pos(meta),
        )

    def listcomp_ifonly(self, meta, children):
        return ListCompIf(condition=children[0], true_expr=children[1], position=self._pos(meta))

    def listcomp_ifelse(self, meta, children):
        return ListCompIfElse(
            condition=children[0],
            true_expr=children[1],
            false_expr=children[2],
            position=self._pos(meta),
        )
