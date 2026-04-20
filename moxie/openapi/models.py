from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

OPENAPI_VERSION = "3.1.0"

class Info(BaseModel):
    title: str
    version: str
    description: Optional[str] = None

class Contact(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None

class License(BaseModel):
    name: str
    url: Optional[str] = None

class ExternalDocs(BaseModel):
    url: str
    description: Optional[str] = None

class Tag(BaseModel):
    name: str
    description: Optional[str] = None
    externalDocs: Optional[ExternalDocs] = None

class OpenAPI(BaseModel):
    openapi: str = OPENAPI_VERSION
    info: Info
    paths: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    components: Dict[str, Any] = Field(default_factory=dict)
    tags: List[Tag] = Field(default_factory=list)
    externalDocs: Optional[ExternalDocs] = None

# We use Any for nested structures to avoid overly complex pydantic models 
# for the spec itself, as it's generated once.
from typing import Any
