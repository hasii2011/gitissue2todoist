
from abc import ABC
from abc import abstractmethod


class IGitHubAuthDialog(ABC):
    """
    Interface for GitHub Device Flow authentication dialogs.
    """

    @abstractmethod
    async def startAuthentication(self) -> None:
        """
        Starts the GitHub OAuth device flow authentication.
        Displays the device code and polls for the user to complete login.
        """
        pass

    @abstractmethod
    def show(self) -> None:
        """
        Displays the authentication dialog to the user.
        """
        pass
