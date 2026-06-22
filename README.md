# openscad_lalr_parser

A fast LALR(1) parser for the OpenSCAD language with AST generation, powered by [Lark](https://github.com/lark-parser/lark).

[![Tests](https://github.com/BelfrySCAD/openscad_lalr_parser/actions/workflows/pytest.yml/badge.svg)](https://github.com/BelfrySCAD/openscad_lalr_parser/actions/workflows/pytest.yml)
[![PyPI version](https://img.shields.io/pypi/v/openscad-lalr-parser)](https://pypi.org/project/openscad-lalr-parser/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Overview

`openscad_lalr_parser` parses OpenSCAD source code using a Lark-based LALR(1) parser and produces
an abstract syntax tree (AST). The AST node classes are identical to those in the
[openscad_parser](https://github.com/BelfrySCAD/openscad_parser) library, making it a drop-in
replacement with significantly better performance.

### Why LALR?

- **Speed**: LALR(1) parsing is O(n) in the input size — no PEG backtracking overhead.
- **Predictability**: Parse time is always proportional to input size.
- **Compatibility**: Produces the same AST node types as `openscad_parser`.

## Installation

```bash
pip install openscad-lalr-parser
```

For YAML output support:

```bash
pip install openscad-lalr-parser[yaml]
```

### From Source

```bash
git clone https://github.com/BelfrySCAD/openscad_lalr_parser.git
cd openscad_lalr_parser
pip install -e ".[dev]"
```

## Quick Start

### Parse a String

```python
from openscad_lalr_parser import getASTfromString

ast = getASTfromString("cube([1, 2, 3]);")
for node in ast:
    print(node)
```

### Parse a File

```python
from openscad_lalr_parser import getASTfromFile

ast = getASTfromFile("model.scad")
for node in ast:
    print(node)
```

Files are cached by modification time — repeated calls to `getASTfromFile()` with the same
unchanged file return instantly. A disk cache is also maintained for persistence across
interpreter sessions.

### Include Comments

```python
ast = getASTfromString("""
    // A comment
    x = 42; /* inline */
""", include_comments=True)
```

Comments are returned as `CommentLine`, `CommentSpan`, and `BlankLine` nodes at the top level.
Inline comments adjacent to expressions are wrapped in `CommentedExpr` nodes with
`leading_comments` and `trailing_comments` fields.

### Scope Analysis

```python
from openscad_lalr_parser import getASTfromString, build_scopes

ast = getASTfromString('''
    x = 10;
    function double(n) = n * 2;
    module box(size) { cube(size); }
''')

root_scope = build_scopes(ast)
print(root_scope.lookup_variable("x"))
print(root_scope.lookup_function("double"))
print(root_scope.lookup_module("box"))
```

### Serialization

```python
from openscad_lalr_parser import getASTfromString, ast_to_json, ast_from_json

ast = getASTfromString("cube(10);")

# Serialize to JSON
json_str = ast_to_json(ast, indent=2)

# Deserialize back to AST nodes
ast2 = ast_from_json(json_str)
```

YAML serialization is available when PyYAML is installed:

```python
from openscad_lalr_parser import ast_to_yaml, ast_from_yaml

yaml_str = ast_to_yaml(ast)
ast2 = ast_from_yaml(yaml_str)
```

### Pretty-Printing

```python
from openscad_lalr_parser import getASTfromString, to_openscad

ast = getASTfromString("module box(w,h){cube([w,h,1]);}")
print(to_openscad(ast, indent_width=4))
```

Output:

```openscad
module box(w, h) {
    cube([w, h, 1]);
}
```

## CLI

The `openscad-lalr` command-line tool parses OpenSCAD files and outputs JSON, YAML, or
reformatted source.

```bash
# Parse to JSON (default)
openscad-lalr model.scad

# Pretty-print / reformat
openscad-lalr --format model.scad

# YAML output
openscad-lalr --yaml model.scad

# Read from stdin
echo 'cube(10);' | openscad-lalr -

# Include comments in output
openscad-lalr --with-comments model.scad

# Custom indentation
openscad-lalr --format --indent 2 model.scad

# Skip include resolution
openscad-lalr --no-includes model.scad
```

## API Reference

### Parsing Functions

| Function | Description |
|---|---|
| `getASTfromString(code, include_comments=False, origin="<string>")` | Parse OpenSCAD source code and return its AST. |
| `getASTfromFile(file, include_comments=False, process_includes=True)` | Parse a file with mtime-based caching and optional include resolution. |
| `getASTfromLibraryFile(currfile, libfile, ...)` | Find and parse a library file using OpenSCAD's search path rules. |
| `parse_ast(code, origin="<string>")` | Low-level parse returning AST nodes (no comment processing). |
| `findLibraryFile(currfile, libfile)` | Find a library file path without parsing it. |
| `clear_ast_cache()` | Clear the in-memory and on-disk AST caches. |

### Serialization Functions

| Function | Description |
|---|---|
| `ast_to_json(ast, indent=None)` | Serialize AST nodes to a JSON string. |
| `ast_from_json(json_str)` | Deserialize AST nodes from a JSON string. |
| `ast_to_dict(ast)` | Convert AST nodes to plain dicts. |
| `ast_from_dict(data)` | Reconstruct AST nodes from dicts. |
| `ast_to_yaml(ast)` | Serialize AST nodes to YAML (requires PyYAML). |
| `ast_from_yaml(yaml_str)` | Deserialize AST nodes from YAML. |
| `to_openscad(ast, indent_width=4)` | Pretty-print AST back to OpenSCAD source. |

### Scope Analysis

| Function / Class | Description |
|---|---|
| `build_scopes(ast)` | Build scope tree for top-level AST nodes. Returns root `Scope`. |
| `Scope` | Lexical scope with `lookup_variable()`, `lookup_function()`, `lookup_module()`. |

### AST Node Classes

All AST nodes inherit from `ASTNode`. The main categories are:

**Literals**: `Identifier`, `StringLiteral`, `NumberLiteral`, `BooleanLiteral`, `UndefinedLiteral`, `RangeLiteral`

**Operators**: `AdditionOp`, `SubtractionOp`, `MultiplicationOp`, `DivisionOp`, `ModuloOp`, `ExponentOp`, `UnaryMinusOp`, `LogicalAndOp`, `LogicalOrOp`, `LogicalNotOp`, `BitwiseAndOp`, `BitwiseOrOp`, `BitwiseNotOp`, `BitwiseShiftLeftOp`, `BitwiseShiftRightOp`, `EqualityOp`, `InequalityOp`, `GreaterThanOp`, `GreaterThanOrEqualOp`, `LessThanOp`, `LessThanOrEqualOp`, `TernaryOp`

**Expressions**: `PrimaryCall`, `PrimaryIndex`, `PrimaryMember`, `LetOp`, `EchoOp`, `AssertOp`, `FunctionLiteral`, `ListComprehension`

**List Comprehensions**: `ListCompFor`, `ListCompCFor`, `ListCompIf`, `ListCompIfElse`, `ListCompLet`, `ListCompEach`

**Declarations**: `Assignment`, `FunctionDeclaration`, `ModuleDeclaration`, `ParameterDeclaration`

**Module Instantiations**: `ModularCall`, `ModularFor`, `ModularIntersectionFor`, `ModularLet`, `ModularEcho`, `ModularAssert`, `ModularIf`, `ModularIfElse`

**Modifiers**: `ModularModifierShowOnly`, `ModularModifierHighlight`, `ModularModifierBackground`, `ModularModifierDisable`

**Imports**: `UseStatement`, `IncludeStatement`

**Arguments**: `PositionalArgument`, `NamedArgument`

**Comments**: `CommentLine`, `CommentSpan`, `CommentedExpr`, `BlankLine`

## Comparison with openscad_parser

| Feature | openscad_parser | openscad_lalr_parser |
|---|---|---|
| Parser type | PEG (Arpeggio) | LALR(1) (Lark) |
| AST nodes | ✓ | ✓ (identical) |
| Scope analysis | ✓ | ✓ |
| Comment preservation | ✓ | ✓ |
| Inline comment attachment | ✓ | ✓ |
| Serialization (JSON/YAML) | ✓ | ✓ |
| Pretty-printing | ✓ | ✓ |
| Source maps | — | ✓ |
| CLI tool | — | ✓ (`openscad-lalr`) |
| Disk caching | — | ✓ |
| Performance | Baseline | Faster (LALR, no backtracking) |

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Running Tests with Coverage

```bash
pytest tests/ --cov=src/openscad_lalr_parser --cov-report=term-missing
```

## License

MIT License - Copyright (c) 2025 Belfry OpenSCAD Libraries

See [LICENSE](LICENSE) for full text.
