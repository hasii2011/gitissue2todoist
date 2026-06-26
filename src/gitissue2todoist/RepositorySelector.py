
from logging import Logger
from logging import getLogger

from sys import platform as sysPlatform

from toga import Box
from toga import ErrorDialog
from toga import Label
from toga import Selection

from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.AppCommon import AppCommon
from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.adapters.GitHubConnectionError import GitHubConnectionError

from gitissue2todoist.general.exceptions.AdapterAuthenticationError import AdapterAuthenticationError

from gitissue2todoist.preferences.Preferences import Preferences

from gitissue2todoist.adapters.AsyncHttpxGitHubAdapter import AsyncHttpxGitHubAdapter
from gitissue2todoist.adapters.IAsyncGitHubAdapter import Slug
from gitissue2todoist.adapters.IAsyncGitHubAdapter import Slugs

from gitissue2todoist.dialogs.IAuthenticationDialog import IAuthenticationDialog
from gitissue2todoist.dialogs.AuthenticationDialog import AuthenticationDialog
from gitissue2todoist.dialogs.IOSAuthenticationDialog import IOSAuthenticationDialog

from gitissue2todoist.pubsubengine.MessageType import MessageType
from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine

NO_SELECTION_INDICATOR: str = '--- Select Repository ---'
NO_SELECTION_SLUG:     Slug = Slug(NO_SELECTION_INDICATOR)

class RepositorySelector(Box):
    """

    """
    def __init__(self, pubSubEngine: IPubSubEngine):

        self.logger: Logger = getLogger(__name__)

        style: Pack = Pack(direction=COLUMN, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT)
        super().__init__(style=style)

        self._pubSubEngine:  IPubSubEngine = pubSubEngine
        self._preferences:   Preferences   = Preferences()
        self._githubAdapter: AsyncHttpxGitHubAdapter = AsyncHttpxGitHubAdapter(authenticationToken=self._preferences.gitHubAPIToken)

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
            await self._handleAuthenticationError()
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

    async def _handleAuthenticationError(self):

        authDialog: IAuthenticationDialog = await self._createAppropriateAuthenticationDialog()

        okPressed: bool = await authDialog.showDialog()
        
        if okPressed:
            # Save the new token into preferences
            self._preferences.gitHubAPIToken = authDialog.apiToken
            # Re-initialize the adapter with the new token
            self._githubAdapter = AsyncHttpxGitHubAdapter(authenticationToken=self._preferences.gitHubAPIToken)
            # Try again!
            await self.loadRepositoriesSelectionList()

    async def _createAppropriateAuthenticationDialog(self) -> IAuthenticationDialog:
        """

        Returns:  The platform specific dialog
        """

        dialogTitle:   str = 'GitHub Authentication'
        dialogMessage: str = 'Authentication Failed. Please enter your GitHub API Token:'
        initialToken:  str = self._preferences.gitHubAPIToken

        if sysPlatform == AppCommon.PLATFORM_IOS:
            authDialog: IAuthenticationDialog = IOSAuthenticationDialog(
                title=dialogTitle,
                message=dialogMessage,
                initialToken=initialToken
            )
        elif sysPlatform == AppCommon.PLATFORM_MAC:
            authDialog = AuthenticationDialog(
                title=dialogTitle,
                message=dialogMessage,
                initialToken=initialToken
            )
        else:
            assert False, 'Unsupported platform'

        return authDialog

    async def _handleGitHubConnectionError(self):
        #
        # Tell mypy to stfu
        #
        assert self.window is not None
        # noinspection PyUnresolvedReferences
        await self.window.dialog(
            dialog=ErrorDialog(title='Error', message='GitHub connection error. Try again later')
        )

