import json
import sys

from requests import Response

from git_utils.util import delete_keys, CustomJSONEncoder


def print_response(response: Response):
    """
    Print Response instance to stdout.
    """
    # only pretty-print if stdout is a TTY (not piped anywhere else)
    indent = 2 if sys.stdout.isatty() else None
    dump_kwargs = {
        "ensure_ascii": False,
        "cls": CustomJSONEncoder,
        "indent": indent,
        "sort_keys": True,
    }

    result = response.json()
    # remove keys ending with 'url'
    result = delete_keys(result, lambda k: k.endswith("url"))

    if isinstance(result, dict):
        json.dump(result, sys.stdout, **dump_kwargs)
    else:
        for item in result:
            json.dump(item, sys.stdout, **dump_kwargs)
            sys.stdout.write("\n")
            sys.stdout.flush()
