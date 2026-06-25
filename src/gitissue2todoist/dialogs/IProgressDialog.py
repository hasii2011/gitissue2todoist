
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

    @property
    def position(self) -> Position:
        """
        Abstract write-only property for dialog position.
        """
        raise NotImplementedError('This property is write-only')

    @position.setter
    @abstractmethod
    def position(self, newPosition: Position) -> None:
        pass

    @property
    def updateProgress(self) -> float:
        """
        Write-only property to set the progress bar current value.
        """
        raise NotImplementedError('This property is write-only')

    @updateProgress.setter
    @abstractmethod
    def updateProgress(self, value: float) -> None:
        pass

    @property
    def maxProgressValue(self) -> float:
        """
        Write-only property to set the progress bar maximum value.
        """
        raise NotImplementedError('This property is write-only')

    @maxProgressValue.setter
    @abstractmethod
    def maxProgressValue(self, newValue: float) -> None:
        pass

    @abstractmethod
    def updateMessage(self, message: str) -> None:
        pass

    @abstractmethod
    def destroy(self) -> None:
        pass
