from typing import Callable
from typing import cast

from logging import Logger
from logging import getLogger

from toga import App
from toga import Box
from toga import Button
from toga import Label
from toga import Window

from toga.style import Pack
from toga.style.pack import COLUMN
from toga.style.pack import CENTER

from gitissue2todoist.githubauth.IGitHubAuthDialog import IGitHubAuthDialog
from gitissue2todoist.githubauth.OAuthDeviceFlow import OAuthDeviceFlow


class IOSGithubAuthDialog(IGitHubAuthDialog):
    """
    An iOS-compatible GitHub Authentication dialog.
    
    iOS enforces a strict Single Window architecture. This class 
    bypasses that by temporarily swapping the content of the main_window
    to show the GitHub authorization device code.
    """
    def __init__(self, title: str, clientId: str, onSuccess: Callable[[str], None]) -> None:

        self.logger: Logger = getLogger(__name__)

        self._title:     str                   = title
        self._clientId:  str                   = clientId
        self._onSuccess: Callable[[str], None] = onSuccess

        self._infoLabel: Label = Label(
            'Requesting code from GitHub...',
            style=Pack(margin=10)
        )
        self._codeLabel: Label = Label(
            '',
            style=Pack(margin=10, font_size=20, font_weight='bold')
        )
        
        self._cancelButton: Button = Button(
            'Cancel',
            on_press=self._onCancel,
            style=Pack(margin=10)
        )
        
        mainBox: Box = Box(style=Pack(direction=COLUMN, align_items=CENTER, margin=20))
        mainBox.add(self._infoLabel)
        mainBox.add(self._codeLabel)
        mainBox.add(self._cancelButton)
        
        self._dialogContent:   Box        = mainBox
        self._originalContent: Box | None = None

    def show(self) -> None:
        
        assert App.app is not None, 'App must be initialized'
        app: App = App.app
        
        _win = app.main_window
        assert _win is not None
        assert isinstance(_win, Window)

        mainWindow: Window = _win
        
        # Save the current UI and deploy the new one
        self._originalContent = cast(Box, mainWindow.content)
        mainWindow.content = self._dialogContent

    async def startAuthentication(self) -> None:
        
        oauthFlow: OAuthDeviceFlow = OAuthDeviceFlow(self._clientId)
        
        try:
            oauthFlow.executePhase1()
            
            self._infoLabel.text = 'Please enter this code in your browser:'
            self._codeLabel.text = oauthFlow.userCode
            
            accessToken: str = await oauthFlow.executePhase2()
            
            self._infoLabel.text = 'Authentication Successful!'
            self._codeLabel.text = 'Closing...'
            
            self._onSuccess(accessToken)
            self._closeDialog()
            
        except RuntimeError as e:
            self._infoLabel.text = str(e)
            self._codeLabel.text = ''

    # noinspection PyUnusedLocal
    def _onCancel(self, widget) -> None:
        self._closeDialog()

    def _closeDialog(self) -> None:
        
        assert App.app is not None, 'App must be initialized'
        app: App = App.app
        
        _win = app.main_window
        assert _win is not None
        assert isinstance(_win, Window)
        
        mainWindow: Window = _win
        
        if self._originalContent is not None:
            mainWindow.content = self._originalContent
