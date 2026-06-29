from typing import cast


from requests import Response
from requests import get

from toga import App
from toga import Box
from toga import Button
from toga import Label
from toga import MainWindow
from toga.style import Pack
from toga.style.pack import COLUMN
from toga.style.pack import CENTER

from githubauth.GithubAuthDialog import GithubAuthDialog

GITHUB_CLIENT_ID: str = 'Ov23liHxUC2bdLShZn4h'

class DemoGithubAuthDialog(App):
    
    def __init__(self, formalName: str, appId: str):
        super().__init__(formal_name=formalName, app_id=appId)
        self.infoLabel:  Label  = cast(Label, None)
        self.authButton: Button = cast(Button, None)
    
    def startup(self) -> None:
        mainBox: Box = Box(style=Pack(direction=COLUMN, align_items=CENTER, margin=20))
        
        self.infoLabel: Label = Label(
            'Click the button to authenticate via the Dialog',
            style=Pack(margin=10)
        )
        
        self.authButton: Button = Button(
            'Authenticate with GitHub',
            on_press=self.openAuthDialog,
            style=Pack(margin=10)
        )
        
        mainBox.add(self.infoLabel)
        mainBox.add(self.authButton)
        
        mainWindow: MainWindow = MainWindow(title='GitHub Auth Dialog Demo')
        mainWindow.content = mainBox
        mainWindow.show()
        
        self.main_window = mainWindow

    # noinspection PyUnusedLocal
    async def openAuthDialog(self, widget: Button) -> None:

        clientId: str = GITHUB_CLIENT_ID

        self.authButton.enabled = False
        self.infoLabel.text = 'Dialog opened. Please complete authentication.'
        
        authDialog: GithubAuthDialog = GithubAuthDialog(
            title='GitHub Device Authorization',
            clientId=clientId,
            onSuccess=self.onAuthComplete
        )
        
        authDialog.show()
        
        # Start the authorization process inside the dialog
        await authDialog.startAuthentication()
        
    def onAuthComplete(self, accessToken: str) -> None:
        """
        This callback receives we need to access the user repos
        Args:
            accessToken:

        Returns:

        """
        self.infoLabel.text = 'Token received! Fetching profile...'

        loginName: str = self._getUserLoginName(accessToken)

        self.infoLabel.text = f'Welcome, {loginName}! authorization was successful.'
        self.authButton.enabled = True

    def _getUserLoginName(self, accessToken: str) -> str:

        authHeaders: dict[str, str] = {

            'Authorization': f'Bearer {accessToken}',
            'Accept': 'application/vnd.github.v3+json'
        }
        userResponse: Response = get('https://api.github.com/user', headers=authHeaders)
        profileData: dict = userResponse.json()

        loginName: str = profileData.get('login', 'Unknown')
        return loginName


def main() -> App:
    return DemoGithubAuthDialog('Dialog Demo', 'org.hasii.dialogdemo')


if __name__ == '__main__':
    main().main_loop()
