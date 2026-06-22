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

import os
import platform
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


# --- Parser singleton ---

_GRAMMAR_PATH = Path(__file__).parent / "grammar.lark"

_parser_cache: dict[str, Lark] = {}


def _get_parser() -> Lark:
    """Get or create the cached Lark LALR parser."""
    key = "standard"
    if key not in _parser_cache:
        _parser_cache[key] = Lark(
            _GRAMMAR_PATH.read_text(),
            parser="lalr",
            propagate_positions=True,
            maybe_placeholders=False,
        )
    return _parser_cache[key]


# --- Public API ---

def parse_ast(code: str, origin: str = "<string>") -> list[ASTNode] | None:
    """Parse OpenSCAD code and return AST nodes.

    Args:
        code: The OpenSCAD source code string to parse.
        origin: Origin identifier for source position tracking.

    Returns:
        List of top-level AST nodes, or None on syntax error.
    """
    parser = _get_parser()
    try:
        tree = parser.parse(code)
    except UnexpectedInput as e:
        line = getattr(e, 'line', None) or 0
        column = getattr(e, 'column', None) or 0
        lines = code.split('\n')
        print(f"Syntax error in {origin} at line {line}, column {column}:")
        if 1 <= line <= len(lines):
            error_line = lines[line - 1]
            print(error_line)
            caret_pos = max(0, column - 1)
            if caret_pos > len(error_line):
                caret_pos = len(error_line)
            expanded_caret_pos = len(error_line[:caret_pos].expandtabs())
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
        include_comments: If True, include comments in the AST (not yet supported in LALR parser).
        origin: Origin identifier for source location tracking.

    Returns:
        List of AST nodes, or None if the code contains syntax errors.

    Example:
        ast = getASTfromString("cube([1,2,3]);")
    """
    return parse_ast(code, origin=origin)


def findLibraryFile(currfile: str, libfile: str) -> Optional[str]:
    """Find a library file using OpenSCAD's search path rules.

    Searches for the library file in the following order:
    1. Directory of the current file (if currfile is provided)
    2. Directories specified in OPENSCADPATH environment variable
    3. Platform-specific default library directories

    Args:
        currfile: Full path to the current OpenSCAD file (can be empty string).
        libfile: Partial or full path to the library file to find.

    Returns:
        Full path to the found library file, or None if not found.
    """
    dirs = []

    if currfile:
        dirs.append(os.path.dirname(os.path.abspath(currfile)))

    pathsep = ":"
    dflt_path = ""
    system = platform.system()

    if system == "Windows":
        dflt_path = os.path.join(os.path.expanduser("~"), "Documents", "OpenSCAD", "libraries")
        pathsep = ";"
    elif system == "Darwin":
        dflt_path = os.path.expanduser("~/Documents/OpenSCAD/libraries")
    elif system == "Linux":
        dflt_path = os.path.expanduser("~/.local/share/OpenSCAD/libraries")

    env = os.getenv("OPENSCADPATH", dflt_path)
    if env:
        for path in env.split(pathsep):
            expanded_path = os.path.expandvars(path)
            if expanded_path:
                dirs.append(expanded_path)

    for d in dirs:
        test_file = os.path.join(d, libfile)
        if os.path.isfile(test_file):
            return test_file

    return None


# --- AST caching ---

_ast_cache: dict[tuple[str, bool], tuple[list[ASTNode] | None, float]] = {}
_resolved_cache: dict[tuple[str, bool, bool], tuple[list[ASTNode] | None, float]] = {}


def clear_ast_cache():
    """Clear the in-memory AST cache."""
    _ast_cache.clear()
    _resolved_cache.clear()


def _parse_single_file(file_path: str, include_comments: bool = False) -> list[ASTNode] | None:
    """Parse a single file without resolving includes. Uses memory cache."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} not found")

    current_mtime = os.path.getmtime(file_path)
    cache_key = (file_path, include_comments)

    if cache_key in _ast_cache:
        cached_ast, cached_mtime = _ast_cache[cache_key]
        if cached_mtime == current_mtime:
            return cached_ast

    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    ast = parse_ast(code, origin=file_path)
    _ast_cache[cache_key] = (ast, current_mtime)
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
                raise FileNotFoundError(
                    f"Included file '{filename}' not found. "
                    f"Searched relative to: {current_file if current_file else 'current directory'}"
                )
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

    The function caches AST trees in memory. Cache entries are automatically
    invalidated if a file's modification timestamp changes.

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

    resolved_key = (file_path, include_comments, True)
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
        raise FileNotFoundError(
            f"Library file '{libfile}' not found in search paths. "
            f"Searched in: current file directory, OPENSCADPATH, and platform default paths."
        )

    ast = getASTfromFile(found_file, include_comments=include_comments, process_includes=process_includes)
    return ast, os.path.abspath(found_file)
