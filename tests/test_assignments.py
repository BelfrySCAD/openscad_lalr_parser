"""Tests for variable assignments."""
from openscad_lalr_parser import (
    getASTfromString,
    Assignment,
    NumberLiteral,
    Identifier,
    AdditionOp,
    ModuleDeclaration,
    ModularCall,
    ModularFor,
    ModularLet,
)


class TestAssignments:
    def test_simple_assignment(self, parse):
        ast = parse("x = 10;")
        assert isinstance(ast[0], Assignment)
        assert ast[0].name.name == "x"
        assert isinstance(ast[0].expr, NumberLiteral)
        assert ast[0].expr.val == 10.0

    def test_expression_assignment(self, parse):
        ast = parse("y = x + 5;")
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, AdditionOp)

    def test_multiple_assignments(self, parse):
        ast = parse("x = 1;\ny = 2;\nz = 3;")
        assert len(ast) == 3
        assert all(isinstance(a, Assignment) for a in ast)

    def test_assignment_str(self, parse):
        ast = parse("x = 10;")
        assert str(ast[0]) == "x = 10"

    def test_dollar_var_assignment(self, parse):
        ast = parse("$fn = 64;")
        assert ast[0].name.name == "$fn"

    def test_assignment_position(self, parse):
        ast = parse("x = 10;")
        assert ast[0].position is not None
        assert ast[0].position.line == 1

    def test_assignment_with_expression(self, parse):
        """Test assignment with expression."""
        ast = parse("x = 1 + 2;")
        assert ast is not None
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, AdditionOp)

    def test_assignment_in_block(self, parse):
        """Test assignment in block."""
        ast = parse("module wrapper() { x = 1; y = 2; }")
        assert ast is not None
        decl = ast[0]
        assert isinstance(decl, ModuleDeclaration)
        # Assignments inside a module block become children
        assignments = [c for c in decl.children if isinstance(c, Assignment)]
        assert len(assignments) == 2

    def test_assignment_in_module(self, parse):
        """Test assignment in module."""
        ast = parse("module test() { x = 1; }")
        assert ast is not None
        decl = ast[0]
        assert isinstance(decl, ModuleDeclaration)
        assignments = [c for c in decl.children if isinstance(c, Assignment)]
        assert len(assignments) == 1
        assert assignments[0].name.name == "x"


class TestStatements:
    """Test statement parsing."""

    def test_empty_statement(self, parse):
        """Test empty statement (bare semicolon)."""
        ast = parse("cube(1);;")
        assert ast is not None

    def test_multiple_empty_statements(self, parse):
        """Test multiple empty statements."""
        ast = parse("cube(1);;;")
        assert ast is not None

    def test_block_statement(self, parse):
        """Test block statement."""
        ast = parse("module wrapper() {}")
        assert ast is not None

    def test_block_with_statements(self, parse):
        """Test block with statements."""
        ast = parse("module wrapper() { x = 1; y = 2; }")
        assert ast is not None
        decl = ast[0]
        assert isinstance(decl, ModuleDeclaration)

    def test_nested_blocks(self, parse):
        """Test nested blocks."""
        ast = parse("module outer() { module inner() { x = 1; } }")
        assert ast is not None
        outer = ast[0]
        assert isinstance(outer, ModuleDeclaration)


class TestArgumentLists:
    """Test argument list parsing."""

    def test_empty_arguments(self, parse):
        """Test empty argument list."""
        ast = parse("test();")
        assert ast is not None
        assert isinstance(ast[0], ModularCall)
        assert len(ast[0].arguments) == 0

    def test_arguments_trailing_comma(self, parse):
        """Test arguments with trailing comma."""
        ast = parse("test(1, 2,);")
        assert ast is not None
        assert isinstance(ast[0], ModularCall)

    def test_arguments_named(self, parse):
        """Test named arguments."""
        ast = parse("test(x=1, y=2);")
        assert ast is not None
        assert isinstance(ast[0], ModularCall)
        assert len(ast[0].arguments) == 2

    def test_arguments_mixed(self, parse):
        """Test mixed positional and named arguments."""
        ast = parse("test(1, y=2);")
        assert ast is not None
        assert isinstance(ast[0], ModularCall)
        assert len(ast[0].arguments) == 2


class TestAssignmentExpressions:
    """Test assignment expressions (in for loops, etc.)."""

    def test_assignment_expr_simple(self, parse):
        """Test simple assignment expression in for loop."""
        ast = parse("for (i = [0:1]) cube(1);")
        assert ast is not None
        assert isinstance(ast[0], ModularFor)

    def test_assignment_expr_multiple(self, parse):
        """Test multiple assignment expressions in for loop."""
        ast = parse("for (i = [0:1], j = [0:1]) cube(1);")
        assert ast is not None
        assert isinstance(ast[0], ModularFor)

    def test_assignment_expr_in_let(self, parse):
        """Test assignment expression in let."""
        ast = parse("let(x = 1, y = 2) cube(1);")
        assert ast is not None
        assert isinstance(ast[0], ModularLet)


class TestScopeAnalysis:
    def test_build_scopes(self):
        from openscad_lalr_parser import getASTfromString, build_scopes
        ast = getASTfromString("x = 10;\ny = 20;")
        scope = build_scopes(ast)
        assert scope.lookup_variable("x") is not None
        assert scope.lookup_variable("y") is not None
        assert scope.lookup_variable("z") is None

    def test_function_scope(self):
        from openscad_lalr_parser import getASTfromString, build_scopes
        ast = getASTfromString("function add(a, b) = a + b;")
        scope = build_scopes(ast)
        assert scope.lookup_function("add") is not None
        assert scope.lookup_variable("add") is None

    def test_module_scope(self):
        from openscad_lalr_parser import getASTfromString, build_scopes
        ast = getASTfromString("module box(size) { cube(size); }")
        scope = build_scopes(ast)
        assert scope.lookup_module("box") is not None
