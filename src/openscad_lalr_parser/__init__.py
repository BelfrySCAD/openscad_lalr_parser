"""OpenSCAD LALR(1) Parser — fast parsing of OpenSCAD source code with AST generation.

This package provides a Lark-based LALR(1) parser for the OpenSCAD language.
It produces an AST with node classes identical to those in the openscad_parser
library, enabling drop-in replacement for parsing tasks.

Usage:
    from openscad_lalr_parser import getASTfromString, getASTfromFile

    ast = getASTfromString("cube([1,2,3]);")
    ast = getASTfromFile("model.scad")
"""
from __future__ import annotations

import dataclasses
import contextlib
import contextvars
import functools
import hashlib
import json
import os
import pickle
import platform
import re
from pathlib import Path
from typing import Optional

from lark import Lark
from lark.exceptions import UnexpectedInput

from .nodes import (
    Position,
    ASTNode,
    CommentLine,
    BlankLine,
    CommentSpan,
    CommentedExpr,
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
    RenderExpression,
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
    VectorElement,
    ListCompLet,
    ListCompEach,
    ListCompFor,
    ListCompCFor,
    ListCompIf,
    ListCompIfElse,
    ListComprehension,
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

from .scope import Scope, build_scopes
from .transformer import OpenSCADTransformer
from .source_map import SourceMap, SourceSegment, create_source_map_from_origins, process_includes as process_includes_func
from .pretty_print import to_openscad
from .serialization import (
    ast_to_dict,
    ast_to_json,
    ast_from_dict,
    ast_from_json,
    ast_to_yaml,
    ast_from_yaml,
)


# --- Parser singleton ---

_GRAMMAR_PATH = Path(__file__).parent / "grammar.lark"

_parser_cache: dict[str, Lark] = {}

# Strict-commas mode: reject the trailing commas OpenSCAD 2021.01 rejected --
# in a call's arguments and a let/for/intersection_for assignment list --
# while keeping the ones it accepted: list literals, list comprehensions and
# parameter declarations (measured against 2021.01; openscad_cpp_parser #9).
# A context variable rather than a parameter on every entry point, as the C++
# parser's StrictCommaScope is thread-local: it nests, restores on exit
# (including when a parse raises), and every cache below keys on it, so a
# strict parse is never served a lenient tree.
_STRICT_COMMAS: contextvars.ContextVar[bool] = contextvars.ContextVar("strict_commas", default=False)


@contextlib.contextmanager
def strict_commas(enabled: bool = True):
    """Parse as OpenSCAD 2021.01 did, rejecting `cube(1,)` and `let(x=1,)`::

        with strict_commas():
            ast = getASTfromFile("model.scad")
    """
    token = _STRICT_COMMAS.set(enabled)
    try:
        yield
    finally:
        _STRICT_COMMAS.reset(token)


def _get_parser() -> Lark:
    """Get or create the cached Lark LALR parser for the current comma mode."""
    strict = _STRICT_COMMAS.get()
    key = "strict" if strict else "standard"
    if key not in _parser_cache:
        grammar = _GRAMMAR_PATH.read_text()
        if strict:
            for rule in ('assignments_expr: (assignment_expr ("," assignment_expr)* ","?)?',
                         'arguments: (argument ("," argument)* ","?)?'):
                assert rule in grammar, rule
                grammar = grammar.replace(rule, rule.replace(' ","?)?', ')?'))
        _parser_cache[key] = Lark(
            grammar,
            parser="lalr",
            propagate_positions=True,
            maybe_placeholders=False,
        )
    return _parser_cache[key]


# --- Comment extraction for include_comments mode ---

_COMMENT_RE = re.compile(
    r'//([^\n]*)'           # single-line comment
    r'|/\*([\s\S]*?)\*/'    # multi-line comment
    r'|"(?:[^"\\]|\\[\s\S])*"'  # string literal (skip); a backslash may escape a newline
)


def _extract_comments(code: str, origin: str) -> list[ASTNode]:
    """Extract all comments from source code as AST nodes."""
    comments = []
    for m in _COMMENT_RE.finditer(code):
        if m.group(1) is not None:
            text = m.group(1)
            start = m.start()
            line = code[:start].count('\n') + 1
            last_nl = code.rfind('\n', 0, start)
            col = start - last_nl if last_nl >= 0 else start + 1
            pos = Position(origin=origin, line=line, column=col,
                           start_offset=start, end_offset=m.end())
            comments.append(CommentLine(position=pos, text=text))
        elif m.group(2) is not None:
            text = m.group(2)
            start = m.start()
            line = code[:start].count('\n') + 1
            last_nl = code.rfind('\n', 0, start)
            col = start - last_nl if last_nl >= 0 else start + 1
            pos = Position(origin=origin, line=line, column=col,
                           start_offset=start, end_offset=m.end())
            comments.append(CommentSpan(position=pos, text=text))
    return comments


def _is_inline_comment(comment: ASTNode, code: str) -> bool:
    """Return True if the comment shares a source line with non-comment code."""
    start = comment.position.start_offset
    end = comment.position.end_offset
    line_start = code.rfind('\n', 0, start)
    line_start = 0 if line_start < 0 else line_start + 1
    before = code[line_start:start].strip()
    if before:
        return True
    if isinstance(comment, CommentSpan):
        last_line_end = code.find('\n', end)
        if last_line_end < 0:
            last_line_end = len(code)
        after = code[end:last_line_end].strip()
        if after and not after.startswith('//') and not after.startswith('/*'):
            return True
    return False


def _classify_comments(comments: list[ASTNode], code: str) -> tuple[list[ASTNode], list[ASTNode]]:
    """Split comments into (inline, standalone) lists."""
    inline = []
    standalone = []
    for c in comments:
        if _is_inline_comment(c, code):
            inline.append(c)
        else:
            standalone.append(c)
    return inline, standalone


_SKIP_FIELDS = frozenset(('position', 'scope', 'leading_comments', 'trailing_comments',
                           'pre_name_comments', 'post_name_comments', 'post_params_comments'))


_STATEMENT_LIST_FIELDS = ("children", "body", "true_branch", "false_branch")
_STATEMENT_TYPES = (ModuleInstantiation, ModuleDeclaration, FunctionDeclaration)
# What an inline comment can wrap: expressions, and list-comprehension
# elements (`each`, `if`, `for` ...), which aren't Expressions -- with only
# those between them, a comment had nothing to attach to and was dropped.
_ATTACHABLE = (Expression, VectorElement)


def _blank_comments(code: str, comments: list) -> str:
    """`code` with every comment replaced by spaces (newlines kept), so
    looking back past comments for the previous real character is easy."""
    chars = list(code)
    for c in comments:
        for i in range(c.position.start_offset, c.position.end_offset):
            if chars[i] != "\n":
                chars[i] = " "
    return "".join(chars)


def _place_comment(stmts: list, comment, blanked: str, same_line: bool, top: bool = False) -> str:
    """Put `comment` into the statement list where it falls between
    statements, descending into nested blocks. Returns "placed", "head"
    (inside a statement's non-block part -- arguments, a condition -- where
    expression attachment takes it) or "top" (an own-line comment between
    top-level statements, which _inject_comments places with its blank
    lines)."""
    cs = comment.position.start_offset
    for node in stmts:
        if isinstance(node, (CommentLine, CommentSpan, BlankLine)):
            continue
        pos = node.position
        if pos.start_offset <= cs < pos.end_offset:
            return _place_in_statement(node, comment, blanked, same_line)
    if top and not same_line:
        return "top"
    index = sum(1 for n in stmts if n.position.start_offset < cs)  # comments come in source order
    if index == 0 and top:
        return "head"
    if isinstance(comment, CommentLine):
        comment.same_line = same_line
    stmts.insert(index, comment)
    return "placed"


def _place_in_statement(node, comment, blanked: str, same_line: bool) -> str:
    child = getattr(node, "child", None)  # the #/%/!/* modifiers wrap one statement
    if isinstance(child, ASTNode):
        return _place_in_statement(child, comment, blanked, same_line)
    # The block the comment is in: the last one starting before it (an if/else
    # has two). Failing that, the next block if only its `{` comes between
    # (`module m() { // why`, or an own-line comment atop the block).
    cs = comment.position.start_offset
    block = next_block = None
    for name in _STATEMENT_LIST_FIELDS:
        stmts = getattr(node, name, None)
        if not isinstance(stmts, list):
            continue
        # By its first STATEMENT: a comment placed there already may come first.
        first = next((n for n in stmts if isinstance(n, ASTNode)
                      and not isinstance(n, (CommentLine, CommentSpan, BlankLine))), None)
        if first is None:
            continue
        if first.position.start_offset <= cs:
            block = stmts
        elif next_block is None:
            next_block = stmts
    inside_block = block is not None and any(
        n.position.start_offset <= cs < n.position.end_offset
        for n in block if not isinstance(n, (CommentLine, CommentSpan, BlankLine)))
    if not inside_block and next_block is not None and blanked[:cs].rstrip().endswith("{"):
        block = next_block  # atop a block: an else's, even with the if's block before it
    if block is None:
        return "head"
    return _place_comment(block, comment, blanked, same_line)


def _attach_inline_comments(ast_nodes: list[ASTNode], inline_comments: list[ASTNode]) -> list[ASTNode]:
    """Returns the comments it found no place for, for the caller to keep as
    top-level ones: dropping them lost the text."""
    """Walk AST and wrap expressions adjacent to inline comments in CommentedExpr."""
    if not inline_comments:
        return []
    inline_comments.sort(key=lambda c: c.position.start_offset)
    used: set[int] = set()
    for node in ast_nodes:
        _walk_attach(node, inline_comments, used)

    # Attach remaining unused inline comments as trailing on the nearest
    # preceding top-level node's last expression field.
    for ci, comment in enumerate(inline_comments):
        if ci in used:
            continue
        cs = comment.position.start_offset
        best_node = None
        for node in ast_nodes:
            if isinstance(node, (CommentLine, CommentSpan, BlankLine)):
                continue
            if node.position.end_offset <= cs:
                best_node = node
        if best_node is not None:
            _attach_trailing_to_last_expr(best_node, comment)
            used.add(ci)

    return [c for ci, c in enumerate(inline_comments) if ci not in used]


def _attach_trailing_to_last_expr(node: ASTNode, comment: ASTNode):
    """Attach a trailing comment to the last Expression field in node."""
    last_expr_info = None
    for f in dataclasses.fields(node):
        if f.name in _SKIP_FIELDS:
            continue
        val = getattr(node, f.name)
        if isinstance(val, Expression):
            last_expr_info = (node, f.name, None, val)
        elif isinstance(val, list):
            for idx, item in enumerate(val):
                if isinstance(item, Expression):
                    last_expr_info = (node, f.name, idx, item)
                elif isinstance(item, ASTNode):
                    for cf in dataclasses.fields(item):
                        if cf.name in _SKIP_FIELDS:
                            continue
                        cval = getattr(item, cf.name)
                        if isinstance(cval, Expression):
                            last_expr_info = (item, cf.name, None, cval)
    if last_expr_info is None:
        return
    owner, fname, lidx, expr = last_expr_info
    if isinstance(expr, CommentedExpr):
        expr.trailing_comments.append(comment)
    else:
        wrapped = CommentedExpr(
            position=expr.position,
            leading_comments=[],
            trailing_comments=[comment],
            expr=expr,
        )
        if lidx is None:
            setattr(owner, fname, wrapped)
        else:
            getattr(owner, fname)[lidx] = wrapped


def _walk_attach(node: ASTNode, comments: list[ASTNode], used: set[int]):
    """Recursively attach inline comments to Expression fields of node."""
    if not isinstance(node, ASTNode) or isinstance(node, (CommentedExpr, CommentLine, CommentSpan)):
        return

    ns = node.position.start_offset
    ne = node.position.end_offset

    has_relevant = any(
        i not in used and ns <= comments[i].position.start_offset < ne
        for i in range(len(comments))
    )
    if not has_relevant:
        for f in dataclasses.fields(node):
            if f.name in _SKIP_FIELDS:
                continue
            val = getattr(node, f.name)
            if isinstance(val, ASTNode):
                _walk_attach(val, comments, used)
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, ASTNode):
                        _walk_attach(item, comments, used)
        return

    # Collect wrappable Expression fields, including from non-Expression
    # containers like PositionalArgument, NamedArgument, ParameterDeclaration.
    # Each entry: (owner_node, field_name, list_index_or_None, expr)
    expr_fields = []
    non_expr_children = []

    for f in dataclasses.fields(node):
        if f.name in _SKIP_FIELDS:
            continue
        if f.name == "step" and getattr(node, "implicit_step", False):
            continue  # synthesized for [a:b]; it spans the whole range and would swallow its comments
        val = getattr(node, f.name)
        if isinstance(val, _ATTACHABLE) and not isinstance(val, CommentedExpr):
            expr_fields.append((node, f.name, None, val))
        elif isinstance(val, ASTNode):
            non_expr_children.append(val)
        elif isinstance(val, list):
            for idx, item in enumerate(val):
                if isinstance(item, _ATTACHABLE) and not isinstance(item, CommentedExpr):
                    expr_fields.append((node, f.name, idx, item))
                elif isinstance(item, _STATEMENT_TYPES) or (f.name in _STATEMENT_LIST_FIELDS and isinstance(item, ASTNode)):
                    # A child statement (an assignment in a block too): its
                    # own walk attaches its comments. Mined here, its NAME
                    # became one of this node's expressions, and a comment in
                    # this node's arguments landed on it (`translate([1, // c`
                    # ... `cube // c(1);`, or a last parameter's comment on
                    # the body's first assignment).
                    non_expr_children.append(item)
                elif isinstance(item, ASTNode):
                    _collect_container_exprs(item, expr_fields, non_expr_children)

    expr_fields.sort(key=lambda x: x[3].position.start_offset)

    leading_map: dict[int, list] = {ei: [] for ei in range(len(expr_fields))}
    trailing_map: dict[int, list] = {ei: [] for ei in range(len(expr_fields))}

    child_spans = [(c.position.start_offset, c.position.end_offset) for c in non_expr_children]
    for ci, comment in enumerate(comments):
        if ci in used:
            continue
        cs = comment.position.start_offset
        if cs < ns or cs >= ne:
            continue
        if any(s <= cs < e for s, e in child_spans):
            continue  # inside a child statement: its own walk places it

        attached = False
        for ei, (owner, fname, lidx, expr) in enumerate(expr_fields):
            es = expr.position.start_offset
            if cs < es:
                leading_map[ei].append((ci, comment))
                used.add(ci)
                attached = True
                break
            elif cs >= expr.position.end_offset:
                continue
            # Inside this expression: the recursion below attaches it within.
            # Falling through made it the NEXT expression's leading comment.
            attached = True
            break
        if not attached and expr_fields:
            last_ei = len(expr_fields) - 1
            if cs >= expr_fields[last_ei][3].position.end_offset:
                trailing_map[last_ei].append((ci, comment))
                used.add(ci)

    for ei, (owner, fname, lidx, expr) in enumerate(expr_fields):
        leading = [c for _, c in leading_map[ei]]
        trailing = [c for _, c in trailing_map[ei]]

        if leading or trailing:
            wrapped = CommentedExpr(
                position=expr.position,
                leading_comments=leading,
                trailing_comments=trailing,
                expr=expr,
            )
            if lidx is None:
                setattr(owner, fname, wrapped)
            else:
                getattr(owner, fname)[lidx] = wrapped

        _walk_attach(expr, comments, used)

    for child in non_expr_children:
        _walk_attach(child, comments, used)


