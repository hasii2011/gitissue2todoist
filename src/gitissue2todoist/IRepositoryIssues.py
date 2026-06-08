
from typing import List
from typing import NewType

from abc import ABC
from abc import abstractmethod

from gitissue2todoist.Preferences import Preferences

from gitissue2todoist.adapters.HttpxGitHubAdapter import HttpxGitHubAdapter
from gitissue2todoist.adapters.IGitHubAdapter import AbbreviatedGitIssue
from gitissue2todoist.adapters.IGitHubAdapter import AbbreviatedGitIssues
from gitissue2todoist.adapters.IGitHubAdapter import IGitHubAdapter
from gitissue2todoist.adapters.IGitHubAdapter import Slug
from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine

SelectedIssues = NewType('SelectedIssues', List[str])
IssueTitles    = NewType('IssueTitles',    List[str])

class IRepositoryIssues(ABC):

    def __init__(self, pubSubEngine: IPubSubEngine):

        self._preferences:  Preferences   = Preferences()
        self._pubSubEngine: IPubSubEngine = pubSubEngine

    @property
    @abstractmethod
    def selectedIssues(self) -> SelectedIssues:
        """
        Returns: A list of selected values
        """
        pass

    def _getAssociatedIssues(self, repositoryName: Slug, milestoneTitle: str) -> IssueTitles:
        """

        Args:
            repositoryName:
            milestoneTitle:

        """
        gitHubAdapter: IGitHubAdapter = HttpxGitHubAdapter(authenticationToken=self._preferences.gitHubAPIToken)

        gitIssues: AbbreviatedGitIssues = gitHubAdapter.getAbbreviatedIssues(
            repoName=repositoryName,
            milestoneTitle=milestoneTitle
        )
        issueTitles: IssueTitles = IssueTitles([])
        for issue in gitIssues:
            gitIssue: AbbreviatedGitIssue = issue
            issueTitle: str = gitIssue.issueTitle
            issueTitles.append(issueTitle)

        return issueTitles
