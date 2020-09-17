import logging
import os

import click

import git_utils
from . import print_response
from .api import API


@click.group(help="Execute GitHub API requests")
@click.version_option(git_utils.__version__)
@click.option(
    "-t",
    "--token",
    default=os.environ.get("GITHUB_TOKEN"),
    help="API authorization token.",
)
@click.option(
    "-v", "--verbose", count=True, help="Log extra information (repeat for even more)."
)
@click.pass_context
def cli(ctx: click.Context, token: str, verbose: int):
    level = logging.WARNING - (verbose * 10)
    # (none) = 0 => 30 = WARNING
    # -v     = 1 => 20 = INFO
    # -vv    = 2 => 10 = DEBUG
    # -vvv   = 3 =>  0 = NOTSET
    logging.basicConfig(level=level)
    logger = logging.getLogger("github-api")
    logger.debug("Logging at level %d", level)
    if token:
        api = API.from_token(token)
    else:
        logger.warning("Could not find token; continuing without authentication.")
        api = API()
    # pass along API instance to subcommands:
    ctx.ensure_object(dict)
    ctx.obj["api"] = api


@cli.command()
@click.argument("path")
@click.pass_context
def path(ctx: click.Context, path: str):
    """
    Perform GitHub API request and print the response.

    PATH is an arbitrary API path; e.g., "/user"
    """
    # TODO: figure out how to make this the default action
    # (where it runs if none of the other subcommands match)
    print_response(ctx.obj["api"].request(path))


@cli.command()
@click.option(
    "-o", "--owner", required=True, help="repository owner (user/organization)"
)
@click.option("-r", "--repo", required=True, help="repository name")
@click.pass_context
def commits(ctx: click.Context, owner: str, repo: str):
    ctx.obj["api"].commits(owner, repo)


@cli.command()
@click.option(
    "-o", "--owner", required=True, help="repository owner (user/organization)"
)
@click.option("-r", "--repo", required=True, help="repository name")
@click.pass_context
def watchers(ctx: click.Context, owner: str, repo: str):
    ctx.obj["api"].watchers(owner, repo)


@cli.command()
@click.option(
    "-o", "--owner", required=True, help="repository owner (user/organization)"
)
@click.option("-r", "--repo", required=True, help="repository name")
@click.option("-p", "--path", help="path in repository to list contents of", default="")
@click.pass_context
def contents(ctx: click.Context, owner: str, repo: str, path: str):
    ctx.obj["api"].contents(owner, repo, path)


main = cli.main


if __name__ == "__main__":
    main()
