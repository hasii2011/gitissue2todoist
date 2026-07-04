from dataclasses import dataclass
from typing import Callable
from typing import cast
from typing import List

from logging import Logger
from logging import getLogger

from sys import platform as sysPlatform

from asyncio import AbstractEventLoop

from toga import Box
from toga import Button
from toga import Table
from toga import Widget

from toga.style import Pack

from toga.style.pack import COLUMN
from toga.style.pack import ROW

from gitissue2todoist.AppCommon import AppCommon
from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.TodoistCommon import TodoistCommon
from gitissue2todoist.adapters.AsyncHttpxGitHubAdapter import AsyncHttpxGitHubAdapter
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import IntermediateStatus
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import IssueOwner

from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import Slugs
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import AbbreviatedGitIssue
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import AbbreviatedGitIssues
from gitissue2todoist.dialogs.IAuthenticationDialog import IAuthenticationDialog
from gitissue2todoist.general.exceptions.AdapterAuthenticationError import AdapterAuthenticationError

from gitissue2todoist.owner.MultiRepositorySelect import ISSUE_DATA_KEY
from gitissue2todoist.owner.MultiRepositorySelect import MultiRepositorySelect
from gitissue2todoist.owner.IMultiRepositorySelect import IMultiRepositorySelect
from gitissue2todoist.owner.MobileMultiRepositorySelect import MobileMultiRepositorySelect

from gitissue2todoist.preferences.Preferences import Preferences
from gitissue2todoist.preferences.SecureTokenManager import SecureTokenManager

from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine
from gitissue2todoist.pubsubengine.MessageType import MessageType

from gitissue2todoist.strategy.TodoistStrategyTypes import CloneInformation
from gitissue2todoist.strategy.TodoistStrategyTypes import TaskInfoList

@dataclass
class RetrievalResult:
    shouldRetry:     bool
    retrievedIssues: AbbreviatedGitIssues | None

