# git-utils


## Instructions

Install with [GNU Stow](https://www.gnu.org/software/stow/):

    git clone https://github.com/chbrown/git-utils
    cd git-utils
    stow -t /usr/local/bin bin


## Functionality

### gh

Open any [GitHub](https://github.com/) page(s) which the current git repository has as remotes.

    cd ~/scripts
    gh # opens https://github.com/chbrown/scripts in your browser


### git-remote-tags

Wrapping around `git ls-remote --tags git://...` to get the good stuff:

    git-remote-tags chbrown/amulet

Assumes github.


# git-statuses

Summarize multiple git repositories by running `git status -sb` on each one and color-coding the output (using ANSI escapes).
It's a quick way to see which repositories have uncommitted/unpushed changes.

    git-statuses ~/github/*/


### git-submodule-rm

Until git 1.8.3 rolls around:

    git-submodule-rm static/lib

Thanks goes to [stackoverflow](http://stackoverflow.com/questions/1260748/how-do-i-remove-a-git-submodule).


### git.io

Use the git.io URL shortener (https://git.io/blog-announcement) to shorten GitHub.com URLs.

    git.io https://blog.github.com/2011-11-10-git-io-github-url-shortener/ blog-announcement


### github-api

Send requests to the GitHub REST API v3 and print responses nicely.
Automatically pulls in `$GITHUB_TOKEN` environment variable, if available, to authorize requests.

    github-api path /user
    github-api path /user/emails
    github-api path /user/issues
    github-api path /users/isaacs
    github-api path /orgs/utcompling/members
    github-api path /repos/chbrown/rfc6902/events | jq

Not yet supported:

    github-api path /repos/chbrown/rfc6902/issues state=closed

Special-purpose subcommands:

**`commits`** gets the first and last 100 commits for a repository.
This is helpful because it's not easy to find when a repository was started on the GitHub website.

    github-api commits --owner chbrown --repo rfc6902

**`contents`** gets the contents of a file or directory (up to 1000 entries):

    github-api contents --owner chbrown --repo scripts --path /


## License

Copyright 2013–2018 Christopher Brown.
[MIT Licensed](https://chbrown.github.io/licenses/MIT/#2013-2018).
