from functools import partial
from typing import Any, Callable, Iterator, Tuple
import json
import logging
import os
import re
import sys
import urllib

from requests import Session, Response
from requests.models import CaseInsensitiveDict

logger = logging.getLogger(__name__)


def delete_keys(value: Any, pred: Callable[[str], bool]) -> Any:
    """
    Remove key-value pairs where pred(key) is True, recursing into dicts and lists.
    """
    if isinstance(value, dict):
        return {k: delete_keys(v, pred) for k, v in value.items() if not pred(k)}
    if isinstance(value, list):
        return [delete_keys(item, pred) for item in value]
    return value


delete_url_keys = partial(delete_keys, pred=lambda k: k.endswith("url"))


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, CaseInsensitiveDict):
            return dict(o.items())
        return json.JSONEncoder.default(self, o)


def print_response(response: Response):
    """
    Print Response instance to stdout.
    """
    # only pretty-print if stdout is a TTY (not piped anywhere else)
    indent = 2 if sys.stdout.isatty() else None
    dump_kwargs = {
        "ensure_ascii": False,
        "cls": CustomJSONEncoder,
        "indent": indent,
        "sort_keys": True,
    }

    result = response.json()
    # remove keys ending with 'url'
    result = delete_url_keys(result)

    if isinstance(result, dict):
        json.dump(result, sys.stdout, **dump_kwargs)
    else:
        for item in result:
            json.dump(item, sys.stdout, **dump_kwargs)
            sys.stdout.write("\n")
            sys.stdout.flush()


def _parse_links(links_string: str) -> Iterator[Tuple[str, str]]:
    """
    Parse a header string like: (the newline should be just a single space)
    '<https://api.github.com/repositories/12345/commits?page=2>; rel="next",
     <https://api.github.com/repositories/12345/commits?page=5>; rel="last"'
    into a key-value pairs with these possible keys: next, last, first, prev
    """
    # The filter(None, ...) handles the case where links_string is the empty string
    for link_string in filter(None, re.split(r",\s*", links_string)):
        href_string, rel_string = re.split(r";\s*", link_string)
        href_match = re.match(r"<(.+)>", href_string)
        rel_match = re.match(r'rel="(.+)"', rel_string)
        yield rel_match.group(1), href_match.group(1)


class Client:
    def __init__(self):
        self.session = Session()
        self.session.headers["Accept"] = "application/vnd.github.v3+json"

    @classmethod
    def from_env(
        cls, user_var: str = "GITHUB_USER", password_var: str = "GITHUB_TOKEN"
    ):
        user = os.getenv(user_var)
        password = os.getenv(password_var)
        client = cls()
        client.session.auth = (user, password)  # HTTPBasicAuth(user, password)
        logger.debug("Authenticating with user %r and password", user)
        return client

    @classmethod
    def from_token(cls, token: str):
        client = cls()
        client.session.headers["Authorization"] = f"token {token}"
        logger.debug("Authenticating with token: ...%s", token[-8:])
        return client

    def request(self, url_or_path: str, method: str = "GET", **kwargs) -> Response:
        """
        Perform generic GitHub API request, returning Response model.
        """
        # Prefix `url_or_path` with the API root if it does not already start with it.
        url = urllib.parse.urljoin("https://api.github.com/", url_or_path)
        logger.debug("Requesting URL: %s", url)
        response = self.session.request(method, url, **kwargs)
        logger.debug("Response headers: %s", response.headers)
        return response

    def get(self, url: str, **kwargs):
        return self.request(url, method="GET", **kwargs)

    def post(self, url: str, **kwargs):
        return self.request(url, method="POST", **kwargs)

    def delete(self, url: str, **kwargs):
        return self.request(url, method="DELETE", **kwargs)

    def iter_requests(self, url: str, **kwargs) -> Iterator[Response]:
        """
        Iterate over paginated responses.
        """
        kwargs.setdefault("params", {}).setdefault("per_page", 100)
        response = self.request(url, **kwargs)
        yield response
        links = dict(_parse_links(response.headers.get("Link", "")))
        # the last page has no rel="next" link
        if "next" in links:
            yield from self.iter_requests(links["next"], **kwargs)

    def iter_items(self, url: str, **kwargs) -> Iterator:
        """
        Assuming each response is a JSON list.
        """
        for response in self.iter_requests(url, **kwargs):
            yield from response.json()

    def request_and_print_first_and_last_pages(self, url: str, **kwargs):
        kwargs.setdefault("params", {}).setdefault("per_page", 100)
        response = self.request(url, **kwargs)
        print_response(response)
        links = dict(_parse_links(response.headers.get("Link", "")))
        # jump to last page if there are multiple pages
        if "last" in links:
            logger.info("...")
            response = self.request(links["last"], **kwargs)
            print_response(response)


class API(Client):
    def commits(self, owner: str, repo: str):
        url = f"/repos/{owner}/{repo}/commits"
        self.request_and_print_first_and_last_pages(url)

    def watchers(self, owner: str, repo: str):
        url = f"/repos/{owner}/{repo}/subscribers"
        self.request_and_print_first_and_last_pages(url)

    def contents(self, owner: str, repo: str, path: str = ""):
        url = f"/repos/{owner}/{repo}/contents/{path}"
        self.request_and_print_first_and_last_pages(url)
