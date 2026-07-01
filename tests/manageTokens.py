# /// script
# requires-python = ">=3.13.13"
# dependencies = [
#     "click",
#     "keyring",
#     "codeallybasic",
# ]
# ///
from click import clear
from click import group
from click import option
from click import secho

from keyring import delete_password
from keyring import set_password
from keyring import get_password
from keyring.errors import PasswordDeleteError

from sys import path
from pathlib import Path

TOKEN_COLOR:   str = 'cyan'
NORMAL_COLOR:  str = 'green'
WARNING_COLOR: str = 'yellow'
ERROR_COLOR:   str = 'red'

GITHUB_LONG_OPTION:   str = '--github'
TODOIST_LONG_OPTION:  str = '--todoist'
GITHUB_SHORT_OPTION:  str = '-g'
TODOIST_SHORT_OPTION: str = '-t'

CLEAR_TOKEN_ERROR_MSG: str = (
    f"Please specify which token to clear "
    f"({GITHUB_SHORT_OPTION}/{GITHUB_LONG_OPTION}, "
    f"{TODOIST_SHORT_OPTION}/{TODOIST_LONG_OPTION}, or -a/--all)."
)

SET_TOKEN_ERROR_MSG: str = (
    f"Please provide a token to set using "
    f"{GITHUB_SHORT_OPTION}/{GITHUB_LONG_OPTION} <token> or "
    f"{TODOIST_SHORT_OPTION}/{TODOIST_LONG_OPTION} <token>."
)

SHOW_TOKEN_ERROR_MSG: str = (
    f"Please specify which token to show "
    f"({GITHUB_SHORT_OPTION}/{GITHUB_LONG_OPTION}, "
    f"{TODOIST_SHORT_OPTION}/{TODOIST_LONG_OPTION}, or -a/--all)."
)

# Inject the src/ directory so the isolated uv environment can find the local package
path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from gitissue2todoist.preferences.SecureTokenManager import SERVICE_NAME
from gitissue2todoist.preferences.SecureTokenManager import GITHUB_TOKEN_KEY
from gitissue2todoist.preferences.SecureTokenManager import TODOIST_TOKEN_KEY


@group()
def cli():
    """
    Developer script to manage API tokens in the macOS Keychain.
    'Group' all of our sub-commands attached to it.
    This is the master command that holds everything else together.
    The decorator @cli.command(), is telling the sub commands to attach themselves
    this cli group!

    In the click community it is the defacto standard to use 'cli' for the root group.
    """
    pass

@cli.command(name='clearToken')
@option(GITHUB_SHORT_OPTION,  GITHUB_LONG_OPTION,  is_flag=True, help='Clear the GitHub token.')
@option(TODOIST_SHORT_OPTION, TODOIST_LONG_OPTION, is_flag=True, help='Clear the Todoist token.')
@option('-a', '--all', 'clear_all', is_flag=True, help='Clear all tokens.')
def clearToken(github: bool, todoist: bool, clear_all: bool):
    """
    Clear tokens from the keychain.
    """
    if not (github or todoist or clear_all):
        secho(CLEAR_TOKEN_ERROR_MSG, fg=ERROR_COLOR)
        return

    if github or clear_all:
        try:
            delete_password(SERVICE_NAME, GITHUB_TOKEN_KEY)
            secho("GitHub token cleared.", fg=NORMAL_COLOR)
        except PasswordDeleteError:
            secho("GitHub token was not found in the keychain.", fg=WARNING_COLOR)

    if todoist or clear_all:
        try:
            delete_password(SERVICE_NAME, TODOIST_TOKEN_KEY)
            secho("Todoist token cleared.", fg=NORMAL_COLOR)
        except PasswordDeleteError:
            secho("Todoist token was not found in the keychain.", fg=WARNING_COLOR)

@cli.command(name='setToken')
@option(GITHUB_SHORT_OPTION,  GITHUB_LONG_OPTION,  help='Set the GitHub token.')
@option(TODOIST_SHORT_OPTION, TODOIST_LONG_OPTION, help='Set the Todoist token.')
def setToken(github: str, todoist: str):
    """Set tokens in the keychain."""
    if not (github or todoist):
        secho(SET_TOKEN_ERROR_MSG, fg=ERROR_COLOR)
        return

    if github:
        set_password(SERVICE_NAME, GITHUB_TOKEN_KEY, github)
        secho("GitHub token successfully saved to the keychain.", fg=NORMAL_COLOR)

    if todoist:
        set_password(SERVICE_NAME, TODOIST_TOKEN_KEY, todoist)
        secho("Todoist token successfully saved to the keychain.", fg=NORMAL_COLOR)

@cli.command(name='showToken')
@option(GITHUB_SHORT_OPTION,  GITHUB_LONG_OPTION,  is_flag=True, help='Show the GitHub token.')
@option(TODOIST_SHORT_OPTION, TODOIST_LONG_OPTION, is_flag=True, help='Show the Todoist token.')
@option('-a', '--all', 'show_all', is_flag=True, help='Show all tokens.')
def showToken(github: bool, todoist: bool, show_all: bool):
    """Show tokens from the keychain."""
    if not (github or todoist or show_all):
        secho(SHOW_TOKEN_ERROR_MSG, fg=ERROR_COLOR)
        return

    if github or show_all:
        gh_token = get_password(SERVICE_NAME, GITHUB_TOKEN_KEY)
        if gh_token:
            secho(f"GitHub token: {gh_token}", fg=TOKEN_COLOR)
        else:
            secho("GitHub token: [Not Found]", fg=WARNING_COLOR)

    if todoist or show_all:
        td_token = get_password(SERVICE_NAME, TODOIST_TOKEN_KEY)
        if td_token:
            secho(f"Todoist token: {td_token}", fg=TOKEN_COLOR)
        else:
            secho("Todoist token: [Not Found]", fg=WARNING_COLOR)

if __name__ == '__main__':
    clear()
    cli()
