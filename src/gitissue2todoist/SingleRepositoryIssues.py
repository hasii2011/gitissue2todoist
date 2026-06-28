
from typing import List
from typing import cast

from logging import Logger
from logging import getLogger

from toga import Box
from toga import Button
from toga import Table

from toga.style import Pack
from toga.style.pack import COLUMN
from toga.sources import Row

from gitissue2todoist.IRepositoryIssues import IRepositoryIssues
from gitissue2todoist.IRepositoryIssues import ISSUE_DATA_KEY
from gitissue2todoist.IRepositoryIssues import ISSUE_TITLE_KEY
from gitissue2todoist.IRepositoryIssues import IssueData
from gitissue2todoist.IRepositoryIssues import REPOSITORY_NAME_NOT_SET

from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.adapters.IAsyncGitHubAdapter import AbbreviatedGitIssues
from gitissue2todoist.adapters.IAsyncGitHubAdapter import MilestoneTitle

from gitissue2todoist.adapters.IAsyncGitHubAdapter import Slug
from gitissue2todoist.adapters.IAsyncGitHubAdapter import AbbreviatedGitIssue

from gitissue2todoist.pubsubengine.MessageType import MessageType
from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine
from gitissue2todoist.strategy.TodoistStrategyTypes import CloneInformation

from gitissue2todoist.general.exceptions.AdapterAuthenticationError import AdapterAuthenticationError
from gitissue2todoist.adapters.GitHubServiceUnavailableError import GitHubServiceUnavailableError
from gitissue2todoist.adapters.GitHubConnectionError import GitHubConnectionError


class SingleRepositoryIssues(Box, IRepositoryIssues):
    """
    A container with single column Table with multiple_select enabled and a Button
    """
    def __init__(self, pubSubEngine: IPubSubEngine):
        self.logger: Logger = getLogger(__name__)

        style: Pack = Pack(direction=COLUMN, flex=1, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT, gap=15)
        super().__init__(style=style)

        IRepositoryIssues.__init__(self, pubSubEngine=pubSubEngine)

        self._selectionTable: Table = Table(
            columns=[ISSUE_TITLE_KEY],
            multiple_select=True,
            show_headings=False,
            style=Pack(flex=1),
        )
        buttonContainer, cloneButton = UICommon.createRightAlignedButton(buttonText='Clone', onPressHandler=self._onClone)

        # Disabled until issues are selected
        self._cloneButton: Button = cloneButton
        self._cloneButton.enabled = False

        self.add(self._selectionTable)
        self.add(buttonContainer)

        self._selectionTable.on_select = self._onSelectionChanged

        self._repositoryName: Slug = REPOSITORY_NAME_NOT_SET

        self._pubSubEngine.subscribe(messageType=MessageType.SELECTED_REPOSITORY_CHANGED, listener=self._selectedRepositoryChangedListener)
        self._pubSubEngine.subscribe(messageType=MessageType.SELECTED_MILESTONE_CHANGED,  listener=self._selectedMilestoneChangedListener)

    @property
    def selectedIssues(self) -> AbbreviatedGitIssues:
        """

        Returns: A list of selected values were toggled ON.
        """
        selectedIssues: AbbreviatedGitIssues = AbbreviatedGitIssues([])
        # Cast explicitly informs type checkers that multiple_select=True returns a List[Row]
        selectedRows: List[Row] = cast(List[Row], self._selectionTable.selection)

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

    # noinspection PyUnusedLocal
    def _onSelectionChanged(self, widget, **kwargs):
        """
        Handle selection changes
        When multiple_select=True, widget.selection returns a list of Row objects
        You can access the data using getattr matching the heading (lowercased/underscored usually)
        or by indexing.

        Args:
            widget:
            **kwargs:

        """
        selectedRows = cast(list, widget.selection)
        if selectedRows:
            self._cloneButton.enabled = True
        else:
            self._cloneButton.enabled = False

    # noinspection PyUnusedLocal
    def _onClone(self, widget):

        cloneInformation: CloneInformation = self._createCloneInformation()

        self._pubSubEngine.sendMessage(
            messageType=MessageType.CLONE_ISSUES,
            cloneInformation=cloneInformation,
        )

    def _selectedMilestoneChangedListener(self, repositoryName: Slug, milestoneTitle: MilestoneTitle):
        """
        We need to save the current milestone title
        And load theeeee appropriate issues

        Args:
            repositoryName:
            milestoneTitle:
        """
        assert repositoryName == self._repositoryName, 'They should match'
        self._milestoneTitle = milestoneTitle

        import asyncio
        asyncio.create_task(self._fetchIssuesAsync(repositoryName=repositoryName, milestoneTitle=milestoneTitle))

    async def _fetchIssuesAsync(self, repositoryName: Slug, milestoneTitle: MilestoneTitle) -> None:
        try:
            issueData: IssueData = await self._getIssueData(repositoryName=repositoryName, milestoneTitle=milestoneTitle)
            #
            # Stuff the entire data and table magically figures out which item to use via the 'columns' definition
            # during its initialization
            #
            self._selectionTable.data = issueData
        except AdapterAuthenticationError as e:
            self.logger.error(f'Authentication failed when fetching issues: {e}')
            await self.displayFatalError(window=self.window, errorType='Authentication')
        except GitHubServiceUnavailableError as e:
            self.logger.error(f'GitHub service unavailable: {e}')
            await self.displayFatalError(window=self.window, errorType='Service Unavailable')
        except GitHubConnectionError as e:
            self.logger.error(f'Connection error when fetching issues: {e}')
            await self.displayFatalError(window=self.window, errorType='Connection')

    def _selectedRepositoryChangedListener(self, repositoryName: Slug):
        """
        We need to save the current repository

        Args:
            repositoryName:

        """
        self._repositoryName = repositoryName
