
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

from gitissue2todoist.Preferences import Preferences
from gitissue2todoist.dialogs.IAuthenticationDialog import IAuthenticationDialog


class AuthenticationDialog(Window, IAuthenticationDialog):
    """
    A traditional secondary Window acting as a dialog.
    """
    def __init__(self, preferences: Preferences):

        super().__init__(title="GitHub Authentication")

        self.logger:       Logger                = getLogger(__name__)
        self._preferences: Preferences           = preferences
        self._future:      asyncio.Future | None = None
        self._tokenInput:  TextInput             = TextInput(value=self._preferences.gitHubAPIToken, style=Pack(flex=1))

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

    def _createDialogContent(self) -> Box:

        saveButton:   Button = Button('Save', on_press=self._onSave, style=Pack(padding=5))
        cancelButton: Button = Button('Cancel', on_press=self._onCancel, style=Pack(padding=5))

        buttonBox: Box = Box(children=[saveButton, cancelButton], style=Pack(direction=ROW, padding_top=10))

        authBox: Box = Box(
            children=[
                Label('Authentication Failed. Please enter your GitHub API Token:', style=Pack(padding_bottom=5)),
                self._tokenInput,
                buttonBox
            ],
            style=Pack(direction=COLUMN, padding=20)
        )
        return authBox

    # noinspection PyUnusedLocal
    def _onSave(self, widget):
        self._preferences.gitHubAPIToken = self._tokenInput.value
        self.close()
        if self._future and not self._future.done():
            self._future.set_result(True)

    # noinspection PyUnusedLocal
    def _onCancel(self, widget):
        self.close()
        if self._future and not self._future.done():
            self._future.set_result(False)
