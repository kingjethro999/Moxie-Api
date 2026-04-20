from typing import Any

from pydantic import BaseModel, Field

OPENAPI_VERSION = "3.1.0"

class Info(BaseModel):
    title: str
    version: str
    description: str | None = None

class Contact(BaseModel):
    name: str | None = None
    url: str | None = None
    email: str | None = None

class License(BaseModel):
    name: str
    url: str | None = None

class ExternalDocs(BaseModel):
    url: str
    description: str | None = None

class Tag(BaseModel):
    name: str
    description: str | None = None
    externalDocs: ExternalDocs | None = None

class OpenAPI(BaseModel):
    openapi: str = OPENAPI_VERSION
    info: Info
    paths: dict[str, dict[str, Any]] = Field(default_factory=dict)
    components: dict[str, Any] = Field(default_factory=dict)
    tags: list[Tag] = Field(default_factory=list)
    externalDocs: ExternalDocs | None = None
