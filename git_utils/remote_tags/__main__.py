from urllib.parse import urlsplit, urlunsplit

import click

import git_utils
from ..repo import ls_remote_tags


@click.command()
@click.version_option(git_utils.__version__)
@click.argument("repository")
@click.option("-s", "--default-scheme", default="git", show_default=True)
@click.option("-h", "--default-host", default="github.com", show_default=True)
def cli(repository: str, default_scheme: str, default_host: str):
    """
    git-ls-remote --tags without the fluff.

    REPOSITORY can be a URL, the path part of a URL (in which case the scheme and
    host are added from the --default-{scheme,host} options), or filepath.
    """
    split_result = urlsplit(repository)
    split_result = split_result._replace(
        scheme=split_result.scheme or default_scheme,
        netloc=split_result.netloc or default_host,
    )
    repository = urlunsplit(split_result)

    for _, tag in ls_remote_tags(repository):
        print(tag)


main = cli.main


if __name__ == "__main__":
    main()
