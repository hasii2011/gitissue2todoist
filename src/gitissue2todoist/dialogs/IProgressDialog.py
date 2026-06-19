
from abc import ABC
from abc import abstractmethod

from toga import Position


class IProgressDialog(ABC):

    @abstractmethod
    def showDialog(self) -> None:
        """
        Displays the secondary progress window and starts the progress bar animation.

        This method must be called after the main Toga application has been instantiated,
        as it explicitly registers the new window with the active `toga.App` instance.
        """
        pass

    @abstractmethod
    def _setPosition(self, position: Position) -> None:
        pass

    position = property(fset=_setPosition, doc='Abstract write-only property for dialog position.')

    @abstractmethod
    def updateMessage(self, message: str) -> None:
        pass

    @abstractmethod
    def destroy(self) -> None:
        pass
