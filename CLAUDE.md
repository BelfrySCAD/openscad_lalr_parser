# CLAUDE.md — OpenSCAD LALR Parser

## Build & Test

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src/openscad_lalr_parser --cov-report=term-missing
```

## Architecture

### Data Flow

```
OpenSCAD source code
    ↓
Lark LALR(1) Parser (grammar.lark)
    ↓
Lark Parse Tree
    ↓
OpenSCADTransformer (transformer.py)
    ↓
AST Nodes (nodes.py)
    ↓ (optional)
Comment Attachment (__init__.py — inline → CommentedExpr, standalone → top-level)
    ↓ (optional)
Scope Analysis (scope.py)
    ↓ (optional)
Serialization (serialization.py — JSON/YAML/dict) or Pretty-Print (pretty_print.py)
```

### Key Files

- `src/openscad_lalr_parser/grammar.lark` — Lark EBNF grammar for OpenSCAD (LALR(1))
- `src/openscad_lalr_parser/transformer.py` — Lark Transformer converting parse trees to AST nodes
- `src/openscad_lalr_parser/nodes.py` — All AST node dataclasses with `build_scope()` methods
- `src/openscad_lalr_parser/scope.py` — Scope class and `build_scopes()` function
- `src/openscad_lalr_parser/__init__.py` — Public API, comment attachment, caching (memory + disk)
- `src/openscad_lalr_parser/pretty_print.py` — `to_openscad()` AST-to-source formatter
- `src/openscad_lalr_parser/serialization.py` — JSON/YAML/dict serialize and deserialize
- `src/openscad_lalr_parser/source_map.py` — Source map for tracking origins across includes
- `src/openscad_lalr_parser/cli.py` — `openscad-lalr` CLI entry point

### Design Patterns

- **Transformer pattern**: `OpenSCADTransformer` uses Lark's `@v_args(meta=True)` to receive position metadata for every rule
- **Dataclass AST nodes**: All nodes are Python `@dataclass` with `position: Position` and optional `scope: Scope`
- **Transparent rules**: Expression precedence uses Lark's `?rule` syntax for transparent intermediate rules
- **Singleton parser**: The Lark parser is created once and cached in `_parser_cache`
- **Two-phase comment attachment**: Comments extracted separately (Lark `%ignore`), then classified as inline vs standalone and attached to AST nodes via `CommentedExpr` wrapping or top-level injection

### AST Node Hierarchy

```
ASTNode
├── Expression
│   ├── Primary (Identifier, StringLiteral, NumberLiteral, BooleanLiteral, UndefinedLiteral, RangeLiteral)
│   ├── Binary Ops (AdditionOp, SubtractionOp, ... EqualityOp, LogicalAndOp, etc.)
│   ├── Unary Ops (UnaryMinusOp, LogicalNotOp, BitwiseNotOp)
│   ├── TernaryOp, LetOp, EchoOp, AssertOp
│   ├── FunctionLiteral, PrimaryCall, PrimaryIndex, PrimaryMember
│   ├── ListComprehension, CommentedExpr
│   └── VectorElement subclasses (ListCompFor, ListCompIf, etc.)
├── ModuleInstantiation
│   ├── ModularCall, ModularFor, ModularIntersectionFor, ModularLet
│   ├── ModularEcho, ModularAssert, ModularIf, ModularIfElse
│   └── Modifiers (ShowOnly, Highlight, Background, Disable)
├── Assignment, ModuleDeclaration, FunctionDeclaration
├── UseStatement, IncludeStatement
└── Comments (CommentLine, CommentSpan, BlankLine)
```

### Test Organization

- `test_lexical.py` — Literals, identifiers
- `test_expressions.py` — Operators, precedence, postfix
- `test_vectors.py` — Vectors, ranges, list comprehensions
- `test_modules.py` — Module definitions, calls, modifiers
- `test_functions.py` — Function definitions, function literals
- `test_control.py` — if/else, for, let, echo, assert
- `test_use_include.py` — use/include statements
- `test_assignments.py` — Variable assignments, scope analysis
- `test_pretty_print.py` — Pretty-printer output, inline comments
- `test_ast_convenience.py` — Serialization, deserialization, AST utilities
- `test_source_map.py` — Source map tracking
- `test_complex.py` — Real-world OpenSCAD scenarios, edge cases
- `test_cli.py` — CLI argument handling, output formats
