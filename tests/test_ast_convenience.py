"""Tests for AST convenience functions: getASTfromString, getASTfromFile, getASTfromLibraryFile."""

import os
import sys
import time
import tempfile
from io import StringIO
import pytest
from openscad_lalr_parser import (
    getASTfromString,
    getASTfromFile,
    getASTfromLibraryFile,
    findLibraryFile,
    clear_ast_cache,
    Assignment,
    ModuleDeclaration,
    FunctionDeclaration,
    Identifier,
    NumberLiteral,
    AdditionOp,
    LogicalNotOp,
    BitwiseNotOp,
    IncludeStatement,
    Position,
    ModularCall,
    CommentLine,
    CommentSpan,
)


class TestGetASTfromString:
    def test_simple_assignment(self):
        code = "x = 42;"
        ast = getASTfromString(code)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 1
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].name, Identifier)
        assert ast[0].name.name == "x"
        assert isinstance(ast[0].expr, NumberLiteral)
        assert ast[0].expr.val == 42

    def test_complex_expression(self):
        code = "result = 10 + 5;"
        ast = getASTfromString(code)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 1
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, AdditionOp)
        assert isinstance(ast[0].expr.left, NumberLiteral)
        assert ast[0].expr.left.val == 10
        assert isinstance(ast[0].expr.right, NumberLiteral)
        assert ast[0].expr.right.val == 5

    def test_logical_not_expression(self):
        code = "x = !true;"
        ast = getASTfromString(code)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 1
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, LogicalNotOp)

    def test_bitwise_not_expression(self):
        code = "x = ~1;"
        ast = getASTfromString(code)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 1
        assert isinstance(ast[0], Assignment)
        assert isinstance(ast[0].expr, BitwiseNotOp)

    def test_module_declaration(self):
        code = "module test() { cube(10); }"
        ast = getASTfromString(code)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 1
        assert isinstance(ast[0], ModuleDeclaration)
        assert isinstance(ast[0].name, Identifier)
        assert ast[0].name.name == "test"

    def test_function_declaration(self):
        code = "function add(x, y) = x + y;"
        ast = getASTfromString(code)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 1
        assert isinstance(ast[0], FunctionDeclaration)
        assert isinstance(ast[0].name, Identifier)
        assert ast[0].name.name == "add"

    def test_empty_code(self):
        code = ""
        ast = getASTfromString(code)

        assert ast is None or (isinstance(ast, list) and len(ast) == 0)

    def test_multiple_statements(self):
        code = "x = 1; y = 2; z = 3;"
        ast = getASTfromString(code)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 3
        for i, assignment in enumerate(ast):
            assert isinstance(assignment, Assignment)
            assert assignment.name.name == ["x", "y", "z"][i]


