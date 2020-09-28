from typing import List
import logging
import os

from colorama import Fore
import click
import git

import git_utils
from .snapshot import create, iter_report

logger = logging.getLogger(__name__)


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
        try:
            with git.Repo(git_dir) as repo:
                snapshot = create(repo)
                for line in iter_report(snapshot):
                    print(line)
        except git.exc.InvalidGitRepositoryError:  # pylint: disable=no-member
            print(f"{Fore.LIGHTBLACK_EX}Not a valid git repo: {git_dir!r}{Fore.RESET}")
        print()


main = cli.main


if __name__ == "__main__":
    main()