def _collect_container_exprs(container: ASTNode, expr_fields: list, non_expr_children: list):
    """Extract Expression fields from a non-Expression container node."""
    found_expr = False
    for f in dataclasses.fields(container):
        if f.name in _SKIP_FIELDS:
            continue
        val = getattr(container, f.name)
        if isinstance(val, Expression) and not isinstance(val, CommentedExpr):
            expr_fields.append((container, f.name, None, val))
            found_expr = True
        elif isinstance(val, list):
            for idx, item in enumerate(val):
                if isinstance(item, Expression) and not isinstance(item, CommentedExpr):
                    expr_fields.append((container, f.name, idx, item))
                    found_expr = True
    if not found_expr:
        non_expr_children.append(container)


def _find_char_skipping_comments(code: str, frm: int, ch: str, comments: list[ASTNode]) -> int:
    """Scan raw source from `frm` for the next occurrence of `ch`, skipping
    over any already-extracted comment span encountered along the way (so a
    stray '(' or ')' inside a comment's own text is never mistaken for the
    real token). Returns -1 if not found.

    Needed because the grammar captures no location for the parameter
    list's own '(' / ')' tokens -- only NAME and the whole declaration's
    span are available (see transformer.py's
    function_definition/module_definition/parameter_with_default).
    """
    i = frm
    n = len(code)
    while i < n:
        skipped = False
        for c in comments:
            if c is not None and c.position.start_offset == i:
                i = c.position.end_offset
                skipped = True
                break
        if skipped:
            continue
        if code[i] == ch:
            return i
        i += 1
    return -1


