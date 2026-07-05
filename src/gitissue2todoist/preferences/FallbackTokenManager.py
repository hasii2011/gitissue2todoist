
from json import load
from json import dump
from json import JSONDecodeError

from pathlib import Path

from codeallybasic.SingletonV3 import SingletonV3


class FallbackFailedError(Exception):
    """Raised when the fallback token storage mechanism fails."""
    pass


class FallbackTokenManager(metaclass=SingletonV3):
    """
    Handles file-based token storage as a fallback mechanism for when 
    the system Keyring is unavailable.
    """

    def readFallback(self, key: str) -> str | None:
        
        filePath: Path = self._getFallbackFilePath()

        if filePath.exists():
            try:
                with filePath.open('r') as fileHandle:
                    tokenData: dict = load(fileHandle)
                    return tokenData.get(key)
            except (OSError, JSONDecodeError) as fallbackError:
                raise FallbackFailedError('Failed to read from fallback token file.') from fallbackError

        return None

    def writeFallback(self, key: str, token: str) -> None:
        
        filePath: Path = self._getFallbackFilePath()
        tokenData: dict = {}

        if filePath.exists():
            try:
                with filePath.open('r') as fileHandle:
                    tokenData = load(fileHandle)
            except (OSError, JSONDecodeError) as fallbackError:
                raise FallbackFailedError('Failed to read previous state from fallback token file during write.') from fallbackError

        tokenData[key] = token

        with filePath.open('w') as fileHandle:
            dump(tokenData, fileHandle)

    def _getFallbackFilePath(self) -> Path:
        
        from toga import App

        togaApp: App | None = App.app
        if togaApp is None:
            raise RuntimeError('Toga app instance is not initialized.')

        configPath: Path = togaApp.paths.config
        configPath.mkdir(parents=True, exist_ok=True)

        return configPath / 'secure_tokens.json'
