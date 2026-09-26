"""Comprehensive tests for scope analysis: Scope class, build_scopes(), and
build_scope() on every AST node type."""

from openscad_lalr_parser import (
    getASTfromString,
    build_scopes,
    Scope,
    # AST node types
    Assignment,
    FunctionDeclaration,
    ModuleDeclaration,
    ParameterDeclaration,
    Identifier,
    NumberLiteral,
    StringLiteral,
    BooleanLiteral,
    UndefinedLiteral,
    LetOp,
    EchoOp,
    AssertOp,
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
    ListComprehension,
    ListCompFor,
    ListCompCFor,
    ListCompLet,
    ListCompIf,
    ListCompIfElse,
    ListCompEach,
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
    NamedArgument,
    PositionalArgument,
    RangeLiteral,
)


# ---------------------------------------------------------------------------
# 1. TestScopeBasics - unit tests for the Scope class itself
# ---------------------------------------------------------------------------


class TestScopeBasics:
    """Tests for the Scope dataclass in isolation (no parsing)."""

    def test_empty_scope(self):
        scope = Scope()
        assert scope.parent is None
        assert scope.variables == {}
        assert scope.functions == {}
        assert scope.modules == {}

    def test_lookup_variable_not_found(self):
        scope = Scope()
        assert scope.lookup_variable("x") is None

    def test_lookup_function_not_found(self):
        scope = Scope()
        assert scope.lookup_function("f") is None

    def test_lookup_module_not_found(self):
        scope = Scope()
        assert scope.lookup_module("m") is None

    def test_child_scope(self):
        parent = Scope()
        child = parent.child_scope()
        assert child.parent is parent
        assert child.variables == {}
        assert child.functions == {}
        assert child.modules == {}

    def test_repr_empty(self):
        scope = Scope()
        r = repr(scope)
        assert "root" in r
        assert "vars=[none]" in r
        assert "funcs=[none]" in r
        assert "mods=[none]" in r

    def test_define_and_lookup_variable(self):
        scope = Scope()
        ast = getASTfromString("x = 1;")
        node = ast[0]
        scope.define_variable("x", node)
        assert scope.lookup_variable("x") is node

    def test_define_and_lookup_function(self):
        scope = Scope()
        ast = getASTfromString("function f(a) = a;")
        node = ast[0]
        scope.define_function("f", node)
        assert scope.lookup_function("f") is node

    def test_define_and_lookup_module(self):
        scope = Scope()
        ast = getASTfromString("module m() { cube(1); }")
        node = ast[0]
        scope.define_module("m", node)
        assert scope.lookup_module("m") is node

    def test_lookup_variable_in_parent(self):
        parent = Scope()
        child = parent.child_scope()
        ast = getASTfromString("x = 1;")
        node = ast[0]
        parent.define_variable("x", node)
        assert child.lookup_variable("x") is node

    def test_lookup_function_in_parent(self):
        parent = Scope()
        child = parent.child_scope()
        ast = getASTfromString("function f(a) = a;")
        node = ast[0]
        parent.define_function("f", node)
        assert child.lookup_function("f") is node

    def test_lookup_module_in_parent(self):
        parent = Scope()
        child = parent.child_scope()
        ast = getASTfromString("module m() { cube(1); }")
        node = ast[0]
        parent.define_module("m", node)
        assert child.lookup_module("m") is node

    def test_repr_with_bindings(self):
        scope = Scope()
        ast_var = getASTfromString("x = 1;")
        scope.define_variable("x", ast_var[0])
        ast_func = getASTfromString("function f() = 1;")
        scope.define_function("f", ast_func[0])
        ast_mod = getASTfromString("module m() { cube(1); }")
        scope.define_module("m", ast_mod[0])
        r = repr(scope)
        assert "x" in r
        assert "f" in r
        assert "m" in r
        assert "root" in r


# ---------------------------------------------------------------------------
# 2. TestScopeBuilderBasics - build_scopes() convenience function
# ---------------------------------------------------------------------------


