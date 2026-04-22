# Moxie Plugins Documentation

Moxie supports a powerful plugin system that allows you to easily integrate third-party services and libraries. All plugins now support **Built-in Environment Variable Support**, meaning they can automatically read secrets and configuration from a `.env` file or system environment variables.

---

## 1. Supabase Plugin

The Supabase plugin provides a seamless way to integrate Supabase into your Moxie application. It automatically handles client initialization and registers the client in the Dependency Injection (DI) container.

### Configuration
You can configure the plugin either by passing parameters directly or by using environment variables.

**Environment Variables:**
- `SUPABASE_URL`: Your Supabase project URL.
- `SUPABASE_KEY`: Your Supabase project API key (service role or anon key).

### Usage
```python
from moxie import Moxie
from moxie.plugins.supabase import SupabasePlugin

app = Moxie()

# Automatic configuration from .env
supabase = SupabasePlugin()
app.add_plugin(supabase)

@app.get("/data")
async def get_data(client: SupabasePlugin = Depends()):
    response = client.client.table("your_table").select("*").execute()
    return response.data
```

---

## 2. Firebase Plugin

The Firebase plugin allows you to use the Firebase Admin SDK within Moxie. It supports both service account credentials and default initialization.

### Configuration
**Environment Variables:**
- `FIREBASE_CREDENTIALS`: Path to your service account JSON file.

### Usage
```python
from moxie import Moxie
from moxie.plugins.firebase import FirebasePlugin

app = Moxie()

# Automatic configuration from .env
firebase = FirebasePlugin()
app.add_plugin(firebase)
```

---

## 3. SQLAlchemy Plugin

The SQLAlchemy plugin provides asynchronous database support using SQLAlchemy. It manages the engine lifecycle and provides a dependency for getting database sessions.

### Configuration
**Environment Variables:**
- `DATABASE_URL`: Your database connection string (e.g., `postgresql+asyncpg://user:pass@localhost/db`).

### Usage
```python
from moxie import Moxie
from moxie.plugins.sqlalchemy import SQLAlchemyPlugin

app = Moxie()

# Automatic configuration from .env
db_plugin = SQLAlchemyPlugin()
app.add_plugin(db_plugin)

@app.get("/users")
async def list_users(db = Depends(db_plugin.get_db)):
    # Use 'db' as an AsyncSession
    ...
```

---

## Built-in Environment Support

Moxie includes a built-in `.env` loader. When you use the `Settings` class or any of the built-in plugins, Moxie will look for a `.env` file in your project root and load it into `os.environ`.

### Custom Settings
You can also use the `Settings` class for your own application configuration:

```python
from moxie.config import Settings

# Reads keys starting with APP_ (e.g., APP_DEBUG, APP_PORT)
settings = Settings("APP")

debug = settings.debug # Accesses APP_DEBUG
port = settings.get("port", 8000)
```
