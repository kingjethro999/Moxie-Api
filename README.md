# 🚀 Moxie API

A lightweight, high-performance, and "battery-included" ASGI web framework for Python. Built for modern development with a focus on speed, developer experience, and seamless integrations.

## ✨ Features

- **⚡ High Performance**: Built on top of `anyio`, `httptools`, and `h11` for maximum throughput.
- **🛡️ Type-Safe**: Native support for Pydantic models with automatic request validation.
- **🔌 Plugin System**: Easily integrate with services like **Supabase**, **Firebase**, and **SQLAlchemy**.
- **🛠️ Dependency Injection**: Powerful and intuitive DI system with automatic parameter inference.
- **🔒 Security First**: Built-in support for JWT and API Key authentication.
- **📦 Middleware**: Robust middleware stack including CORS, GZip, TrustedHost, and more.
- **📄 Auto OpenAPI**: Automatic documentation generation (Swagger UI).
- **🧪 Testing Suite**: Built-in `TestClient` for effortless API testing.

---

## 🚀 Quickstart

Create a file named `app.py`:

```python
from moxie import Moxie, Body
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

app = Moxie(title="Moxie Demo")

@app.get("/")
async def root(name: str = "World"):
    return {"message": f"Welcome to Moxie, {name}!"}

@app.post("/items")
async def create_item(item: Item):
    return {"item": item, "status": "created"}
```

Run your API:

```bash
moxie dev app:app
```

Now visit `http://127.0.0.1:8000/docs` to see your interactive documentation!

---

## 🔌 Plugins See [PLUGINS.MD](./PLUGINS.MD) for full details

Moxie makes it easy to integrate with your favorite services.

### SQLAlchemy (Async)
```python
from moxie.plugins.sqlalchemy import SQLAlchemyPlugin

db_plugin = SQLAlchemyPlugin(database_url="sqlite+aiosqlite:///./test.db")
app.install(db_plugin)

@app.get("/users")
async def get_users(db = Depends(db_plugin.get_db)):
    # db is an AsyncSession
    ...
```

### Supabase
```python
from moxie.plugins.supabase import SupabasePlugin

sb = SupabasePlugin(url="URL", key="KEY")
app.install(sb)

@app.get("/data")
async def data(client = Depends(sb.get_client)):
    ...
```

---

## 🧪 Testing

Testing is a first-class citizen in Moxie. Use the `TestClient` to test your endpoints without running a server:

```python
from moxie.testing import TestClient
from app import app

client = TestClient(app)

def test_root():
    response = client.get("/?name=Developer")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to Moxie, Developer!"
```

---

## 🧩 Middleware

Moxie includes several built-in middlewares:

```python
from moxie.middleware import CORSMiddleware, GZipMiddleware

# Cross-Origin Resource Sharing
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Response Compression
app.add_middleware(GZipMiddleware, minimum_size=500)
```

---

## 🛠️ CLI Tools

Bootstrapping a new project is easy:

```bash
# Create a base project
moxie new my_project

# Create a project with a specific integration
moxie new my_db_project --template sqlalchemy
```

Other CLI commands:
- `moxie dev`: Start the development server with auto-reload.
- `moxie routes`: List all registered routes.
- `moxie openapi`: Generate and export OpenAPI schema.

---

## 📜 License

Moxie is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.
