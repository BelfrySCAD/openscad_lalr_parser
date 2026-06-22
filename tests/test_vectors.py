"""Tests for vectors, ranges, and list comprehensions."""
from openscad_lalr_parser import (
    getASTfromString,
    Assignment,
    ListComprehension,
    RangeLiteral,
    NumberLiteral,
    StringLiteral,
    BooleanLiteral,
    Identifier,
    ListCompFor,
    ListCompCFor,
    ListCompIf,
    ListCompIfElse,
    ListCompLet,
    ListCompEach,
    PrimaryIndex,
)


class TestVectors:
    def test_empty_vector(self, parse):
        ast = parse("x = [];")
        assert isinstance(ast[0].expr, ListComprehension)
        assert len(ast[0].expr.elements) == 0

    def test_simple_vector(self, parse):
        ast = parse("x = [1, 2, 3];")
        assert isinstance(ast[0].expr, ListComprehension)
        assert len(ast[0].expr.elements) == 3

    def test_nested_vector(self, parse):
        ast = parse("x = [[1, 2], [3, 4]];")
        assert isinstance(ast[0].expr, ListComprehension)
        assert len(ast[0].expr.elements) == 2
        assert isinstance(ast[0].expr.elements[0], ListComprehension)

    def test_trailing_comma(self, parse):
        ast = parse("x = [1, 2, 3,];")
        assert isinstance(ast[0].expr, ListComprehension)
        assert len(ast[0].expr.elements) == 3

    def test_vector_str(self, parse):
        ast = parse("x = [1, 2, 3];")
        assert str(ast[0].expr) == "[1, 2, 3]"

    def test_vector_single_element(self, parse):
        """Test vector with single element."""
        ast = parse("x = [1];")
        assert isinstance(ast[0].expr, ListComprehension)
        assert len(ast[0].expr.elements) == 1

    def test_vector_mixed_types(self, parse):
        """Test vector with mixed types."""
        ast = parse('x = [1, "hello", true];')
        assert isinstance(ast[0].expr, ListComprehension)
        assert len(ast[0].expr.elements) == 3
        assert isinstance(ast[0].expr.elements[0], NumberLiteral)
        assert isinstance(ast[0].expr.elements[1], StringLiteral)
        assert isinstance(ast[0].expr.elements[2], BooleanLiteral)

    def test_vector_with_expressions(self, parse):
        """Test vector with expressions."""
        ast = parse("x = [1 + 2, 3 * 4, 5 / 6];")
        assert isinstance(ast[0].expr, ListComprehension)
        assert len(ast[0].expr.elements) == 3


class TestRanges:
    def test_two_part_range(self, parse):
        ast = parse("x = [0:10];")
        assert isinstance(ast[0].expr, RangeLiteral)
        assert ast[0].expr.start.val == 0.0
        assert ast[0].expr.end.val == 10.0
        assert ast[0].expr.step.val == 1.0

    def test_three_part_range(self, parse):
        ast = parse("x = [0:2:10];")
        assert isinstance(ast[0].expr, RangeLiteral)
        assert ast[0].expr.start.val == 0.0
        assert ast[0].expr.step.val == 2.0
        assert ast[0].expr.end.val == 10.0

    def test_range_str(self, parse):
        ast = parse("x = [0:2:10];")
        assert "0" in str(ast[0].expr)
        assert "10" in str(ast[0].expr)

    def test_range_negative(self, parse):
        """Test range with negative numbers."""
        ast = parse("x = [-5:5];")
        assert isinstance(ast[0].expr, RangeLiteral)

    def test_range_expressions(self, parse):
        """Test range with expressions."""
        ast = parse("x = [0:2*5:10];")
        assert isinstance(ast[0].expr, RangeLiteral)


