
from typing import cast
from typing import Tuple
from typing import SupportsFloat

from toga import App
from toga import Box
from toga import Label
from toga import Position
from toga import ProgressBar
from toga import Window

from toga.style import Pack
from toga.style.pack import COLUMN, CENTER

from gitissue2todoist.dialogs.IProgressDialog import IProgressDialog

LABEL_MARGIN_BOTTOM: int             = 10
PROGRESS_BAR_WIDTH:  int             = 250
PROGRESS_BOX_MARGIN: int             = 20
WINDOW_SIZE:         Tuple[int, int] = (300, 100)

INDETERMINATE_PROGRESS_MAX: SupportsFloat   = cast(SupportsFloat, cast(object, None))

class ProgressDialog(IProgressDialog):
    """
    A desktop-compatible Progress Dialog overlay for Toga applications.

    This class manages a secondary modal-like popup `toga.Window` to display an
    indeterminate progress bar and a status message. It runs asynchronously
    while preventing the user from manually closing the window and interrupting the
    ongoing background task.
    """

    def __init__(self, title: str = 'Working...', maxProgressValue: SupportsFloat = INDETERMINATE_PROGRESS_MAX):
        """

        Initializes the ProgressDialog UI components.

        Args:
            title (str): The text displayed in the header of the secondary popup window.
                Defaults to 'Working...'.
        """
        self._title: str = title
        
        # Toga UI Elements
        self._statusLabel: Label = Label(text='Initializing...', style=Pack(margin_bottom=LABEL_MARGIN_BOTTOM))
        
        # Indeterminate progress bar sweeps back and forth (max defaults to 1.0)
        self._progressBar: ProgressBar = ProgressBar(style=Pack(width=PROGRESS_BAR_WIDTH), max=maxProgressValue)
        
        self._progressBox: Box = Box(
            children=[self._statusLabel, self._progressBar],
            style=Pack(direction=COLUMN, align_items=CENTER, margin=PROGRESS_BOX_MARGIN)
        )
        
        # Instantiate a secondary popup Window
        self._progressWindow: Window = Window(
            title=self._title, 
            size=WINDOW_SIZE, 
            resizable=False,
            closable=False     # Prevent user from closing it manually
        )
        self._progressWindow.content = self._progressBox

    @property
    def position(self) -> Position:
        """Write-only property to set the position of the dialog."""
        raise NotImplementedError('This property is write-only')

    @position.setter
    def position(self, newPosition: Position) -> None:
        self._progressWindow.position = newPosition

    @property
    def updateProgress(self) -> float:
        """Write-only property to set the progress bar current value."""
        raise NotImplementedError('This property is write-only')

    @updateProgress.setter
    def updateProgress(self, value: float) -> None:
        self._progressBar.value = value

    @property
    def maxProgressValue(self) -> float:
        """
        Write-only property to set the progress bar maximum value.
        """
        raise NotImplementedError('This property is write-only')

    @maxProgressValue.setter
    def maxProgressValue(self, newValue: float) -> None:
        """
        Kills the sweeping animation so it can accept values!

        Args:
            newValue:

        """
        self._progressBar.stop()
        self._progressBar.max = newValue

    def showDialog(self) -> None:
        """
        Displays the secondary progress window and starts the progress bar animation.
        
        This method must be called after the main Toga application has been instantiated, 
        as it explicitly registers the new window with the active `toga.App` instance.
        """
        assert App.app is not None
        app: App = App.app
        app.windows.add(self._progressWindow)
        
        self._progressWindow.show()
        self._progressBar.start()

    def updateMessage(self, message: str) -> None:
        """
        Dynamically updates the status label text displayed above the progress bar.

        Args:
            message (str): The new status message to display to the user.
        """
        self._statusLabel.text = message

    def destroy(self) -> None:
        """
        Stops the progress bar animation and completely closes the popup window.
        
        This method should always be called inside a `finally` block to guarantee that 
        the secondary window closes, even if the background task encounters an error.
        """
        self._progressBar.stop()
        self._progressWindow.close()