class TestScopeBuilderBasics:
    """Tests for the build_scopes() top-level function."""

    def test_build_scopes_returns_scope(self):
        ast = getASTfromString("x = 1;")
        scope = root = build_scopes(ast)
        assert isinstance(scope, Scope)

    def test_empty_ast(self):
        scope = root = build_scopes([])
        assert isinstance(scope, Scope)
        assert scope.variables == {}
        assert scope.functions == {}
        assert scope.modules == {}

    def test_simple_assignment(self):
        ast = getASTfromString("x = 42;")
        scope = root = build_scopes(ast)
        assert scope.lookup_variable("x") is not None
        assert scope.lookup_variable("x") is ast[0]

    def test_assignment_scope_attached(self):
        ast = getASTfromString("x = 42;")
        scope = root = build_scopes(ast)
        assert root.scope_of(ast[0]) is scope

    def test_multiple_assignments(self):
        ast = getASTfromString("x = 1;\ny = 2;\nz = 3;")
        scope = root = build_scopes(ast)
        assert scope.lookup_variable("x") is ast[0]
        assert scope.lookup_variable("y") is ast[1]
        assert scope.lookup_variable("z") is ast[2]


# ---------------------------------------------------------------------------
# 3. TestFunctionScope
# ---------------------------------------------------------------------------


class TestFunctionScope:
    """Tests for scope analysis of function declarations."""

    def test_function_in_root(self):
        ast = getASTfromString("function add(a, b) = a + b;")
        scope = root = build_scopes(ast)
        assert scope.lookup_function("add") is ast[0]

    def test_parameters_in_function_scope(self):
        ast = getASTfromString("function add(a, b) = a + b;")
        scope = root = build_scopes(ast)
        func = ast[0]
        assert isinstance(func, FunctionDeclaration)
        # The function body expression should have a child scope
        body_scope = root.scope_of(func.expr)
        assert body_scope is not None
        assert body_scope.parent is not None
        assert body_scope.lookup_variable("a") is not None
        assert body_scope.lookup_variable("b") is not None

    def test_function_sees_outer_vars(self):
        ast = getASTfromString("x = 10;\nfunction f(a) = a + x;")
        scope = root = build_scopes(ast)
        func = ast[1]
        body_scope = root.scope_of(func.expr)
        # The outer variable x should be visible through parent chain
        assert body_scope.lookup_variable("x") is not None

    def test_parameter_with_default(self):
        ast = getASTfromString("function f(a=5) = a;")
        scope = root = build_scopes(ast)
        func = ast[0]
        assert isinstance(func, FunctionDeclaration)
        param = func.parameters[0]
        assert isinstance(param, ParameterDeclaration)
        assert param.default is not None

    def test_parameter_default_visited_in_caller_scope(self):
        """Parameter defaults are evaluated in the caller scope, not the
        function body scope."""
        ast = getASTfromString("x = 10;\nfunction f(a=x) = a;")
        scope = root = build_scopes(ast)
        func = ast[1]
        param = func.parameters[0]
        # The default expression should be scoped to the caller (parent) scope,
        # not the function body scope.
        default_scope = root.scope_of(param.default)
        assert default_scope is not None
        assert default_scope.lookup_variable("x") is not None


# ---------------------------------------------------------------------------
# 4. TestModuleScope
# ---------------------------------------------------------------------------


class TestModuleScope:
    """Tests for scope analysis of module declarations."""

    def test_module_in_root(self):
        ast = getASTfromString("module box(size) { cube(size); }")
        scope = root = build_scopes(ast)
        assert scope.lookup_module("box") is ast[0]

    def test_parameters_in_module_scope(self):
        ast = getASTfromString("module box(size) { cube(size); }")
        scope = root = build_scopes(ast)
        mod = ast[0]
        assert isinstance(mod, ModuleDeclaration)
        # Children of the module should be in a child scope that has 'size'
        child = mod.children[0]
        child_scope = root.scope_of(child)
        assert child_scope is not None
        assert child_scope.lookup_variable("size") is not None

    def test_parameter_with_default(self):
        ast = getASTfromString("module box(size=10) { cube(size); }")
        scope = root = build_scopes(ast)
        mod = ast[0]
        param = mod.parameters[0]
        assert param.default is not None

    def test_nested_function_in_module(self):
        ast = getASTfromString(
            "module m() {\n"
            "  function helper(x) = x * 2;\n"
            "  cube(helper(5));\n"
            "}"
        )
        scope = root = build_scopes(ast)
        mod = ast[0]
        assert isinstance(mod, ModuleDeclaration)
        # The module body scope should contain the hoisted function
        body_child = mod.children[0]
        body_scope = root.scope_of(body_child)
        assert body_scope.lookup_function("helper") is not None