def _claim_comment_spans_in_range(lo: int, hi: int, out: list, comments: list) -> None:
    """Moves every CommentSpan in `comments` whose start offset falls in
    [lo, hi) into `out`, nulling its slot in `comments` in place so a later
    pass (the inline/standalone split) never sees it again."""
    if lo >= hi:
        return
    for idx, c in enumerate(comments):
        if c is None or not isinstance(c, CommentSpan):
            continue
        cs = c.position.start_offset
        if lo <= cs < hi:
            out.append(c)
            comments[idx] = None


def _claim_decl_signature_comments(decl: ASTNode, name: Identifier, parameters: list[ParameterDeclaration],
                                    body_start: int, pre_name: list, post_name: list, post_params: list,
                                    code: str, comments: list) -> None:
    """Claims '/* */' comments (CommentSpan only -- these fields' own
    declared type) in every structural gap a FunctionDeclaration/
    ModuleDeclaration doesn't expose as any Expression field: before the
    name, between the name and the parameter list, between adjacent
    parameters (including a parameter with no default value, which
    _walk_attach's own generic Expression-field scan never visits at all,
    since it only descends into fields whose value IS an Expression),
    between the last parameter and ')', and between ')' and the body.

    ponytail: when there are zero parameters, the "between name and '('"
    and "between '(' and ')'" gaps are both real but there's no parameter
    to own the latter -- folded into post_params_comments rather than
    adding a dedicated field neither language's AST declares.
    """
    name_start = name.position.start_offset
    name_end = name.position.end_offset
    _claim_comment_spans_in_range(decl.position.start_offset, name_start, pre_name, comments)

    open_paren = _find_char_skipping_comments(code, name_end, '(', comments)
    paren_open_pos = open_paren if open_paren >= 0 else name_end
    _claim_comment_spans_in_range(name_end, paren_open_pos, post_name, comments)
    cursor = open_paren + 1 if open_paren >= 0 else name_end

    for p in parameters:
        _claim_comment_spans_in_range(cursor, p.position.start_offset, p.leading_comments, comments)
        cursor = p.position.end_offset

    close_paren = _find_char_skipping_comments(code, cursor, ')', comments)
    paren_close_pos = close_paren if close_paren >= 0 else cursor
    if parameters:
        _claim_comment_spans_in_range(cursor, paren_close_pos, parameters[-1].trailing_comments, comments)
    else:
        _claim_comment_spans_in_range(cursor, paren_close_pos, post_params, comments)
    cursor = close_paren + 1 if close_paren >= 0 else cursor
    _claim_comment_spans_in_range(cursor, body_start, post_params, comments)


