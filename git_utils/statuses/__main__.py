from typing import List
import os
import re
import subprocess

import click

import git_utils

committed_re = re.compile(r"^## ([-a-z]+)...origin/\1\s*$")

RESET_ALL = "\x1b[0m"
REVERSE = "\x1b[7m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
BLUE = "\x1b[34m"
MAGENTA = "\x1b[35m"
RESET_FORE = "\x1b[39m"


def reverse(string: str) -> str:
    return REVERSE + string + RESET_ALL


def fore(color: str, string: str) -> str:
    return color + string + RESET_FORE


def print_git_report(git_dir: str, verbose: bool = False):
    git_proc = subprocess.run(
        ["git", "status", "-sb"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=git_dir,
        universal_newlines=True,
        check=False,
    )
    if git_proc.returncode == 0 and committed_re.match(git_proc.stdout):
        if verbose:
            print(f"({git_dir} is clean and committed)")
    else:
        print(reverse(git_dir))
        # print "$?", git_process.returncode
        if git_proc.stdout:
            branch, changes = git_proc.stdout.split("\n", 1)
            if not committed_re.match(branch):
                print(fore(MAGENTA, branch))
            for change in changes.split("\n"):
                if change.startswith(" M"):
                    print(fore(BLUE, change))
                elif change.startswith(" A"):
                    print(fore(GREEN, change))
                elif change.startswith(" D"):
                    print(fore(RED, change))
                elif change.startswith("??"):
                    print(fore(YELLOW, change))
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
