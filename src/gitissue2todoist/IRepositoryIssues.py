
from typing import Dict
from typing import List
from typing import cast
from typing import Union
from typing import NewType

from abc import ABC
from abc import abstractmethod

from gitissue2todoist.Preferences import Preferences

from gitissue2todoist.adapters.HttpxGitHubAdapter import HttpxGitHubAdapter

from gitissue2todoist.adapters.IGitHubAdapter import AbbreviatedGitIssue
from gitissue2todoist.adapters.IGitHubAdapter import AbbreviatedGitIssues
from gitissue2todoist.adapters.IGitHubAdapter import IGitHubAdapter
from gitissue2todoist.adapters.IGitHubAdapter import Slug
from gitissue2todoist.adapters.IGitHubAdapter import MilestoneTitle

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

class IRepositoryIssues(ABC):

    def __init__(self, pubSubEngine: IPubSubEngine):

        self._preferences:  Preferences   = Preferences()
        self._pubSubEngine: IPubSubEngine = pubSubEngine

        self._repositoryName: Slug           = cast(Slug, None)             # noqa
        self._milestoneTitle: MilestoneTitle = cast(MilestoneTitle, None)   # noqa

    @property
    @abstractmethod
    def selectedIssues(self) -> AbbreviatedGitIssues:
        """
        Returns: A list of selected values
        """
        pass

    def _getIssueData(self, repositoryName: Slug, milestoneTitle: str) -> IssueData:
        """
        Queries GitHub and synthesizes abbreviated Git Issues and a list of synthetic
        dictionaries usable to display on either Mac OS X or IOS
        Args:
            repositoryName:
            milestoneTitle:

        Returns:  A list of data row dictionaries

        """
        gitHubAdapter: IGitHubAdapter = HttpxGitHubAdapter(authenticationToken=self._preferences.gitHubAPIToken)

        gitIssues: AbbreviatedGitIssues = gitHubAdapter.getAbbreviatedIssues(
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

    def _cloneSelectedIssues(self) -> CloneInformation:

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
