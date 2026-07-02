
from typing import Any
from typing import Dict
from typing import List
from typing import NewType
from typing import Union
from typing import Callable

from abc import ABC
from abc import abstractmethod

from dataclasses import dataclass

from asyncio import AbstractEventLoop

from logging import Logger

from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import Slugs
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import IssueOwner
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import IntermediateStatus
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import AbbreviatedGitIssue
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import AbbreviatedGitIssues

from gitissue2todoist.adapters.AsyncHttpxGitHubAdapter import AsyncHttpxGitHubAdapter

from gitissue2todoist.AppCommon import AppCommon

from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.dialogs.IAuthenticationDialog import IAuthenticationDialog

from gitissue2todoist.preferences.Preferences import Preferences
from gitissue2todoist.preferences.SecureTokenManager import SecureTokenManager

from gitissue2todoist.general.exceptions.AdapterAuthenticationError import AdapterAuthenticationError

from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine


@dataclass
class RetrievalResult:
    shouldRetry:     bool
    retrievedIssues: AbbreviatedGitIssues | None

IssueDataRow = NewType('IssueDataRow', Dict[str, Union[str, AbbreviatedGitIssue]])
IssueData    = NewType('IssueData',    List[IssueDataRow])
IssueKey     = NewType('IssueKey', str)

ISSUE_DATA_KEY:  IssueKey = IssueKey('abbreviatedGitIssue')
ISSUE_SLUG_KEY:  IssueKey = IssueKey('issueSlug')
ISSUE_TITLE_KEY: IssueKey = IssueKey('issueTitle')


class IMultiRepositoryIssuesPanel(ABC):

    def __init__(self, pubSubEngine: IPubSubEngine):

        self._pubSubEngine: IPubSubEngine = pubSubEngine
        self._preferences:  Preferences   = Preferences()
    
    # We define type hints for properties that the child classes must provide or that we assume exist
    logger: Logger
    _preferences: Preferences
    _progressDlg: Any  # UICommon dialog

    @abstractmethod
    async def _handleGeneralError(self, error: Exception) -> None:
        pass

    async def _doRetrieval(self, repositories: Slugs) -> AbbreviatedGitIssues | None:
        """
        This method is the outer loop that contains the base and retry logic to actually attempt the
        issue retrieval
        It instantiates the progress dialog

        Args:
            repositories:

        """
        from asyncio import AbstractEventLoop
        from asyncio import get_running_loop
        from functools import partial

        finalIssues: AbbreviatedGitIssues | None = None
        loop:        AbstractEventLoop           = get_running_loop()
        
        while True:
            self._progressDlg = UICommon.setupProgressDialog(
                title='Retrieving Issues...',
                maxProgressValue=float(len(repositories))
            )

            callback = partial(self._progressStatusCallback, loop)

            result: RetrievalResult = await self._attemptIssueRetrieval(
                repositories=repositories,
                threadSafeCallback=callback
            )
            
            if result.shouldRetry:
                continue
            else:
                finalIssues = result.retrievedIssues
                break
                
        return finalIssues

    async def _attemptIssueRetrieval(self, repositories: Slugs, threadSafeCallback: Callable) -> RetrievalResult:
        """
        Executes a single attempt to retrieve issues for the selected repositories.
        
        Handles the background thread execution and intercepts any authentication 
        errors. If authentication fails, it prompts the user for new credentials 
        and signals whether the caller should retry the retrieval.

        Args:
            repositories:       A list of repository slugs to fetch issues from.
            threadSafeCallback: A callable used to safely update the UI from the background thread.

        Returns:
            RetrievalResult: A dataclass containing a boolean flag (`shouldRetry`)
            indicating if the operation should be attempted again with new credentials, and the
            `retrievedIssues` if the operation was successful.
        """
        
        # We instantiate this every time so it grabs the freshest API token
        apiToken: str = AppCommon.getAuthenticationToken(
            fallbackMessage=AppCommon.NO_GITHUB_TOKEN_MESSAGE,
            tokenRetrievalMethod=lambda: SecureTokenManager().gitHubToken
        )
            
        githubAdapter = AsyncHttpxGitHubAdapter(authenticationToken=apiToken)
        
        try:
            retrievedIssues: AbbreviatedGitIssues = await githubAdapter.getIssuesAssignedToOwner(
                slugs=repositories,
                issueOwner=IssueOwner(self._preferences.gitHubUserName),
                callback=threadSafeCallback
            )

            self._progressDlg.destroy()
            self.logger.debug(f'{retrievedIssues}')

            return RetrievalResult(shouldRetry=False, retrievedIssues=retrievedIssues)

        except AdapterAuthenticationError as e:
            self._progressDlg.destroy()
            self.logger.error(f'{e=}')

            authDialog: IAuthenticationDialog = await UICommon.setupAuthenticationDialog(
                dialogTitle='GitHub Authentication Failed',
                dialogMessage='Enter GitHub Credentials;  Only need the user name for strategy all',
                apiToken=apiToken,
                gitHubUserName=self._preferences.gitHubUserName
            )
            okPressed: bool = await authDialog.showDialog()

            if okPressed:
                SecureTokenManager().gitHubToken = authDialog.apiToken
                return RetrievalResult(shouldRetry=True, retrievedIssues=None)
            else:
                return RetrievalResult(shouldRetry=False, retrievedIssues=None)

        except Exception as ue:
            self._progressDlg.destroy()
            await self._handleGeneralError(error=ue)
            return RetrievalResult(shouldRetry=False, retrievedIssues=None)

    def _progressStatusCallback(self, loop: AbstractEventLoop, status: IntermediateStatus) -> None:
        """
        Updates the UI progress bar safely from a background thread.
        """
        msg: str = f'Processed {status.currentRepoCount}/{status.totalNumberOfRepos}: {status.nameOfRepoJustProcessed}'

        def updateUI(uiMsg: str, uiCount: float):
            self._progressDlg.updateMessage(uiMsg)
            self._progressDlg.updateProgress = uiCount

        loop.call_soon_threadsafe(updateUI, msg, float(status.currentRepoCount))
        self.logger.info(f'{msg}')
