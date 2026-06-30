
from typing import Dict
from typing import cast

from logging import Logger
from logging import getLogger

from toga import Box
from toga import Button
from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.IRepositoryIssues import IRepositoryIssues
from gitissue2todoist.IRepositoryIssues import ISSUE_DATA_KEY
from gitissue2todoist.IRepositoryIssues import ISSUE_TITLE_KEY
from gitissue2todoist.IRepositoryIssues import IssueData
from gitissue2todoist.IRepositoryIssues import IssueDataRow

from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import AbbreviatedGitIssue
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import AbbreviatedGitIssues
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import MilestoneTitle

from gitissue2todoist.components.MobileMultiSelect import MobileMultiSelect
from gitissue2todoist.components.MobileMultiSelect import MultiSelectValues

from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import Slug
from gitissue2todoist.components.MobileMultiSelect import SelectedValues

from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine
from gitissue2todoist.pubsubengine.MessageType import MessageType
from gitissue2todoist.strategy.TodoistStrategyTypes import CloneInformation

from gitissue2todoist.general.exceptions.AdapterAuthenticationError import AdapterAuthenticationError
from gitissue2todoist.adapters.GitHubServiceUnavailableError import GitHubServiceUnavailableError
from gitissue2todoist.adapters.GitHubConnectionError import GitHubConnectionError


class MobileSingleRepositoryIssues(Box, IRepositoryIssues):

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

        self._issueData: IssueData            = cast(IssueData, None)     # noqa

        self._pubSubEngine.subscribe(messageType=MessageType.SELECTED_REPOSITORY_CHANGED, listener=self._selectedRepositoryChangedListener)
        self._pubSubEngine.subscribe(messageType=MessageType.SELECTED_MILESTONE_CHANGED,  listener=self._selectedMilestoneChangedListener)

    @property
    def selectedIssues(self) -> AbbreviatedGitIssues:
        """

        Returns: A list of selected issues (toggled ON)
        """
        selectedValues: SelectedValues = self._mobileMultiSelect.selectedValues
        self.logger.info(f'{selectedValues=}')

        abbreviatedGitIssues: AbbreviatedGitIssues = AbbreviatedGitIssues([])

        # Build the issue name to AbbreviatedGitIssue
        issueLookup: Dict[str, AbbreviatedGitIssue] = {
            cast(str, row[ISSUE_TITLE_KEY]): cast(AbbreviatedGitIssue, row[ISSUE_DATA_KEY])
            for row in self._issueData
        }
        # Look selected issues
        for issueTitle in selectedValues:
            selectedIssue: AbbreviatedGitIssue = cast(AbbreviatedGitIssue,issueLookup.get(issueTitle))
            abbreviatedGitIssues.append(selectedIssue)

        return abbreviatedGitIssues

    # noinspection PyUnusedLocal
    def _onClone(self, widget):
        cloneInformation: CloneInformation = self._createCloneInformation()

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

    def _selectedMilestoneChangedListener(self, repositoryName: Slug, milestoneTitle: MilestoneTitle):

        import asyncio
        asyncio.create_task(self._fetchIssuesAsync(repositoryName=repositoryName, milestoneTitle=milestoneTitle))

    async def _fetchIssuesAsync(self, repositoryName: Slug, milestoneTitle: MilestoneTitle) -> None:
        try:
            issueData: IssueData = await self._getIssueData(repositoryName=repositoryName, milestoneTitle=milestoneTitle)
            self.logger.debug(f'{issueData=}')

            values: MultiSelectValues = MultiSelectValues([])

            for issue in issueData:
                issueDataRow: IssueDataRow = issue
                values.append(cast(AbbreviatedGitIssue, issueDataRow[ISSUE_DATA_KEY]).issueTitle)

            self._issueData = issueData
            self.logger.debug(f'values=')
            self._mobileMultiSelect.setValues(MultiSelectValues(cast(list, values)))
            self._milestoneTitle = milestoneTitle
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
