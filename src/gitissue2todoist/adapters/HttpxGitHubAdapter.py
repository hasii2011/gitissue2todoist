
from typing import Any
from typing import List

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
from gitissue2todoist.adapters.IGitHubAdapter import AbbreviatedGitIssues

from gitissue2todoist.adapters.AdapterAuthenticationError import AdapterAuthenticationError
from gitissue2todoist.adapters.GitHubConnectionError import GitHubConnectionError
from gitissue2todoist.adapters.GitHubServiceUnavailableError import GitHubServiceUnavailableError

AUTHENTICATION_FAILED: str = 'Authentication failed'
CONNECTION_FAILED:     str = 'Connection failed:'
SERVICE_DOWN:          str = 'GitHub service unavailable:'

PER_PAGE_PARAMETER_NAME:     str = 'per_page'
USER_REPOS_ENDPOINT:         str = 'https://api.github.com/user/repos'
MILESTONES_BY_REPO_ENDPOINT: str = ''
AUTH_TOKEN_NAME:             str = 'Bearer'

GenericJson = List[dict[str, Any]]


class HttpxGitHubAdapter(IGitHubAdapter):

    def __init__(self, authenticationToken: str):

        # self._userName:            str = userName
        self._authenticationToken: str = authenticationToken

        self._preferences: Preferences = Preferences()
        
    def getRepositoryNames(self) -> Slugs:
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'{AUTH_TOKEN_NAME} {self._authenticationToken}'
        }
        
        try:

            response: Response = get(
                USER_REPOS_ENDPOINT,
                headers=headers,
                params={PER_PAGE_PARAMETER_NAME: self._preferences.maxReposToRetrieve}
            )
            
            response.raise_for_status()
                
            repos: GenericJson= response.json()
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
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'{AUTH_TOKEN_NAME} {self._authenticationToken}'
        }
        
        try:
            response: Response = get(
                f'https://api.github.com/repos/{repoName}/milestones',
                headers=headers,
                params={PER_PAGE_PARAMETER_NAME: self._preferences.maxReposToRetrieve}
            )
            
            response.raise_for_status()
            
            milestones:      GenericJson     = response.json()
            milestoneTitles: MilestoneTitles = MilestoneTitles([])

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
        return AbbreviatedGitIssues([])

    def getIssuesAssignedToOwner(self, slugs: Slugs, issueOwner: IssueOwner, callback: IssuesCallback) -> AbbreviatedGitIssues:
        return AbbreviatedGitIssues([])
