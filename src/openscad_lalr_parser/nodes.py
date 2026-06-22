from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .scope import Scope


@dataclass
class Position:
    """Represents a location in a source origin.

    Attributes:
        origin: Identifier for the source origin (e.g., file path, "<editor>", etc.)
        line: Line number (1-indexed)
        column: Column number (1-indexed)
        start_offset: 0-based character offset of the token start within the origin's content
        end_offset: 0-based character offset one past the token end within the origin's content
    """
    origin: str
    line: int
    column: int
    start_offset: int = 0
    end_offset: int = 0

    def __repr__(self):
        return f"{self.origin}:{self.line}:{self.column}[{self.start_offset}:{self.end_offset}]"


# --- AST nodes classes. ---

@dataclass
class ASTNode(object):
    """Base class for all AST nodes.

    All AST nodes in the OpenSCAD parser inherit from this class. It provides
    a common interface for source position tracking and string representation.

    Attributes:
        position: The source position of this node in the original OpenSCAD code.
        scope: The lexical scope at this node's location, populated by build_scope().
            This attribute is set dynamically after AST construction and may be None
            if build_scope() has not been called. Access via node.scope.
    """
    position: "Position"
    scope: "Scope | None" = field(default=None, kw_only=True)

    def __str__(self) -> str:
        """Return a string representation of the AST node."""
        raise NotImplementedError

    def build_scope(self, parent_scope: "Scope") -> None:
        """Assign parent_scope to this node. Leaf nodes use this default."""
        self.scope = parent_scope


@dataclass
class CommentLine(ASTNode):
    """Represents a single-line OpenSCAD comment.

    Single-line comments in OpenSCAD start with // and continue to the end of the line.

    Attributes:
        text: The comment text without the leading // marker.
    """
    text: str

    def __str__(self):
        return f"//{self.text}"


@dataclass
class BlankLine(ASTNode):
    """A preserved blank line between consecutive single-line comment blocks."""

    def __str__(self):
        return ""

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope


@dataclass
class CommentSpan(ASTNode):
    """Represents a multi-line OpenSCAD comment span.

    Multi-line comments in OpenSCAD are enclosed between /* and */.

    Attributes:
        text: The comment text without the /* and */ markers.
    """
    text: str

    def __str__(self):
        return f"/*{self.text}*/"


@dataclass
class Expression(ASTNode):
    """Base class for all OpenSCAD expressions.

    Expressions are constructs that evaluate to a value. This includes:
    - Literals (numbers, strings, booleans)
    - Operators (arithmetic, logical, comparison, etc.)
    - Function calls
    - Variable references
    - Complex expressions combining the above

    All expression nodes in the AST inherit from this class.
    """
    pass


@dataclass
class CommentedExpr(Expression):
    """An expression preceded and/or followed by inline block comments.

    Produced when include_comments=True and /* */ appears adjacent to a
    sub-expression (argument value, vector element, ternary arm, etc.).

    Attributes:
        leading_comments: Block comments before the expression, in source order.
        trailing_comments: Block comments after the expression, in source order.
        expr: The wrapped expression.
    """
    leading_comments: list["CommentSpan | CommentLine"]
    trailing_comments: list["CommentSpan | CommentLine"]
    expr: Expression

    def __str__(self):
        parts = [str(c) for c in self.leading_comments]
        parts.append(str(self.expr))
        parts.extend(str(c) for c in self.trailing_comments)
        return " ".join(parts)

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        for c in self.leading_comments:
            c.build_scope(parent_scope)
        for c in self.trailing_comments:
            c.build_scope(parent_scope)
        self.expr.build_scope(parent_scope)


@dataclass
class Primary(Expression):
    """Base class for all OpenSCAD primary (atomic) value types.

    Primary expressions are the most basic expressions that cannot be further
    decomposed. This includes literals and identifiers.
    """
    pass


@dataclass
class Identifier(Primary):
    """Represents an OpenSCAD identifier (variable or function name).

    Attributes:
        name: The identifier name as a string.
    """
    name: str

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Identifier('{self.name}')"


@dataclass
class StringLiteral(Primary):
    """Represents an OpenSCAD string literal.

    Attributes:
        val: The string value without the surrounding quotes.
    """
    val: str

    def __str__(self):
        return f'"{self.val}"'


@dataclass
class NumberLiteral(Primary):
    """Represents an OpenSCAD numeric literal.

    Attributes:
        val: The numeric value as a float.
    """
    val: float

    def __str__(self):
        s = str(self.val)
        if 'e' not in s and s.endswith('.0'):
            return s[:-2]
        return s


