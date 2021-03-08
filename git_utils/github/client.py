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

    def iter_responses(self, url: str, **kwargs) -> Iterator[requests.Response]:
        """
        Iterate over paginated responses.
        """
        kwargs.setdefault("params", {}).setdefault("per_page", 100)
        try:
            response = self.request(url, **kwargs)
        except requests.exceptions.HTTPError as exc:
            # intercept '409 Conflict' errors (which indicate an empty repo)
            if exc.response.status_code == 409:
                logger.debug("Stopping due to 409 error: %s", exc)
                return
            # re-raise all other errors
            raise
        yield response
        link_header = response.headers.get("Link", "")
        links = {
            link["rel"]: link["url"]
            for link in requests.utils.parse_header_links(link_header)
        }
        # the last page has no rel="next" link
        if "next" in links:
            yield from self.iter_responses(links["next"], **kwargs)

    def iter_items(self, url: str, **kwargs) -> Iterator:
        """
        Assuming each response is a JSON list.
        """
        for response in self.iter_responses(url, **kwargs):
            yield from response.json()

    def iter_first_and_last_responses(
        self, url: str, **kwargs
    ) -> Iterator[requests.Response]:
        kwargs.setdefault("params", {}).setdefault("per_page", 100)
        response = self.request(url, **kwargs)
        yield response
        link_header = response.headers.get("Link", "")
        links = {
            link["rel"]: link["url"]
            for link in requests.utils.parse_header_links(link_header)
        }
        # jump to last page if there are multiple pages
        if "last" in links:
            response = self.request(links["last"], **kwargs)
            yield response

    def iter_repos(
        self,
        username: str = None,
        org: str = None,
        type: str = None,  # all | owner | public | private | forks | sources | member | internal
        sort: str = None,  # created | updated | pushed | full_name
        direction: str = None,  # asc | desc
        visibility: str = None,  # all | public | private
        affiliation: str = None,  # owner + collaborator + organization_member
    ) -> Iterator[dict]:
        """
        Docs: https://docs.github.com/en/rest/reference/repos#list-repositories-for-the-authenticated-user
              https://docs.github.com/en/rest/reference/repos#list-repositories-for-a-user
              https://docs.github.com/en/rest/reference/repos#list-organization-repositories
        """
        path = "/user/repos"
        if username:
            path = f"/users/{username}/repos"
        elif org:
            path = f"/orgs/{org}/repos"
        params = {
            "type": type,
            "sort": sort,
            "direction": direction,
            "visibility": visibility,
            "affiliation": affiliation,
        }
        yield from self.iter_items(path, params=params)

    def iter_commits(
        self,
        owner: str,
        repo: str,
        sha: str = None,
        path: str = None,
        author: str = None,
        since: str = None,
        until: str = None,
    ) -> Iterator[dict]:
        """
        Docs: https://docs.github.com/en/rest/reference/repos#list-commits
        """
        params = {
            "sha": sha,
            "path": path,
            "author": author,
            "since": since,
            "until": until,
        }
        yield from self.iter_items(f"/repos/{owner}/{repo}/commits", params=params)

    def iter_branches(
        self,
        owner: str,
        repo: str,
        protected: str = None,
    ) -> Iterator[dict]:
        """
        Docs: https://docs.github.com/en/rest/reference/repos#list-branches
        """
        params = {"protected": protected}
        yield from self.iter_items(f"/repos/{owner}/{repo}/branches", params=params)

    def iter_all_commits(
        self, owner: str, repo: str, author: str = None
    ) -> Iterator[dict]:
        """
        Iterate over all commits in all branches.
        """
        branches = list(self.iter_branches(owner, repo))
        logger.debug(
            "Getting all commits from all %d branches: %s",
            len(branches),
            ", ".join(branch["name"] for branch in branches),
        )
        seen_shas = set()
        for branch in branches:
            branch_name = branch["name"]
            for commit in self.iter_commits(
                owner, repo, sha=branch_name, author=author
            ):
                sha = commit["sha"]
                # since we're always iterating upward through the tree, from HEAD to the initial commit,
                # I think (?) we can assume that if we run into a SHA we've already seen,
                # continuing along that path will only retrace our steps from a previous branch
                # (But idk, maybe there's some weird merge functionality that might void that guarantee?)
                if sha in seen_shas:
                    logger.debug(
                        "Breaking out of branch %r early (already seen %r)",
                        branch_name,
                        sha,
                    )
                    break
                seen_shas.add(sha)
                yield commit
