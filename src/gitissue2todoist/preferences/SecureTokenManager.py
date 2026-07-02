
from keyring import set_password
from keyring import get_password
from keyring.errors import NoKeyringError
import json
from pathlib import Path

from codeallybasic.SingletonV3 import SingletonV3

SERVICE_NAME: str = 'org.gitissue2todoist.gitissue2todoist'
GITHUB_TOKEN_KEY: str = 'github_token'
TODOIST_TOKEN_KEY: str = 'todoist_token'


class SecureTokenManager(metaclass=SingletonV3):
    """
    Abstracts keychain operations to securely store authentication tokens
    in the macOS and iOS Keychain rather than plaintext INI files.
    """

    def _getFallbackFilePath(self) -> Path:

        from toga import App

        configPath: Path = App.app.paths.config
        configPath.mkdir(parents=True, exist_ok=True)

        return configPath / 'secure_tokens.json'

    def _readFallback(self, key: str) -> str | None:

        filePath: Path = self._getFallbackFilePath()

        if filePath.exists():
            try:
                with filePath.open('r') as fileHandle:
                    tokenData: dict = json.load(fileHandle)
                    return tokenData.get(key)
            except Exception:
                pass

        return None

    def _writeFallback(self, key: str, token: str) -> None:

        filePath: Path = self._getFallbackFilePath()
        tokenData: dict = {}

        if filePath.exists():
            try:
                with filePath.open('r') as fileHandle:
                    tokenData = json.load(fileHandle)
            except Exception:
                pass

        tokenData[key] = token

        with filePath.open('w') as fileHandle:
            json.dump(tokenData, fileHandle)

    @property
    def gitHubToken(self) -> str | None:

        try:
            return get_password(
                service_name=SERVICE_NAME,
                username=GITHUB_TOKEN_KEY
            )
        except NoKeyringError:
            return self._readFallback(key=GITHUB_TOKEN_KEY)
        
    @gitHubToken.setter
    def gitHubToken(self, token: str) -> None:

        try:
            set_password(
                service_name=SERVICE_NAME,
                username=GITHUB_TOKEN_KEY,
                password=token
            )
        except NoKeyringError:
            self._writeFallback(key=GITHUB_TOKEN_KEY, token=token)

    @property
    def todoistToken(self) -> str | None:

        try:
            return get_password(
                service_name=SERVICE_NAME,
                username=TODOIST_TOKEN_KEY
            )
        except NoKeyringError:
            return self._readFallback(key=TODOIST_TOKEN_KEY)

    @todoistToken.setter
    def todoistToken(self, token: str) -> None:

        try:
            set_password(
                service_name=SERVICE_NAME,
                username=TODOIST_TOKEN_KEY,
                password=token
            )
        except NoKeyringError:
            self._writeFallback(key=TODOIST_TOKEN_KEY, token=token)
