import datetime
import decimal
import json
import uuid
from typing import Any


class MoxieJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if hasattr(obj, "__json__"):
            return obj.__json__()
        return super().default(obj)

def json_dumps(obj: Any, **kwargs: Any) -> str:
    kwargs.setdefault("cls", MoxieJSONEncoder)
    return json.dumps(obj, **kwargs)

def json_loads(s: str, **kwargs: Any) -> Any:
    return json.loads(s, **kwargs)
