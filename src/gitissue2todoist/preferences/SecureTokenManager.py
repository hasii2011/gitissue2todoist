
from keyring import set_password
from keyring import get_password
from keyring.errors import NoKeyringError
from codeallybasic.SingletonV3 import SingletonV3

from gitissue2todoist.preferences.FallbackTokenManager import FallbackTokenManager


SERVICE_NAME:      str = 'org.gitissue2todoist.gitissue2todoist'
GITHUB_TOKEN_KEY:  str = 'GitHubToken'
TODOIST_TOKEN_KEY: str = 'TodoistToken'


class SecureTokenManager(metaclass=SingletonV3):
    """
    Abstracts keychain operations to securely store authentication tokens
    in the macOS and iOS Keychain rather than plaintext INI files.
    """

    @property
    def gitHubToken(self) -> str | None:

        try:
            return get_password(
                service_name=SERVICE_NAME,
                username=GITHUB_TOKEN_KEY
            )
        except NoKeyringError:
            return FallbackTokenManager().readFallback(key=GITHUB_TOKEN_KEY)
        
    @gitHubToken.setter
    def gitHubToken(self, token: str) -> None:

        try:
            set_password(
                service_name=SERVICE_NAME,
                username=GITHUB_TOKEN_KEY,
                password=token
            )
        except NoKeyringError:
            FallbackTokenManager().writeFallback(key=GITHUB_TOKEN_KEY, token=token)

    @property
    def todoistToken(self) -> str | None:

        try:
            return get_password(
                service_name=SERVICE_NAME,
                username=TODOIST_TOKEN_KEY
            )
        except NoKeyringError:
            return FallbackTokenManager().readFallback(key=TODOIST_TOKEN_KEY)

    @todoistToken.setter
    def todoistToken(self, token: str) -> None:

        try:
            set_password(
                service_name=SERVICE_NAME,
                username=TODOIST_TOKEN_KEY,
                password=token
            )
        except NoKeyringError:
            FallbackTokenManager().writeFallback(key=TODOIST_TOKEN_KEY, token=token)