class TestGetASTfromFile:
    def test_parse_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            test_file = f.name
            f.write("x = 42;")

        try:
            ast = getASTfromFile(test_file)

            assert ast is not None
            assert isinstance(ast, list)
            assert len(ast) == 1
            assert isinstance(ast[0], Assignment)
            assert ast[0].name.name == "x"
        finally:
            os.unlink(test_file)

    def test_file_caching(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            test_file = f.name
            f.write("x = 42;")

        try:
            ast1 = getASTfromFile(test_file)
            ast2 = getASTfromFile(test_file)

            assert ast1 is ast2
        finally:
            os.unlink(test_file)

    def test_cache_invalidation_on_modification(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            test_file = f.name
            f.write("x = 42;")

        try:
            ast1 = getASTfromFile(test_file)

            time.sleep(0.1)
            with open(test_file, 'w') as f:
                f.write("y = 100;")

            ast2 = getASTfromFile(test_file)

            assert ast1 is not None
            assert ast2 is not None
            assert ast1 is not ast2
            assert isinstance(ast1[0], Assignment)
            assert ast1[0].name.name == "x"
            assert isinstance(ast2[0], Assignment)
            assert ast2[0].name.name == "y"
        finally:
            os.unlink(test_file)

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            getASTfromFile("nonexistent_file.scad")

    def test_multiple_files_cached_independently(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f1:
            file1 = f1.name
            f1.write("x = 1;")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f2:
            file2 = f2.name
            f2.write("y = 2;")

        try:
            ast1a = getASTfromFile(file1)
            ast2a = getASTfromFile(file2)

            ast1b = getASTfromFile(file1)
            ast2b = getASTfromFile(file2)

            assert ast1a is ast1b
            assert ast2a is ast2b
            assert ast1a is not ast2a
        finally:
            os.unlink(file1)
            os.unlink(file2)

    def test_process_includes_false_keeps_include_nodes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")
            lib_file = os.path.join(temp_dir, "lib.scad")

            with open(lib_file, "w") as f:
                f.write("x = 1;")
            with open(main_file, "w") as f:
                f.write("include <lib.scad>;\n")

            ast = getASTfromFile(main_file, process_includes=False)
            assert ast is not None
            assert any(isinstance(node, IncludeStatement) for node in ast)

    def test_clear_cache(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            test_file = f.name
            f.write("x = 42;")

        try:
            ast1 = getASTfromFile(test_file)
            clear_ast_cache()
            ast2 = getASTfromFile(test_file)

            assert ast1 is not ast2
        finally:
            os.unlink(test_file)


class TestFindLibraryFile:
    def test_find_in_current_file_directory(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            current_file = f.name
            f.write("// main file")

        lib_dir = os.path.dirname(current_file)
        lib_file = os.path.join(lib_dir, "library.scad")
        with open(lib_file, 'w') as f:
            f.write("cube(10);")

        try:
            found = findLibraryFile(current_file, "library.scad")
            assert found == lib_file
        finally:
            os.unlink(current_file)
            os.unlink(lib_file)

    def test_find_with_nested_path(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            current_file = f.name
            f.write("// main file")

        lib_dir = os.path.dirname(current_file)
        utils_dir = os.path.join(lib_dir, "utils")
        os.makedirs(utils_dir, exist_ok=True)
        lib_file = os.path.join(utils_dir, "math.scad")
        with open(lib_file, 'w') as f:
            f.write("function add(x, y) = x + y;")

        try:
            found = findLibraryFile(current_file, "utils/math.scad")
            assert found == lib_file
        finally:
            os.unlink(current_file)
            os.unlink(lib_file)
            os.rmdir(utils_dir)

    def test_not_found_returns_none(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            current_file = f.name
            f.write("// main file")

        try:
            found = findLibraryFile(current_file, "nonexistent.scad")
            assert found is None
        finally:
            os.unlink(current_file)

    def test_empty_current_file(self):
        found = findLibraryFile("", "nonexistent.scad")
        assert found is None

    def test_find_library_file_windows_env_path(self, monkeypatch):
        import platform
        with tempfile.TemporaryDirectory() as temp_dir:
            lib_dir1 = os.path.join(temp_dir, "libs1")
            lib_dir2 = os.path.join(temp_dir, "libs2")
            os.makedirs(lib_dir1)
            os.makedirs(lib_dir2)
            target = os.path.join(lib_dir2, "lib.scad")
            with open(target, "w") as f:
                f.write("x = 1;")

            monkeypatch.setattr(platform, "system", lambda: "Windows")
            monkeypatch.setenv("OPENSCADPATH", f"{lib_dir1};{lib_dir2}")

            found = findLibraryFile("", "lib.scad")
            assert found == target

    def test_find_library_file_darwin_env_path(self, monkeypatch):
        import platform
        with tempfile.TemporaryDirectory() as temp_dir:
            lib_dir = os.path.join(temp_dir, "libraries")
            os.makedirs(lib_dir)
            target = os.path.join(lib_dir, "lib.scad")
            with open(target, "w") as f:
                f.write("x = 1;")

            monkeypatch.setattr(platform, "system", lambda: "Darwin")
            monkeypatch.setenv("OPENSCADPATH", lib_dir)

            found = findLibraryFile("", "lib.scad")
            assert found == target


class TestGetASTfromLibraryFile:
    def test_find_and_parse_library_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            current_file = f.name
            f.write("// main file")

        lib_dir = os.path.dirname(current_file)
        lib_file = os.path.join(lib_dir, "library.scad")
        with open(lib_file, 'w') as f:
            f.write("cube(10);")

        try:
            ast, path = getASTfromLibraryFile(current_file, "library.scad")

            assert ast is not None
            assert isinstance(ast, list)
            assert len(ast) >= 1
            assert isinstance(ast[0], ModularCall)
            assert ast[0].name.name == "cube"
            assert path == os.path.abspath(lib_file)
        finally:
            os.unlink(current_file)
            os.unlink(lib_file)

    def test_find_and_parse_nested_library_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            current_file = f.name
            f.write("// main file")

        lib_dir = os.path.dirname(current_file)
        utils_dir = os.path.join(lib_dir, "utils")
        os.makedirs(utils_dir, exist_ok=True)
        lib_file = os.path.join(utils_dir, "math.scad")
        with open(lib_file, 'w') as f:
            f.write("function add(x, y) = x + y;")

        try:
            ast, path = getASTfromLibraryFile(current_file, "utils/math.scad")

            assert ast is not None
            assert isinstance(ast, list)
            assert len(ast) == 1
            assert isinstance(ast[0], FunctionDeclaration)
            assert ast[0].name.name == "add"
            assert path == os.path.abspath(lib_file)
        finally:
            os.unlink(current_file)
            os.unlink(lib_file)
            os.rmdir(utils_dir)

    def test_library_file_not_found(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            current_file = f.name
            f.write("// main file")

        try:
            with pytest.raises(FileNotFoundError) as exc_info:
                getASTfromLibraryFile(current_file, "nonexistent.scad")

            assert "not found in search paths" in str(exc_info.value)
        finally:
            os.unlink(current_file)

    def test_library_file_caching(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            current_file = f.name
            f.write("// main file")

        lib_dir = os.path.dirname(current_file)
        lib_file = os.path.join(lib_dir, "library.scad")
        with open(lib_file, 'w') as f:
            f.write("cube(10);")

        try:
            ast1, path1 = getASTfromLibraryFile(current_file, "library.scad")
            ast2, path2 = getASTfromLibraryFile(current_file, "library.scad")

            assert ast1 is ast2
            assert path1 == path2
            assert path1 == os.path.abspath(lib_file)
        finally:
            os.unlink(current_file)
            os.unlink(lib_file)

    def test_without_current_file(self):
        with pytest.raises(FileNotFoundError):
            getASTfromLibraryFile("", "nonexistent_library.scad")


class TestIncludeComments:
    def test_getASTfromString_comments_excluded_by_default(self):
        code = "// This is a comment\nx = 5;"
        ast = getASTfromString(code)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 1
        assert isinstance(ast[0], Assignment)
        assert not any(isinstance(node, CommentLine) for node in ast)
        assert not any(isinstance(node, CommentSpan) for node in ast)

    def test_getASTfromString_comments_included_when_requested(self):
        code = "// This is a comment\nx = 5;"
        ast = getASTfromString(code, include_comments=True)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 2
        comment_nodes = [node for node in ast if isinstance(node, CommentLine)]
        assert len(comment_nodes) == 1
        assert comment_nodes[0].text == " This is a comment"
        assignment_nodes = [node for node in ast if isinstance(node, Assignment)]
        assert len(assignment_nodes) == 1

    def test_getASTfromString_multi_line_comment_included(self):
        code = "/* This is a\nmulti-line comment */\nx = 5;"
        ast = getASTfromString(code, include_comments=True)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 2
        comment_nodes = [node for node in ast if isinstance(node, CommentSpan)]
        assert len(comment_nodes) == 1
        assert "This is a\nmulti-line comment" in comment_nodes[0].text
        assignment_nodes = [node for node in ast if isinstance(node, Assignment)]
        assert len(assignment_nodes) == 1

    def test_getASTfromString_comments_excluded_when_false(self):
        code = "// This is a comment\nx = 5;"
        ast = getASTfromString(code, include_comments=False)

        assert ast is not None
        assert isinstance(ast, list)
        assert len(ast) == 1
        assert isinstance(ast[0], Assignment)
        assert not any(isinstance(node, CommentLine) for node in ast)

    def test_getASTfromFile_comments_excluded_by_default(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            f.write("// This is a comment\nx = 5;")
            temp_file = f.name

        try:
            ast = getASTfromFile(temp_file)

            assert ast is not None
            assert isinstance(ast, list)
            assert len(ast) == 1
            assert isinstance(ast[0], Assignment)
            assert not any(isinstance(node, CommentLine) for node in ast)
        finally:
            os.unlink(temp_file)

    def test_getASTfromFile_comments_included_when_requested(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            f.write("// This is a comment\nx = 5;")
            temp_file = f.name

        try:
            ast = getASTfromFile(temp_file, include_comments=True)

            assert ast is not None
            assert isinstance(ast, list)
            assert len(ast) == 2
            comment_nodes = [node for node in ast if isinstance(node, CommentLine)]
            assert len(comment_nodes) == 1
            assignment_nodes = [node for node in ast if isinstance(node, Assignment)]
            assert len(assignment_nodes) == 1
        finally:
            os.unlink(temp_file)

    def test_getASTfromFile_cache_separate_for_comments(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
            f.write("// This is a comment\nx = 5;")
            temp_file = f.name

        try:
            clear_ast_cache()

            ast1 = getASTfromFile(temp_file, include_comments=False)
            assert ast1 is not None
            assert len(ast1) == 1
            assert not any(isinstance(node, CommentLine) for node in ast1)

            ast2 = getASTfromFile(temp_file, include_comments=True)
            assert ast2 is not None
            assert len(ast2) == 2
            assert any(isinstance(node, CommentLine) for node in ast2)

            ast3 = getASTfromFile(temp_file, include_comments=False)
            assert ast3 is not None
            assert len(ast3) == 1
            assert not any(isinstance(node, CommentLine) for node in ast3)
        finally:
            os.unlink(temp_file)

    def test_getASTfromLibraryFile_comments_parameter(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            lib_file = os.path.join(temp_dir, "test_lib.scad")
            with open(lib_file, 'w') as f:
                f.write("// Library comment\nx = 5;")

            ast1, path1 = getASTfromLibraryFile("", lib_file, include_comments=False)
            assert ast1 is not None
            assert len(ast1) == 1
            assert not any(isinstance(node, CommentLine) for node in ast1)

            ast2, path2 = getASTfromLibraryFile("", lib_file, include_comments=True)
            assert ast2 is not None
            assert len(ast2) == 2
            assert any(isinstance(node, CommentLine) for node in ast2)


class TestCommentAttachment:
    """_attach_inline_comments/_attach_trailing_to_last_expr/_walk_attach's
    less-common paths: comments that can't attach to any specific
    sub-expression during the main walk and fall back to being attached as
    trailing on the nearest preceding top-level node instead, plus a few
    genuinely defensive branches exercised via direct calls (matching this
    module's own private-function-tests-directly convention, e.g.
    test_pretty_print.py's TestAsListHelper/TestCoalesceParenBracket)."""

    def test_comment_after_semicolon_attaches_as_trailing_fallback(self):
        # `// trailing` sits *after* the assignment's own closing `;`, so
        # it's outside the Assignment node's own position span and never
        # found "relevant" during _walk_attach's normal descent -- it's
        # picked up by _attach_inline_comments's fallback pass instead,
        # which walks _attach_trailing_to_last_expr.
        code = "// standalone\ncube(1); // trailing\n"
        ast = getASTfromString(code, include_comments=True)
        assert isinstance(ast[0], CommentLine)
        call = ast[1]
        assert isinstance(call, ModularCall)
        arg_expr = call.arguments[0].expr
        from openscad_lalr_parser.nodes import CommentedExpr
        assert isinstance(arg_expr, CommentedExpr)
        assert any("trailing" in str(c) for c in arg_expr.trailing_comments)

    def test_block_comment_with_no_preceding_code_but_trailing_code(self):
        # A CommentSpan with nothing before it on its own line is only
        # "inline" (not standalone) if there's real code *after* it on that
        # same line -- the specific condition _is_inline_comment checks
        # once its "something precedes it" check has already failed.
        code = "x = 1 +\n/* mid */ 2;\n"
        ast = getASTfromString(code, include_comments=True)
        assert len(ast) == 1  # attached inline, not a standalone top-level node

    def test_multiple_trailing_comments_on_same_target(self):
        # Two inline comments that both end up unused after the main walk
        # and both resolve to the same nearest-preceding node -- the second
        # one appends onto the first's already-wrapped CommentedExpr rather
        # than re-wrapping.
        code = "cube(1); /* one */ /* two */\n"
        ast = getASTfromString(code, include_comments=True)
        from openscad_lalr_parser.nodes import CommentedExpr
        arg_expr = ast[0].arguments[0].expr
        assert isinstance(arg_expr, CommentedExpr)

    def test_modifier_prefixed_call_comment_recurses_into_child(self):
        # ModularModifierShowOnly/Highlight/Background/Disable each carry a
        # single non-Expression `.child` field (the modified call) -- an
        # inline comment inside that child's own arguments is only found by
        # recursing into non_expr_children, not the direct expr_fields scan.
        code = "!cube(/* note */ 1);"
        ast = getASTfromString(code, include_comments=True)
        from openscad_lalr_parser.nodes import CommentedExpr, ModularModifierShowOnly
        assert isinstance(ast[0], ModularModifierShowOnly)
        arg_expr = ast[0].child.arguments[0].expr
        assert isinstance(arg_expr, CommentedExpr)

    def test_multiple_commented_statements_skip_already_used_comments(self):
        # Two separate statements each with their own inline comment --
        # exercises _walk_attach's per-node comment scan correctly skipping
        # a comment already consumed while processing an earlier node/field,
        # and skipping comments outside the current node's own span.
        code = "x = foo(/* a */ 2, 3 /* b */);\ny = bar(/* c */ 4);\n"
        ast = getASTfromString(code, include_comments=True)
        assert len(ast) == 2

    # --- Direct calls: genuinely defensive/unreachable-via-real-parsing branches ---

    def test_attach_inline_comments_skips_comment_nodes_in_ast_list(self):
        # _attach_inline_comments is always called (see getASTfromString's
        # own call order) *before* standalone comments are spliced into the
        # node list by _inject_comments, so its own "skip comment/blank-line
        # nodes while scanning for the nearest preceding real node" guard is
        # never actually exercised through the normal pipeline. Called
        # directly here with a hand-built ast_nodes list that already mixes
        # a comment node in, matching the shape a future caller passing an
        # already-comment-injected list would produce.
        from openscad_lalr_parser import _attach_inline_comments
        from openscad_lalr_parser.nodes import CommentedExpr, NumberLiteral

        lead_comment = CommentLine(position=Position(origin="<t>", line=1, column=1, start_offset=0, end_offset=5), text=" lead")
        a = Assignment(
            position=Position(origin="<t>", line=1, column=1, start_offset=6, end_offset=16),
            name=Identifier(position=Position(origin="<t>", line=1, column=1, start_offset=6, end_offset=7), name="x"),
            expr=NumberLiteral(position=Position(origin="<t>", line=1, column=1, start_offset=10, end_offset=11), val=1.0),
        )
        unused = CommentSpan(position=Position(origin="<t>", line=1, column=1, start_offset=20, end_offset=30), text=" trailing ")
        _attach_inline_comments([lead_comment, a], [unused])
        assert isinstance(a.expr, CommentedExpr)

    def test_walk_attach_no_op_on_already_wrapped_node(self):
        # _walk_attach's own early-return guard for a node that's already a
        # CommentedExpr/CommentLine/CommentSpan -- never reached through
        # real parsing (nothing recurses into an already-wrapped node), so
        # called directly.
        from openscad_lalr_parser import _walk_attach
        lead_comment = CommentLine(position=Position(origin="<t>", line=1, column=1, start_offset=0, end_offset=5), text=" x")
        assert _walk_attach(lead_comment, [], set()) is None

    def test_attach_trailing_to_last_expr_direct_expression_list_item(self):
        # A node whose relevant field is a list of *bare* Expressions
        # (rather than Expressions wrapped in Argument/Assignment
        # containers) -- ListComprehension.elements has this shape, but a
        # ListComprehension is never itself a fallback target through real
        # parsing (only top-level statements are); called directly against
        # one to exercise _attach_trailing_to_last_expr's own generic
        # field-introspection for this shape.
        from openscad_lalr_parser import _attach_trailing_to_last_expr
        from openscad_lalr_parser.nodes import CommentedExpr, ListComprehension, NumberLiteral
        pos = Position(origin="<t>", line=1, column=1, start_offset=0, end_offset=10)
        lc = ListComprehension(position=pos, elements=[NumberLiteral(position=pos, val=1.0)])
        comment = CommentSpan(position=Position(origin="<t>", line=1, column=1, start_offset=20, end_offset=30), text=" x ")
        _attach_trailing_to_last_expr(lc, comment)
        assert isinstance(lc.elements[0], CommentedExpr)

    def test_attach_trailing_to_last_expr_no_expression_field_is_a_no_op(self):
        # A node with no Expression-typed field at all (last_expr_info stays
        # None) -- BlankLine has no fields beyond position/scope.
        from openscad_lalr_parser import _attach_trailing_to_last_expr
        from openscad_lalr_parser.nodes import BlankLine
        pos = Position(origin="<t>", line=1, column=1, start_offset=0, end_offset=0)
        bl = BlankLine(position=pos)
        comment = CommentSpan(position=Position(origin="<t>", line=1, column=1, start_offset=5, end_offset=10), text=" x ")
        assert _attach_trailing_to_last_expr(bl, comment) is None

    def test_collect_container_exprs_list_of_expressions_field(self):
        # _collect_container_exprs's own "container's relevant field is a
        # list containing bare Expression items" branch -- every real
        # container this function is documented for (PositionalArgument,
        # NamedArgument, ParameterDeclaration) only ever has a *bare*
        # Expression field, never a list of them, so this branch is
        # exercised with a minimal purpose-built container matching the
        # shape instead.
        from dataclasses import dataclass
        from openscad_lalr_parser import _collect_container_exprs
        from openscad_lalr_parser.nodes import ASTNode, NumberLiteral

        @dataclass(slots=True)
        class _DummyExprListContainer(ASTNode):
            items: list

        pos = Position(origin="<t>", line=1, column=1, start_offset=0, end_offset=10)
        container = _DummyExprListContainer(position=pos, items=[NumberLiteral(position=pos, val=1.0)])
        expr_fields, non_expr_children = [], []
        _collect_container_exprs(container, expr_fields, non_expr_children)
        assert len(expr_fields) == 1
        assert expr_fields[0][:3] == (container, "items", 0)
        assert non_expr_children == []

    def test_collect_container_exprs_with_no_expr_fields_becomes_non_expr_child(self):
        from dataclasses import dataclass
        from openscad_lalr_parser import _collect_container_exprs
        from openscad_lalr_parser.nodes import ASTNode

        @dataclass(slots=True)
        class _DummyEmptyContainer(ASTNode):
            pass

        pos = Position(origin="<t>", line=1, column=1, start_offset=0, end_offset=0)
        container = _DummyEmptyContainer(position=pos)
        expr_fields, non_expr_children = [], []
        _collect_container_exprs(container, expr_fields, non_expr_children)
        assert expr_fields == []
        assert non_expr_children == [container]


class TestErrorReporting:
    def test_error_shows_line_and_caret(self):
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            result = getASTfromString('x = ')
            output = buffer.getvalue()

            assert "Syntax error" in output
            assert "line 1" in output
            assert "column" in output
            assert "^" in output
        finally:
            sys.stdout = old_stdout

    def test_error_caret_position_single_line(self):
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            result = getASTfromString('x = 5 +')
            output = buffer.getvalue()

            assert "x = 5 +" in output
            assert "^" in output
        finally:
            sys.stdout = old_stdout

    def test_error_caret_position_multi_line(self):
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            result = getASTfromString('x = 5;\ny = 10 +')
            output = buffer.getvalue()

            assert "y = 10 +" in output
            assert "^" in output
            assert "line 2" in output
        finally:
            sys.stdout = old_stdout

    def test_error_with_origin(self):
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            result = getASTfromString('x = ', origin='test.scad')
            output = buffer.getvalue()

            assert "test.scad" in output or "<string>" in output
        finally:
            sys.stdout = old_stdout

    def test_error_format_components(self):
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            result = getASTfromString('x = ')
            output = buffer.getvalue()

            assert "Syntax error" in output
            assert "line" in output
            assert "column" in output
            assert "^" in output
        finally:
            sys.stdout = old_stdout

    def test_error_with_tabs(self):
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            result = getASTfromString('x\t= ')
            output = buffer.getvalue()

            assert "Syntax error" in output
            assert "^" in output
        finally:
            sys.stdout = old_stdout

    def test_error_with_source_map(self):
        from openscad_lalr_parser.source_map import SourceMap
        from openscad_lalr_parser import parse_ast

        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()

        try:
            source_map = SourceMap()
            source_map.add_origin("test.scad", "x = ")
            combined_code = source_map.get_combined_string()

            result = parse_ast(combined_code, source_map=source_map)
            output = buffer.getvalue()

            assert "Syntax error" in output
            assert "^" in output
        finally:
            sys.stdout = old_stdout

    def test_error_reporting_without_source_map(self):
        from openscad_lalr_parser import parse_ast

        old_stdout = sys.stdout
        try:
            buffer = StringIO()
            sys.stdout = buffer

            result = parse_ast("x = ;", origin="test.scad", source_map=None)
            output = buffer.getvalue()

            assert "Syntax error" in output
            assert "test.scad" in output
            assert "^" in output
        finally:
            sys.stdout = old_stdout

    def test_get_ast_from_file_error_handling(self):
        with pytest.raises(FileNotFoundError):
            getASTfromFile("nonexistent_file_that_does_not_exist.scad")

        with tempfile.TemporaryDirectory() as temp_dir:
            fake_file = os.path.join(temp_dir, "fake.scad")
            os.makedirs(fake_file, exist_ok=True)

            with pytest.raises(Exception):
                getASTfromFile(fake_file)

    def test_get_ast_from_file_process_includes_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = os.path.join(temp_dir, "main.scad")

            with open(main_file, 'w') as f:
                f.write("x = 5;\ninclude <nonexistent.scad>\n")

            with pytest.raises(Exception):
                getASTfromFile(main_file, process_includes=True)

    def test_error_reporting_caret_position_edge_cases(self):
        from openscad_lalr_parser import parse_ast
        from openscad_lalr_parser.source_map import SourceMap

        source_map = SourceMap()
        source_map.add_origin("test.scad", "x = ;")

        old_stdout = sys.stdout
        try:
            buffer = StringIO()
            sys.stdout = buffer

            combined_code = source_map.get_combined_string()
            result = parse_ast(combined_code, origin="test.scad", source_map=source_map)
            output = buffer.getvalue()

            assert "Syntax error" in output
            assert "^" in output
        finally:
            sys.stdout = old_stdout

    def test_error_reporting_line_out_of_range(self):
        from openscad_lalr_parser import parse_ast

        old_stdout = sys.stdout
        try:
            buffer = StringIO()
            sys.stdout = buffer

            result = parse_ast("x = ;", origin="test.scad", source_map=None)
            output = buffer.getvalue()
            assert "Syntax error" in output
        finally:
            sys.stdout = old_stdout

    def test_find_library_file_windows_path(self):
        import platform
        if platform.system() == "Windows":
            result = findLibraryFile("", "nonexistent.scad")
            assert result is None or isinstance(result, str)

    def test_find_library_file_linux_path(self):
        import platform
        if platform.system() == "Linux":
            result = findLibraryFile("", "nonexistent.scad")
            assert result is None or isinstance(result, str)
