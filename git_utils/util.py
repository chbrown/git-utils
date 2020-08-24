from pathlib import Path
from typing import Any, Callable, Iterator, Union
import json
import os
import re

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


def walk(top: Union[Path, os.DirEntry]) -> Iterator[Union[Path, os.DirEntry]]:
    """
    Recursively iterate over all paths in `top`.
    """
    yield top
    if top.is_dir():
        for child in os.scandir(top):
            yield from walk(child)


def sumsize(top: Union[str, Path]) -> int:
    """
    Iterate through all paths in `top`, stat each one, and return total sum of sizes.
    """
    top = Path(top)
    return sum(path.stat().st_size for path in walk(top))


def normalize_url(url: str) -> str:
    """
    Fix git URLs with "alternative scp-like syntax", returning other URLs unchanged.
    """
    if m := re.match(r"^([^:/?#]+@)?([^:/?#]+):([^/].+)$", url):
        #               ↑ 1=user    ↑ 2=host   ↑ 3=path + query + fragment
        return f"ssh://{m.group(1)}{m.group(2)}/{m.group(3)}"
    return url
