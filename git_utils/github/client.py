from typing import Iterator
import logging
import os
import urllib

from requests import Session, Response
from requests.utils import parse_header_links

logger = logging.getLogger(__name__)


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
        response.raise_for_status()
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
        links = {
            link["rel"]: link["url"]
            for link in parse_header_links(response.headers.get("Link", ""))
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
