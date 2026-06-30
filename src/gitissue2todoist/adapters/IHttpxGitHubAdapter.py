
from typing import List
from typing import Callable
from typing import NewType

from abc import ABC
from abc import abstractmethod

from dataclasses import field
from dataclasses import dataclass

MilestoneTitle  = NewType('MilestoneTitle', str)
MilestoneTitles = NewType('MilestoneTitles', List[MilestoneTitle])
IssueOwner      = NewType('IssueOwner',      str)


def createLabelsFactory() -> List[str]:
    return []


@dataclass
class AbbreviatedGitIssue:


    slug:         str = ''
    issueTitle:   str = ''
    issueHTMLURL: str = ''
    body:         str = ''
    labels:       List[str] = field(default_factory=createLabelsFactory)


AbbreviatedGitIssues = NewType('AbbreviatedGitIssues', List[AbbreviatedGitIssue])

Slug  = NewType('Slug',  str)
Slugs = NewType('Slugs', List[Slug])

@dataclass
class IntermediateStatus:
    totalNumberOfRepos:      int        # Total repos we are processing
    currentRepoCount:        int
    nameOfRepoJustProcessed: Slug
    numberOfIssues:          int        # in the just process repo

IssuesCallback = Callable[[IntermediateStatus], None]
"""
The callback for .getIssuesAssignedToOwner;  Allows reporting intermediate status

"""


class IHttpxGitHubAdapter(ABC):

    @abstractmethod
    def getRepositoryNames(self) -> Slugs:
        pass

    @abstractmethod
    def getMileStoneTitles(self, repoName: Slug) -> MilestoneTitles:
        """
        Args:
            repoName: The repository name
        """
        pass

    @abstractmethod
    def getAbbreviatedIssues(self, repoName: Slug, milestoneTitle: str) -> AbbreviatedGitIssues:
        """
        Given a repo name and a milestone title return a simplified list of Git issues

        Args:
            repoName:       The GitHub repository name
            milestoneTitle: The milestone title that we filter on

        Returns:
            A list of abbreviated Git issues
        """
        pass

    @abstractmethod
    def getIssuesAssignedToOwner(self, slugs: Slugs, issueOwner: IssueOwner, callback: IssuesCallback) -> AbbreviatedGitIssues:
        """
        Creates an abbreviated list open issues assigned to the issue owner

        Args:
            slugs:          GitHub Slugs;  e.g. 'hasii2011/pyut'
            issueOwner:     The ones we are looking for
            callback:       Status reporting callback

        Returns:  A list of issues assigned to the user.
        """
        pass
