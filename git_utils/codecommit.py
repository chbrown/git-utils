from datetime import datetime
import logging
import re
import urllib.parse

from botocore.exceptions import ClientError
from git import Repo

from .repo import remotes_urls, TemporaryRepo
from .util import sumsize, normalize_url, alias_url

logger = logging.getLogger(__name__)


def is_codecommit_url(urlstring: str) -> bool:
    split_result = urllib.parse.urlsplit(normalize_url(urlstring))
    hostname = split_result.hostname
    return re.match(r"^git-codecommit\.[-0-9a-z]+\.amazonaws\.com$", hostname)


def get_or_create_repository(
    client: "botocore.client.CodeCommit",
    name: str,
    description: str = None,
    tags: dict = None,
) -> dict:
    """
    Get or create CodeCommit repository identified by `name`.

    `description` and `tags` are only used during creation.
    """
    try:
        return client.get_repository(repositoryName=name)
    except ClientError as exc:
        if exc.response.get("Error").get("Code") != "RepositoryDoesNotExistException":
            # IDK but it's looking bad
            raise
        # otherwise, fine, we'll just create it
        return client.create_repository(
            repositoryName=name, repositoryDescription=description, tags=tags
        )


def mirror(
    client: "botocore.client.CodeCommit",
    url: str,
    name: str,
    min_updated: str = "2050-01-01",
):
    """
    Mirror git repo at `url` to existing or new CodeCommit repository.

    If such a CodeCommit repository already exists and its "updated" tag's value is
    after `min_updated`, stop.
    """
    metadata = get_or_create_repository(
        client, name, alias_url(url), {"group": "mirror", "source": url}
    ).get("repositoryMetadata")
    # compare "updated" tag with `min_updated` value
    resourceArn = metadata["Arn"]
    tags = client.list_tags_for_resource(resourceArn=resourceArn).get("tags")
    updated = tags.get("updated", "1970-01-01")
    if updated >= min_updated:
        logger.debug("Last updated on %r; not updating", updated)
        return
    # ok, update
    with TemporaryRepo.clone_from(url) as repo:
        total_size = sumsize(repo.working_dir)
        logger.debug("Cloned repo, using %s bytes on disk", f"{total_size:,}")
        cloneUrlSsh = metadata["cloneUrlSsh"]
        logger.info("Pushing %r -> %r", url, cloneUrlSsh)
        repo.git.push("--mirror", cloneUrlSsh)
    # update "updated" tag with current timestamp
    client.tag_resource(
        resourceArn=resourceArn,
        tags={"updated": datetime.now().astimezone().isoformat(timespec="seconds")},
    )


def archive(
    client: "botocore.client.CodeCommit",
    repo: Repo,
    name: str,
):
    """
    Archive git.Repo `repo` to existing or new CodeCommit repository.

    Adds resulting CodeCommit (SSH) URL to `repo`'s remotes.
    """
    # throw if there's more than one non-CodeCommit remote
    (url,) = (url for url in remotes_urls(repo) if not is_codecommit_url(url))
    metadata = get_or_create_repository(
        client, name, alias_url(url), {"group": "archive", "source": url}
    ).get("repositoryMetadata")
    # push from local Repo
    cloneUrlSsh = metadata["cloneUrlSsh"]
    logger.info("Pushing %r -> %r", repo, cloneUrlSsh)
    repo.git.push("--mirror", cloneUrlSsh)
    # add new remote
    repo.create_remote("aws", cloneUrlSsh)
    # update "updated" tag, even though we don't read from it
    resourceArn = metadata["Arn"]
    client.tag_resource(
        resourceArn=resourceArn,
        tags={"updated": datetime.now().astimezone().isoformat(timespec="seconds")},
    )