# ---------------------------------------------------------------------------
# 5. TestHoisting
# ---------------------------------------------------------------------------


class TestHoisting:
    """Tests for hoisting of assignments and declarations within scopes."""

    def test_assignment_hoisted_in_module(self):
        ast = getASTfromString(
            "module m() {\n"
            "  cube(val);\n"
            "  val = 10;\n"
            "}"
        )
        scope = root = build_scopes(ast)
        mod = ast[0]
        # The cube call is before the assignment, but val should be hoisted
        call_node = mod.children[0]
        assert root.scope_of(call_node).lookup_variable("val") is not None


# ---------------------------------------------------------------------------
# 6. TestLetExpressions
# ---------------------------------------------------------------------------


class TestLetExpressions:
    """Tests for scope analysis of let expressions."""

    def test_let_op_creates_scope(self):
        ast = getASTfromString("x = let(a=1, b=2) a + b;")
        scope = root = build_scopes(ast)
        let_node = ast[0].expr
        assert isinstance(let_node, LetOp)
        body_scope = root.scope_of(let_node.body)
        assert body_scope is not None
        assert body_scope.lookup_variable("a") is not None
        assert body_scope.lookup_variable("b") is not None

    def test_let_vars_not_in_outer_scope(self):
        ast = getASTfromString("x = let(a=1) a;")
        scope = root = build_scopes(ast)
        # 'a' should NOT be visible in the root scope
        assert scope.lookup_variable("a") is None
        # But 'x' should be
        assert scope.lookup_variable("x") is not None


# ---------------------------------------------------------------------------
# 7. TestModularConstructs
# ---------------------------------------------------------------------------


