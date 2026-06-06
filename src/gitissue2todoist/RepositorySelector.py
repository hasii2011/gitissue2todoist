
from logging import Logger
from logging import getLogger

from toga import Box
from toga import ErrorDialog
from toga import Label
from toga import Selection

from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.adapters.GitHubConnectionError import GitHubConnectionError
from gitissue2todoist.adapters.AdapterAuthenticationError import AdapterAuthenticationError

from gitissue2todoist.Preferences import Preferences
from gitissue2todoist.adapters.HttpxGitHubAdapter import HttpxGitHubAdapter
from gitissue2todoist.adapters.IGitHubAdapter import Slug
from gitissue2todoist.adapters.IGitHubAdapter import Slugs

from gitissue2todoist.pubsubengine.MessageType import MessageType
from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine

NO_SELECTION_INDICATOR: str = '--- Select Repository ---'
NO_SELECTION_SLUG:     Slug = Slug(NO_SELECTION_INDICATOR)

class RepositorySelector(Box):
    """

    """
    def __init__(self, pubSubEngine: IPubSubEngine):

        self.logger: Logger = getLogger(__name__)

        super().__init__(style=Pack(direction=COLUMN))

        self._pubSubEngine:  IPubSubEngine = pubSubEngine
        self._preferences:   Preferences   = Preferences()
        self._githubAdapter: HttpxGitHubAdapter = HttpxGitHubAdapter(authenticationToken=self._preferences.gitHubAPIToken)

        repositoryLabel: Label = Label(
            'Repositories',
            style=Pack(margin=(2, 5)),
        )
        self._repositorySelection: Selection = Selection()

        self._repositorySelection.on_change = self._onSelectionChanged

        self.add(repositoryLabel)
        self.add(self._repositorySelection)

    async def populateRepositories(self):
        import asyncio

        try:
            # Run the synchronous GitHub query in a background thread to prevent UI freezing
            repoNames: Slugs = await asyncio.to_thread(self._githubAdapter.getRepositoryNames)
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
            self._pubSubEngine.sendMessage(messageType=MessageType.LOAD_MILESTONES, repositoryName=repositoryName)
            pass    # send message to listener


    async def _handleAuthenticationError(self):
        import sys
        
        if sys.platform == 'ios':
            from gitissue2todoist.dialogs.IOSAuthenticationDialog import IOSAuthenticationDialog
            authDialog = IOSAuthenticationDialog(preferences=self._preferences)
        elif sys.platform == 'darwin':
            from gitissue2todoist.dialogs.AuthenticationDialog import AuthenticationDialog
            authDialog = AuthenticationDialog(preferences=self._preferences)
        else:
            assert False, 'Unsupported platform'

        okPressed: bool = await authDialog.show_dialog()
        
        if okPressed:
            # Re-initialize the adapter with the new token
            self._githubAdapter = HttpxGitHubAdapter(authenticationToken=self._preferences.gitHubAPIToken)
            # Try again!
            await self.populateRepositories()

    async def _handleGitHubConnectionError(self):
        #
        # Tell mypy to stfu
        #
        assert self.window is not None
        # noinspection PyUnresolvedReferences
        await self.window.dialog(
            dialog=ErrorDialog(title='Error', message='GitHub connection error. Try again later')
        )