class TestListComprehensions:
    def test_for_comprehension(self, parse):
        ast = parse("x = [for (i=[0:5]) i];")
        assert isinstance(ast[0].expr, ListComprehension)
        assert len(ast[0].expr.elements) == 1
        assert isinstance(ast[0].expr.elements[0], ListCompFor)

    def test_c_for_comprehension(self, parse):
        ast = parse("x = [for (i=0; i<5; i=i+1) i];")
        assert isinstance(ast[0].expr, ListComprehension)
        assert isinstance(ast[0].expr.elements[0], ListCompCFor)

    def test_if_comprehension(self, parse):
        ast = parse("x = [for (i=[0:5]) if (i > 2) i];")
        lc = ast[0].expr
        assert isinstance(lc, ListComprehension)
        for_elem = lc.elements[0]
        assert isinstance(for_elem, ListCompFor)
        assert isinstance(for_elem.body, ListCompIf)

    def test_ifelse_comprehension(self, parse):
        ast = parse("x = [for (i=[0:5]) if (i > 2) i else -i];")
        lc = ast[0].expr
        for_elem = lc.elements[0]
        assert isinstance(for_elem, ListCompFor)
        assert isinstance(for_elem.body, ListCompIfElse)

    def test_let_comprehension(self, parse):
        ast = parse("x = [let (a=1) for (i=[0:3]) i];")
        assert isinstance(ast[0].expr, ListComprehension)
        assert isinstance(ast[0].expr.elements[0], ListCompLet)

    def test_let_expr_in_vector(self, parse):
        ast = parse("x = [let (a=1) a];")
        assert isinstance(ast[0].expr, ListComprehension)
        from openscad_lalr_parser import LetOp
        assert isinstance(ast[0].expr.elements[0], LetOp)

    def test_each_comprehension(self, parse):
        ast = parse("x = [each [1, 2, 3]];")
        assert isinstance(ast[0].expr, ListComprehension)
        assert isinstance(ast[0].expr.elements[0], ListCompEach)

    def test_multiple_assignments_for(self, parse):
        ast = parse("x = [for (i=[0:2], j=[0:2]) [i, j]];")
        lc = ast[0].expr
        for_elem = lc.elements[0]
        assert isinstance(for_elem, ListCompFor)
        assert len(for_elem.assignments) == 2

    def test_each_ast_detail(self, parse):
        ast = parse("x = [each [1, 2, 3]];")
        outer = ast[0].expr
        assert isinstance(outer, ListComprehension)
        assert len(outer.elements) == 1
        each = outer.elements[0]
        assert isinstance(each, ListCompEach)
        inner = each.body
        assert isinstance(inner, ListComprehension)
        assert len(inner.elements) == 3
        assert all(isinstance(e, NumberLiteral) for e in inner.elements)

    def test_each_str(self, parse):
        ast = parse("x = [each [1, 2, 3]];")
        assert str(ast[0].expr) == "[each [1, 2, 3]]"

    def test_each_in_for(self, parse):
        ast = parse("x = [for (i = [0:2]) each [i, i+1]];")
        lc = ast[0].expr
        assert isinstance(lc.elements[0], ListCompFor)

    def test_nested_each(self, parse):
        ast = parse("x = [each [each [1, 2, 3]]];")
        outer = ast[0].expr
        each = outer.elements[0]
        assert isinstance(each, ListCompEach)

    def test_for_if_comprehension(self, parse):
        ast = parse("x = [for (i = [0:10]) if (i % 2 == 0) i * 2];")
        assert isinstance(ast[0].expr, ListComprehension)

    def test_for_let_if_comprehension(self, parse):
        ast = parse("x = [for (i = [0:10]) let(j = i * 2) if (j > 5) j];")
        assert isinstance(ast[0].expr, ListComprehension)

    def test_paren_listcomp(self, parse):
        ast = parse("x = [(for (i = [0:3]) i)];")
        assert isinstance(ast[0].expr, ListComprehension)
        assert len(ast[0].expr.elements) == 1
        assert isinstance(ast[0].expr.elements[0], ListCompFor)

    def test_two_for_elements(self, parse):
        ast = parse("x = [for (i = [0:3]) i, for (j = [0:2]) j];")
        comp = ast[0].expr
        assert isinstance(comp, ListComprehension)
        assert len(comp.elements) == 2
        assert all(isinstance(e, ListCompFor) for e in comp.elements)

    def test_mixed_elements(self, parse):
        ast = parse("x = [1, for (i = [0:2]) i, 3];")
        comp = ast[0].expr
        assert isinstance(comp, ListComprehension)
        assert len(comp.elements) == 3

    def test_listcomp_for_expression(self, parse):
        """Test list comprehension with expression body."""
        ast = parse("x = [for (i = [0:5]) i * 2];")
        assert isinstance(ast[0].expr, ListComprehension)
        assert isinstance(ast[0].expr.elements[0], ListCompFor)

    def test_listcomp_for_nested(self, parse):
        """Test nested list comprehension."""
        ast = parse("x = [for (i = [0:5]) [for (j = [0:3]) i + j]];")
        assert isinstance(ast[0].expr, ListComprehension)
        assert isinstance(ast[0].expr.elements[0], ListCompFor)

    def test_listcomp_if_nested(self, parse):
        """Test nested if in list comprehension."""
        ast = parse("x = [for (i = [0:5]) if (i > 0) if (i < 5) i];")
        assert isinstance(ast[0].expr, ListComprehension)

    def test_listcomp_let_simple(self, parse):
        """Test list comprehension with let inside for."""
        ast = parse("x = [for (i = [0:5]) let(j = i * 2) j];")
        assert isinstance(ast[0].expr, ListComprehension)

    def test_listcomp_let_multiple(self, parse):
        """Test list comprehension with multiple let assignments."""
        ast = parse("x = [for (i = [0:5]) let(j = i * 2, k = j + 1) k];")
        assert isinstance(ast[0].expr, ListComprehension)

    def test_listcomp_let_nested(self, parse):
        """Test nested let in list comprehension."""
        ast = parse("x = [for (i = [0:5]) let(j = i * 2) let(k = j + 1) k];")
        assert isinstance(ast[0].expr, ListComprehension)

    def test_listcomp_nested_complex(self, parse):
        """Test complex nested list comprehension."""
        ast = parse("x = [for (i = [0:5]) [for (j = [0:3]) if (i + j > 3) i + j]];")
        assert isinstance(ast[0].expr, ListComprehension)

    def test_listcomp_parentheses(self, parse):
        """Test list comprehension with parenthesised body expression."""
        ast = parse("x = [for (i = [0:5]) (i * 2)];")
        assert isinstance(ast[0].expr, ListComprehension)

    def test_listcomp_nested_parentheses(self, parse):
        """Test list comprehension with nested parenthesised for."""
        ast = parse("x = [for (i = [0:5]) (for (j = [0:3]) i + j)];")
        assert isinstance(ast[0].expr, ListComprehension)

    def test_listcomp_paren_expr_ast(self, parse):
        """Parenthesised listcomp element builds correct AST."""
        ast = parse("x = [(for (i = [0:3]) i)];")
        assert isinstance(ast[0], Assignment)
        comp = ast[0].expr
        assert isinstance(comp, ListComprehension)
        assert len(comp.elements) == 1
        assert isinstance(comp.elements[0], ListCompFor)


