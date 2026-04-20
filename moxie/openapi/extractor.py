import inspect
import re
from typing import Any, Union

from moxie.openapi.schema import SchemaCollector, python_type_to_schema
from moxie.router import Route


class OperationExtractor:
    def __init__(self, collector: SchemaCollector) -> None:
        self.collector = collector

    def extract(self, route: Route) -> dict[str, Any]:
        handler = route.handler
        sig = inspect.signature(handler)
        docstring = inspect.getdoc(handler) or ""
        
        # 1. Parse docstring
        doc_summary, doc_description, doc_params, doc_returns, doc_raises = self._parse_google_docstring(docstring)
        
        # 2. Prefer route metadata over docstring
        summary = route.summary or doc_summary
        description = route.description or doc_description
        
        parameters = []
        request_body = None
        
        # Extract path parameters from route pattern
        path_param_names = re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)(?::[a-zA-Z_][a-zA-Z0-9_]*)?\}", route.path)
        
        for name, param in sig.parameters.items():
            # Skip special types
            from moxie.background import BackgroundTasks
            from moxie.request import Request
            # Simplified check for special types
            if name in ["request", "ws", "tasks"] or param.annotation in [Request, BackgroundTasks]:
                continue
                
            param_description = doc_params.get(name, "")
            
            if name in path_param_names:
                parameters.append({
                    "name": name,
                    "in": "path",
                    "required": True,
                    "description": param_description,
                    "schema": python_type_to_schema(param.annotation, self.collector)
                })
            elif self._is_body_type(param.annotation) and any(m in ["POST", "PUT", "PATCH"] for m in route.methods):
                if request_body is None:
                    request_body = {
                        "content": {
                            "application/json": {
                                "schema": python_type_to_schema(param.annotation, self.collector)
                            }
                        },
                        "required": True,
                        "description": param_description
                    }
            else:
                # Default to query parameter
                parameters.append({
                    "name": name,
                    "in": "query",
                    "required": param.default is inspect.Parameter.empty,
                    "description": param_description,
                    "schema": python_type_to_schema(param.annotation, self.collector)
                })

        # Responses
        responses = {}
        
        # Default 200/204 response
        if sig.return_annotation is None or sig.return_annotation is type(None):
            responses["204"] = {"description": doc_returns or "No Content"}
        else:
            responses["200"] = {
                "description": doc_returns or "Successful Response",
                "content": {
                    "application/json": {
                        "schema": python_type_to_schema(sig.return_annotation, self.collector)
                    }
                }
            }
            
        # Add raises from docstring
        for status_code, exc_desc in doc_raises.items():
            responses[str(status_code)] = {"description": exc_desc}
            
        # Merge with route.responses
        for status, resp_meta in route.responses.items():
            responses[str(status)] = resp_meta

        operation = {
            "summary": summary,
            "description": description,
            "operationId": route.operation_id,
            "tags": route.tags,
            "parameters": parameters,
            "responses": responses,
            "deprecated": route.deprecated
        }
        
        if request_body:
            operation["requestBody"] = request_body
            
        # Add security requirements from guards
        if route.guards:
            operation["security"] = [{g.scheme_name: []} for g in route.guards]

        return operation

    def _parse_google_docstring(self, docstring: str) -> tuple[str, str, dict[str, str], str, dict[int, str]]:
        """Parses a Google-style docstring."""
        if not docstring:
            return "", "", {}, "", {}

        sections = re.split(r"\n\s*(Args|Returns|Raises):\s*\n", docstring, flags=re.IGNORECASE)
        
        main_body = sections[0].strip()
        summary = main_body.split("\n")[0] if main_body else ""
        description = "\n".join(main_body.split("\n")[1:]).strip() if "\n" in main_body else ""
        
        params = {}
        returns = ""
        raises = {}
        
        current_section = None
        for i in range(1, len(sections), 2):
            section_name = sections[i].lower()
            section_content = sections[i+1]
            
            if section_name == "args":
                for match in re.finditer(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)$", section_content, re.MULTILINE):
                    name, desc = match.groups()
                    params[name] = desc.strip()
            elif section_name == "returns":
                returns = section_content.strip()
            elif section_name == "raises":
                for match in re.finditer(r"^\s*(?:HTTPException\((\d+)\)|(\w+)):\s*(.*)$", section_content, re.MULTILINE):
                    code, exc_name, desc = match.groups()
                    if code:
                        raises[int(code)] = desc.strip()
                    # We could map exc_name to status codes too if we had a registry
                    
        return summary, description, params, returns, raises

    def _is_body_type(self, tp: Any) -> bool:
        # Also check for Optional[BaseModel] or Union[BaseModel, None]
        from typing import get_args, get_origin

        from pydantic import BaseModel
        origin = get_origin(tp)
        if origin is Union:
            args = get_args(tp)
            return any(inspect.isclass(a) and issubclass(a, BaseModel) for a in args if a is not type(None))
            
        if inspect.isclass(tp) and issubclass(tp, BaseModel):
            return True
        return False
