from typing import List
import os
import re
import subprocess

from colorama import Fore, Style
import click

import git_utils

COMMITTED_PATTERN = r"^## ([-a-z]+)...origin/\1\s*$"


def reverse(string: str) -> str:
    return "\x1b[7m" + string + Style.RESET_ALL


def fore(color: str, string: str) -> str:
    return color + string + Fore.RESET


def print_git_report(git_dir: str, verbose: bool = False):
    git_proc = subprocess.run(
        ["git", "status", "-sb"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=git_dir,
        universal_newlines=True,
        check=False,
    )
    if git_proc.returncode == 0 and re.match(COMMITTED_PATTERN, git_proc.stdout):
        if verbose:
            print(f"({git_dir} is clean and committed)")
    else:
        print(reverse(git_dir))
        # print "$?", git_process.returncode
        if git_proc.stdout:
            branch, changes = git_proc.stdout.split("\n", 1)
            if not re.match(COMMITTED_PATTERN, branch):
                print(fore(Fore.MAGENTA, branch))
            for change in changes.split("\n"):
                if change.startswith(" M"):
                    print(fore(Fore.BLUE, change))
                elif change.startswith(" A"):
                    print(fore(Fore.GREEN, change))
                elif change.startswith(" D"):
                    print(fore(Fore.RED, change))
                elif change.startswith("??"):
                    print(fore(Fore.YELLOW, change))
                else:
                    print(change)
        if git_proc.stderr:
            # if verbose:
            print(git_proc.stderr)


@click.command()
@click.version_option(git_utils.__version__)
@click.argument("git_dirs", type=click.Path(exists=True, file_okay=False), nargs=-1)
@click.option("-v", "--verbose", is_flag=True, help="Log extra information")
def cli(git_dirs: List[str], verbose: bool):
    """
    Print statuses for multiple git repositories.

    GIT_DIRS defaults to child directories of the current working directory.
    """
    if not git_dirs:
        git_dirs = [child for child in os.listdir() if os.path.isdir(child)]

    for git_dir in git_dirs:
        print_git_report(git_dir, verbose)


main = cli.main


if __name__ == "__main__":
    main()