class MultiRepositoryIssuesPanel(Box):

    def __init__(self, pubSubEngine: IPubSubEngine):

        style: Pack = Pack(direction=COLUMN, flex=1, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT, gap=15)
        super().__init__(style=style)

        self.logger:        Logger        = getLogger(__name__)
        self._preferences:  Preferences   = Preferences()
        self._pubSubEngine: IPubSubEngine = pubSubEngine

        multiRepositorySelect: IMultiRepositorySelect
        if self._preferences.debugMobileMultiRepositoryIssues:
            multiRepositorySelect = MobileMultiRepositorySelect(
                pubSubEngine=pubSubEngine,
                itemSelectCallback=self._onItemSelected,
                itemDeselectCallback=self._onItemDeselect
            )
        else:
            if sysPlatform == AppCommon.PLATFORM_MAC:
                multiRepositorySelect = MultiRepositorySelect(
                    pubSubEngine=pubSubEngine,
                    itemSelectCallback=self._onItemSelected,
                    itemDeselectCallback=self._onItemDeselect
                )
            elif sysPlatform == AppCommon.PLATFORM_IOS:
                multiRepositorySelect = MobileMultiRepositorySelect(
                    pubSubEngine=pubSubEngine,
                    itemSelectCallback=self._onItemSelected,
                    itemDeselectCallback=self._onItemDeselect
                )
            else:
                assert False, 'Unsupported Platform'

        self._cloneButton:     Button               = cast(Button, None)                # noqa
        self._selectAllButton: Button               = cast(Button, None)                # noqa
        self._retrievedIssues: AbbreviatedGitIssues = cast(AbbreviatedGitIssues, None)  # noqa

        self.add(cast(Widget, multiRepositorySelect))       # Trust me these are Widgets
        self.add(self._createButtons())

        self._multiRepositorySelect: IMultiRepositorySelect = multiRepositorySelect

        self._pubSubEngine.subscribe(MessageType.RETRIEVE_OWNER_ISSUES, listener=self._retrieveOwnerIssuesListener)

    @property
    def selectedIssues(self) -> AbbreviatedGitIssues:

        from toga.sources import Row

        selectedIssues: AbbreviatedGitIssues = AbbreviatedGitIssues([])

        # Cast explicitly to tell type checkers that multiple_select=True returns a List[Row]
        selectedRows: List[Row] = cast(List[Row], self._issueTable.selection)
        if selectedRows:
            for row in selectedRows:
                togaRow: Row = row
                # Use getattr to bypass static type checker warnings for dynamic Row attributes
                abbreviatedGitIssue: AbbreviatedGitIssue = getattr(togaRow, ISSUE_DATA_KEY)

                self.logger.debug(f'Currently selected: {abbreviatedGitIssue}')
                selectedIssues.append(abbreviatedGitIssue)
        else:
            self.logger.warning('Nothing selected.')

        return selectedIssues

    def _retrieveOwnerIssuesListener(self, repositories: Slugs):
        """
        The listener that knows how to retrieve all issues across the published
        repositories
        Spawns an async task;  Once complete reload the issue table

        Args:
            repositories:
        """
        from asyncio import create_task

        async def retrieveIssuesAndSetSelector():
            retrievedIssues: AbbreviatedGitIssues | None = await self._doRetrieval(repositories)
            
            if retrievedIssues is not None:
                self._retrievedIssues = retrievedIssues
                self._multiRepositorySelect.setValues(retrievedIssues)

        create_task(retrieveIssuesAndSetSelector())
        self._selectAllButton.enabled = True

    async def _doRetrieval(self, repositories: Slugs) -> AbbreviatedGitIssues | None:
        """
        This method is the outer loop that contains the base and retry logic to actually attempt the
        issue retrieval
        It instantiates the progress dialog

        Args:
            repositories:

        """
        from asyncio import AbstractEventLoop
        from asyncio import get_running_loop
        from functools import partial

        finalIssues: AbbreviatedGitIssues | None = None
        loop: AbstractEventLoop = get_running_loop()

        while True:
            self._progressDlg = UICommon.setupProgressDialog(
                title='Retrieving Issues...',
                maxProgressValue=float(len(repositories))
            )

            callback: Callable = partial(self._progressStatusCallback, loop)

            result: RetrievalResult = await self._attemptIssueRetrieval(
                repositories=repositories,
                threadSafeCallback=callback
            )

            if result.shouldRetry:
                continue
            else:
                finalIssues = result.retrievedIssues
                break

        return finalIssues

    async def _attemptIssueRetrieval(self, repositories: Slugs, threadSafeCallback: Callable) -> RetrievalResult:
        """
        Executes a single attempt to retrieve issues for the selected repositories.

        Handles the background thread execution and intercepts any authentication
        errors. If authentication fails, it prompts the user for new credentials
        and signals whether the caller should retry the retrieval.

        Args:
            repositories:       A list of repository slugs to fetch issues from.
            threadSafeCallback: A callable used to safely update the UI from the background thread.

        Returns:
            RetrievalResult: A dataclass containing a boolean flag (`shouldRetry`)
            indicating if the operation should be attempted again with new credentials, and the
            `retrievedIssues` if the operation was successful.
        """

        # We instantiate this every time so it grabs the freshest API token
        apiToken: str = AppCommon.getAuthenticationToken(
            fallbackMessage=AppCommon.NO_GITHUB_TOKEN_MESSAGE,
            tokenRetrievalMethod=lambda: SecureTokenManager().gitHubToken
        )

        githubAdapter: AsyncHttpxGitHubAdapter = AsyncHttpxGitHubAdapter(authenticationToken=apiToken)

        try:
            retrievedIssues: AbbreviatedGitIssues = await githubAdapter.getIssuesAssignedToOwner(
                slugs=repositories,
                issueOwner=IssueOwner(self._preferences.gitHubUserName),
                callback=threadSafeCallback
            )

            self._progressDlg.destroy()
            self.logger.debug(f'{retrievedIssues}')

            return RetrievalResult(shouldRetry=False, retrievedIssues=retrievedIssues)

        except AdapterAuthenticationError as e:
            self._progressDlg.destroy()
            self.logger.error(f'{e=}')

            authDialog: IAuthenticationDialog = await UICommon.setupAuthenticationDialog(
                dialogTitle='GitHub Authentication Failed',
                dialogMessage='Enter GitHub Credentials;  Only need the user name for strategy all',
                apiToken=apiToken,
                gitHubUserName=self._preferences.gitHubUserName
            )
            okPressed: bool = await authDialog.showDialog()

            if okPressed:
                SecureTokenManager().gitHubToken = authDialog.apiToken
                return RetrievalResult(shouldRetry=True, retrievedIssues=None)
            else:
                return RetrievalResult(shouldRetry=False, retrievedIssues=None)

        except Exception as ue:
            self._progressDlg.destroy()
            await self._handleGeneralError(error=ue)
            return RetrievalResult(shouldRetry=False, retrievedIssues=None)

    def _progressStatusCallback(self, loop: AbstractEventLoop, status: IntermediateStatus) -> None:
        """
        Updates the UI progress bar safely from a background thread.
        """
        msg: str = f'Processed {status.currentRepoCount}/{status.totalNumberOfRepos}: {status.nameOfRepoJustProcessed}'

        def updateUI(uiMsg: str, uiCount: float) -> None:
            self._progressDlg.updateMessage(uiMsg)
            self._progressDlg.updateProgress = uiCount

        loop.call_soon_threadsafe(updateUI, msg, float(status.currentRepoCount))
        self.logger.info(f'{msg}')

    async def _handleGeneralError(self, error: Exception) -> None:
        self.logger.error(f'General Error: {error}')

    def _createButtons(self) -> Box:
        """
        Modifies:
                self._cloneButton
                self._selectAllButton

        Returns:  The container for appropriate display in parent
        """

        selectAllButton: Button = Button('Select All', on_press=self._onSelectAll)
        cloneButton:     Button = Button('Clone',      on_press=self._onClone, style=Pack(margin_left=10, margin_right=10))

        selectAllButton.enabled = False
        cloneButton.enabled     = False

        spacerBox: Box = Box(style=Pack(flex=1))
        buttonBox: Box = Box(children=[spacerBox, selectAllButton, cloneButton], style=Pack(direction=ROW, margin_top=10, margin_bottom=10))

        self._selectAllButton = selectAllButton
        self._cloneButton     = cloneButton

        return buttonBox

    # noinspection PyUnusedLocal
    def _onClone(self, widget: Widget) -> None:

        ci: CloneInformation = self._createCloneInformation()

        self._pubSubEngine.sendMessage(MessageType.CLONE_ISSUES, cloneInformation=ci)
        #
        self._issueTable.data         = []
        self._cloneButton.enabled     = False
        self._selectAllButton.enabled = False

    # noinspection PyUnusedLocal
    def _onIssueSelected(self, repositoryList: Table) -> None:
        self._cloneButton.enabled = True

    # noinspection PyUnusedLocal
    def _onSelectAll(self, widget: Widget) -> None:
        """
        Args:
            widget:

        """
        # noinspection PyProtectedMember
        self._multiRepositorySelect.selectAll()
        self._cloneButton.enabled = True

    def _createCloneInformation(self) -> CloneInformation:

        selectedIssues: AbbreviatedGitIssues = self.selectedIssues

        cloneInformation: CloneInformation = CloneInformation()
        cloneInformation.repositoryTask    = 'Repository Task ignored for this strategy'
        cloneInformation.milestoneNameTask = 'Milestone Name Task ignored for this strategy'

        tasksToClone: TaskInfoList = TodoistCommon.toTaskInfoList(abbreviatedGitIssues=selectedIssues)

        cloneInformation.tasksToClone = tasksToClone

        return cloneInformation

    def _onItemSelected(self):
        self.logger.info(f'Item Selected')
        self._cloneButton.enabled = True

    def _onItemDeselect(self, lastItemDeselected: bool):
        if lastItemDeselected:
            self._cloneButton.enabled =False