class TestListCompCFor:
    def test_one_init_one_incr(self, parse):
        ast = parse("x = [for (i = 0; i < 5; i = i + 1) i];")
        cfor = ast[0].expr.elements[0]
        assert isinstance(cfor, ListCompCFor)
        assert len(cfor.inits) == 1
        assert len(cfor.incrs) == 1

    def test_two_inits(self, parse):
        ast = parse("x = [for (i = 0, j = 1; i < 5; i = i + 1) i];")
        cfor = ast[0].expr.elements[0]
        assert isinstance(cfor, ListCompCFor)
        assert len(cfor.inits) == 2
        assert all(isinstance(a, Assignment) for a in cfor.inits)

    def test_two_incrs(self, parse):
        ast = parse("x = [for (i = 0; i < 5; i = i + 1, j = i * 2) i];")
        cfor = ast[0].expr.elements[0]
        assert isinstance(cfor, ListCompCFor)
        assert len(cfor.incrs) == 2
        assert all(isinstance(a, Assignment) for a in cfor.incrs)

    def test_both_zero(self, parse):
        """Test C-for with zero inits and zero incrs."""
        ast = parse("x = [for ( ; i < 5 ; ) i];")
        cfor = ast[0].expr.elements[0]
        assert isinstance(cfor, ListCompCFor)
        assert cfor.inits == []
        assert cfor.incrs == []

    def test_zero_inits(self, parse):
        """Test C-for with zero inits."""
        ast = parse("x = [for ( ; i < 5 ; i = i + 1) i];")
        cfor = ast[0].expr.elements[0]
        assert isinstance(cfor, ListCompCFor)
        assert cfor.inits == []
        assert isinstance(cfor.inits, list)

    def test_one_init(self, parse):
        """Test C-for with one init."""
        ast = parse("x = [for (i = 0 ; i < 5 ; i = i + 1) i];")
        cfor = ast[0].expr.elements[0]
        assert isinstance(cfor, ListCompCFor)
        assert len(cfor.inits) == 1
        assert isinstance(cfor.inits, list)
        assert all(isinstance(a, Assignment) for a in cfor.inits)

    def test_three_inits(self, parse):
        """Test C-for with three inits."""
        ast = parse("x = [for (i = 0, j = 1, k = 2 ; i < 5 ; i = i + 1) i];")
        cfor = ast[0].expr.elements[0]
        assert isinstance(cfor, ListCompCFor)
        assert len(cfor.inits) == 3
        assert isinstance(cfor.inits, list)
        assert all(isinstance(a, Assignment) for a in cfor.inits)

    def test_zero_incrs(self, parse):
        """Test C-for with zero incrs."""
        ast = parse("x = [for (i = 0 ; i < 5 ; ) i];")
        cfor = ast[0].expr.elements[0]
        assert isinstance(cfor, ListCompCFor)
        assert cfor.incrs == []
        assert isinstance(cfor.incrs, list)

    def test_one_incr(self, parse):
        """Test C-for with one incr."""
        ast = parse("x = [for (i = 0 ; i < 5 ; i = i + 1) i];")
        cfor = ast[0].expr.elements[0]
        assert isinstance(cfor, ListCompCFor)
        assert len(cfor.incrs) == 1
        assert isinstance(cfor.incrs, list)
        assert all(isinstance(a, Assignment) for a in cfor.incrs)

    def test_three_incrs(self, parse):
        """Test C-for with three incrs."""
        ast = parse("x = [for (i = 0 ; i < 5 ; i = i + 1, j = i * 2, k = 3) i];")
        cfor = ast[0].expr.elements[0]
        assert isinstance(cfor, ListCompCFor)
        assert len(cfor.incrs) == 3
        assert isinstance(cfor.incrs, list)
        assert all(isinstance(a, Assignment) for a in cfor.incrs)


