from typing import Iterator
import logging
import os
import urllib

import requests

logger = logging.getLogger(__name__)


class Client:
    def __init__(self):
        self.scheme = "https"
        self.netloc = "api.github.com"
        self.session = requests.Session()
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

    def request(self, url: str, method: str = "GET", **kwargs) -> requests.Response:
        """
        Perform generic GitHub API request, returning Response model.
        """
        # set default scheme and netloc and separate query
        scheme, netloc, path, query, fragment = urllib.parse.urlsplit(url)
        url = urllib.parse.urlunsplit(
            (scheme or self.scheme, netloc or self.netloc, path, None, fragment)
        )
        # merge query from url with params, giving precedence to values from url
        if query:
            kwargs.setdefault("params", {}).update(urllib.parse.parse_qsl(query))
        logger.debug("Requesting URL: %s", url)
        response = self.session.request(method, url, **kwargs)
        logger.debug("Response headers: %s", response.headers)
        response.raise_for_status()
        return response

    def get(self, url: str, **kwargs):
        return self.request(url, method="GET", **kwargs)

    def post(self, url: str, **kwargs):
        return self.request(url, method="POST", **kwargs)

    def delete(self, url: str, **kwargs):
        return self.request(url, method="DELETE", **kwargs)

    def iter_requests(self, url: str, **kwargs) -> Iterator[requests.Response]:
        """
        Iterate over paginated responses.
        """
        kwargs.setdefault("params", {}).setdefault("per_page", 100)
        response = self.request(url, **kwargs)
        yield response
        link_header = response.headers.get("Link", "")
        links = {
            link["rel"]: link["url"]
            for link in requests.utils.parse_header_links(link_header)
        }
        # the last page has no rel="next" link
        if "next" in links:
            yield from self.iter_requests(links["next"], **kwargs)

    def iter_items(self, url: str, **kwargs) -> Iterator:
        """
        Assuming each response is a JSON list.
        """
        for response in self.iter_requests(url, **kwargs):
            yield from response.json()
