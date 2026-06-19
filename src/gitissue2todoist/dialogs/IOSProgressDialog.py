from typing import cast

from toga import App
from toga import Box
from toga import Label
from toga import Position
from toga import ProgressBar
from toga import Window

from toga.style import Pack
from toga.style.pack import COLUMN
from toga.style.pack import CENTER

from gitissue2todoist.dialogs.IProgressDialog import IProgressDialog

class IOSProgressDialog(IProgressDialog):
    """
    An iOS-compatible Progress Dialog overlay.
    
    iOS enforces a strict Single Window architecture and will raise a 
    RuntimeError if a secondary toga.Window is instantiated. This class 
    bypasses that by temporarily swapping the content of the main_window.
    """
    def __init__(self, title: str = 'Working...'):

        self._title: str = title
        
        self._statusLabel: Label = Label(text='Initializing...', style=Pack(margin_bottom=10))
        self._progressBar: ProgressBar = ProgressBar(style=Pack(width=250))
        
        self._progressBox: Box = Box(
            children=[self._statusLabel, self._progressBar],
            style=Pack(direction=COLUMN, align_items=CENTER, margin=20)
        )
        
        self._originalContent: Box | None = None

    def _setPosition(self, position: Position) -> None:
        raise NotImplementedError('Explicitly setting dialog positions is not supported on iOS.')

    position = property(fset=_setPosition, doc='No-op write-only property to satisfy IProgressDialog.')

    def showDialog(self) -> None:
        """
        Displays the progress overlay by swapping out the main window's content.
        """
        assert App.app is not None, 'App must be instantiated'
        app: App = App.app
        
        _win = app.main_window
        assert _win is not None
        assert isinstance(_win, Window)

        mainWindow: Window = _win
        
        # Safely capture the user's active screen
        self._originalContent = cast(Box, mainWindow.content)
        
        # Inject the HUD overlay
        mainWindow.content = self._progressBox
        
        self._progressBar.start()

    def updateMessage(self, message: str) -> None:
        self._statusLabel.text = message

    def destroy(self) -> None:
        """
        Stops the animation and restores the original UI content.
        """
        self._progressBar.stop()
        
        if self._originalContent is not None:
            assert App.app is not None
            app: App = App.app
            _win = app.main_window
            assert _win is not None
            assert isinstance(_win, Window)

            # Restore the user's screen seamlessly
            _win.content = self._originalContent
            self._originalContent = None
