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


# --- Comment extraction for include_comments mode ---

_COMMENT_RE = re.compile(
    r'//([^\n]*)'           # single-line comment
    r'|/\*([\s\S]*?)\*/'    # multi-line comment
    r'|"(?:[^"\\]|\\.)*"'   # string literal (skip)
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


def _inject_comments(ast_nodes: list[ASTNode], comments: list[ASTNode], code: str, origin: str) -> list[ASTNode]:
    """Merge comment nodes into AST node list based on source positions."""
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
                for gap_line in range(prev_end_line + 1, cl):
                    line_content = code.split('\n')[gap_line - 1] if gap_line <= len(code.split('\n')) else ''
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
        comments = _extract_comments(code, origin)
        ast = _inject_comments(ast, comments, code, origin)

    return ast


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


_find_library_file = findLibraryFile


# --- AST caching (in-memory) ---

_ast_cache: dict[tuple[str, bool], tuple[list[ASTNode] | None, float]] = {}
_resolved_cache: dict[tuple[str, bool, bool], tuple[list[ASTNode] | None, float]] = {}


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


def _disk_cache_path(file_path: str, include_comments: bool) -> Optional[str]:
    cache_dir = _get_disk_cache_dir()
    if not cache_dir:
        return None
    key = f"{file_path}:{include_comments}"
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
    cache_key = (file_path, include_comments)

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
        comments = _extract_comments(code, file_path)
        ast = _inject_comments(ast, comments, code, file_path)

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
