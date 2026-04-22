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

    def add_route(self, path: str, methods: list[str], route_obj: Any) -> None:
        node = self.root
        # Clean path and split
        parts = path.strip("/").split("/")
        if path == "/":
            parts = [""]

        for part in parts:
            if part.startswith("{") and part.endswith("}"):
                inner = part[1:-1]
                if ":" in inner:
                    name, type_name = inner.split(":", 1)
                else:
                    name, type_name = inner, "str"

                # We use ":" as a key for param nodes to differ from static segments
                if ":" not in node.children:
                    param_node = TrieNode()
                    param_node.is_param = True
                    param_node.param_name = name
                    converter_class = CONVERTERS.get(type_name, CONVERTERS["str"])
                    param_node.param_converter = converter_class()
                    node.children[":"] = param_node
                node = node.children[":"]
            else:
                if part not in node.children:
                    node.children[part] = TrieNode()
                node = node.children[part]

        for method in methods:
            node.routes[method.upper()] = route_obj

    def resolve(self, path: str, method: str) -> tuple[Any, dict[str, Any]] | None:
        parts = path.strip("/").split("/")
        if path == "/":
            parts = [""]

        params = {}
        node = self.root

        for _, part in enumerate(parts):
            # Check if current node is an ASGI mount
            # We check "ANY" or any method because ASGI apps usually handle all methods
            # but we need to see if the route object is an ASGIRoute.
            for route in node.routes.values():
                if getattr(route, "is_asgi", False):
                    return route, params

            if part in node.children:
                node = node.children[part]
            elif ":" in node.children:
                node = node.children[":"]
                try:
                    if node.param_converter:
                        val = node.param_converter.convert(part)
                        params[node.param_name] = val
                    else:
                        params[node.param_name] = part
                except ValueError:
                    return None
            else:
                return None

        route_obj = node.routes.get(method.upper()) or node.routes.get("ANY")
        if route_obj:
            return route_obj, params
        return None


class CompiledRouter:
    def __init__(self) -> None:
        self.matcher = RouterMatcher()

    def add_route(self, route: Any) -> None:
        self.matcher.add_route(route.path, route.methods, route)

    def resolve(self, path: str, method: str) -> tuple[Any, dict[str, Any]] | None:
        return self.matcher.resolve(path, method)
