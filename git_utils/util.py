from collections.abc import Set
from pathlib import Path
from typing import Any, Callable, Iterable, Union
import json
import os
import re
import urllib.parse

from filesystemlib import walk
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


def sumsize(top: Union[str, Path]) -> int:
    """
    Iterate through all paths in `top`, stat each one, and return total sum of sizes.
    """
    return sum(map(os.path.getsize, walk(Path(top))))


def normalize_url(url: str) -> str:
    """
    Fix git URLs with "alternative scp-like syntax", returning other URLs unchanged.
    """
    if m := re.match(r"^([^:/?#]+@)?([^:/?#]+):([^/].+)$", url):
        #               ↑ 1=user    ↑ 2=host   ↑ 3=path + query + fragment
        return f"ssh://{m.group(1)}{m.group(2)}/{m.group(3)}"
    return url


HOSTNAME_ALIASES = {
    "github.com": "github",
    "gist.github.com": "gist",
    "bitbucket.org": "bitbucket",
    "gitlab.com": "gitlab",
}


def alias_url(url: str) -> str:
    """
    Shorten git URL to aliased form if possible, otherwise return URL unchanged.
    """
    split_result = urllib.parse.urlsplit(normalize_url(url))
    if alias := HOSTNAME_ALIASES.get(split_result.hostname):
        # remove leading slash and trailing .git from path
        path = split_result.path.lstrip("/")
        path = re.sub(r"\.git$", "", path)
        return f"{alias}:{path}"
    return url


def autoname(url: str) -> str:
    """
    Generate flat repo name from URL based on hostname.

    github.com      => `{owner}--{repo}`
    bitbucket.org   => `bitbucket--{owner}--{repo}`
    code.google.com => `googlecode--{project}`
    """
    split_result = urllib.parse.urlsplit(normalize_url(url))
    hostname = split_result.hostname
    path = split_result.path
    if hostname == "github.com":
        path = path.strip("/").removesuffix(".git")
        return "--".join(path.split("/"))
    if hostname == "bitbucket.org":
        path = path.strip("/")
        return "--".join(("bitbucket", *path.split("/")))
    if hostname == "code.google.com":
        path = split_result.path.removeprefix("/p").strip("/")
        return "--".join(("googlecode", path))
    raise NotImplementedError(f"Don't know how to autoname URL: {url}")


class LazySet(Set):
    def __init__(self, iterable: Iterable):
        self.iterator = iter(iterable)
        self.set = set()

    def __contains__(self, item):
        if item in self.set:
            return True
        for new_item in self.iterator:
            self.set.add(new_item)
            if item == new_item:
                return True
        return False

    def __iter__(self):
        for item in self.set:
            yield item
        for item in self.iterator:
            self.set.add(item)
            yield item

    def __len__(self):
        return sum(1 for _ in iter(self))
