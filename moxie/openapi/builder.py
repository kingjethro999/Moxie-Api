from typing import Any, Dict, List, Optional, TYPE_CHECKING

from moxie.openapi.models import OPENAPI_VERSION
from moxie.openapi.schema import SchemaCollector
from moxie.openapi.extractor import OperationExtractor

if TYPE_CHECKING:
    from moxie.app import Moxie

class OpenAPIBuilder:
    def __init__(self, app: "Moxie") -> None:
        self.app = app
        self._spec: Optional[Dict[str, Any]] = None

    def build(self) -> Dict[str, Any]:
        """Build and return the full OpenAPI 3.1 document as a dict."""
        collector = SchemaCollector()
        extractor = OperationExtractor(collector)
        
        paths: Dict[str, Dict[str, Any]] = {}
        tags_seen = set()
        security_schemes = {}

        # Walk all routes in the app
        for route in self.app.router.routes:
            if not route.include_in_schema:
                continue
            
            # Ensure path starts with /
            path = route.path
            if not path.startswith("/"):
                path = "/" + path
            
            if path not in paths:
                paths[path] = {}
            
            operation = extractor.extract(route)
            
            for method in route.methods:
                paths[path][method.lower()] = operation
                
            for tag in route.tags:
                tags_seen.add(tag)
                
            # Collect security schemes from guards
            for guard in route.guards:
                if guard.scheme_name not in security_schemes:
                    security_schemes[guard.scheme_name] = guard.openapi_security_scheme

        spec = {
            "openapi": OPENAPI_VERSION,
            "info": {
                "title": self.app.title,
                "version": self.app.version,
                "description": self.app.description or "",
            },
            "paths": paths,
            "components": {
                "schemas": collector.schemas,
                "securitySchemes": security_schemes,
            },
            "tags": [{"name": tag} for tag in sorted(tags_seen)],
        }
        
        self._spec = spec
        return spec

    def invalidate(self) -> None:
        """Clear the cache — forces rebuild on next access."""
        self._spec = None

    @property
    def spec(self) -> Dict[str, Any]:
        """Cached spec. Calls build() on first access."""
        if self._spec is None:
            self.build()
        return self._spec
