from typing import Any, Callable
import json

from requests.models import CaseInsensitiveDict


def delete_keys(value: Any, pred: Callable[[str], bool]) -> Any:
    """
    Remove key-value pairs where pred(key) is True, recursing into dicts and lists.
    """
    if isinstance(value, dict):
        return {k: delete_keys(v, pred) for k, v in value.items() if not pred(k)}
    if isinstance(value, list):
        return [delete_keys(item, pred) for item in value]
    return value


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, CaseInsensitiveDict):
            return dict(o.items())
        return json.JSONEncoder.default(self, o)