class TestModularConstructs:
    """Tests for scope analysis of modular (statement-level) constructs."""

    def test_for_creates_scope(self):
        ast = getASTfromString("for (i=[0:5]) cube(i);")
        scope = root = build_scopes(ast)
        for_node = ast[0]
        assert isinstance(for_node, ModularFor)
        body = for_node.body
        if isinstance(body, list):
            body = body[0]
        body_scope = root.scope_of(body)
        assert body_scope is not None
        assert body_scope.lookup_variable("i") is not None
        # 'i' should not be in the root scope
        assert scope.lookup_variable("i") is None

    def test_if_creates_scope(self):
        ast = getASTfromString("if (true) cube(1);")
        scope = root = build_scopes(ast)
        if_node = ast[0]
        assert isinstance(if_node, ModularIf)
        # The true branch should get its own child scope
        branch = if_node.true_branch
        if isinstance(branch, list):
            branch = branch[0]
        assert root.scope_of(branch) is not None
        assert root.scope_of(branch).parent is scope

    def test_let_creates_scope(self):
        ast = getASTfromString("let (x=5) cube(x);")
        scope = root = build_scopes(ast)
        let_node = ast[0]
        assert isinstance(let_node, ModularLet)
        child = let_node.children[0]
        assert root.scope_of(child) is not None
        assert root.scope_of(child).lookup_variable("x") is not None

    def test_if_single_branch(self):
        ast = getASTfromString("if (x) cube(1);")
        scope = root = build_scopes(ast)
        if_node = ast[0]
        assert isinstance(if_node, ModularIf)
        branch = if_node.true_branch
        if isinstance(branch, list):
            branch = branch[0]
        assert root.scope_of(branch) is not None

    def test_if_else_single_branches(self):
        ast = getASTfromString("if (x) cube(1); else sphere(2);")
        scope = root = build_scopes(ast)
        ie_node = ast[0]
        assert isinstance(ie_node, ModularIfElse)
        true_branch = ie_node.true_branch
        if isinstance(true_branch, list):
            true_branch = true_branch[0]
        false_branch = ie_node.false_branch
        if isinstance(false_branch, list):
            false_branch = false_branch[0]
        assert root.scope_of(true_branch) is not None
        assert root.scope_of(false_branch) is not None
        # Each branch gets its own scope
        assert root.scope_of(true_branch) is not root.scope_of(false_branch)

    def test_for_list_body(self):
        ast = getASTfromString("for (i=[0:3]) { cube(i); sphere(i); }")
        scope = root = build_scopes(ast)
        for_node = ast[0]
        assert isinstance(for_node, ModularFor)
        body = for_node.body
        if isinstance(body, list):
            for child in body:
                assert root.scope_of(child).lookup_variable("i") is not None
        else:
            assert root.scope_of(body).lookup_variable("i") is not None

    def test_echo_with_children(self):
        ast = getASTfromString('echo("test") cube(1);')
        scope = root = build_scopes(ast)
        echo_node = ast[0]
        assert isinstance(echo_node, ModularEcho)
        assert root.scope_of(echo_node) is scope
        if echo_node.children:
            for child in echo_node.children:
                assert root.scope_of(child) is not None

    def test_assert_with_children(self):
        ast = getASTfromString("assert(x > 0) cube(x);")
        scope = root = build_scopes(ast)
        assert_node = ast[0]
        assert isinstance(assert_node, ModularAssert)
        assert root.scope_of(assert_node) is scope
        if assert_node.children:
            for child in assert_node.children:
                assert root.scope_of(child) is not None

    def test_call_empty_children(self):
        ast = getASTfromString("cube(1);")
        scope = root = build_scopes(ast)
        call = ast[0]
        assert isinstance(call, ModularCall)
        assert root.scope_of(call) is scope

    def test_modifier_show_only(self):
        ast = getASTfromString("! cube(1);")
        scope = root = build_scopes(ast)
        mod = ast[0]
        assert isinstance(mod, ModularModifierShowOnly)
        assert root.scope_of(mod) is scope
        assert root.scope_of(mod.child) is not None

    def test_modifier_highlight(self):
        ast = getASTfromString("# cube(1);")
        scope = root = build_scopes(ast)
        mod = ast[0]
        assert isinstance(mod, ModularModifierHighlight)
        assert root.scope_of(mod) is scope
        assert root.scope_of(mod.child) is not None

    def test_modifier_background(self):
        ast = getASTfromString("% cube(1);")
        scope = root = build_scopes(ast)
        mod = ast[0]
        assert isinstance(mod, ModularModifierBackground)
        assert root.scope_of(mod) is scope
        assert root.scope_of(mod.child) is not None

    def test_modifier_disable(self):
        ast = getASTfromString("* cube(1);")
        scope = root = build_scopes(ast)
        mod = ast[0]
        assert isinstance(mod, ModularModifierDisable)
        assert root.scope_of(mod) is scope
        assert root.scope_of(mod.child) is not None


# ---------------------------------------------------------------------------
# 8. TestFunctionLiteralRecursion
# ---------------------------------------------------------------------------


