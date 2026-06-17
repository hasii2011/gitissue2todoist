
from abc import ABC
from abc import abstractmethod

from toga import Box


class IAuthenticationDialog(ABC):

    @abstractmethod
    async def showDialog(self) -> bool:
        """
        Displays the authentication overlay and waits for user input.

        Returns:
            True if the user saved a new token, False if canceled.
        """
        pass

    @abstractmethod
    def _createDialogContent(self) -> Box:
        pass

    @property
    @abstractmethod
    def apiToken(self) -> str:
        """
        Returns the entered API token. 
        Only valid if showDialog() returned True.
        """
        pass

    @abstractmethod
    def _onOk(self, widget):
        pass

    @abstractmethod
    def _onCancel(self, widget):
        pass
