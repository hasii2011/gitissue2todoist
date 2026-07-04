
from logging import Logger
from logging import getLogger

from typing import Dict
from typing import List
from typing import Union
from typing import NewType
from typing import cast

from toga import Table
from toga.style import Pack

from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import AbbreviatedGitIssue
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import AbbreviatedGitIssues

from gitissue2todoist.owner.IMultiRepositorySelect import SelectedIssues
from gitissue2todoist.owner.IMultiRepositorySelect import ItemSelectCallback
from gitissue2todoist.owner.IMultiRepositorySelect import ItemDeselectCallback
from gitissue2todoist.owner.IMultiRepositorySelect import IMultiRepositorySelect

from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine

IssueDataRow = NewType('IssueDataRow', Dict[str, Union[str, AbbreviatedGitIssue]])
IssueData    = NewType('IssueData',    List[IssueDataRow])
IssueKey     = NewType('IssueKey', str)

ISSUE_DATA_KEY:  IssueKey = IssueKey('abbreviatedGitIssue')
ISSUE_SLUG_KEY:  IssueKey = IssueKey('issueSlug')
ISSUE_TITLE_KEY: IssueKey = IssueKey('issueTitle')


class MultiRepositorySelect(Table, IMultiRepositorySelect):

    def __init__(self, pubSubEngine: IPubSubEngine, itemSelectCallback: ItemSelectCallback, itemDeselectCallback: ItemDeselectCallback):

        self.logger: Logger = getLogger(__name__)

        super().__init__(
            columns=['issueSlug', 'issueTitle'],
            accessors=[ISSUE_SLUG_KEY, ISSUE_TITLE_KEY],
            multiple_select=True,
            show_headings=True,
            style=Pack(flex=1),
            data=[],
            on_select = self._onIssueSelected
        )
        IMultiRepositorySelect.__init__(self, pubSubEngine=pubSubEngine, itemSelectCallback=itemSelectCallback, itemDeselectCallback=itemDeselectCallback)

    @property
    def selectedIssues(self) -> SelectedIssues:

        from toga.sources import Row

        selectedIssues: SelectedIssues = SelectedIssues([])

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

    def setValues(self, retrievedIssues: AbbreviatedGitIssues) -> None:

        if retrievedIssues is not None:

            self.logger.info(f'Setting {len(retrievedIssues)} issues!')

            issueData: IssueData = IssueData([])
            for issue in retrievedIssues:

                gitIssue:     AbbreviatedGitIssue = issue
                issueSlug:    str                 = gitIssue.slug
                issueTitle:   str                 = gitIssue.issueTitle
                issueDataRow: IssueDataRow        = IssueDataRow({})

                issueDataRow[ISSUE_SLUG_KEY] = issueSlug
                issueDataRow[ISSUE_TITLE_KEY] = issueTitle

                issueDataRow[ISSUE_DATA_KEY] = gitIssue

                issueData.append(issueDataRow)

            self.data = issueData

    def selectAll(self):
        """
        Access the underlying native macOS NSTableView and call selectAll_

        Safely grab the native NSTableView and trigger the OS-level 'Select All' action

        This OSX specific

        """
        # noinspection PyProtectedMember
        self._impl.native.documentView.selectAll_(None)


    # noinspection PyUnusedLocal
    def _onIssueSelected(self, repositoryList: Table) -> None:
        self._itemSelectCallback()
