
from typing import Dict
from typing import List
from typing import Union
from typing import NewType
from typing import Optional

from abc import ABC
from abc import abstractmethod

from toga import Window
from toga import ErrorDialog

from gitissue2todoist.preferences.Preferences import Preferences

from gitissue2todoist.adapters.AsyncHttpxGitHubAdapter import AsyncHttpxGitHubAdapter

from gitissue2todoist.adapters.IAsyncGitHubAdapter import AbbreviatedGitIssue
from gitissue2todoist.adapters.IAsyncGitHubAdapter import AbbreviatedGitIssues
from gitissue2todoist.adapters.IAsyncGitHubAdapter import IAsyncGitHubAdapter
from gitissue2todoist.adapters.IAsyncGitHubAdapter import Slug
from gitissue2todoist.adapters.IAsyncGitHubAdapter import MilestoneTitle

from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine
from gitissue2todoist.strategy.TodoistStrategyTypes import CloneInformation
from gitissue2todoist.strategy.TodoistStrategyTypes import TaskInfo
from gitissue2todoist.strategy.TodoistStrategyTypes import TaskInfoList

SelectedIssues = NewType('SelectedIssues', List[str])

IssueKey    = NewType('IssueKey', str)

IssueDataRow = NewType('IssueDataRow', Dict[str, Union[str, AbbreviatedGitIssue]])

IssueData = NewType('IssueData', List[IssueDataRow])

ISSUE_TITLE_KEY: IssueKey = IssueKey('issue')
ISSUE_DATA_KEY:  IssueKey = IssueKey('abbreviatedGitIssue')

REPOSITORY_NAME_NOT_SET: Slug           = Slug('REMEMBER_TO_TRACK_THE_CURRENT_REPOSITORY_NAME')
MILESTONE_NAME_NOT_SET:  MilestoneTitle = MilestoneTitle('REMEMBER_TO_TRACK_THE_CURRENT_MILESTONE_NAME')

class IRepositoryIssues(ABC):

    def __init__(self, pubSubEngine: IPubSubEngine):

        self._preferences:  Preferences   = Preferences()
        self._pubSubEngine: IPubSubEngine = pubSubEngine

        self._repositoryName: Slug           = REPOSITORY_NAME_NOT_SET
        self._milestoneTitle: MilestoneTitle = MILESTONE_NAME_NOT_SET

    @property
    @abstractmethod
    def selectedIssues(self) -> AbbreviatedGitIssues:
        """
        Returns: A list of selected values
        """
        pass

    async def _getIssueData(self, repositoryName: Slug, milestoneTitle: str) -> IssueData:
        """
        Queries GitHub and synthesizes abbreviated Git Issues and a list of synthetic
        dictionaries usable to display on either Mac OS X or IOS
        Args:
            repositoryName:
            milestoneTitle:

        Returns:  A list of data row dictionaries

        """
        gitHubAdapter: IAsyncGitHubAdapter = AsyncHttpxGitHubAdapter(authenticationToken=self._preferences.gitHubAPIToken)

        gitIssues: AbbreviatedGitIssues = await gitHubAdapter.getAbbreviatedIssues(
            repoName=repositoryName,
            milestoneTitle=milestoneTitle
        )
        issueData: IssueData = IssueData([])
        for issue in gitIssues:
            gitIssue: AbbreviatedGitIssue = issue
            issueTitle: str = gitIssue.issueTitle
            issueDataRow: IssueDataRow = IssueDataRow({})

            issueDataRow[ISSUE_TITLE_KEY] = issueTitle
            issueDataRow[ISSUE_DATA_KEY]  = gitIssue

            issueData.append(issueDataRow)

        return issueData

    def _createCloneInformation(self) -> CloneInformation:

        selectedIssues: AbbreviatedGitIssues = self.selectedIssues

        cloneInformation: CloneInformation = CloneInformation()
        cloneInformation.repositoryTask    = self._repositoryName
        cloneInformation.milestoneNameTask = self._milestoneTitle

        tasksToClone: TaskInfoList = self._convertToTasksToClone(abbreviatedGitIssues=selectedIssues)

        cloneInformation.tasksToClone = tasksToClone

        return cloneInformation

    def _convertToTasksToClone(self, abbreviatedGitIssues: AbbreviatedGitIssues) -> TaskInfoList:
        """

        Args:
            abbreviatedGitIssues:

        Returns:

        """

        taskInfolist: TaskInfoList = TaskInfoList([])

        for abbreviatedGitIssue in abbreviatedGitIssues:

            simpleGitIssue: AbbreviatedGitIssue = abbreviatedGitIssue

            taskInfo: TaskInfo = TaskInfo()
            taskInfo.gitIssueName = simpleGitIssue.issueTitle
            taskInfo.gitIssueURL  = simpleGitIssue.issueHTMLURL
            taskInfo.slug         = simpleGitIssue.slug
            taskInfo.labels       = simpleGitIssue.labels.copy()

            taskInfolist.append(taskInfo)

        return taskInfolist

    async def displayFatalError(self, window: Optional[Window], errorType: str) -> None:
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
