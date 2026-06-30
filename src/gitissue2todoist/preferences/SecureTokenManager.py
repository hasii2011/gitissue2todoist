
from keyring import get_password
from keyring import set_password


class SecureTokenManager:
    """
    Abstracts keychain operations to securely store authentication tokens
    in the macOS and iOS Keychain rather than plaintext INI files.
    """
    
    SERVICE_NAME:      str = 'org.gitissue2todoist.gitissue2todoist'
    GITHUB_TOKEN_KEY:  str = 'github_token'
    TODOIST_TOKEN_KEY: str = 'todoist_token'
    
    @classmethod
    def saveGitHubToken(cls, token: str) -> None:
        set_password(service_name=cls.SERVICE_NAME, username=cls.GITHUB_TOKEN_KEY, password=token)

    @classmethod
    def getGitHubToken(cls) -> str | None:
        return get_password(service_name=cls.SERVICE_NAME, username=cls.GITHUB_TOKEN_KEY)
        
    @classmethod
    def saveTodoistToken(cls, token: str) -> None:
        set_password(service_name=cls.SERVICE_NAME, username=cls.TODOIST_TOKEN_KEY, password=token)

    @classmethod
    def getTodoistToken(cls) -> str | None:
        return get_password(service_name=cls.SERVICE_NAME, username=cls.TODOIST_TOKEN_KEY)
