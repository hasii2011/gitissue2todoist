
from keyring import set_password
from keyring import get_password

from codeallybasic.SingletonV3 import SingletonV3


class SecureTokenManager(metaclass=SingletonV3):
    """
    Abstracts keychain operations to securely store authentication tokens
    in the macOS and iOS Keychain rather than plaintext INI files.
    """
    
    SERVICE_NAME:      str = 'org.gitissue2todoist.gitissue2todoist'
    GITHUB_TOKEN_KEY:  str = 'github_token'
    TODOIST_TOKEN_KEY: str = 'todoist_token'

    @property
    def gitHubToken(self) -> str | None:

        return get_password(
            service_name=self.SERVICE_NAME, 
            username=self.GITHUB_TOKEN_KEY
        )
        
    @gitHubToken.setter
    def gitHubToken(self, token: str) -> None:

        set_password(
            service_name=self.SERVICE_NAME, 
            username=self.GITHUB_TOKEN_KEY, 
            password=token
        )

    @property
    def todoistToken(self) -> str | None:

        return get_password(
            service_name=self.SERVICE_NAME, 
            username=self.TODOIST_TOKEN_KEY
        )

    @todoistToken.setter
    def todoistToken(self, token: str) -> None:

        set_password(
            service_name=self.SERVICE_NAME, 
            username=self.TODOIST_TOKEN_KEY, 
            password=token
        )
