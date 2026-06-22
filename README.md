# openscad_lalr_parser

A fast LALR(1) parser for the OpenSCAD language with AST generation, powered by [Lark](https://github.com/lark-parser/lark).

[![Tests](https://github.com/BelfrySCAD/openscad_lalr_parser/actions/workflows/pytest.yml/badge.svg)](https://github.com/BelfrySCAD/openscad_lalr_parser/actions/workflows/pytest.yml)

## Overview

`openscad_lalr_parser` parses OpenSCAD source code using a Lark-based LALR(1) parser and produces
an abstract syntax tree (AST). The AST node classes are identical to those in the
[openscad_parser](https://github.com/BelfrySCAD/openscad_parser) library, enabling easy migration
between the two parsers.

### Why LALR?

- **Speed**: LALR(1) parsing is O(n) in the input size, making it significantly faster than PEG
  backtracking parsers for large files.
- **Predictability**: LALR parsers never backtrack, so parse time is always proportional to input size.
- **Compatibility**: Produces the same AST node types as `openscad_parser`.

## Installation

```bash
pip install openscad_lalr_parser
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

## API Reference

### Parsing Functions

| Function | Description |
|---|---|
| `getASTfromString(code, include_comments=False, origin="<string>")` | Parse an OpenSCAD code string and return its AST. |
| `getASTfromFile(file, include_comments=False, process_includes=True)` | Parse an OpenSCAD file and return its AST. Caches results by mtime. |
| `getASTfromLibraryFile(currfile, libfile, ...)` | Find and parse a library file using OpenSCAD's search path rules. |
| `parse_ast(code, origin="<string>")` | Low-level parse function returning AST nodes. |
| `findLibraryFile(currfile, libfile)` | Find a library file without parsing it. |
| `clear_ast_cache()` | Clear the in-memory AST cache. |

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
| AST nodes | Identical | Identical |
| Scope analysis | Yes | Yes |
| Comment preservation | Yes | Planned |
| Serialization (JSON/YAML) | Yes | Not yet |
| Pretty-printing | Yes | Not yet |
| Performance | Good | Faster for large files |

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
