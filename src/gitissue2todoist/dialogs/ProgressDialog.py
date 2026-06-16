from typing import Tuple

from toga import App
from toga import Box
from toga import Label
from toga import Position
from toga import ProgressBar
from toga import Window

from toga.style import Pack
from toga.style.pack import COLUMN, CENTER

LABEL_MARGIN_BOTTOM: int             = 10
PROGRESS_BAR_WIDTH:  int             = 250
PROGRESS_BOX_MARGIN: int             = 20
WINDOW_SIZE:         Tuple[int, int] = (300, 100)

class ProgressDialog:
    """
    A desktop-compatible Progress Dialog overlay for Toga applications.

    This class manages a secondary modal-like popup `toga.Window` to display an
    indeterminate progress bar and a status message. It runs asynchronously
    while preventing the user from manually closing the window and interrupting the
    ongoing background task.
    """

    def __init__(self, title: str = 'Working...'):
        """
        Initializes the ProgressDialog UI components.

        Args:
            title (str): The text displayed in the header of the secondary popup window.
                Defaults to 'Working...'.
        """
        self._title: str = title
        
        # Toga UI Elements
        self._statusLabel: Label = Label(text='Initializing...', style=Pack(margin_bottom=LABEL_MARGIN_BOTTOM))
        
        # Indeterminate progress bar sweeps back and forth (max defaults to None)
        self._progressBar: ProgressBar = ProgressBar(style=Pack(width=PROGRESS_BAR_WIDTH))
        
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

    def _setPosition(self, position: Position):
        self._progressWindow.position = position

    position = property(fset=_setPosition, doc='Write-only property to set the position of the dialog.')

    def show(self) -> None:
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
