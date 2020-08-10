from git import Repo
import git_utils.repo


def test_remotes_urls():
    repo = Repo()
    assert git_utils.repo.remotes_urls(repo) == {"git@github.com:chbrown/git-utils.git"}


def test_heads_commits():
    repo = Repo()
    hexshas = {commit.hexsha for commit in git_utils.repo.heads_commits(repo)}
    assert hexshas >= {
        "e2504d9c72ac83e904c755ef0364cc1d699e3db1",  # first commit
        "468b665ae1da7953b7f412642f0bdfcef8833a78",  # recent commit
    }
