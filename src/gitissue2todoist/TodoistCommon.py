
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import AbbreviatedGitIssue
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import AbbreviatedGitIssues

from gitissue2todoist.strategy.TodoistStrategyTypes import TaskInfo
from gitissue2todoist.strategy.TodoistStrategyTypes import TaskInfoList

class TodoistCommon:

    @classmethod
    def toTaskInfoList(cls, abbreviatedGitIssues: AbbreviatedGitIssues) -> TaskInfoList:
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