@dataclass
class BooleanLiteral(Primary):
    """Represents an OpenSCAD boolean literal.

    Attributes:
        val: The boolean value (True or False).
    """
    val: bool

    def __str__(self):
        return "true" if self.val else "false"


@dataclass
class UndefinedLiteral(Primary):
    """Represents an OpenSCAD undefined literal (undef)."""

    def __str__(self):
        return "undef"


@dataclass
class ParameterDeclaration(ASTNode):
    """Represents a parameter declaration in a function or module definition.

    Attributes:
        name: The parameter name as an Identifier.
        default: The default value expression, or None if no default is provided.
        leading_comments: Comments appearing before the parameter name.
        trailing_comments: Comments appearing after the parameter name (before = or ,/).
    """
    name: Identifier
    default: Expression|None
    leading_comments: list["CommentSpan"] = field(default_factory=list)
    trailing_comments: list["CommentSpan"] = field(default_factory=list)

    def __str__(self):
        has_default = self.default is not None and not isinstance(self.default, UndefinedLiteral)
        return f"{self.name}{f'={self.default}' if has_default else ''}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        for c in self.leading_comments:
            c.build_scope(parent_scope)
        self.name.build_scope(parent_scope)
        for c in self.trailing_comments:
            c.build_scope(parent_scope)
        if self.default:
            caller_scope = parent_scope.parent if parent_scope.parent else parent_scope
            self.default.build_scope(caller_scope)


@dataclass
class Argument(ASTNode):
    """Base class for function and module call arguments."""
    pass


@dataclass
class PositionalArgument(Argument):
    """Represents a positional argument in a function or module call.

    Attributes:
        expr: The expression value of the argument.
    """
    expr: Expression

    def __str__(self):
        return f"{self.expr}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.expr.build_scope(parent_scope)


@dataclass
class NamedArgument(Argument):
    """Represents a named argument in a function or module call.

    Attributes:
        name: The parameter name as an Identifier.
        expr: The expression value of the argument.
    """
    name: Identifier
    expr: Expression

    def __str__(self):
        return f"{self.name}={self.expr}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.name.build_scope(parent_scope)
        self.expr.build_scope(parent_scope)


@dataclass
class RangeLiteral(Primary):
    """Represents an OpenSCAD range literal.

    Attributes:
        start: The starting value of the range.
        end: The ending value of the range.
        step: The step size between values.
    """
    start: Expression
    end: Expression
    step: Expression

    def __str__(self):
        return f"[{self.start} : {self.step} : {self.end}]"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.start.build_scope(parent_scope)
        self.end.build_scope(parent_scope)
        self.step.build_scope(parent_scope)


@dataclass
class Assignment(ASTNode):
    """Represents a variable assignment in OpenSCAD.

    Attributes:
        name: The variable name as an Identifier.
        expr: The expression value being assigned.
    """
    name: Identifier
    expr: Expression

    def __str__(self):
        return f"{self.name} = {self.expr}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.name.build_scope(parent_scope)
        self.expr.build_scope(parent_scope)


@dataclass
class LetOp(Expression):
    """Represents an OpenSCAD let expression.

    Attributes:
        assignments: List of variable assignments local to this expression.
        body: The expression that uses the assigned variables.
    """
    assignments: list[Assignment]
    body: Expression

    def __str__(self):
        return f"let({', '.join(str(assignment) for assignment in self.assignments)}) {self.body}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        let_scope = parent_scope.child_scope()
        for assignment in self.assignments:
            let_scope.define_variable(assignment.name.name, assignment)
            assignment.build_scope(let_scope)
        self.body.build_scope(let_scope)


@dataclass
class EchoOp(Expression):
    """Represents an OpenSCAD echo expression.

    Attributes:
        arguments: List of arguments to print (can be positional or named).
        body: The expression to evaluate and return.
    """
    arguments: list[Argument]
    body: Expression

    def __str__(self):
        args = ', '.join(str(arg) for arg in self.arguments)
        if isinstance(self.body, UndefinedLiteral):
            return f"echo({args})"
        return f"echo({args}) {self.body}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        for arg in self.arguments:
            arg.build_scope(parent_scope)
        self.body.build_scope(parent_scope)


@dataclass
class AssertOp(Expression):
    """Represents an OpenSCAD assert expression.

    Attributes:
        arguments: List of arguments (typically condition and optional message).
        body: The expression to return if assertion passes.
    """
    arguments: list[Argument]
    body: Expression

    def __str__(self):
        args = ', '.join(str(arg) for arg in self.arguments)
        if isinstance(self.body, UndefinedLiteral):
            return f"assert({args})"
        return f"assert({args}) {self.body}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        for arg in self.arguments:
            arg.build_scope(parent_scope)
        self.body.build_scope(parent_scope)


