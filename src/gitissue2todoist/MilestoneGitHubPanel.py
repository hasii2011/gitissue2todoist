
from typing import cast

from typing import Optional

from logging import Logger
from logging import getLogger

from sys import platform as sysPlatform

from toga import Box
from toga import ErrorDialog
from toga import Label
from toga import Widget
from toga import Selection
from toga import Window

from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.AppCommon import AppCommon
from gitissue2todoist.IRepositoryIssues import IRepositoryIssues
from gitissue2todoist.SingleRepositoryIssues import SingleRepositoryIssues
from gitissue2todoist.MobileSingleRepositoryIssues import MobileSingleRepositoryIssues

from gitissue2todoist.preferences.Preferences import Preferences
from gitissue2todoist.preferences.SecureTokenManager import SecureTokenManager
from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import Slug
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import MilestoneTitles
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import MilestoneTitle
from gitissue2todoist.adapters.AsyncHttpxGitHubAdapter import AsyncHttpxGitHubAdapter

from gitissue2todoist.pubsubengine.MessageType import MessageType
from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine

from gitissue2todoist.general.exceptions.AdapterAuthenticationError import AdapterAuthenticationError
from gitissue2todoist.adapters.GitHubServiceUnavailableError import GitHubServiceUnavailableError
from gitissue2todoist.adapters.GitHubConnectionError import GitHubConnectionError


class MilestoneGitHubPanel(Box):

    def __init__(self, pubSubEngine: IPubSubEngine):

        self.logger: Logger = getLogger(__name__)
        style: Pack = Pack(direction=COLUMN, flex=1, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT, gap=15)
        super().__init__(style=style)

        self._pubSubEngine:  IPubSubEngine = pubSubEngine
        self._preferences:   Preferences   = Preferences()
        self._githubAdapter: AsyncHttpxGitHubAdapter = cast(AsyncHttpxGitHubAdapter, None)        # noqa

        mileStonesLabel: Label = UICommon.createStandardSectionTitle('Repository Milestone Titles')
        self._mileStoneSelection: Selection = Selection(
            items=[],
            on_change=self._onMilestoneSelectedHandler
        )
        mileStonesBox: Box = Box(children=[mileStonesLabel, self._mileStoneSelection], style=Pack(direction=COLUMN))

        issuesLabel:      Label = UICommon.createStandardSectionTitle('Issues')
        repositoryIssues: IRepositoryIssues

        if self._preferences.debugMobileIssueSelector:
            repositoryIssues = MobileSingleRepositoryIssues(pubSubEngine=self._pubSubEngine)  # temp so I can test it
        else:
            if sysPlatform == AppCommon.PLATFORM_MAC:
                repositoryIssues = SingleRepositoryIssues(pubSubEngine=self._pubSubEngine)
            elif sysPlatform == AppCommon.PLATFORM_IOS:
                repositoryIssues = MobileSingleRepositoryIssues(pubSubEngine=self._pubSubEngine)
            else:
                assert False, 'Unsupported platform'

        issuesBox: Box = Box(
            children=[issuesLabel, cast(Widget, repositoryIssues)],
            style=Pack(direction=COLUMN, flex=1)
        )

        self.add(mileStonesBox)
        self.add(issuesBox)

        self._pubSubEngine.subscribe(messageType=MessageType.SELECTED_REPOSITORY_CHANGED, listener=self._selectedRepositoryChangedListener)

        self._repositoryName: Slug = Slug('')         # set by ._loadMilestonesListener

    def _selectedRepositoryChangedListener(self, repositoryName: Slug):
        """
        We need to load some new milestones

        Delay getting the GitHub Adapter as long as possible in case the authentication token has
        changed

        Args:
            repositoryName:

        """
        self._repositoryName = repositoryName
        self.logger.info(f'Time to load milestones for {repositoryName}')
        
        apiToken: str = AppCommon.getAuthenticationToken(
            fallbackMessage=AppCommon.NO_GITHUB_TOKEN_MESSAGE,
            tokenRetrievalMethod=lambda: SecureTokenManager().gitHubToken
        )
            
        self._githubAdapter = AsyncHttpxGitHubAdapter(authenticationToken=apiToken)

        from asyncio import create_task
        create_task(self._fetchMilestoneTitlesAsync(repositoryName=repositoryName))

    async def _fetchMilestoneTitlesAsync(self, repositoryName: Slug) -> None:
        try:
            milestoneTitles: MilestoneTitles = await self._githubAdapter.getMileStoneTitles(repoName=repositoryName)
            self._mileStoneSelection.items = milestoneTitles
        except AdapterAuthenticationError as e:
            self.logger.error(f'Authentication failed when fetching milestones: {e}')
            await self._displayFatalError(window=self.window, errorType='Authentication')
        except GitHubServiceUnavailableError as e:
            self.logger.error(f'GitHub service unavailable: {e}')
            await self._displayFatalError(window=self.window, errorType='Service Unavailable')
        except GitHubConnectionError as e:
            self.logger.error(f'Connection error when fetching milestones: {e}')
            await self._displayFatalError(window=self.window, errorType='Connection')

    # noinspection PyUnusedLocal
    def _onMilestoneSelectedHandler(self, widget):

        selectedMilestoneTitle: MilestoneTitle = cast(MilestoneTitle, self._mileStoneSelection.value)
        # noinspection PyTypeChecker
        self.logger.info(f'{selectedMilestoneTitle=}')
        self._pubSubEngine.sendMessage(
            messageType=MessageType.SELECTED_MILESTONE_CHANGED,
            repositoryName=self._repositoryName,
            milestoneTitle=selectedMilestoneTitle
        )
        UICommon.popDownPicker(selection=self._mileStoneSelection)

    async def _displayFatalError(self, window: Optional[Window], errorType: str) -> None:
        """
        Displays a fatal error dialog.

        Args:
            window:
            errorType:
        """
        assert window is not None
        errorMessage: str = f'You got an {errorType} error.\n\nPlease exit the application and restart it.'
        # noinspection PyUnresolvedReferences
        await window.dialog(dialog=ErrorDialog(title='Fatal Error', message=errorMessage))
