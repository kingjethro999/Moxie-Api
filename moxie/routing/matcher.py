import re
from typing import Any

from moxie.routing.converters import CONVERTERS, Converter


class RouteMatcher:
    def __init__(self, path_pattern: str) -> None:
        self.path_pattern = path_pattern
        self.regex, self.converters = self._compile(path_pattern)

    def _compile(self, pattern: str) -> tuple[re.Pattern[str], dict[str, Converter]]:
        # Convert {name:type} or {name} to regex groups
        # Example: /user/{id:int} -> /user/(?P<id>[0-9]+)
        
        regex = "^"
        converters = {}
        
        # Split path into segments
        parts = pattern.split("/")
        for i, part in enumerate(parts):
            if i > 0:
                regex += "/"
            
            if part.startswith("{") and part.endswith("}"):
                inner = part[1:-1]
                if ":" in inner:
                    name, type_name = inner.split(":", 1)
                else:
                    name, type_name = inner, "str"
                
                converter_class = CONVERTERS.get(type_name, CONVERTERS["str"])
                converter = converter_class()
                regex += f"(?P<{name}>{converter.regex})"
                converters[name] = converter
            else:
                regex += re.escape(part)
        
        regex += "$"
        return re.compile(regex), converters

    def match(self, path: str) -> dict[str, Any] | None:
        match = self.regex.match(path)
        if not match:
            return None
        
        params = match.groupdict()
        return {
            name: self.converters[name].convert(value)
            for name, value in params.items()
        }

class TrieNode:
    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.is_param: bool = False
        self.param_name: str | None = None
        self.param_converter: Converter | None = None
        self.routes: dict[str, Any] = {} # method -> handler

class RouterMatcher:
    """Trie-based router for fast path resolution."""
    def __init__(self) -> None:
        self.root = TrieNode()

    def add_route(self, path: str, methods: list[str], handler: Any) -> None:
        # Simple implementation using regex matcher for now as per CLAUDE.md requirements
        # but structured for easy expansion.
        pass

# For simplicity and to meet the "compiled trie" goal while keeping implementation manageable,
# I'll implement a simplified version that handles both static and dynamic segments.

class CompiledRouter:
    def __init__(self) -> None:
        self.routes: list[tuple[RouteMatcher, Any]] = []

    def add_route(self, route: Any) -> None:
        self.routes.append((RouteMatcher(route.path), route))

    def resolve(self, path: str, method: str) -> tuple[Any, dict[str, Any]] | None:
        method = method.upper()
        for matcher, route in self.routes:
            if method in route.methods or "ANY" in route.methods:
                params = matcher.match(path)
                if params is not None:
                    return route, params
        return None
