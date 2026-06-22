"""JSON and YAML serialization for OpenSCAD AST trees."""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Sequence
from typing import Any

from .nodes import (
    Position,
    ASTNode,
    CommentLine,
    CommentSpan,
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


_NODE_REGISTRY: dict[str, type[ASTNode]] = {
    cls.__name__: cls
    for cls in [
        CommentLine,
        CommentSpan,
        Identifier,
        StringLiteral,
        NumberLiteral,
        BooleanLiteral,
        UndefinedLiteral,
        RangeLiteral,
        ParameterDeclaration,
        PositionalArgument,
        NamedArgument,
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
        ListCompLet,
        ListCompEach,
        ListCompFor,
        ListCompCFor,
        ListCompIf,
        ListCompIfElse,
        ListComprehension,
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
    ]
}


def _serialize_position(position: Position) -> dict[str, Any]:
    return {
        "origin": position.origin,
        "line": position.line,
        "column": position.column,
        "start_offset": position.start_offset,
        "end_offset": position.end_offset,
    }


def _serialize_value(value: Any, include_position: bool) -> Any:
    if value is None:
        return None
    elif isinstance(value, ASTNode):
        return _serialize_node(value, include_position)
    elif isinstance(value, list):
        return [_serialize_value(item, include_position) for item in value]
    elif isinstance(value, (str, int, float, bool)):
        return value
    else:
        raise TypeError(f"Unsupported type for serialization: {type(value)}")


def _serialize_node(node: ASTNode, include_position: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "_type": node.__class__.__name__,
    }

    if include_position:
        result["_position"] = _serialize_position(node.position)

    for field in dataclasses.fields(node):
        if field.name in ("position", "scope"):
            continue
        value = getattr(node, field.name)
        result[field.name] = _serialize_value(value, include_position)

    return result


def ast_to_dict(
    ast: ASTNode | Sequence[ASTNode] | None,
    include_position: bool = True,
) -> dict[str, Any] | list[dict[str, Any]] | None:
    if ast is None:
        return None
    elif isinstance(ast, Sequence) and not isinstance(ast, str):
        return [_serialize_node(node, include_position) for node in ast]
    elif isinstance(ast, ASTNode):
        return _serialize_node(ast, include_position)
    else:
        raise TypeError(f"Expected ASTNode, Sequence[ASTNode], or None, got {type(ast)}")


def ast_to_json(
    ast: ASTNode | Sequence[ASTNode] | None,
    include_position: bool = True,
    indent: int | None = 2,
) -> str:
    data = ast_to_dict(ast, include_position=include_position)
    return json.dumps(data, indent=indent)


def _deserialize_position(data: dict[str, Any]) -> Position:
    return Position(
        origin=data["origin"],
        line=data["line"],
        column=data["column"],
        start_offset=data.get("start_offset", 0),
        end_offset=data.get("end_offset", 0),
    )


def _deserialize_value(value: Any) -> Any:
    if value is None:
        return None
    elif isinstance(value, dict) and "_type" in value:
        return _deserialize_node(value)
    elif isinstance(value, list):
        return [_deserialize_value(item) for item in value]
    elif isinstance(value, (str, int, float, bool)):
        return value
    else:
        raise TypeError(f"Unsupported type for deserialization: {type(value)}")


def _deserialize_node(data: dict[str, Any]) -> ASTNode:
    if "_type" not in data:
        raise ValueError("Missing '_type' field in node data")

    type_name = data["_type"]
    if type_name not in _NODE_REGISTRY:
        raise ValueError(f"Unknown node type: {type_name}")

    node_class = _NODE_REGISTRY[type_name]

    if "_position" in data:
        position = _deserialize_position(data["_position"])
    else:
        position = Position(origin="<unknown>", line=0, column=0)

    field_names = {f.name for f in dataclasses.fields(node_class) if f.name != "position"}

    kwargs: dict[str, Any] = {"position": position}
    for key, value in data.items():
        if key.startswith("_"):
            continue
        if key in field_names:
            kwargs[key] = _deserialize_value(value)

    return node_class(**kwargs)


def ast_from_dict(data: dict[str, Any] | list[dict[str, Any]] | None) -> ASTNode | list[ASTNode] | None:
    if data is None:
        return None
    elif isinstance(data, list):
        return [_deserialize_node(item) for item in data]
    else:
        return _deserialize_node(data)


def ast_from_json(json_str: str) -> ASTNode | list[ASTNode] | None:
    data = json.loads(json_str)
    return ast_from_dict(data)


def ast_to_yaml(
    ast: ASTNode | Sequence[ASTNode] | None,
    include_position: bool = True,
) -> str:
    try:
        import yaml
    except ImportError:
        raise ImportError(
            "PyYAML is required for YAML serialization. "
            "Install it with: pip install openscad_lalr_parser[yaml]"
        )

    data = ast_to_dict(ast, include_position=include_position)
    return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)


def ast_from_yaml(yaml_str: str) -> ASTNode | list[ASTNode] | None:
    try:
        import yaml
    except ImportError:
        raise ImportError(
            "PyYAML is required for YAML deserialization. "
            "Install it with: pip install openscad_lalr_parser[yaml]"
        )

    data = yaml.safe_load(yaml_str)
    return ast_from_dict(data)
