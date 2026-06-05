
from typing import Any
from typing import Dict
from typing import List

from httpx import URL
from httpx import get
from httpx import codes
from httpx import Response
from httpx import RequestError
from httpx import HTTPStatusError

from gitissue2todoist.Preferences import Preferences
from gitissue2todoist.adapters.IGitHubAdapter import Slugs
from gitissue2todoist.adapters.IGitHubAdapter import Slug
from gitissue2todoist.adapters.IGitHubAdapter import IssueOwner
from gitissue2todoist.adapters.IGitHubAdapter import IGitHubAdapter
from gitissue2todoist.adapters.IGitHubAdapter import MilestoneTitles
from gitissue2todoist.adapters.IGitHubAdapter import IssuesCallback
from gitissue2todoist.adapters.IGitHubAdapter import AbbreviatedGitIssue
from gitissue2todoist.adapters.IGitHubAdapter import AbbreviatedGitIssues

from gitissue2todoist.adapters.AdapterAuthenticationError import AdapterAuthenticationError
from gitissue2todoist.adapters.GitHubConnectionError import GitHubConnectionError
from gitissue2todoist.adapters.GitHubServiceUnavailableError import GitHubServiceUnavailableError

AUTHENTICATION_FAILED: str = 'Authentication failed'
CONNECTION_FAILED:     str = 'Connection failed:'
SERVICE_DOWN:          str = 'GitHub service unavailable:'

PER_PAGE_PARAMETER_NAME:     str = 'per_page'
USER_REPOS_ENDPOINT:         URL = URL('https://api.github.com/user/repos')
MILESTONES_BY_REPO_ENDPOINT: str = ''
AUTH_TOKEN_NAME:             str = 'Bearer'

GenericJson     = Dict[str, Any]
GenericJsonList = List[GenericJson]


class HttpxGitHubAdapter(IGitHubAdapter):

    ALL_ISSUES_INDICATOR: str = 'All'
    OPEN_ISSUE_INDICATOR: str = 'open'

    def __init__(self, authenticationToken: str):

        self._authenticationToken: str = authenticationToken

        self._preferences: Preferences = Preferences()

        self._headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'{AUTH_TOKEN_NAME} {self._authenticationToken}'
        }

    def getRepositoryNames(self) -> Slugs:

        try:
            response: Response = get(
                USER_REPOS_ENDPOINT,
                headers=self._headers,
                params={PER_PAGE_PARAMETER_NAME: self._preferences.maxReposToRetrieve}
            )
            
            response.raise_for_status()
                
            repos: GenericJsonList= response.json()
            slugs: Slugs                = Slugs([])
            for repo in repos:
                slugs.append(Slug(repo['full_name']))
                

        except HTTPStatusError as e:
            if e.response.status_code in (codes.UNAUTHORIZED, codes.FORBIDDEN):
                raise AdapterAuthenticationError(AUTHENTICATION_FAILED) from e
            raise GitHubServiceUnavailableError(f'{SERVICE_DOWN} {str(e)}') from e
        except RequestError as e:
            raise GitHubConnectionError(f'{CONNECTION_FAILED} {str(e)}') from e

        return slugs

    def getMileStoneTitles(self, repoName: Slug) -> MilestoneTitles:

        try:
            url: URL = URL(f'https://api.github.com/repos/{repoName}/milestones')
            response: Response = get(
                url=url,
                headers=self._headers,
                params={PER_PAGE_PARAMETER_NAME: self._preferences.maxReposToRetrieve}
            )
            
            response.raise_for_status()
            
            milestones: GenericJsonList= response.json()
            milestoneTitles: MilestoneTitles = MilestoneTitles([HttpxGitHubAdapter.ALL_ISSUES_INDICATOR])
            for milestone in milestones:
                milestoneTitles.append(milestone['title'])
                
        except HTTPStatusError as e:
            if e.response.status_code in (codes.UNAUTHORIZED, codes.FORBIDDEN):
                raise AdapterAuthenticationError(AUTHENTICATION_FAILED) from e
            raise GitHubServiceUnavailableError(f'{SERVICE_DOWN} {str(e)}') from e
        except RequestError as e:
            raise GitHubConnectionError(f'{CONNECTION_FAILED} {str(e)}') from e

        return milestoneTitles

    def getAbbreviatedIssues(self, repoName: Slug, milestoneTitle: str) -> AbbreviatedGitIssues:

        try:
            url: URL = URL(f'https://api.github.com/repos/{repoName}/issues')
            response: Response = get(
                url=url,
                headers=self._headers,
                params={
                    'state': HttpxGitHubAdapter.OPEN_ISSUE_INDICATOR,
                    PER_PAGE_PARAMETER_NAME: self._preferences.maxReposToRetrieve
                }
            )
            
            response.raise_for_status()
            
            openGitIssues:   GenericJsonList = response.json()
            simpleGitIssues: AbbreviatedGitIssues = AbbreviatedGitIssues([])
            
            if milestoneTitle == HttpxGitHubAdapter.ALL_ISSUES_INDICATOR:
                for openIssue in openGitIssues:
                    simpleGitIssues.append(self._createAbbreviatedGitIssue(slug=repoName, fullGitIssue=openIssue))
            else:
                for openIssue in openGitIssues:
                    milestone: dict[str, Any] | None = openIssue.get('milestone')
                    if milestone is not None and milestone.get('title') == milestoneTitle:
                        simpleGitIssues.append(self._createAbbreviatedGitIssue(slug=repoName, fullGitIssue=openIssue))
                        
        except HTTPStatusError as e:
            if e.response.status_code in (codes.UNAUTHORIZED, codes.FORBIDDEN):
                raise AdapterAuthenticationError('Authentication failed') from e
            raise GitHubServiceUnavailableError(f'GitHub service unavailable: {str(e)}') from e
        except RequestError as e:
            raise GitHubConnectionError(f'Connection failed: {str(e)}') from e

        return simpleGitIssues

    def getIssuesAssignedToOwner(self, slugs: Slugs, issueOwner: IssueOwner, callback: IssuesCallback) -> AbbreviatedGitIssues:
        return AbbreviatedGitIssues([])
        
    def _createAbbreviatedGitIssue(self, slug: Slug, fullGitIssue: GenericJson) -> AbbreviatedGitIssue:
        """
        Takes generic JSON and puts it in our data class

        Args:
            slug:
            fullGitIssue:

        Returns: AbbreviatedGitIssue

        """

        simpleIssue: AbbreviatedGitIssue = AbbreviatedGitIssue()
        
        simpleIssue.slug         = str(slug)
        simpleIssue.issueTitle   = fullGitIssue.get('title', '')
        simpleIssue.issueHTMLURL = fullGitIssue.get('html_url', '')
        
        body: str | None = fullGitIssue.get('body')
        simpleIssue.body = body if body is not None else ''
        
        labels: GenericJsonList = fullGitIssue.get('labels', [])
        for label in labels:
            simpleIssue.labels.append(label.get('name', ''))
            
        return simpleIssue
