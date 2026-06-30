from typing import Callable

from toga import Box
from toga import Label
from toga import Window

from toga.style import Pack
from toga.style.pack import COLUMN
from toga.style.pack import CENTER

from gitissue2todoist.githubauth.OAuthDeviceFlow import OAuthDeviceFlow
from gitissue2todoist.githubauth.IGitHubAuthDialog import IGitHubAuthDialog


class GitHubAuthDialog(Window, IGitHubAuthDialog):
    
    def __init__(self, title: str, clientId: str, onSuccess: Callable[[str], None]) -> None:

        super().__init__(title=title)

        self._clientId:  str                   = clientId
        self._onSuccess: Callable[[str], None] = onSuccess
        
        self.infoLabel: Label = Label(
            'Requesting code from GitHub...',
            style=Pack(margin=10)
        )
        self.codeLabel: Label = Label(
            '',
            style=Pack(margin=10, font_size=20, font_weight='bold')
        )
        
        mainBox: Box = Box(style=Pack(direction=COLUMN, align_items=CENTER, margin=20))
        mainBox.add(self.infoLabel)
        mainBox.add(self.codeLabel)
        
        self.content = mainBox
        
    async def startAuthentication(self) -> None:
        oauthFlow: OAuthDeviceFlow = OAuthDeviceFlow(self._clientId)
        
        try:
            oauthFlow.executePhase1()
            
            self.infoLabel.text = 'Please enter this code in your browser:'
            self.codeLabel.text = oauthFlow.userCode
            
            accessToken: str = await oauthFlow.executePhase2()
            
            self.infoLabel.text = 'Authentication Successful!'
            self.codeLabel.text = 'Closing dialog...'
            
            self._onSuccess(accessToken)
            self.close()
            
        except RuntimeError as e:
            self.infoLabel.text = str(e)
            self.codeLabel.text = ''