def _walk_attach_decl_comments(node: ASTNode, code: str, comments: list) -> None:
    """Recurses through `node` looking for FunctionDeclaration/
    ModuleDeclaration nodes (which can nest inside a module's own
    children), claiming their signature-gap comments. A generic
    reflection-based walk over dataclass fields (mirrors _walk_attach's own
    field introspection), since -- unlike the C++ port, which needs an
    explicit per-NodeKind switch -- Python's dataclasses.fields() already
    gives a free generic tree walk.
    """
    if not isinstance(node, ASTNode) or isinstance(node, (CommentedExpr, CommentLine, CommentSpan)):
        return

    if isinstance(node, FunctionDeclaration):
        _claim_decl_signature_comments(node, node.name, node.parameters, node.expr.position.start_offset,
                                        node.pre_name_comments, node.post_name_comments, node.post_params_comments,
                                        code, comments)
    elif isinstance(node, ModuleDeclaration):
        body_start = node.children[0].position.start_offset if node.children else node.position.end_offset
        _claim_decl_signature_comments(node, node.name, node.parameters, body_start, node.pre_name_comments,
                                        node.post_name_comments, node.post_params_comments, code, comments)

    for f in dataclasses.fields(node):
        if f.name in _SKIP_FIELDS:
            continue
        val = getattr(node, f.name)
        if isinstance(val, ASTNode):
            _walk_attach_decl_comments(val, code, comments)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, ASTNode):
                    _walk_attach_decl_comments(item, code, comments)


