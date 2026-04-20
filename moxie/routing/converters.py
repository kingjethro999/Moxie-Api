import uuid
from typing import Any, Dict, Protocol, Type, TypeVar

T = TypeVar("T")

class Converter(Protocol):
    regex: str
    def convert(self, value: str) -> Any: ...

class StringConverter:
    regex = "[^/]+"
    def convert(self, value: str) -> str:
        return value

class IntConverter:
    regex = "[0-9]+"
    def convert(self, value: str) -> int:
        return int(value)

class FloatConverter:
    regex = r"[0-9]+(\.[0-9]+)?"
    def convert(self, value: str) -> float:
        return float(value)

class UUIDConverter:
    regex = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    def convert(self, value: str) -> uuid.UUID:
        return uuid.UUID(value)

class PathConverter:
    regex = ".*"
    def convert(self, value: str) -> str:
        return value

CONVERTERS: Dict[str, Type[Converter]] = {
    "str": StringConverter,
    "int": IntConverter,
    "float": FloatConverter,
    "uuid": UUIDConverter,
    "path": PathConverter,
}