@dataclass
class UnaryMinusOp(Expression):
    """Represents an OpenSCAD unary minus (negation) operation.

    Attributes:
        expr: The expression to negate.
    """
    expr: Expression

    def __str__(self):
        return f"-{_lp(self.expr, _prec(self))}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.expr.build_scope(parent_scope)


@dataclass
class AdditionOp(Expression):
    """Represents an OpenSCAD addition operation.

    Attributes:
        left: The left operand expression.
        right: The right operand expression.
    """
    left: Expression
    right: Expression

    def __str__(self):
        p = _prec(self)
        return f"{_lp(self.left, p)} + {_rp(self.right, p)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.right.build_scope(parent_scope)


@dataclass
class SubtractionOp(Expression):
    """Represents an OpenSCAD subtraction operation.

    Attributes:
        left: The left operand expression.
        right: The right operand expression.
    """
    left: Expression
    right: Expression

    def __str__(self):
        p = _prec(self)
        return f"{_lp(self.left, p)} - {_rp(self.right, p)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.right.build_scope(parent_scope)


@dataclass
class MultiplicationOp(Expression):
    """Represents an OpenSCAD multiplication operation.

    Attributes:
        left: The left operand expression.
        right: The right operand expression.
    """
    left: Expression
    right: Expression

    def __str__(self):
        p = _prec(self)
        return f"{_lp(self.left, p)} * {_rp(self.right, p)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.right.build_scope(parent_scope)


@dataclass
class DivisionOp(Expression):
    """Represents an OpenSCAD division operation.

    Attributes:
        left: The left operand expression.
        right: The right operand expression.
    """
    left: Expression
    right: Expression

    def __str__(self):
        p = _prec(self)
        return f"{_lp(self.left, p)} / {_rp(self.right, p)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.right.build_scope(parent_scope)


@dataclass
class ModuloOp(Expression):
    """Represents an OpenSCAD modulo (remainder) operation.

    Attributes:
        left: The left operand expression.
        right: The right operand expression.
    """
    left: Expression
    right: Expression

    def __str__(self):
        p = _prec(self)
        return f"{_lp(self.left, p)} % {_rp(self.right, p)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.right.build_scope(parent_scope)


@dataclass
class ExponentOp(Expression):
    """Represents an OpenSCAD exponentiation operation.

    Attributes:
        left: The base expression.
        right: The exponent expression.
    """
    left: Expression
    right: Expression

    def __str__(self):
        p = _prec(self)
        return f"{_rp(self.left, p)} ^ {_lp(self.right, p)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.right.build_scope(parent_scope)


@dataclass
class BitwiseAndOp(Expression):
    """Represents an OpenSCAD bitwise AND operation.

    Attributes:
        left: The left operand expression.
        right: The right operand expression.
    """
    left: Expression
    right: Expression

    def __str__(self):
        p = _prec(self)
        return f"{_lp(self.left, p)} & {_rp(self.right, p)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.right.build_scope(parent_scope)


@dataclass
class BitwiseOrOp(Expression):
    """Represents an OpenSCAD bitwise OR operation.

    Attributes:
        left: The left operand expression.
        right: The right operand expression.
    """
    left: Expression
    right: Expression

    def __str__(self):
        p = _prec(self)
        return f"{_lp(self.left, p)} | {_rp(self.right, p)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.right.build_scope(parent_scope)


@dataclass
class BitwiseNotOp(Expression):
    """Represents an OpenSCAD bitwise NOT (complement) operation.

    Attributes:
        expr: The expression to complement.
    """
    expr: Expression

    def __str__(self):
        return f"~{_lp(self.expr, _prec(self))}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.expr.build_scope(parent_scope)


@dataclass
class BitwiseShiftLeftOp(Expression):
    """Represents an OpenSCAD bitwise left shift operation.

    Attributes:
        left: The value to shift.
        right: The number of bits to shift left.
    """
    left: Expression
    right: Expression

    def __str__(self):
        p = _prec(self)
        return f"{_lp(self.left, p)} << {_rp(self.right, p)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.right.build_scope(parent_scope)


@dataclass
class BitwiseShiftRightOp(Expression):
    """Represents an OpenSCAD bitwise right shift operation.

    Attributes:
        left: The value to shift.
        right: The number of bits to shift right.
    """
    left: Expression
    right: Expression

    def __str__(self):
        p = _prec(self)
        return f"{_lp(self.left, p)} >> {_rp(self.right, p)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.right.build_scope(parent_scope)