def _attach_declaration_comments(ast_nodes: list[ASTNode], code: str, comments: list) -> None:
    """Claims declaration-signature comments across the whole AST. Must run
    BEFORE _classify_comments/_attach_inline_comments -- a '/* */' comment
    alone on its own line before a parameter is classified *standalone* by
    _is_inline_comment, which this pass still needs to claim, so it operates
    on the full extracted comment list, not just the inline subset.
    """
    for node in ast_nodes:
        _walk_attach_decl_comments(node, code, comments)


def _attach_all_comments(ast: list[ASTNode], code: str, origin: str) -> list[ASTNode]:
    """Shared by getASTfromString/_parse_single_file: extracts comments,
    claims declaration-signature comments first (see
    _attach_declaration_comments), then runs the existing inline/standalone
    pipeline over whatever's left.
    """
    comments = _extract_comments(code, origin)
    blanked = _blank_comments(code, comments)
    _attach_declaration_comments(ast, code, comments)
    comments = [c for c in comments if c is not None]
    inline, standalone = _classify_comments(comments, code)
    # Comments that sit between statements belong in the statement list, at
    # any depth: a `//` ending a statement's line after that statement (it
    # was wrapped round the statement's last expression and printed before
    # the `;`, or after a child module's NAME), an own-line one where it is
    # (it was moved out to top level, after the whole statement). Inside a
    # statement's arguments or condition, expression attachment takes it.
    expr_comments, top_level = [], []
    for c in inline:
        if not (isinstance(c, CommentLine) and _place_comment(ast, c, blanked, True, top=True) == "placed"):
            expr_comments.append(c)
    for c in standalone:
        where = _place_comment(ast, c, blanked, False, top=True)
        if where == "top":
            top_level.append(c)
        elif where == "head":
            expr_comments.append(c)
    top_level += _attach_inline_comments(ast, expr_comments)
    top_level.sort(key=lambda c: c.position.start_offset)
    return _inject_comments(ast, top_level, code, origin)


def _inject_comments(ast_nodes: list[ASTNode], comments: list[ASTNode], code: str, origin: str) -> list[ASTNode]:
    """Merge standalone comment nodes into top-level AST node list."""
    if not comments:
        return ast_nodes

    result = []
    comment_idx = 0
    prev_end_line = 0

    for node in ast_nodes:
        node_line = node.position.line if hasattr(node, 'position') and node.position else float('inf')

        while comment_idx < len(comments) and comments[comment_idx].position.line < node_line:
            comment = comments[comment_idx]
            cl = comment.position.line
            if prev_end_line > 0 and cl - prev_end_line > 1:
                lines = code.split('\n')
                for gap_line in range(prev_end_line + 1, cl):
                    line_content = lines[gap_line - 1] if gap_line <= len(lines) else ''
                    if line_content.strip() == '':
                        result.append(BlankLine(position=Position(
                            origin=origin, line=gap_line, column=1)))
            result.append(comment)
            if isinstance(comment, CommentLine):
                prev_end_line = comment.position.line
            else:
                prev_end_line = comment.position.line + comment.text.count('\n')
            comment_idx += 1

        result.append(node)
        node_end = node.position.line
        if hasattr(node, 'position') and node.position and node.position.end_offset > 0:
            node_end = code[:node.position.end_offset].count('\n') + 1
        prev_end_line = max(prev_end_line, node_end)

    while comment_idx < len(comments):
        comment = comments[comment_idx]
        result.append(comment)
        comment_idx += 1

    return result


