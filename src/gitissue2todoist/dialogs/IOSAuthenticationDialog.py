
from typing import cast

from logging import Logger
from logging import getLogger

import asyncio

from toga import App
from toga import Box
from toga import Button
from toga import Label
from toga import Window
from toga import TextInput

from toga.style import Pack
from toga.style.pack import COLUMN
from toga.style.pack import ROW

from gitissue2todoist.dialogs.IAuthenticationDialog import IAuthenticationDialog


class IOSAuthenticationDialog(IAuthenticationDialog):
    """
    An iOS-compatible Authentication overlay.
    
    iOS enforces a strict Single Window architecture and will raise a 
    RuntimeError if a secondary toga.Window is instantiated. This class 
    bypasses that by temporarily swapping the content of the main_window.
    """
    def __init__(self, title: str, message: str, initialToken: str = ''):

        self.logger: Logger = getLogger(__name__)

        self._title:        str                   = title
        self._message:      str                   = message
        self._initialToken: str                   = initialToken
        self._future:       asyncio.Future | None = None
        self._tokenInput:   TextInput             = cast(TextInput, None)

    async def showDialog(self) -> bool:
        """
        Displays the authentication overlay and waits for user input.
        
        Returns:
            True if the user saved a new token, False if canceled.
        """
        assert App.app is not None, 'I know what i am doing'
        app: App = App.app
        
        # Bind to a local variable so PyCharm respects type narrowing (it ignores asserts on properties)
        _win = app.main_window
        assert _win is not None
        assert isinstance(_win, Window)

        mainWindow: Window = _win
        
        originalContent: Box = cast(Box, mainWindow.content)
        
        loop = asyncio.get_event_loop()
        self._future = loop.create_future()

        mainWindow.content = self._createDialogContent()      # Deploy the form by swapping the mainWindow content
        
        assert self._future is not None, 'I set it!'
        result: bool = await self._future               # Wait for the user asynchronously
        
        mainWindow.content = originalContent            # Restore the original UI content
        
        return result

    @property
    def apiToken(self) -> str:
        return self._tokenInput.value

    def _createDialogContent(self) -> Box:

        self._tokenInput = TextInput(value=self._initialToken, style=Pack(flex=1))

        okButton:     Button = Button('OK', on_press=self._onOk, style=Pack(margin=5))
        cancelButton: Button = Button('Cancel', on_press=self._onCancel, style=Pack(margin=5))

        buttonBox: Box = Box(children=[okButton, cancelButton], style=Pack(direction=ROW, margin_top=10))

        authBox: Box = Box(
            children=[
                Label(self._message, style=Pack(margin_bottom=5)),
                self._tokenInput,
                buttonBox
            ],
            style=Pack(direction=COLUMN, margin=20)
        )
        return authBox

    # noinspection PyUnusedLocal
    def _onOk(self, widget):

        if self._future and not self._future.done():
            self._future.set_result(True)

    # noinspection PyUnusedLocal
    def _onCancel(self, widget):

        assert self._future is not None, 'I set it!'
        self._future.set_result(False)