@dataclass
class LogicalAndOp(Expression):
    """Represents an OpenSCAD logical AND operation.

    Attributes:
        left: The left operand expression.
        right: The right operand expression.
    """
    left: Expression
    right: Expression

    def __str__(self):
        p = _prec(self)
        return f"{_lp(self.left, p)} && {_rp(self.right, p)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.right.build_scope(parent_scope)


@dataclass
class LogicalOrOp(Expression):
    """Represents an OpenSCAD logical OR operation.

    Attributes:
        left: The left operand expression.
        right: The right operand expression.
    """
    left: Expression
    right: Expression

    def __str__(self):
        p = _prec(self)
        return f"{_lp(self.left, p)} || {_rp(self.right, p)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.right.build_scope(parent_scope)


@dataclass
class LogicalNotOp(Expression):
    """Represents an OpenSCAD logical NOT operation.

    Attributes:
        expr: The expression to negate.
    """
    expr: Expression

    def __str__(self):
        return f"!{_lp(self.expr, _prec(self))}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.expr.build_scope(parent_scope)


@dataclass
class TernaryOp(Expression):
    """Represents an OpenSCAD ternary (conditional) expression.

    Attributes:
        condition: The boolean condition to evaluate.
        true_expr: Expression to return if condition is true.
        false_expr: Expression to return if condition is false.
    """
    condition: Expression
    true_expr: Expression
    false_expr: Expression

    def __str__(self):
        return f"{self.condition} ? {self.true_expr} : {self.false_expr}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.condition.build_scope(parent_scope)
        self.true_expr.build_scope(parent_scope)
        self.false_expr.build_scope(parent_scope)


@dataclass
class EqualityOp(Expression):
    """Represents an OpenSCAD equality comparison operation.

    Attributes:
        left: The left operand expression.
        right: The right operand expression.
    """
    left: Expression
    right: Expression

    def __str__(self):
        p = _prec(self)
        return f"{_lp(self.left, p)} == {_rp(self.right, p)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.right.build_scope(parent_scope)


@dataclass
class InequalityOp(Expression):
    """Represents an OpenSCAD inequality comparison operation.

    Attributes:
        left: The left operand expression.
        right: The right operand expression.
    """
    left: Expression
    right: Expression

    def __str__(self):
        p = _prec(self)
        return f"{_lp(self.left, p)} != {_rp(self.right, p)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.right.build_scope(parent_scope)


@dataclass
class GreaterThanOp(Expression):
    """Represents an OpenSCAD greater-than comparison operation.

    Attributes:
        left: The left operand expression.
        right: The right operand expression.
    """
    left: Expression
    right: Expression

    def __str__(self):
        p = _prec(self)
        return f"{_lp(self.left, p)} > {_rp(self.right, p)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.right.build_scope(parent_scope)


@dataclass
class GreaterThanOrEqualOp(Expression):
    """Represents an OpenSCAD greater-than-or-equal comparison operation.

    Attributes:
        left: The left operand expression.
        right: The right operand expression.
    """
    left: Expression
    right: Expression

    def __str__(self):
        p = _prec(self)
        return f"{_lp(self.left, p)} >= {_rp(self.right, p)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.right.build_scope(parent_scope)


@dataclass
class LessThanOp(Expression):
    """Represents an OpenSCAD less-than comparison operation.

    Attributes:
        left: The left operand expression.
        right: The right operand expression.
    """
    left: Expression
    right: Expression

    def __str__(self):
        p = _prec(self)
        return f"{_lp(self.left, p)} < {_rp(self.right, p)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.right.build_scope(parent_scope)


@dataclass
class LessThanOrEqualOp(Expression):
    """Represents an OpenSCAD less-than-or-equal comparison operation.

    Attributes:
        left: The left operand expression.
        right: The right operand expression.
    """
    left: Expression
    right: Expression

    def __str__(self):
        p = _prec(self)
        return f"{_lp(self.left, p)} <= {_rp(self.right, p)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.right.build_scope(parent_scope)


@dataclass
class FunctionLiteral(Expression):
    """Represents an OpenSCAD function literal (anonymous function).

    Attributes:
        parameters: List of parameter declarations.
        body: The expression body of the function.
    """
    parameters: list[ParameterDeclaration]
    body: Expression

    def __str__(self):
        return f"function({', '.join(str(p) for p in self.parameters)}) {self.body}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        func_scope = parent_scope.child_scope()
        for param in self.parameters:
            func_scope.define_variable(param.name.name, param)
            param.build_scope(func_scope)
        self.body.build_scope(func_scope)