# --- Public API ---

def parse_ast(code: str, origin: str = "<string>", source_map: "SourceMap | None" = None) -> list[ASTNode] | None:
    """Parse OpenSCAD code and return AST nodes.

    Args:
        code: The OpenSCAD source code string to parse.
        origin: Origin identifier for source position tracking.
        source_map: Optional SourceMap for tracking positions across multiple origins.

    Returns:
        List of top-level AST nodes, or None on syntax error.
    """
    parser = _get_parser()
    try:
        tree = parser.parse(code)
    except UnexpectedInput as e:
        line = getattr(e, 'line', None) or 0
        column = getattr(e, 'column', None) or 0

        if source_map is not None:
            char_pos = getattr(e, 'pos_in_stream', 0) or 0
            location = source_map.get_location(char_pos)
            error_origin = location.origin
            error_line = location.line
            error_column = location.column
            combined_code = source_map.get_combined_string()
        else:
            error_origin = origin
            error_line = line
            error_column = column
            combined_code = code

        lines = combined_code.split('\n')
        print(f"Syntax error in {error_origin} at line {error_line}, column {error_column}:")
        if 1 <= error_line <= len(lines):
            error_line_text = lines[error_line - 1]
            print(error_line_text)
            caret_pos = max(0, error_column - 1)
            if caret_pos > len(error_line_text):
                caret_pos = len(error_line_text)
            expanded_caret_pos = len(error_line_text[:caret_pos].expandtabs())
            print(' ' * expanded_caret_pos + '^')
        return None

    transformer = OpenSCADTransformer(origin=origin)
    result = transformer.transform(tree)
    if isinstance(result, list):
        return result
    return [result] if result is not None else []


def getASTfromString(code: str, include_comments: bool = False, origin: str = "<string>") -> list[ASTNode] | None:
    """Parse OpenSCAD source code from a string and return its AST.

    Args:
        code: The OpenSCAD source code to parse.
        include_comments: If True, include comments in the AST.
        origin: Origin identifier for source location tracking.

    Returns:
        List of AST nodes, or None if the code contains syntax errors.

    Example:
        ast = getASTfromString("cube([1,2,3]);")
    """
    source_map = SourceMap()
    source_map.add_origin(origin, code)

    ast = parse_ast(code, origin=origin, source_map=source_map)

    if ast is not None and include_comments:
        ast = _attach_all_comments(ast, code, origin)

    return ast


def _windows_documents_dir() -> str:
    """Where Windows says My Documents is -- the same SHGetFolderPathW(
    CSIDL_PERSONAL, SHGFP_TYPE_CURRENT) call OpenSCAD makes -- rather than
    assuming ~/Documents: OneDrive's Known Folder Move, on by default, puts
    it at ~/OneDrive/Documents instead."""
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(260)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf) == 0:  # CSIDL_PERSONAL, SHGFP_TYPE_CURRENT
            return buf.value
    except (AttributeError, OSError):  # not actually on Windows
        pass
    return os.path.join(os.path.expanduser("~"), "Documents")


def librarySearchDirs(currfile: str) -> list[str]:
    """The directories `include`/`use` search, in order, as OpenSCAD's
    parser_init() builds them: the including file's own directory, then
    every OPENSCADPATH entry, then the user's libraries folder.

    OPENSCADPATH adds to the libraries folder rather than replacing it --
    it used to replace it, so setting it for one library hid every other
    one, a BOSL2 in the default folder included.
    """
    dirs = []
    if currfile:
        dirs.append(os.path.dirname(os.path.abspath(currfile)))

    system = platform.system()
    pathsep = ";" if system == "Windows" else ":"
    for path in os.getenv("OPENSCADPATH", "").split(pathsep):
        expanded_path = os.path.expandvars(path)
        if expanded_path:
            dirs.append(expanded_path)

    if system == "Windows":
        dirs.append(os.path.join(_windows_documents_dir(), "OpenSCAD", "libraries"))
    elif system == "Darwin":
        dirs.append(os.path.expanduser("~/Documents/OpenSCAD/libraries"))
    elif system == "Linux":
        dirs.append(os.path.expanduser("~/.local/share/OpenSCAD/libraries"))
    return dirs