class TestFunctionLiteralRecursion:
    """Tests for scope analysis of function literals (anonymous functions)."""

    def test_function_literal_sees_assigned_variable(self):
        ast = getASTfromString("f = function(x) x + 1;")
        scope = root = build_scopes(ast)
        assign = ast[0]
        func_lit = assign.expr
        assert isinstance(func_lit, FunctionLiteral)
        # The function literal body should see 'x' as a parameter
        body_scope = root.scope_of(func_lit.body)
        assert body_scope.lookup_variable("x") is not None

    def test_function_literal_with_default_parameter(self):
        ast = getASTfromString("f = function(x=5) x;")
        scope = root = build_scopes(ast)
        func_lit = ast[0].expr
        assert isinstance(func_lit, FunctionLiteral)
        param = func_lit.parameters[0]
        assert param.default is not None
        body_scope = root.scope_of(func_lit.body)
        assert body_scope.lookup_variable("x") is not None

    def test_function_literal_in_expression(self):
        ast = getASTfromString("x = [1, function(a) a];")
        scope = root = build_scopes(ast)
        lc = ast[0].expr
        assert isinstance(lc, ListComprehension)
        # The second element is the function literal
        func_elem = lc.elements[1]
        # It may be wrapped as an Expression VectorElement
        if isinstance(func_elem, FunctionLiteral):
            func_lit = func_elem
        else:
            # It might be the expression itself
            func_lit = func_elem
            while hasattr(func_lit, 'expr') and not isinstance(func_lit, FunctionLiteral):
                func_lit = func_lit.expr
        assert isinstance(func_lit, FunctionLiteral)
        body_scope = root.scope_of(func_lit.body)
        assert body_scope.lookup_variable("a") is not None

    def test_function_literal_in_ternary_rhs(self):
        ast = getASTfromString("x = true ? 1 : function(a) a;")
        scope = root = build_scopes(ast)
        ternary = ast[0].expr
        assert isinstance(ternary, TernaryOp)
        func_lit = ternary.false_expr
        assert isinstance(func_lit, FunctionLiteral)
        body_scope = root.scope_of(func_lit.body)
        assert body_scope.lookup_variable("a") is not None


# ---------------------------------------------------------------------------
# 9. TestModularCallChildren
# ---------------------------------------------------------------------------


class TestModularCallChildren:
    """Tests for scope analysis of module call arguments and children."""

    def test_call_with_named_argument(self):
        ast = getASTfromString("cube(size=10);")
        scope = root = build_scopes(ast)
        call = ast[0]
        assert isinstance(call, ModularCall)
        named = call.arguments[0]
        assert isinstance(named, NamedArgument)
        assert root.scope_of(named) is scope
        assert root.scope_of(named.name) is scope
        assert root.scope_of(named.expr) is scope

    def test_primary_call_named_argument_visits_name(self):
        ast = getASTfromString("x = f(a=1);")
        scope = root = build_scopes(ast)
        assign = ast[0]
        pcall = assign.expr
        assert isinstance(pcall, PrimaryCall)
        named = pcall.arguments[0]
        assert isinstance(named, NamedArgument)
        assert root.scope_of(named.name) is scope

    def test_call_children_scope(self):
        ast = getASTfromString("translate([0,0,0]) { cube(1); sphere(2); }")
        scope = root = build_scopes(ast)
        call = ast[0]
        assert isinstance(call, ModularCall)
        # Children get a child scope
        for child in call.children:
            assert root.scope_of(child) is not None
            assert root.scope_of(child).parent is scope


# ---------------------------------------------------------------------------
# 10. TestScopeLookup
# ---------------------------------------------------------------------------


class TestScopeLookup:
    """Tests for variable/function/module lookup across scope chains."""

    def test_lookup_in_ancestor_scope_function_and_module(self):
        ast = getASTfromString(
            "x = 1;\n"
            "function f() = x;\n"
            "module m() { cube(x); }"
        )
        scope = root = build_scopes(ast)
        func = ast[1]
        assert isinstance(func, FunctionDeclaration)
        # Function body sees x through parent chain
        assert root.scope_of(func.expr).lookup_variable("x") is not None

        mod = ast[2]
        assert isinstance(mod, ModuleDeclaration)
        child = mod.children[0]
        assert root.scope_of(child).lookup_variable("x") is not None

    def test_lookup_in_parent(self):
        parent = Scope()
        child = parent.child_scope()
        ast = getASTfromString("x = 1;")
        parent.define_variable("x", ast[0])
        assert child.lookup_variable("x") is ast[0]

    def test_shadowing(self):
        ast = getASTfromString(
            "x = 1;\n"
            "function f(x) = x;"
        )
        scope = root = build_scopes(ast)
        func = ast[1]
        # The function body scope should have x as a parameter
        body_scope = root.scope_of(func.expr)
        # The x in function scope is the parameter, not the top-level assignment
        found = body_scope.lookup_variable("x")
        assert found is not None
        # It should be the ParameterDeclaration, not the Assignment
        assert isinstance(found, ParameterDeclaration)


# ---------------------------------------------------------------------------
# 11. TestThreeNamespaces
# ---------------------------------------------------------------------------


