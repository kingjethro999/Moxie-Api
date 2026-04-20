import datetime
import decimal
import enum
import inspect
import uuid
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    get_args,
    get_origin,
)

from pydantic import BaseModel, TypeAdapter

class SchemaCollector:
    def __init__(self) -> None:
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.seen_types: Set[Type[Any]] = set()

    def add_model(self, model_class: Type[BaseModel]) -> str:
        name = model_class.__name__
        if name not in self.schemas:
            # We use pydantic's built-in JSON schema generation
            self.schemas[name] = model_class.model_json_schema()
            # Remove $defs if any and move them to top level components/schemas later
            # (Simplification: for now we just store the schema)
        return name

def python_type_to_schema(tp: Any, collector: SchemaCollector) -> Dict[str, Any]:
    """Convert a Python type annotation to a JSON Schema dict."""
    
    # Handle None
    if tp is None or tp is type(None):
        return {"type": "null"}

    # Handle Pydantic models
    if inspect.isclass(tp) and issubclass(tp, BaseModel):
        name = collector.add_model(tp)
        return {"$ref": f"#/components/schemas/{name}"}

    # Handle standard primitives
    if tp is str:
        return {"type": "string"}
    if tp is int:
        return {"type": "integer"}
    if tp is float:
        return {"type": "number"}
    if tp is bool:
        return {"type": "boolean"}
    if tp is bytes:
        return {"type": "string", "format": "binary"}
    if tp is uuid.UUID:
        return {"type": "string", "format": "uuid"}
    if tp is datetime.datetime:
        return {"type": "string", "format": "date-time"}
    if tp is datetime.date:
        return {"type": "string", "format": "date"}
    if tp is decimal.Decimal:
        return {"type": "number"}

    # Handle Generics (List, Dict, Union, Optional)
    origin = get_origin(tp)
    args = get_args(tp)

    if origin is list or origin is List:
        items_schema = python_type_to_schema(args[0], collector) if args else {}
        return {"type": "array", "items": items_schema}

    if origin is dict or origin is Dict:
        # We assume string keys for OpenAPI
        value_schema = python_type_to_schema(args[1], collector) if len(args) > 1 else {}
        return {"type": "object", "additionalProperties": value_schema}

    if origin is Union:
        # Handle Optional[T] which is Union[T, None]
        non_none_args = [a for a in args if a is not type(None)]
        if len(non_none_args) == 1:
            schema = python_type_to_schema(non_none_args[0], collector)
            if len(args) > len(non_none_args):
                # It was Optional
                if "type" in schema:
                    if isinstance(schema["type"], str):
                        schema["type"] = [schema["type"], "null"]
                    elif isinstance(schema["type"], list):
                        if "null" not in schema["type"]:
                            schema["type"].append("null")
                else:
                    return {"anyOf": [schema, {"type": "null"}]}
            return schema
        else:
            return {"anyOf": [python_type_to_schema(a, collector) for a in args]}

    # Fallback
    return {"type": "object"}