def findLibraryFile(currfile: str, libfile: str) -> Optional[str]:
    """Find a library file using OpenSCAD's search path rules: the first
    directory in librarySearchDirs(currfile) that holds it.

    Args:
        currfile: Full path to the current OpenSCAD file (can be empty string).
        libfile: Partial or full path to the library file to find.

    Returns:
        Full path to the found library file, or None if not found.
    """
    for d in librarySearchDirs(currfile):
        test_file = os.path.join(d, libfile)
        if os.path.isfile(test_file):
            return test_file
    return None


def _not_found(what: str, filename: str, currfile: str) -> str:
    """A not-found message that lists every directory searched. Naming only
    the includer read as "only there was searched"."""
    return f"{what} '{filename}' not found. Searched:" + "".join(
        f"\n  {d}" for d in librarySearchDirs(currfile))


_find_library_file = findLibraryFile


# --- AST caching (in-memory) ---

_ast_cache: dict[tuple[str, bool, bool], tuple[list[ASTNode] | None, float]] = {}
_resolved_cache: dict[tuple[str, bool, bool, bool], tuple[list[ASTNode] | None, float]] = {}


def clear_ast_cache():
    """Clear the in-memory AST cache."""
    _ast_cache.clear()
    _resolved_cache.clear()


# --- Disk caching ---

def _get_disk_cache_dir() -> Optional[str]:
    cache_dir = os.environ.get('OPENSCAD_PARSER_CACHE_DIR')
    if not cache_dir:
        home = os.path.expanduser('~')
        if platform.system() == 'Darwin':
            cache_dir = os.path.join(home, 'Library', 'Caches', 'openscad_lalr_parser')
        elif platform.system() == 'Windows':
            cache_dir = os.path.join(os.environ.get('LOCALAPPDATA', home), 'openscad_lalr_parser', 'cache')
        else:
            cache_dir = os.path.join(home, '.cache', 'openscad_lalr_parser')
    try:
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir
    except OSError:
        return None


@functools.lru_cache(maxsize=None)
def _ast_format_tag() -> str:
    """Changes whenever the grammar or the AST classes do, so a pickled AST
    from another version is never served: an older pickle lacks any field
    added since (RangeLiteral.implicit_step, say) and would raise on access."""
    here = Path(__file__).parent
    h = hashlib.sha256()
    for name in ("grammar.lark", "nodes.py", "transformer.py", "__init__.py"):
        h.update((here / name).read_bytes())
    return h.hexdigest()[:16]


def _disk_cache_path(file_path: str, include_comments: bool) -> Optional[str]:
    cache_dir = _get_disk_cache_dir()
    if not cache_dir:
        return None
    key = f"{file_path}:{include_comments}:{_STRICT_COMMAS.get()}:{_ast_format_tag()}"
    h = hashlib.sha256(key.encode()).hexdigest()[:16]
    return os.path.join(cache_dir, f"{h}.pickle")


def _load_from_disk_cache(file_path: str, include_comments: bool, current_mtime: float) -> Optional[list[ASTNode]]:
    cache_path = _disk_cache_path(file_path, include_comments)
    if not cache_path or not os.path.exists(cache_path):
        return None
    try:
        with open(cache_path, 'rb') as f:
            cached_mtime, ast = pickle.load(f)
        if cached_mtime == current_mtime:
            return ast
    except (OSError, pickle.UnpicklingError, ValueError, EOFError):
        pass
    return None


def _save_to_disk_cache(file_path: str, include_comments: bool, mtime: float, ast: list[ASTNode] | None):
    cache_path = _disk_cache_path(file_path, include_comments)
    if not cache_path:
        return
    try:
        with open(cache_path, 'wb') as f:
            pickle.dump((mtime, ast), f, protocol=pickle.HIGHEST_PROTOCOL)
    except OSError:
        return
    cache_fname = os.path.basename(cache_path)
    _manifest_update(cache_fname, file_path)
    _evict_stale_cache()


def _manifest_path() -> Optional[str]:
    cache_dir = _get_disk_cache_dir()
    if not cache_dir:
        return None
    return os.path.join(cache_dir, "manifest.json")


def _manifest_load() -> dict[str, str]:
    path = _manifest_path()
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _manifest_save(manifest: dict[str, str]):
    path = _manifest_path()
    if not path:
        return
    try:
        with open(path, 'w') as f:
            json.dump(manifest, f)
    except OSError:
        pass


def _manifest_update(cache_fname: str, source_path: str):
    manifest = _manifest_load()
    manifest[cache_fname] = source_path
    _manifest_save(manifest)


def _evict_stale_cache():
    cache_dir = _get_disk_cache_dir()
    if not cache_dir:
        return
    manifest = _manifest_load()
    if not manifest:
        return
    stale_keys = [
        fname for fname, source_path in manifest.items()
        if not os.path.exists(source_path)
    ]
    if not stale_keys:
        return
    for fname in stale_keys:
        cache_file = os.path.join(cache_dir, fname)
        try:
            os.remove(cache_file)
        except OSError:
            pass
        del manifest[fname]
    _manifest_save(manifest)


