from dataclasses import dataclass
from typing import List, Iterator, Tuple
import logging
import os
import re

from colorama import Fore, Style
import click
import git

import git_utils

logger = logging.getLogger(__name__)

Style_REVERSE = "\x1b[7m"
COMMITTED_PATTERN = r"^## ([-a-z]+)...origin/\1$"


@dataclass
class RepoInfo:
    path: str
    branchname_tracking_info: str
    statuses: List[Tuple[str, str]]

    @classmethod
    def from_path(cls, path: str) -> "RepoInfo":
        try:
            with git.Repo(path) as repo:
                # git status --branch --porcelain=v1
                returncode, stdout, stderr = repo.git.status(
                    branch=True, porcelain="v1", with_extended_output=True
                )
                if returncode:
                    logger.debug("git-status failed with exit code: %d", returncode)
                if stderr:
                    logger.debug("git-status error output: %s", stderr)
                branchname_tracking_info, *status_lines = stdout.splitlines()
                statuses = [(line[:2], line[3:]) for line in status_lines]
            return cls(path, branchname_tracking_info, statuses)
        except git.exc.InvalidGitRepositoryError as exc:  # pylint: disable=no-member
            logger.debug("failed to read git repo: %r", exc)
            return cls(path, None, [])

    def format(self) -> Iterator[str]:
        yield f"{Style_REVERSE}{self.path}{Style.RESET_ALL}"
        if not self.branchname_tracking_info:
            yield f"{Fore.LIGHTBLACK_EX}not a git repo{Fore.RESET}"
        elif not re.match(COMMITTED_PATTERN, self.branchname_tracking_info):
            yield f"{Fore.MAGENTA}{self.branchname_tracking_info}{Fore.RESET}"
        elif not self.statuses:
            yield "clean and committed"
        for xy, path in self.statuses:
            if xy == " M":
                yield f"{Fore.BLUE}{xy} {path}{Fore.RESET}"
            elif xy == " A":
                yield f"{Fore.GREEN}{xy} {path}{Fore.RESET}"
            elif xy == " D":
                yield f"{Fore.RED}{xy} {path}{Fore.RESET}"
            elif xy == "??":
                yield f"{Fore.YELLOW}{xy} {path}{Fore.RESET}"
            else:
                yield f"{xy} {path}"


@click.command()
@click.version_option(git_utils.__version__)
@click.argument("git_dirs", type=click.Path(exists=True, file_okay=False), nargs=-1)
def cli(git_dirs: List[str]):
    """
    Print statuses for multiple git repositories.

    GIT_DIRS defaults to child directories of the current working directory.
    """
    if not git_dirs:
        git_dirs = [
            child
            for child in sorted(os.listdir(), key=str.casefold)
            if os.path.isdir(child)
        ]

    for git_dir in git_dirs:
        status = RepoInfo.from_path(git_dir)
        for line in status.format():
            print(line)
        print()


main = cli.main


if __name__ == "__main__":
    main()
