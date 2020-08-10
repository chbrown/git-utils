from pathlib import Path
from typing import Iterable, Iterator, List, Set, Tuple

from git import Commit, Head, Repo


def remotes_urls(repo: Repo) -> Set[str]:
    """Get all URLs in all remotes"""
    return {url for remote in repo.remotes for url in remote.urls}


def heads_commits(repo: Repo) -> Set[Commit]:
    """Get all Commits in all heads"""
    return {commit for head in repo.heads for commit in repo.iter_commits(head)}


def heads_off_remote(repo: Repo) -> List[Head]:
    """Get all Heads that do not coincide with any remote ref"""
    remote_commits = {ref.commit for remote in repo.remotes for ref in remote.refs}
    return [head for head in repo.heads if head.commit not in remote_commits]


def stashes(repo: Repo) -> List[str]:
    """Get stashes (empty list if none)"""
    return repo.git.stash("list").splitlines()


def other_files(repo: Repo) -> List[str]:
    """Get list of 'other' files (empty if none)"""
    return repo.git.ls_files(others=True).splitlines()


def info_lines(
    repo: Repo, ignore_names: Iterable[str] = ("refs",),
) -> Iterator[Tuple[str, str]]:
    """
    Iterate over (filename, line) pairs in .git/info/ directory, ignoring comments.
    """
    ignore_names = set(ignore_names)
    info_path = Path(repo.git_dir) / "info"
    for child in info_path.iterdir():
        name = child.name
        if name not in ignore_names:
            with child.open() as fp:
                for line in fp:
                    line = line.strip()
                    if not line.startswith("#"):
                        yield name, line
