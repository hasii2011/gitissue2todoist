
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

    @abstractmethod
    def _onSave(self, widget):
        pass

    @abstractmethod
    def _onCancel(self, widget):
        pass
