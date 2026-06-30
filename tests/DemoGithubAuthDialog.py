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

from gitissue2todoist.githubauth.GithubAuthDialog import GithubAuthDialog

GITHUB_CLIENT_ID: str = 'Ov23liHxUC2bdLShZn4h'

class DemoGithubAuthDialog(App):
    
    def __init__(self, formalName: str, appId: str):
        super().__init__(formal_name=formalName, app_id=appId)
        self._infoLabel:  Label  = cast(Label, None)
        self._authButton: Button = cast(Button, None)
    
    def startup(self) -> None:
        mainBox: Box = Box(style=Pack(direction=COLUMN, align_items=CENTER, margin=20))
        
        self._infoLabel = Label(
            'Click the button to authenticate via the Dialog',
            style=Pack(margin=10)
        )
        
        self._authButton = Button(
            'Authenticate with GitHub',
            on_press=self.openAuthDialog,
            style=Pack(margin=10)
        )
        
        mainBox.add(self._infoLabel)
        mainBox.add(self._authButton)
        
        mainWindow: MainWindow = MainWindow(title='GitHub Auth Dialog Demo')
        mainWindow.content = mainBox
        mainWindow.show()
        
        self.main_window = mainWindow

    # noinspection PyUnusedLocal
    async def openAuthDialog(self, widget: Button) -> None:

        clientId: str = GITHUB_CLIENT_ID

        self._authButton.enabled = False
        self._infoLabel.text = 'Dialog opened. Please complete authentication.'
        
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
        self._infoLabel.text = 'Token received! Fetching profile...'

        loginName: str = self._getUserLoginName(accessToken)

        self._infoLabel.text = f'Welcome, {loginName}! authorization was successful.'
        self._authButton.enabled = True

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
