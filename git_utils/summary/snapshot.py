from typing import Iterator
import logging
import re

from colorama import Fore, Style
from git import Repo

from ..repo import status

logger = logging.getLogger(__name__)

Style_REVERSE = "\x1b[7m"


def create(repo: Repo) -> dict:
    return {
        "path": repo.working_dir,
        "branch_and_status": status(repo, branch=True),
    }


def iter_report(snapshot: dict) -> Iterator[str]:
    path = snapshot["path"]
    (_, branchname_tracking_info), *statuses = snapshot["branch_and_status"]

    yield f"{Style_REVERSE}{path}{Style.RESET_ALL}"
    if not re.match(r"^([-a-z]+)...origin/\1$", branchname_tracking_info):
        yield f"{Fore.MAGENTA}{branchname_tracking_info}{Fore.RESET}"
    elif not statuses:
        yield "clean and committed"
    for xy, path in statuses:
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
