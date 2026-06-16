from typing import cast

from logging import Logger
from logging import getLogger

from toga import Box
from toga import Button
from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.IRepositoryIssues import IRepositoryIssues
from gitissue2todoist.IRepositoryIssues import ISSUE_DATA_KEY
from gitissue2todoist.IRepositoryIssues import IssueData
from gitissue2todoist.IRepositoryIssues import IssueDataRow
from gitissue2todoist.adapters.IGitHubAdapter import AbbreviatedGitIssue
from gitissue2todoist.adapters.IGitHubAdapter import AbbreviatedGitIssues

from gitissue2todoist.components.MobileMultiSelect import MobileMultiSelect
from gitissue2todoist.components.MobileMultiSelect import MultiSelectValues

from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.adapters.IGitHubAdapter import Slug

from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine
from gitissue2todoist.pubsubengine.MessageType import MessageType
from gitissue2todoist.strategy.TodoistStrategyTypes import CloneInformation


class MobileRepositoryIssues(Box, IRepositoryIssues):

    def __init__(self, pubSubEngine: IPubSubEngine):

        self.logger: Logger = getLogger(__name__)

        style: Pack = Pack(direction=COLUMN, flex=1, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT, gap=15)
        super().__init__(style=style)
        IRepositoryIssues.__init__(self, pubSubEngine=pubSubEngine)

        self._mobileMultiSelect: MobileMultiSelect = MobileMultiSelect(
            itemSelectCallback=self._itemSelectedCallback,
            itemDeselectCallback=self._itemDeselectedCallback
        )

        buttonContainer, cloneButton = UICommon.createRightAlignedButton(buttonText='Clone', onPressHandler=self._onClone)

        # Disabled until issues are selected
        self._cloneButton: Button = cloneButton
        self._cloneButton.enabled = False

        self.add(self._mobileMultiSelect)
        self.add(self._cloneButton)

        self._issueData: IssueData = cast(IssueData, None)     # noqa

        self._pubSubEngine.subscribe(messageType=MessageType.SELECTED_MILESTONE_CHANGED, listener=self._selectedMilestoneChangedListener)

    @property
    def selectedIssues(self) -> AbbreviatedGitIssues:
        """
        TODO:  This needs fixing for this component


        Returns: A list of selected issues (toggled ON)
        """

        abbreviatedGitIssues: AbbreviatedGitIssues = AbbreviatedGitIssues([])

        for issue in self._issueData:
            issueDataRow:        IssueDataRow = issue
            abbreviatedGitIssue: AbbreviatedGitIssue = cast(AbbreviatedGitIssue, issueDataRow[ISSUE_DATA_KEY])
            abbreviatedGitIssues.append(abbreviatedGitIssue)

        return abbreviatedGitIssues

    # noinspection PyUnusedLocal
    def _onClone(self, widget):
        cloneInformation: CloneInformation = self._cloneSelectedIssues()
        self._pubSubEngine.sendMessage(
            messageType=MessageType.CLONE_ISSUES,
            cloneInformation=cloneInformation,
        )

    def _itemSelectedCallback(self) -> None:
        self.logger.debug(f'An item was selected')
        self._cloneButton.enabled = True

    def _itemDeselectedCallback(self, hasNoSelections: bool) -> None:
        self.logger.debug(f'An item was deselected | hasNoSelections: {hasNoSelections}')
        if hasNoSelections:
            self._cloneButton.enabled = False


    def _selectedMilestoneChangedListener(self, repositoryName: Slug, milestoneTitle: str):

        issueData: IssueData = self._getIssueData(repositoryName=repositoryName, milestoneTitle=milestoneTitle)
        self.logger.info(f'{issueData=}')

        values: MultiSelectValues = MultiSelectValues([])

        for issue in issueData:
            issueDataRow: IssueDataRow = issue
            values.append(cast(AbbreviatedGitIssue, issueDataRow[ISSUE_DATA_KEY]).issueTitle)

        self._issueData = issueData
        self.logger.info(f'values=')
        self._mobileMultiSelect.setValues(MultiSelectValues(cast(list, values)))
