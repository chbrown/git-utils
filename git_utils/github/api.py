from .client import Client


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
