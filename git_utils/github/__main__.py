import argparse
import logging
import os

from git_utils import github


def path_command(opts, client: github.Client):
    client.request(opts.path)


def commits_command(opts, client: github.Client):
    client.commits(opts.owner, opts.repo)


def watchers_command(opts, client: github.Client):
    client.watchers(opts.owner, opts.repo)


def contents_command(opts, client: github.Client):
    client.contents(opts.owner, opts.repo, opts.path)


def main():
    parser = argparse.ArgumentParser(
        description="Execute GitHub API requests",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-t",
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="authorization token",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="log extra information (repeat for even more)",
    )

    subparsers = parser.add_subparsers(
        dest="subcommand", help="special-purpose subcommands"
    )

    # TODO: implement a default subcommand of nothing, somehow (argparse fail)
    # see: https://stackoverflow.com/q/6365601
    parser_path = subparsers.add_parser("path")
    parser_path.add_argument("path", help='API path; e.g., "/user"')
    parser_path.set_defaults(func=path_command)

    parser_commits = subparsers.add_parser("commits")
    parser_commits.add_argument(
        "-o", "--owner", help="repository owner (user/organization)"
    )
    parser_commits.add_argument("-r", "--repo", help="repository name")
    parser_commits.set_defaults(func=commits_command)

    parser_contents = subparsers.add_parser("watchers")
    parser_contents.add_argument(
        "-o", "--owner", help="repository owner (user/organization)"
    )
    parser_contents.add_argument("-r", "--repo", help="repository name")
    parser_contents.set_defaults(func=watchers_command)

    parser_contents = subparsers.add_parser("contents")
    parser_contents.add_argument(
        "-o", "--owner", help="repository owner (user/organization)"
    )
    parser_contents.add_argument("-r", "--repo", help="repository name")
    parser_contents.add_argument(
        "-p", "--path", help="path in repository to list contents of"
    )
    parser_contents.set_defaults(func=contents_command)

    opts = parser.parse_args()

    loglevel = 30 - (opts.verbose * 10)
    # (none) = 0 => 30 = WARNING
    # -v     = 1 => 20 = INFO
    # -vv    = 2 => 10 = DEBUG
    # -vvv   = 3 =>  0 = NOTSET
    logging.basicConfig(level=loglevel)
    logger = logging.getLogger("github-api")
    logger.debug("Logging at level %d", loglevel)

    if opts.token:
        api = github.API.from_token(opts.token)
    else:
        logger.warning("Could not find token; continuing without authentication.")
        api = github.API()

    opts.func(opts, api)


if __name__ == "__main__":
    main()
