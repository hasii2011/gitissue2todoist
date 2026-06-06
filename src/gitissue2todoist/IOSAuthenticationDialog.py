from typing import cast

from logging import Logger
from logging import getLogger

import asyncio

from toga import App
from toga import Box
from toga import Button
from toga import Label
from toga import TextInput

from toga.style import Pack
from toga.style.pack import COLUMN
from toga.style.pack import ROW

from gitissue2todoist.Preferences import Preferences


class IOSAuthenticationDialog:
    """
    An iOS-compatible Authentication overlay.
    
    iOS enforces a strict Single Window architecture and will raise a 
    RuntimeError if a secondary toga.Window is instantiated. This class 
    bypasses that by temporarily swapping the content of the main_window.
    """
    def __init__(self, preferences: Preferences):
        self.logger: Logger = getLogger(__name__)
        self._preferences: Preferences = preferences

    async def show_dialog(self) -> bool:
        """
        Displays the authentication overlay and waits for user input.
        
        Returns:
            True if the user saved a new token, False if canceled.
        """
        from toga import Window
        
        assert App.app is not None, 'I know what i am doing'
        app: App = App.app
        
        assert app.main_window is not None
        assert not isinstance(app.main_window, str)
        
        # Cast explicitly to satisfy PyCharm's static type checker
        main_window: Window = cast(Window, app.main_window)
        
        original_content: Box = cast(Box, main_window.content)
        
        loop = asyncio.get_event_loop()
        future: asyncio.Future = loop.create_future()
        
        tokenInput: TextInput = TextInput(value=self._preferences.gitHubAPIToken, style=Pack(flex=1))

        # noinspection PyUnusedLocal
        def save(widget):
            self._preferences.gitHubAPIToken = tokenInput.value
            future.set_result(True)

        # noinspection PyUnusedLocal
        def cancel(widget):
            future.set_result(False)
            
        saveButton:   Button = Button('Save',   on_press=save,   style=Pack(padding=5))
        cancelButton: Button = Button('Cancel', on_press=cancel, style=Pack(padding=5))
        
        buttonBox: Box = Box(children=[saveButton, cancelButton], style=Pack(direction=ROW, padding_top=10))
        
        authBox: Box = Box(
            children=[
                Label('Authentication Failed. Please enter your GitHub API Token:', style=Pack(padding_bottom=5)),
                tokenInput,
                buttonBox
            ], 
            style=Pack(direction=COLUMN, padding=20)
        )
        
        # Deploy the form by swapping the main_window content
        main_window.content = authBox
        
        # Wait for the user asynchronously 
        result: bool = await future
        
        # Restore the original UI content
        main_window.content = original_content
        
        return result
