import logging

from requests.utils import parse_header_links

from . import print_response
from .client import Client

logger = logging.getLogger(__name__)


class API(Client):
    def request_and_print_first_and_last_pages(self, url: str, **kwargs):
        kwargs.setdefault("params", {}).setdefault("per_page", 100)
        response = self.request(url, **kwargs)
        print_response(response)
        links = {
            link["rel"]: link["url"]
            for link in parse_header_links(response.headers.get("Link", ""))
        }
        # jump to last page if there are multiple pages
        if "last" in links:
            logger.info("...")
            response = self.request(links["last"], **kwargs)
            print_response(response)

    def commits(self, owner: str, repo: str):
        url = f"/repos/{owner}/{repo}/commits"
        self.request_and_print_first_and_last_pages(url)

    def watchers(self, owner: str, repo: str):
        url = f"/repos/{owner}/{repo}/subscribers"
        self.request_and_print_first_and_last_pages(url)

    def contents(self, owner: str, repo: str, path: str = ""):
        url = f"/repos/{owner}/{repo}/contents/{path}"
        self.request_and_print_first_and_last_pages(url)