class TestThreeNamespaces:
    """Tests that variables, functions, and modules are in separate namespaces."""

    def test_same_name_in_all_three_namespaces(self):
        ast = getASTfromString(
            "thing = 42;\n"
            "function thing() = 1;\n"
            "module thing() { cube(1); }"
        )
        scope = root = build_scopes(ast)
        var = scope.lookup_variable("thing")
        func = scope.lookup_function("thing")
        mod = scope.lookup_module("thing")
        assert var is not None
        assert func is not None
        assert mod is not None
        assert isinstance(var, Assignment)
        assert isinstance(func, FunctionDeclaration)
        assert isinstance(mod, ModuleDeclaration)
        # All three are distinct nodes
        assert var is not func
        assert var is not mod
        assert func is not mod


# ---------------------------------------------------------------------------
# 12. TestListComprehensionScope
# ---------------------------------------------------------------------------


class TestListComprehensionScope:
    """Tests for scope analysis within list comprehensions."""

    def test_for_scope(self):
        ast = getASTfromString("x = [for (i=[0:3]) i];")
        scope = root = build_scopes(ast)
        lc = ast[0].expr
        assert isinstance(lc, ListComprehension)
        for_elem = lc.elements[0]
        assert isinstance(for_elem, ListCompFor)
        body = for_elem.body
        assert root.scope_of(body) is not None
        assert root.scope_of(body).lookup_variable("i") is not None
        # i should not leak to outer scope
        assert scope.lookup_variable("i") is None

    def test_c_for_scope(self):
        ast = getASTfromString("x = [for (i=0; i<5; i=i+1) i];")
        scope = root = build_scopes(ast)
        lc = ast[0].expr
        assert isinstance(lc, ListComprehension)
        cfor_elem = lc.elements[0]
        assert isinstance(cfor_elem, ListCompCFor)
        body = cfor_elem.body
        assert root.scope_of(body) is not None
        assert root.scope_of(body).lookup_variable("i") is not None

    def test_let_scope(self):
        ast = getASTfromString("x = [let(a=5) for(i=[0:a]) i];")
        scope = root = build_scopes(ast)
        lc = ast[0].expr
        assert isinstance(lc, ListComprehension)
        let_elem = lc.elements[0]
        assert isinstance(let_elem, ListCompLet)
        body = let_elem.body
        assert root.scope_of(body) is not None
        assert root.scope_of(body).lookup_variable("a") is not None

    def test_if_scope(self):
        ast = getASTfromString("x = [for (i=[0:5]) if (i > 2) i];")
        scope = root = build_scopes(ast)
        lc = ast[0].expr
        assert isinstance(lc, ListComprehension)
        for_elem = lc.elements[0]
        assert isinstance(for_elem, ListCompFor)
        if_elem = for_elem.body
        assert isinstance(if_elem, ListCompIf)
        assert root.scope_of(if_elem) is not None
        assert root.scope_of(if_elem.true_expr) is not None

    def test_if_else_scope(self):
        ast = getASTfromString("x = [for (i=[0:5]) if (i > 2) i else -i];")
        scope = root = build_scopes(ast)
        lc = ast[0].expr
        assert isinstance(lc, ListComprehension)
        for_elem = lc.elements[0]
        if_else_elem = for_elem.body
        assert isinstance(if_else_elem, ListCompIfElse)
        assert root.scope_of(if_else_elem.true_expr) is not None
        assert root.scope_of(if_else_elem.false_expr) is not None

    def test_each_scope(self):
        ast = getASTfromString("x = [each [1, 2, 3]];")
        scope = root = build_scopes(ast)
        lc = ast[0].expr
        assert isinstance(lc, ListComprehension)
        each_elem = lc.elements[0]
        assert isinstance(each_elem, ListCompEach)
        assert root.scope_of(each_elem) is not None


# ---------------------------------------------------------------------------
# 13. TestExpressionOpBuildScope
# ---------------------------------------------------------------------------


