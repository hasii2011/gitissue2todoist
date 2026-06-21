from typing import cast
from logging import Logger
from logging import getLogger
import asyncio

from toga import App
from toga import Box
from toga import Button
from toga import Window

from toga.style import Pack
from toga.style.pack import COLUMN
from toga.style.pack import ROW

from gitissue2todoist.preferences.IPreferencesDialog import IPreferencesDialog


class IOSPreferencesDialog(IPreferencesDialog):
    """
    An iOS-compatible Preferences overlay.
    
    iOS enforces a strict Single Window architecture and will raise a 
    RuntimeError if a secondary toga.Window is instantiated. This class 
    bypasses that by temporarily swapping the content of the main_window.
    """
    def __init__(self):
        self.logger: Logger = getLogger(__name__)
        super().__init__()

        self._future:      asyncio.Future | None = None

    async def showDialog(self) -> bool:
        """
        Displays the configuration overlay and waits for user input.
        
        Returns:
            True if the user clicked OK and saved preferences, False if canceled.
        """
        assert App.app is not None, 'I know what I am doing'
        app: App = App.app
        
        # Bind to a local variable so PyCharm respects type narrowing
        _win = app.main_window
        assert _win is not None
        assert isinstance(_win, Window)

        mainWindow: Window = _win
        originalContent: Box = cast(Box, mainWindow.content)
        
        loop = asyncio.get_event_loop()
        self._future = loop.create_future()

        mainWindow.content = self._createDialogContent()  # Deploy the form by swapping the mainWindow content
        
        assert self._future is not None, 'I set it!'
        result: bool = await self._future                 # Wait for the user asynchronously
        
        mainWindow.content = originalContent              # Restore the original UI content
        
        return result

    def _createDialogContent(self) -> Box:
        okButton:     Button = Button('OK', on_press=self._onOk)
        cancelButton: Button = Button('Cancel', on_press=self._onCancel, style=Pack(margin_right=10))

        spacerBox: Box = Box(style=Pack(flex=1))
        buttonBox: Box = Box(children=[spacerBox, cancelButton, okButton], style=Pack(direction=ROW, margin_top=10))

        mainBox: Box = Box(
            children=[
                self._configPanel,
                buttonBox
            ],
            style=Pack(direction=COLUMN, margin=20)
        )
        return mainBox

    # noinspection PyUnusedLocal
    def _onOk(self, widget) -> None:
        self._configPanel.savePreferences()
        
        assert self._future is not None, 'I set it!'
        if not self._future.done():
            self._future.set_result(True)

    # noinspection PyUnusedLocal
    def _onCancel(self, widget) -> None:
        
        assert self._future is not None, 'I set it!'
        if not self._future.done():
            self._future.set_result(False)