class TestListCompForAssignments:
    def test_one_assignment(self, parse):
        ast = parse("x = [for (i = [0:5]) i];")
        lc = ast[0].expr.elements[0]
        assert isinstance(lc, ListCompFor)
        assert len(lc.assignments) == 1
        assert all(isinstance(a, Assignment) for a in lc.assignments)

    def test_two_assignments(self, parse):
        ast = parse("x = [for (i = [0:5], j = [0:3]) i + j];")
        lc = ast[0].expr.elements[0]
        assert isinstance(lc, ListCompFor)
        assert len(lc.assignments) == 2

    def test_three_assignments(self, parse):
        ast = parse("x = [for (i = [0:5], j = [0:3], k = [0:2]) i + j + k];")
        lc = ast[0].expr.elements[0]
        assert isinstance(lc, ListCompFor)
        assert len(lc.assignments) == 3


class TestListCompLetAssignments:
    def test_one_assignment(self, parse):
        ast = parse("x = [let(a = 1) for (i = [0:3]) a + i];")
        lc = ast[0].expr.elements[0]
        assert isinstance(lc, ListCompLet)
        assert len(lc.assignments) == 1

    def test_two_assignments(self, parse):
        ast = parse("x = [let(a = 1, b = 2) for (i = [0:3]) a + b + i];")
        lc = ast[0].expr.elements[0]
        assert isinstance(lc, ListCompLet)
        assert len(lc.assignments) == 2

    def test_three_assignments(self, parse):
        ast = parse("x = [let(a = 1, b = 2, c = 3) for (i = [0:3]) a + b + c + i];")
        lc = ast[0].expr.elements[0]
        assert isinstance(lc, ListCompLet)
        assert len(lc.assignments) == 3


class TestVectorOperations:
    """Test vector operations."""

    def test_vector_assignment(self, parse):
        """Test vector assignment."""
        ast = parse("x = [1, 2, 3];")
        assert ast is not None
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, ListComprehension)

    def test_vector_in_function(self, parse):
        """Test vector in function call."""
        ast = parse("cube([10, 20, 30]);")
        assert ast is not None

    def test_vector_in_expression(self, parse):
        """Test vector in expression."""
        ast = parse("x = [1, 2, 3] + [4, 5, 6];")
        assert ast is not None

    def test_vector_access(self, parse):
        """Test vector element access."""
        ast = parse("x = vec[0];")
        assert ast is not None
        assert isinstance(ast[0], Assignment)
