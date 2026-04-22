import os
from pathlib import Path
from typing import Any, dict


def load_env(dotenv_path: str | Path = ".env") -> None:
    """
    Very simple .env file loader that populates os.environ.
    Supports basic KEY=VALUE format and ignores comments/empty lines.
    """
    path = Path(dotenv_path)
    if not path.exists():
        return

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("\"'").strip()
                
                # Only set if not already present (standard dotenv behavior)
                if key not in os.environ:
                    os.environ[key] = value


class Settings:
    """
    Base class for application settings using environment variables.
    """
    def __init__(self, prefix: str = "", load_dotenv: bool = True) -> None:
        if load_dotenv:
            load_env()
        
        self._prefix = prefix.upper()
        if self._prefix and not self._prefix.endswith("_"):
            self._prefix += "_"

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting by key, automatically applying the prefix."""
        full_key = f"{self._prefix}{key.upper()}"
        return os.environ.get(full_key, default)

    def __getattr__(self, name: str) -> Any:
        """Allow accessing settings as attributes."""
        if name.startswith("_"):
            return super().__getattribute__(name)
        return self.get(name)

    def dict(self) -> dict[str, Any]:
        """Return all settings matching the prefix as a dictionary."""
        settings = {}
        for key, value in os.environ.items():
            if key.startswith(self._prefix):
                settings[key[len(self._prefix):].lower()] = value
        return settings
