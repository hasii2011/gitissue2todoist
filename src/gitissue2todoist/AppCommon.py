from typing import Callable


class AppCommon:

    APP_NAME:     str = 'GitIssueTodoist'
    PLATFORM_IOS: str = 'ios'
    PLATFORM_MAC: str = 'darwin'

    NO_GITHUB_TOKEN_MESSAGE:  str = 'Put Your GitHub API Token Here'
    NO_TODOIST_TOKEN_MESSAGE: str = 'Put Your Todoist API Token Here'

    @classmethod
    def getAuthenticationToken(cls, fallbackMessage: str, tokenRetrievalMethod: Callable[[], str | None]) -> str:
        """
        Retrieves a secure token and provides a safe fallback string if None is returned.
        
        Args:
            fallbackMessage:      The message/default string to use if no token exists
            tokenRetrievalMethod: A callable (like SecureTokenManager.getGitHubToken) that returns str | None
            
        Returns:
            The raw token if it exists, otherwise the fallback message
        """
        rawToken: str | None = tokenRetrievalMethod()
        
        if rawToken is None:
            return fallbackMessage
        else:
            return rawToken
