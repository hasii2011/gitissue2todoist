import asyncio
from logging import Logger
from logging import getLogger

from toga import Box
from toga import Button
from toga import Window

from toga.style import Pack
from toga.style.pack import COLUMN
from toga.style.pack import ROW

from gitissue2todoist.preferences.IPreferencesDialog import IPreferencesDialog


class PreferencesDialog(Window, IPreferencesDialog):
    """
    An async dialog that wraps the ConfigTabbedPanel UI.
    """
    def __init__(self, title: str = 'Configuration'):

        super().__init__(title=title, size=(500, 350))
        IPreferencesDialog.__init__(self)

        self.logger:       Logger                = getLogger(__name__)
        self._future:      asyncio.Future | None = None

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

    # noinspection PyUnusedLocal
    def _onOk(self, widget) -> None:
        self._configPanel.savePreferences()
        self.close()
        if self._future and not self._future.done():
            self._future.set_result(True)

    # noinspection PyUnusedLocal
    def _onCancel(self, widget) -> None:
        self.close()
        if self._future and not self._future.done():
            self._future.set_result(False)