def clear_disk_cache():
    """Clear the on-disk AST cache."""
    cache_dir = _get_disk_cache_dir()
    if cache_dir and os.path.isdir(cache_dir):
        for fname in os.listdir(cache_dir):
            if fname.endswith('.pickle') or fname == 'manifest.json':
                try:
                    os.remove(os.path.join(cache_dir, fname))
                except OSError:
                    pass


# --- File parsing with caching ---

def _parse_single_file(file_path: str, include_comments: bool = False) -> list[ASTNode] | None:
    """Parse a single file without resolving includes. Uses memory and disk cache."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} not found")

    current_mtime = os.path.getmtime(file_path)
    cache_key = (file_path, include_comments, _STRICT_COMMAS.get())

    if cache_key in _ast_cache:
        cached_ast, cached_mtime = _ast_cache[cache_key]
        if cached_mtime == current_mtime:
            return cached_ast

    disk_result = _load_from_disk_cache(file_path, include_comments, current_mtime)
    if disk_result is not None:
        _ast_cache[cache_key] = (disk_result, current_mtime)
        return disk_result

    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    source_map = SourceMap()
    source_map.add_origin(file_path, code)

    ast = parse_ast(code, origin=file_path, source_map=source_map)

    if ast is not None and include_comments:
        ast = _attach_all_comments(ast, code, file_path)

    _ast_cache[cache_key] = (ast, current_mtime)
    _save_to_disk_cache(file_path, include_comments, current_mtime, ast)

    return ast


def _resolve_includes(ast_nodes: list[ASTNode] | None, current_file: str,
                      include_comments: bool = False,
                      visited: set | None = None) -> list[ASTNode] | None:
    """Resolve IncludeStatement nodes by parsing and inlining referenced files."""
    if ast_nodes is None:
        return None
    if visited is None:
        visited = set()

    result = []
    for node in ast_nodes:
        if isinstance(node, IncludeStatement):
            filename = node.filepath.val
            lib_file = findLibraryFile(current_file, filename)
            if lib_file is None:
                raise FileNotFoundError(_not_found("Included file", filename, current_file))
            lib_file = os.path.abspath(lib_file)
            if lib_file in visited:
                continue
            visited.add(lib_file)
            included_ast = _parse_single_file(lib_file, include_comments)
            included_ast = _resolve_includes(included_ast, lib_file, include_comments, visited)
            if included_ast:
                result.extend(included_ast)
        else:
            result.append(node)
    return result


def getASTfromFile(file: str, include_comments: bool = False, process_includes: bool = True) -> list[ASTNode] | None:
    """Parse an OpenSCAD source file and return its AST.

    The function caches AST trees both in memory and on disk. Cache entries are
    automatically invalidated if a file's modification timestamp changes.

    Args:
        file: The OpenSCAD source file path to parse.
        include_comments: If True, include comments in the AST.
        process_includes: If True, process include statements and replace with file contents.

    Returns:
        List of AST nodes, or None if the file contains syntax errors.

    Raises:
        FileNotFoundError: If the specified file does not exist.

    Example:
        ast = getASTfromFile("my_model.scad")
    """
    file_path = os.path.abspath(file)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file} not found")

    current_mtime = os.path.getmtime(file_path)

    if not process_includes:
        return _parse_single_file(file_path, include_comments)

    resolved_key = (file_path, include_comments, True, _STRICT_COMMAS.get())
    if resolved_key in _resolved_cache:
        cached_ast, cached_mtime = _resolved_cache[resolved_key]
        if cached_mtime == current_mtime:
            return cached_ast

    ast = _parse_single_file(file_path, include_comments)
    visited = {file_path}
    ast = _resolve_includes(ast, file_path, include_comments, visited)
    _resolved_cache[resolved_key] = (ast, current_mtime)
    return ast


def getASTfromLibraryFile(currfile: str, libfile: str, include_comments: bool = False, process_includes: bool = True) -> tuple[list[ASTNode] | None, str]:
    """Find and parse an OpenSCAD library file using OpenSCAD's search path rules.

    Args:
        currfile: Full path to the current OpenSCAD file.
        libfile: Partial or full path to the library file to find and parse.
        include_comments: If True, include comments in the AST.
        process_includes: If True, process include statements.

    Returns:
        Tuple of (AST nodes, absolute file path).

    Raises:
        FileNotFoundError: If the library file cannot be found.

    Example:
        ast, path = getASTfromLibraryFile("/path/to/main.scad", "utils/math.scad")
    """
    found_file = findLibraryFile(currfile, libfile)

    if found_file is None:
        raise FileNotFoundError(_not_found("Library file", libfile, currfile))

    ast = getASTfromFile(found_file, include_comments=include_comments, process_includes=process_includes)
    return ast, os.path.abspath(found_file)