@dataclass
class PrimaryCall(Expression):
    """Represents an OpenSCAD function call expression.

    Attributes:
        left: The function expression (typically an Identifier).
        arguments: List of arguments (PositionalArgument or NamedArgument).
    """
    left: Expression
    arguments: list[Argument]

    def __str__(self):
        return f"{self.left}({', '.join(str(arg) for arg in self.arguments)})"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        for arg in self.arguments:
            arg.build_scope(parent_scope)


@dataclass
class PrimaryIndex(Expression):
    """Represents an OpenSCAD array/vector index access expression.

    Attributes:
        left: The expression being indexed (vector, array, or string).
        index: The index expression.
    """
    left: Expression
    index: Expression

    def __str__(self):
        return f"{self.left}[{self.index}]"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.index.build_scope(parent_scope)


@dataclass
class PrimaryMember(Expression):
    """Represents an OpenSCAD member access expression.

    Attributes:
        left: The object expression.
        member: The member name as an Identifier.
    """
    left: Expression
    member: Identifier

    def __str__(self):
        return f"{self.left}.{self.member}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.left.build_scope(parent_scope)
        self.member.build_scope(parent_scope)


@dataclass
class VectorElement(ASTNode):
    """Base class for elements in OpenSCAD list comprehensions."""
    def __str__(self):
        raise NotImplementedError


@dataclass
class ListCompLet(VectorElement):
    """Represents a let expression within a list comprehension.

    Attributes:
        assignments: List of local variable assignments.
        body: The vector element body that uses the assigned variables.
    """
    assignments: list[Assignment]
    body: VectorElement

    def __str__(self):
        return f"let ({', '.join(str(a) for a in self.assignments)}) {self.body}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        let_scope = parent_scope.child_scope()
        for assignment in self.assignments:
            let_scope.define_variable(assignment.name.name, assignment)
            assignment.build_scope(let_scope)
        self.body.build_scope(let_scope)


@dataclass
class ListCompEach(VectorElement):
    """Represents an 'each' expression within a list comprehension.

    Attributes:
        body: The vector element to flatten.
    """
    body: VectorElement

    def __str__(self):
        return f"each {self.body}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.body.build_scope(parent_scope)


@dataclass
class ListCompFor(VectorElement):
    """Represents a for loop within a list comprehension.

    Attributes:
        assignments: List of loop variable assignments.
        body: The expression to evaluate for each iteration.
    """
    assignments: list[Assignment]
    body: VectorElement

    def __str__(self):
        return f"for ({', '.join(str(a) for a in self.assignments)}) {self.body}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        for_scope = parent_scope.child_scope()
        for assignment in self.assignments:
            assignment.scope = for_scope
            for_scope.define_variable(assignment.name.name, assignment)
            assignment.name.build_scope(for_scope)
            assignment.expr.build_scope(parent_scope)
        self.body.build_scope(for_scope)


@dataclass
class ListCompCFor(VectorElement):
    """Represents a C-style for loop within a list comprehension.

    Attributes:
        inits: List of initialization assignments.
        condition: The loop continuation condition.
        incrs: List of increment assignments.
        body: The expression to evaluate for each iteration.
    """
    inits: list[Assignment]
    condition: Expression
    incrs: list[Assignment]
    body: VectorElement

    def __str__(self):
        return f"for ({', '.join(str(a) for a in self.inits)}; {self.condition}; {', '.join(str(a) for a in self.incrs)}) {self.body}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        for_scope = parent_scope.child_scope()
        for assignment in self.inits:
            for_scope.define_variable(assignment.name.name, assignment)
            assignment.build_scope(for_scope)
        self.condition.build_scope(for_scope)
        for assignment in self.incrs:
            assignment.build_scope(for_scope)
        self.body.build_scope(for_scope)


@dataclass
class ListCompIf(VectorElement):
    """Represents an if condition within a list comprehension.

    Attributes:
        condition: The boolean condition to evaluate.
        true_expr: The expression to include if condition is true.
    """
    condition: Expression
    true_expr: VectorElement

    def __str__(self):
        return f"if ({self.condition}) {self.true_expr}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.condition.build_scope(parent_scope)
        self.true_expr.build_scope(parent_scope)


@dataclass
class ListCompIfElse(VectorElement):
    """Represents an if-else condition within a list comprehension.

    Attributes:
        condition: The boolean condition to evaluate.
        true_expr: The expression to include if condition is true.
        false_expr: The expression to include if condition is false.
    """
    condition: Expression
    true_expr: VectorElement
    false_expr: VectorElement

    def __str__(self):
        return f"if ({self.condition}) {self.true_expr} else {self.false_expr}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.condition.build_scope(parent_scope)
        self.true_expr.build_scope(parent_scope)
        self.false_expr.build_scope(parent_scope)


