
from typing import cast
from typing import List

from logging import Logger
from logging import getLogger

from toga import Box
from toga import Button
from toga import Table
from toga import Widget
from toga.style import Pack

from toga.style.pack import COLUMN
from toga.style.pack import ROW

from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.TodoistCommon import TodoistCommon

from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import AbbreviatedGitIssue
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import AbbreviatedGitIssues
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import Slugs
from gitissue2todoist.allissues.IMultiRepositoryIssues import ISSUE_DATA_KEY
from gitissue2todoist.allissues.IMultiRepositoryIssues import ISSUE_SLUG_KEY
from gitissue2todoist.allissues.IMultiRepositoryIssues import ISSUE_TITLE_KEY
from gitissue2todoist.allissues.IMultiRepositoryIssues import IssueData
from gitissue2todoist.allissues.IMultiRepositoryIssues import IssueDataRow
from gitissue2todoist.allissues.IMultiRepositoryIssues import IMultiRepositoryIssues

from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine
from gitissue2todoist.pubsubengine.MessageType import MessageType

from gitissue2todoist.strategy.TodoistStrategyTypes import CloneInformation
from gitissue2todoist.strategy.TodoistStrategyTypes import TaskInfoList


class MultiRepositoryIssues(Box, IMultiRepositoryIssues):

    def __init__(self, pubSubEngine: IPubSubEngine):

        style: Pack = Pack(direction=COLUMN, flex=1, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT, gap=15)
        super().__init__(style=style)
        IMultiRepositoryIssues.__init__(self, pubSubEngine=pubSubEngine)

        self.logger:        Logger        = getLogger(__name__)

        self._issueTable: Table = Table(
            columns=['issueSlug', 'issueTitle'],
            accessors=[ISSUE_SLUG_KEY, ISSUE_TITLE_KEY],
            multiple_select=True,
            show_headings=True,
            style=Pack(flex=1),
            data=[],
            on_select = self._onIssueSelected
        )

        self._cloneButton:     Button               = cast(Button, None)                # noqa
        self._selectAllButton: Button               = cast(Button, None)                # noqa
        self._retrievedIssues: AbbreviatedGitIssues = cast(AbbreviatedGitIssues, None)  # noqa

        self.add(self._issueTable)
        self.add(self._createButtons())

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

        async def _runAndProcess():
            retrievedIssues: AbbreviatedGitIssues | None = await self._doRetrieval(repositories)
            
            if retrievedIssues is not None:
                self.logger.info(f'Successfully captured {len(retrievedIssues)} issues!')
                # TODO: Update UI with retrievedIssues
                issueData: IssueData = IssueData([])
                for issue in retrievedIssues:
                    gitIssue: AbbreviatedGitIssue = issue
                    issueSlug:    str          = gitIssue.slug
                    issueTitle:   str          = gitIssue.issueTitle
                    issueDataRow: IssueDataRow = IssueDataRow({})

                    issueDataRow[ISSUE_SLUG_KEY]  = issueSlug
                    issueDataRow[ISSUE_TITLE_KEY] = issueTitle

                    issueDataRow[ISSUE_DATA_KEY] = gitIssue

                    issueData.append(issueDataRow)

                self._retrievedIssues = retrievedIssues
                self._issueTable.data = issueData

        create_task(_runAndProcess())
        self._selectAllButton.enabled = True

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
        Access the underlying native macOS NSTableView and call selectAll_

        Safely grab the native NSTableView and trigger the OS-level 'Select All' action

        This OSX specific

        Args:
            widget:

        """
        # noinspection PyProtectedMember
        self._issueTable._impl.native.documentView.selectAll_(None)
        self._cloneButton.enabled = True

    def _createCloneInformation(self) -> CloneInformation:

        selectedIssues: AbbreviatedGitIssues = self.selectedIssues

        cloneInformation: CloneInformation = CloneInformation()
        cloneInformation.repositoryTask    = 'Repository Task ignored for this strategy'
        cloneInformation.milestoneNameTask = 'Milestone Name Task ignored for this strategy'

        tasksToClone: TaskInfoList = TodoistCommon.toTaskInfoList(abbreviatedGitIssues=selectedIssues)

        cloneInformation.tasksToClone = tasksToClone

        return cloneInformation
