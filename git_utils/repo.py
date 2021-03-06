from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, Iterable, Iterator, List, Optional, Set, Tuple, Union

from git import Git, Commit, Head, Repo

from .util import LazySet


def find(
    path: Path,
    maxdepth: int = 1,
    sortkey: Callable[[Path], Any] = lambda path: path.as_posix().casefold(),
) -> Iterator[Path]:
    """
    Find git dirs via depth-first pre-order filesystem traversal.
    Stops descending when a git dir is found or when maxdepth is reached.
    E.g., maxdepth=1 searches children of `path` but no further.
    """
    if (path / ".git").exists():
        yield path
    elif maxdepth > 0:
        for child in sorted(path.iterdir(), key=sortkey):
            yield from find(child, maxdepth - 1, sortkey)


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


def status(repo: Repo, branch: bool = False) -> List[Tuple[str, str]]:
    """
    Run `git status --porcelain=v1 [--branch]` and return a list of (XY, status) tuples.
    If branch=True, the first of these which will have XY="##" and status indicating
    the "branchname tracking info"; the rest (if any) will be path statuses.
    """
    return [
        (line[:2], line[3:])
        for line in repo.git.status(porcelain="v1", branch=branch).splitlines()
    ]


def info_lines(
    repo: Repo, ignore_names: Iterable[str] = ("refs",)
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


def ls_remote_tags(repo: Union[Repo, str]) -> Iterator[Tuple[str, str]]:
    """
    Iterate over (commit, tag) pairs from `git-ls-remote --tags`.
    `repo` can be either an on-disk Repo or a URL.
    """
    git, args = (repo.git, ()) if isinstance(repo, Repo) else (Git(), (repo,))
    lines = git.ls_remote(*args, tags=True, quiet=True).splitlines()
    for line in lines:
        commit, tag = line.split()
        # discard tags that end with ^{} (what are those for?)
        if tag.endswith("^{}"):
            continue
        if not tag.startswith("refs/tags/"):
            raise ValueError(f"Encountered unrecognized tag: {tag}")
        tag = tag[len("refs/tags/") :]
        yield commit, tag


class TemporaryRepo(Repo):
    # pylint: disable=arguments-differ
    """
    Acts like a Repo but overrides `clone_from` and `close` in order to create and
    delete a temporary directory.
    """

    temporary_directory: Optional[TemporaryDirectory] = None

    @classmethod
    def clone_from(cls, url: str, bare: bool = True, **kwargs) -> "TemporaryRepo":
        temporary_directory = TemporaryDirectory(suffix=".git", prefix="repo-")
        repo = super().clone_from(url, temporary_directory.name, bare=bare, **kwargs)
        repo.temporary_directory = temporary_directory
        return repo

    def close(self):
        super().close()
        if self.temporary_directory:
            self.temporary_directory.cleanup()


def iter_clone_commits(url: str) -> Iterator[Commit]:
    """
    Clone remote to bare repo in temporary directory and iterate over all commits.

    If clone fails for any reason, simply generates nothing.
    """
    try:
        with TemporaryRepo.clone_from(url) as repo:
            yield from heads_commits(repo)
    except Exception:
        pass


def iter_commits_not_in_remotes(repo: Repo) -> Set[Commit]:
    """
    Select just the commits from the given repo not found in any remote,
    cloning remote(s) into temporary directories as needed.
    """
    clone_binshas = LazySet(
        commit.binsha
        for url in remotes_urls(repo)
        for commit in iter_clone_commits(url)
    )
    return {
        commit for commit in heads_commits(repo) if commit.binsha not in clone_binshas
    }
