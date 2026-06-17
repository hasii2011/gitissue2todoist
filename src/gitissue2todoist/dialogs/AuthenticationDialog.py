
from logging import Logger
from logging import getLogger

import asyncio

from toga import Box
from toga import Button
from toga import Label
from toga import TextInput
from toga import Window

from toga.style import Pack
from toga.style.pack import COLUMN
from toga.style.pack import ROW

from gitissue2todoist.dialogs.IAuthenticationDialog import IAuthenticationDialog


class AuthenticationDialog(Window, IAuthenticationDialog):
    """
    A traditional secondary Window acting as a dialog.
    """
    def __init__(self, title: str, message: str, initialToken: str = ''):

        super().__init__(title=title)

        self.logger:       Logger                = getLogger(__name__)
        self._message:     str                   = message
        self._future:      asyncio.Future | None = None
        self._tokenInput:  TextInput             = TextInput(value=initialToken, style=Pack(flex=1))

        self.content = self._createDialogContent()

    async def showDialog(self) -> bool:
        """
        Displays the window and waits asynchronously for user input.
        """
        loop = asyncio.get_event_loop()
        self._future = loop.create_future()
        
        self.show()

        assert self._future is not None, 'I know what I am doing'
        result: bool = await self._future
        return result

    @property
    def apiToken(self) -> str:
        return self._tokenInput.value

    def _createDialogContent(self) -> Box:

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
        self.close()
        if self._future and not self._future.done():
            self._future.set_result(True)

    # noinspection PyUnusedLocal
    def _onCancel(self, widget):
        self.close()
        if self._future and not self._future.done():
            self._future.set_result(False)