@dataclass
class ListComprehension(Expression):
    """Represents an OpenSCAD list comprehension (vector literal).

    Attributes:
        elements: List of vector elements (expressions, for loops, conditions, etc.).
    """
    elements: list[VectorElement]

    def __str__(self):
        return f"[{', '.join(str(e) for e in self.elements)}]"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        for elem in self.elements:
            elem.build_scope(parent_scope)


@dataclass
class ModuleInstantiation(ASTNode):
    """Base class for all OpenSCAD module instantiations."""
    pass


@dataclass
class ModularCall(ModuleInstantiation):
    """Represents a module call (module instantiation).

    Attributes:
        name: The module name as an Identifier.
        arguments: List of arguments (PositionalArgument or NamedArgument).
        children: List of child module instantiations (for transformations).
    """
    name: Identifier
    arguments: list[Argument]
    children: list[ModuleInstantiation]

    def __str__(self):
        return f"{self.name}({', '.join(str(arg) for arg in self.arguments)})"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.name.build_scope(parent_scope)
        for arg in self.arguments:
            arg.build_scope(parent_scope)
        if self.children:
            children_scope = parent_scope.child_scope()
            _collect_hoisted_declarations(self.children, children_scope)
            for child in self.children:
                child.build_scope(children_scope)


@dataclass
class ModularFor(ModuleInstantiation):
    """Represents a for loop module instantiation.

    Attributes:
        assignments: List of loop variable assignments.
        body: The module instantiation to execute for each iteration.
    """
    assignments: list[Assignment]
    body: ModuleInstantiation

    def __str__(self):
        return f"for ({', '.join(str(assignment) for assignment in self.assignments)}) {self.body}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        for_scope = parent_scope.child_scope()
        for assignment in self.assignments:
            assignment.scope = for_scope
            for_scope.define_variable(assignment.name.name, assignment)
            assignment.name.build_scope(for_scope)
            assignment.expr.build_scope(parent_scope)
        body = self.body if isinstance(self.body, list) else [self.body]
        _collect_hoisted_declarations(body, for_scope)
        for node in body:
            node.build_scope(for_scope)


@dataclass
class ModularIntersectionFor(ModuleInstantiation):
    """Represents an intersection_for loop module instantiation.

    Attributes:
        assignments: List of loop variable assignments.
        body: The module instantiation to execute for each iteration.
    """
    assignments: list[Assignment]
    body: ModuleInstantiation

    def __str__(self):
        return f"intersection_for ({', '.join(str(assignment) for assignment in self.assignments)}) {self.body}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        for_scope = parent_scope.child_scope()
        for assignment in self.assignments:
            assignment.scope = for_scope
            for_scope.define_variable(assignment.name.name, assignment)
            assignment.name.build_scope(for_scope)
            assignment.expr.build_scope(parent_scope)
        body = self.body if isinstance(self.body, list) else [self.body]
        _collect_hoisted_declarations(body, for_scope)
        for node in body:
            node.build_scope(for_scope)


@dataclass
class ModularLet(ModuleInstantiation):
    """Represents a let statement for module instantiations.

    Attributes:
        assignments: List of local variable assignments.
        children: List of child module instantiations that can use the variables.
    """
    assignments: list[Assignment]
    children: list[ModuleInstantiation]

    def __str__(self):
        return f"let ({', '.join(str(assignment) for assignment in self.assignments)}) {', '.join(str(child) for child in self.children)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        let_scope = parent_scope.child_scope()
        for assignment in self.assignments:
            let_scope.define_variable(assignment.name.name, assignment)
            assignment.build_scope(let_scope)
        _collect_hoisted_declarations(self.children, let_scope)
        for child in self.children:
            child.build_scope(let_scope)


@dataclass
class ModularEcho(ModuleInstantiation):
    """Represents an echo statement for module instantiations.

    Attributes:
        arguments: List of arguments to print (can be positional or named).
        children: List of child module instantiations to render.
    """
    arguments: list[Argument]
    children: list[ModuleInstantiation]

    def __str__(self):
        return f"echo({', '.join(str(arg) for arg in self.arguments)}) {', '.join(str(child) for child in self.children)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        for arg in self.arguments:
            arg.build_scope(parent_scope)
        if self.children:
            children_scope = parent_scope.child_scope()
            _collect_hoisted_declarations(self.children, children_scope)
            for child in self.children:
                child.build_scope(children_scope)


