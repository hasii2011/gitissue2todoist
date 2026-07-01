
from logging import Logger
from logging import getLogger

from sys import platform as sysPlatform

from asyncio import create_task

from requests import get
from requests import Response

from toga import Box
from toga import ErrorDialog
from toga import Label
from toga import Selection

from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.AppCommon import AppCommon
from gitissue2todoist.githubauth.GitHubAuthDialog import GitHubAuthDialog
from gitissue2todoist.githubauth.IGitHubAuthDialog import IGitHubAuthDialog
from gitissue2todoist.githubauth.IOSGithubAuthDialog import IOSGithubAuthDialog
from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.general.exceptions.AdapterAuthenticationError import AdapterAuthenticationError

from gitissue2todoist.preferences.Preferences import Preferences
from gitissue2todoist.preferences.SecureTokenManager import SecureTokenManager

from gitissue2todoist.adapters.GitHubConnectionError import GitHubConnectionError
from gitissue2todoist.adapters.AsyncHttpxGitHubAdapter import AsyncHttpxGitHubAdapter
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import Slug
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import Slugs

from gitissue2todoist.pubsubengine.MessageType import MessageType
from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine


NO_SELECTION_INDICATOR: str  = '--- Select Repository ---'
NO_SELECTION_SLUG:      Slug = Slug(NO_SELECTION_INDICATOR)

GITHUB_CLIENT_ID: str = 'Ov23liHxUC2bdLShZn4h'

class RepositorySelector(Box):
    """

    """
    def __init__(self, pubSubEngine: IPubSubEngine):

        self.logger: Logger = getLogger(__name__)

        style: Pack = Pack(direction=COLUMN, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT)
        super().__init__(style=style)

        self._pubSubEngine:  IPubSubEngine = pubSubEngine
        self._preferences:   Preferences   = Preferences()
        apiToken: str = AppCommon.getAuthenticationToken(
            fallbackMessage=AppCommon.NO_GITHUB_TOKEN_MESSAGE,
            tokenRetrievalMethod=lambda: SecureTokenManager().gitHubToken
        )
            
        self._githubAdapter: AsyncHttpxGitHubAdapter = AsyncHttpxGitHubAdapter(authenticationToken=apiToken)

        repositoryLabel:           Label     = UICommon.createStandardSectionTitle('Repositories')
        self._repositorySelection: Selection = Selection()

        self._repositorySelection.on_change = self._onSelectionChanged

        self.add(repositoryLabel)
        self.add(self._repositorySelection)

    async def loadRepositoriesSelectionList(self):
        try:
            repoNames: Slugs = await self._githubAdapter.getRepositoryNames()
            repoNames.sort()
            repoNames.insert(0, NO_SELECTION_SLUG)

            self._repositorySelection.items = repoNames
        except AdapterAuthenticationError:
            # await self._handleAuthenticationError()
            await self._openAuthDialog()
        except GitHubConnectionError:
            await self._handleGitHubConnectionError()

    def _onSelectionChanged(self, selection: Selection):

        # I know it is a string
        # noinspection PyTypeChecker
        repositoryName: str  = selection.value            # type: ignore

        if repositoryName == NO_SELECTION_INDICATOR:
            pass
        else:
            self.logger.info(f'{repositoryName=}')
            self._pubSubEngine.sendMessage(messageType=MessageType.SELECTED_REPOSITORY_CHANGED, repositoryName=repositoryName)
            UICommon.popDownPicker(selection=self._repositorySelection)

    async def _openAuthDialog(self) -> None:

        clientId: str = GITHUB_CLIENT_ID

        # self._authButton.enabled = False
        # self._infoLabel.text = 'Dialog opened. Please complete authentication.'
        self.logger.info('Dialog opened. Please complete authentication.')
        
        dialogTitle: str = 'GitHub Device Authorization'
        authDialog:  IGitHubAuthDialog  # Declare the type hint here once

        if self._preferences.debugMobileAuthorizationDialog:
            authDialog = IOSGithubAuthDialog(
                title=dialogTitle,
                clientId=clientId,
                onSuccess=self._onAuthComplete
            )
        else:
            if sysPlatform == AppCommon.PLATFORM_IOS:
                authDialog = IOSGithubAuthDialog(
                    title=dialogTitle,
                    clientId=clientId,
                    onSuccess=self._onAuthComplete
                )
            elif sysPlatform == AppCommon.PLATFORM_MAC:
                authDialog = GitHubAuthDialog(
                    title=dialogTitle,
                    clientId=clientId,
                    onSuccess=self._onAuthComplete
                )
            else:
                assert False, 'Unsupported platform'

        authDialog.show()

        # Start the authorization process inside the dialog
        await authDialog.startAuthentication()

    async def _handleGitHubConnectionError(self):
        #
        # Tell mypy to stfu
        #
        assert self.window is not None
        # noinspection PyUnresolvedReferences
        await self.window.dialog(
            dialog=ErrorDialog(title='Error', message='GitHub connection error. Try again later')
        )

    def _onAuthComplete(self, accessToken: str) -> None:
        """
        This callback receives the token we need to access the user repos

        Args:
            accessToken:
        """
        SecureTokenManager().gitHubToken = accessToken
        # Re-initialize the adapter with the new token
        self._githubAdapter = AsyncHttpxGitHubAdapter(authenticationToken=accessToken)
        # Try again!
        create_task(self.loadRepositoriesSelectionList())

        self.logger.info('Token received! Fetching profile...')
        loginName: str = self._getUserLoginName(accessToken)
        self.logger.info(f'Welcome, {loginName}! authorization was successful.')

    def _getUserLoginName(self, accessToken: str) -> str:

        authHeaders: dict[str, str] = {

            'Authorization': f'Bearer {accessToken}',
            'Accept': 'application/vnd.github.v3+json'
        }
        userResponse: Response = get('https://api.github.com/user', headers=authHeaders)
        profileData: dict = userResponse.json()

        loginName: str = profileData.get('login', 'Unknown')

        # self._infoLabel.text = f'Welcome, {loginName}! authorization was successful.'

        return loginName
