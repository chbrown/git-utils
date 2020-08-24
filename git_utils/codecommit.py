from botocore.exceptions import ClientError


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
            repositoryName=name, repositoryDescription=description, tags=tags,
        )