@dataclass
class ModularAssert(ModuleInstantiation):
    """Represents an assert statement for module instantiations.

    Attributes:
        arguments: List of arguments (typically condition and optional message).
        children: List of child module instantiations to render if assertion passes.
    """
    arguments: list[Argument]
    children: list[ModuleInstantiation]

    def __str__(self):
        return f"assert({', '.join(str(arg) for arg in self.arguments)}) {', '.join(str(child) for child in self.children)}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        for arg in self.arguments:
            arg.build_scope(parent_scope)
        if self.children:
            children_scope = parent_scope.child_scope()
            _collect_hoisted_declarations(self.children, children_scope)
            for child in self.children:
                child.build_scope(children_scope)


@dataclass
class ModularIf(ModuleInstantiation):
    """Represents an if statement for module instantiations (without else).

    Attributes:
        condition: The boolean condition to evaluate.
        true_branch: The module instantiation to render if condition is true.
    """
    condition: Expression
    true_branch: ModuleInstantiation

    def __str__(self):
        return f"if ({self.condition}) {self.true_branch}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.condition.build_scope(parent_scope)
        true_scope = parent_scope.child_scope()
        branch = self.true_branch if isinstance(self.true_branch, list) else [self.true_branch]
        _collect_hoisted_declarations(branch, true_scope)
        for node in branch:
            node.build_scope(true_scope)


@dataclass
class ModularIfElse(ModuleInstantiation):
    """Represents an if-else statement for module instantiations.

    Attributes:
        condition: The boolean condition to evaluate.
        true_branch: The module instantiation to render if condition is true.
        false_branch: The module instantiation to render if condition is false.
    """
    condition: Expression
    true_branch: ModuleInstantiation
    false_branch: ModuleInstantiation

    def __str__(self):
        return f"if ({self.condition}) {self.true_branch} else {self.false_branch}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.condition.build_scope(parent_scope)
        true_scope = parent_scope.child_scope()
        true_branch = self.true_branch if isinstance(self.true_branch, list) else [self.true_branch]
        _collect_hoisted_declarations(true_branch, true_scope)
        for node in true_branch:
            node.build_scope(true_scope)
        false_scope = parent_scope.child_scope()
        false_branch = self.false_branch if isinstance(self.false_branch, list) else [self.false_branch]
        _collect_hoisted_declarations(false_branch, false_scope)
        for node in false_branch:
            node.build_scope(false_scope)


@dataclass
class ModularModifierShowOnly(ModuleInstantiation):
    """Represents the '!' (show only) module modifier.

    Attributes:
        child: The module instantiation to show exclusively.
    """
    child: ModuleInstantiation

    def __str__(self):
        return f"!{self.child}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.child.build_scope(parent_scope)


@dataclass
class ModularModifierHighlight(ModuleInstantiation):
    """Represents the '#' (highlight) module modifier.

    Attributes:
        child: The module instantiation to highlight.
    """
    child: ModuleInstantiation

    def __str__(self):
        return f"#{self.child}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.child.build_scope(parent_scope)


@dataclass
class ModularModifierBackground(ModuleInstantiation):
    """Represents the '%' (background) module modifier.

    Attributes:
        child: The module instantiation to render as background.
    """
    child: ModuleInstantiation

    def __str__(self):
        return f"%{self.child}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.child.build_scope(parent_scope)


@dataclass
class ModularModifierDisable(ModuleInstantiation):
    """Represents the '*' (disable) module modifier.

    Attributes:
        child: The module instantiation to disable.
    """
    child: ModuleInstantiation

    def __str__(self):
        return f"*{self.child}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        self.child.build_scope(parent_scope)


@dataclass
class ModuleDeclaration(ASTNode):
    """Represents an OpenSCAD module declaration (definition).

    Attributes:
        name: The module name as an Identifier.
        parameters: List of parameter declarations.
        children: List of statements in the module body.
        pre_name_comments: Comments between 'module' keyword and name.
        post_name_comments: Comments between name and '('.
        post_params_comments: Comments between ')' and '{'.
    """
    name: Identifier
    parameters: list[ParameterDeclaration]
    children: list[ModuleInstantiation | Assignment | "FunctionDeclaration | ModuleDeclaration"]
    pre_name_comments: list["CommentSpan"] = field(default_factory=list)
    post_name_comments: list["CommentSpan"] = field(default_factory=list)
    post_params_comments: list["CommentSpan"] = field(default_factory=list)

    def __str__(self):
        params = ', '.join(str(param) for param in self.parameters)
        children = ', '.join(str(child) for child in self.children)
        return f"module {self.name}({params}) {{ {children} }}"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        for c in self.pre_name_comments:
            c.build_scope(parent_scope)
        self.name.build_scope(parent_scope)
        for c in self.post_name_comments:
            c.build_scope(parent_scope)
        mod_scope = parent_scope.child_scope()
        for param in self.parameters:
            mod_scope.define_variable(param.name.name, param)
            param.build_scope(mod_scope)
        for c in self.post_params_comments:
            c.build_scope(mod_scope)
        _collect_hoisted_declarations(self.children, mod_scope)
        for child in self.children:
            child.build_scope(mod_scope)