class TestExpressionOpBuildScope:
    """Tests that build_scope propagates through all expression operator types."""

    def test_echo_op(self):
        ast = getASTfromString('x = echo("val") 1;')
        scope = root = build_scopes(ast)
        echo = ast[0].expr
        assert isinstance(echo, EchoOp)
        assert root.scope_of(echo) is scope
        assert root.scope_of(echo.body) is scope

    def test_assert_op(self):
        ast = getASTfromString("x = assert(true) 1;")
        scope = root = build_scopes(ast)
        assert_op = ast[0].expr
        assert isinstance(assert_op, AssertOp)
        assert root.scope_of(assert_op) is scope
        assert root.scope_of(assert_op.body) is scope

    def test_division_op(self):
        ast = getASTfromString("x = 10 / 2;")
        scope = root = build_scopes(ast)
        div = ast[0].expr
        assert isinstance(div, DivisionOp)
        assert root.scope_of(div) is scope
        assert root.scope_of(div.left) is scope
        assert root.scope_of(div.right) is scope

    def test_modulo_op(self):
        ast = getASTfromString("x = 10 % 3;")
        scope = root = build_scopes(ast)
        mod = ast[0].expr
        assert isinstance(mod, ModuloOp)
        assert root.scope_of(mod) is scope
        assert root.scope_of(mod.left) is scope
        assert root.scope_of(mod.right) is scope

    def test_exponent_op(self):
        ast = getASTfromString("x = 2 ^ 3;")
        scope = root = build_scopes(ast)
        exp = ast[0].expr
        assert isinstance(exp, ExponentOp)
        assert root.scope_of(exp) is scope
        assert root.scope_of(exp.left) is scope
        assert root.scope_of(exp.right) is scope

    def test_bitwise_and_op(self):
        ast = getASTfromString("x = 5 & 3;")
        scope = root = build_scopes(ast)
        op = ast[0].expr
        assert isinstance(op, BitwiseAndOp)
        assert root.scope_of(op) is scope
        assert root.scope_of(op.left) is scope
        assert root.scope_of(op.right) is scope

    def test_bitwise_or_op(self):
        ast = getASTfromString("x = 5 | 3;")
        scope = root = build_scopes(ast)
        op = ast[0].expr
        assert isinstance(op, BitwiseOrOp)
        assert root.scope_of(op) is scope
        assert root.scope_of(op.left) is scope
        assert root.scope_of(op.right) is scope

    def test_bitwise_not_op(self):
        ast = getASTfromString("x = ~5;")
        scope = root = build_scopes(ast)
        op = ast[0].expr
        assert isinstance(op, BitwiseNotOp)
        assert root.scope_of(op) is scope
        assert root.scope_of(op.expr) is scope

    def test_bitwise_shift_left_op(self):
        ast = getASTfromString("x = 1 << 4;")
        scope = root = build_scopes(ast)
        op = ast[0].expr
        assert isinstance(op, BitwiseShiftLeftOp)
        assert root.scope_of(op) is scope
        assert root.scope_of(op.left) is scope
        assert root.scope_of(op.right) is scope

    def test_bitwise_shift_right_op(self):
        ast = getASTfromString("x = 16 >> 2;")
        scope = root = build_scopes(ast)
        op = ast[0].expr
        assert isinstance(op, BitwiseShiftRightOp)
        assert root.scope_of(op) is scope
        assert root.scope_of(op.left) is scope
        assert root.scope_of(op.right) is scope

    def test_logical_and_op(self):
        ast = getASTfromString("x = true && false;")
        scope = root = build_scopes(ast)
        op = ast[0].expr
        assert isinstance(op, LogicalAndOp)
        assert root.scope_of(op) is scope
        assert root.scope_of(op.left) is scope
        assert root.scope_of(op.right) is scope

    def test_logical_or_op(self):
        ast = getASTfromString("x = true || false;")
        scope = root = build_scopes(ast)
        op = ast[0].expr
        assert isinstance(op, LogicalOrOp)
        assert root.scope_of(op) is scope
        assert root.scope_of(op.left) is scope
        assert root.scope_of(op.right) is scope

    def test_logical_not_op(self):
        ast = getASTfromString("x = !true;")
        scope = root = build_scopes(ast)
        op = ast[0].expr
        assert isinstance(op, LogicalNotOp)
        assert root.scope_of(op) is scope
        assert root.scope_of(op.expr) is scope

    def test_inequality_op(self):
        ast = getASTfromString("x = 1 != 2;")
        scope = root = build_scopes(ast)
        op = ast[0].expr
        assert isinstance(op, InequalityOp)
        assert root.scope_of(op) is scope
        assert root.scope_of(op.left) is scope
        assert root.scope_of(op.right) is scope

    def test_gte_op(self):
        ast = getASTfromString("x = 1 >= 2;")
        scope = root = build_scopes(ast)
        op = ast[0].expr
        assert isinstance(op, GreaterThanOrEqualOp)
        assert root.scope_of(op) is scope
        assert root.scope_of(op.left) is scope
        assert root.scope_of(op.right) is scope

    def test_lte_op(self):
        ast = getASTfromString("x = 1 <= 2;")
        scope = root = build_scopes(ast)
        op = ast[0].expr
        assert isinstance(op, LessThanOrEqualOp)
        assert root.scope_of(op) is scope
        assert root.scope_of(op.left) is scope
        assert root.scope_of(op.right) is scope

    def test_primary_index(self):
        ast = getASTfromString("x = v[0];")
        scope = root = build_scopes(ast)
        idx = ast[0].expr
        assert isinstance(idx, PrimaryIndex)
        assert root.scope_of(idx) is scope
        assert root.scope_of(idx.left) is scope
        assert root.scope_of(idx.index) is scope

    def test_primary_member(self):
        ast = getASTfromString("x = v.x;")
        scope = root = build_scopes(ast)
        mem = ast[0].expr
        assert isinstance(mem, PrimaryMember)
        assert root.scope_of(mem) is scope
        assert root.scope_of(mem.left) is scope
        assert root.scope_of(mem.member) is scope


