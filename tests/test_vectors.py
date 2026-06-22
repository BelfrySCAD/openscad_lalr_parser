"""Tests for vectors, ranges, and list comprehensions."""
from openscad_lalr_parser import (
    getASTfromString,
    Assignment,
    ListComprehension,
    RangeLiteral,
    NumberLiteral,
    ListCompFor,
    ListCompCFor,
    ListCompIf,
    ListCompIfElse,
    ListCompLet,
    ListCompEach,
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