@dataclass
class FunctionDeclaration(ASTNode):
    """Represents an OpenSCAD function declaration (definition).

    Attributes:
        name: The function name as an Identifier.
        parameters: List of parameter declarations.
        expr: The expression body that the function evaluates to.
        pre_name_comments: Comments between 'function' keyword and name.
        post_name_comments: Comments between name and '('.
        post_params_comments: Comments between ')' and '='.
    """
    name: Identifier
    parameters: list[ParameterDeclaration]
    expr: Expression
    pre_name_comments: list["CommentSpan"] = field(default_factory=list)
    post_name_comments: list["CommentSpan"] = field(default_factory=list)
    post_params_comments: list["CommentSpan"] = field(default_factory=list)

    def __str__(self):
        params = ', '.join(str(param) for param in self.parameters)
        return f"function {self.name}({params}) = {self.expr};"

    def build_scope(self, parent_scope: "Scope") -> None:
        self.scope = parent_scope
        for c in self.pre_name_comments:
            c.build_scope(parent_scope)
        self.name.build_scope(parent_scope)
        for c in self.post_name_comments:
            c.build_scope(parent_scope)
        func_scope = parent_scope.child_scope()
        for param in self.parameters:
            func_scope.define_variable(param.name.name, param)
            param.build_scope(func_scope)
        for c in self.post_params_comments:
            c.build_scope(func_scope)
        self.expr.build_scope(func_scope)


@dataclass
class UseStatement(ASTNode):
    """Represents an OpenSCAD 'use' statement.

    Attributes:
        filepath: The file path as a StringLiteral (without angle brackets).
    """
    filepath: StringLiteral

    def __str__(self):
        return f"use <{self.filepath.val}>"


@dataclass
class IncludeStatement(ASTNode):
    """Represents an OpenSCAD 'include' statement.

    Attributes:
        filepath: The file path as a StringLiteral (without angle brackets).
    """
    filepath: StringLiteral

    def __str__(self):
        return f"include <{self.filepath.val}>"


# ---------------------------------------------------------------------------
# Operator precedence helpers (used by __str__ methods to emit parentheses)
# ---------------------------------------------------------------------------

_PREC: dict[type, int] = {
    TernaryOp: 10,
    LogicalOrOp: 20,
    LogicalAndOp: 30,
    EqualityOp: 40, InequalityOp: 40,
    LessThanOp: 50, LessThanOrEqualOp: 50, GreaterThanOp: 50, GreaterThanOrEqualOp: 50,
    BitwiseOrOp: 55,
    BitwiseAndOp: 57,
    BitwiseShiftLeftOp: 58, BitwiseShiftRightOp: 58,
    AdditionOp: 60, SubtractionOp: 60,
    MultiplicationOp: 70, DivisionOp: 70, ModuloOp: 70,
    UnaryMinusOp: 80, LogicalNotOp: 80, BitwiseNotOp: 80,
    ExponentOp: 90,
}


def _prec(node) -> int:
    if isinstance(node, CommentedExpr):
        return _prec(node.expr)
    return _PREC.get(type(node), 99)


def _lp(child, parent_prec: int) -> str:
    """Left-operand: parenthesize when child binds strictly looser than parent."""
    return f"({child})" if _prec(child) < parent_prec else str(child)


def _rp(child, parent_prec: int) -> str:
    """Right-operand: parenthesize when child binds looser than OR equal to parent."""
    return f"({child})" if _prec(child) <= parent_prec else str(child)


def _collect_hoisted_declarations(nodes, scope: "Scope") -> None:
    """Scan a list of nodes and register assignments, functions, and modules in scope."""
    for node in nodes:
        if isinstance(node, Assignment):
            scope.define_variable(node.name.name, node)
        elif isinstance(node, FunctionDeclaration):
            scope.define_function(node.name.name, node)
        elif isinstance(node, ModuleDeclaration):
            scope.define_module(node.name.name, node)