# ---------------------------------------------------------------------------
# 14. TestIntersectionForBuildScope
# ---------------------------------------------------------------------------


class TestIntersectionForBuildScope:
    """Tests for scope analysis of intersection_for constructs."""

    def test_scope(self):
        ast = getASTfromString("intersection_for (i=[0:3]) cube(i);")
        scope = root = build_scopes(ast)
        ifor = ast[0]
        assert isinstance(ifor, ModularIntersectionFor)
        body = ifor.body
        if isinstance(body, list):
            body = body[0]
        assert root.scope_of(body) is not None
        assert root.scope_of(body).lookup_variable("i") is not None
        # i should not be in root scope
        assert scope.lookup_variable("i") is None

    def test_block_body(self):
        ast = getASTfromString("intersection_for (i=[0:3]) { cube(i); sphere(i); }")
        scope = root = build_scopes(ast)
        ifor = ast[0]
        assert isinstance(ifor, ModularIntersectionFor)
        body = ifor.body
        if isinstance(body, list):
            for child in body:
                assert root.scope_of(child).lookup_variable("i") is not None
        else:
            assert root.scope_of(body).lookup_variable("i") is not None


# ---------------------------------------------------------------------------
# 15. TestHoistedModuleDeclaration
# ---------------------------------------------------------------------------


class TestHoistedModuleDeclaration:
    """Tests that nested module declarations are hoisted within their scope."""

    def test_nested_module_is_hoisted(self):
        ast = getASTfromString(
            "module outer() {\n"
            "  inner();\n"
            "  module inner() { cube(1); }\n"
            "}"
        )
        scope = root = build_scopes(ast)
        outer = ast[0]
        assert isinstance(outer, ModuleDeclaration)
        # The call to inner() precedes its declaration, but it should be
        # hoisted and visible in the module body scope.
        call_node = outer.children[0]
        assert isinstance(call_node, ModularCall)
        assert root.scope_of(call_node).lookup_module("inner") is not None

    def test_nested_module_not_visible_in_outer_scope(self):
        ast = getASTfromString(
            "module outer() {\n"
            "  module inner() { cube(1); }\n"
            "}"
        )
        scope = root = build_scopes(ast)
        # inner should NOT be visible in the root scope
        assert scope.lookup_module("inner") is None
        # But outer should be
        assert scope.lookup_module("outer") is not None
