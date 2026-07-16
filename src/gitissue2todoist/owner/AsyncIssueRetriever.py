
from typing import Callable

from logging import Logger
from logging import getLogger

from asyncio import AbstractEventLoop

from dataclasses import dataclass
from dataclasses import field

from gitissue2todoist.AppCommon import AppCommon
from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.adapters.AsyncHttpxGitHubAdapter import AsyncHttpxGitHubAdapter
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import IntermediateStatus
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import IssueOwner
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import Slugs
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import AbbreviatedGitIssues

from gitissue2todoist.dialogs.IAuthenticationDialog import IAuthenticationDialog

from gitissue2todoist.general.exceptions.AdapterAuthenticationError import AdapterAuthenticationError

from gitissue2todoist.preferences.Preferences import Preferences
from gitissue2todoist.preferences.SecureTokenManager import SecureTokenManager

def abbreviatedGitIssuesFactory() -> AbbreviatedGitIssues:
    """
    Factory method to create  the AbbreviatedGitIssues data structure;

    Returns:  A new data structure
    """
    return AbbreviatedGitIssues([])


@dataclass
class RetrievalResult:
    shouldRetry:     bool
    retrievedIssues: AbbreviatedGitIssues = field(default_factory=abbreviatedGitIssuesFactory)


class AsyncIssueRetriever:
    """
    Dedicated class to handle the asynchronous retrieval of issues, including
    authentication retries and progress dialog management.
    """
    def __init__(self):
        
        self.logger:        Logger      = getLogger(__name__)
        self._preferences:  Preferences = Preferences()
        self._progressDlg               = None

    async def retrieveIssues(self, repositories: Slugs) -> AbbreviatedGitIssues:
        """
        Assumes that the input repository names are the ones associated with the GitHub
        username in the preferences

        Args:
            repositories:   The repositories to query

        Returns:  The abbreviated Git issues associated with the input repositories

        """
        
        from asyncio import get_running_loop

        finalIssues: AbbreviatedGitIssues = abbreviatedGitIssuesFactory()
        loop:        AbstractEventLoop    = get_running_loop()   # Grab the UI Loop
        #
        #  This is the retry loop
        #
        while True:
            self._progressDlg = UICommon.setupProgressDialog(
                title='Retrieving Issues...',
                maxProgressValue=float(len(repositories))
            )

            callback: Callable = lambda intermediateStatus: self._progressStatusCallback(loop, intermediateStatus)

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

        Args:
            repositories:
            threadSafeCallback:

        Returns: The dataclass RetrievalResult that indicates whether a retry is needed;  If .shouldRetry
        is False, then .retrievedIssues has the list of abbreviated Git issues

        """
        
        apiToken: str = AppCommon.getAuthenticationToken(
            fallbackMessage=AppCommon.NO_GITHUB_TOKEN_MESSAGE,
            tokenRetrievalMethod=lambda: SecureTokenManager().gitHubToken
        )

        githubAdapter: AsyncHttpxGitHubAdapter = AsyncHttpxGitHubAdapter(authenticationToken=apiToken)

        issueOwner: IssueOwner = IssueOwner(self._preferences.gitHubUserName)
        self.logger.info(f'Retrieving issues: {issueOwner=}')
        try:
            retrievedIssues: AbbreviatedGitIssues = await githubAdapter.getIssuesAssignedToOwner(
                slugs=repositories,
                issueOwner=IssueOwner(issueOwner),
                callback=threadSafeCallback
            )

            if self._progressDlg:
                self._progressDlg.destroy()
            
            self.logger.debug(f'{retrievedIssues}')
            return RetrievalResult(shouldRetry=False, retrievedIssues=retrievedIssues)

        except AdapterAuthenticationError as authError:
            if self._progressDlg:
                self._progressDlg.destroy()
            
            self.logger.error(f'{authError=}')

            authDialog: IAuthenticationDialog = await UICommon.setupAuthenticationDialog(
                dialogTitle='GitHub Authentication Failed',
                dialogMessage='Enter GitHub Credentials;  Only need the user name for strategy all',
                apiToken=apiToken,
                gitHubUserName=self._preferences.gitHubUserName
            )
            okPressed: bool = await authDialog.showDialog()

            if okPressed:
                SecureTokenManager().gitHubToken = authDialog.apiToken
                return RetrievalResult(shouldRetry=True, retrievedIssues=abbreviatedGitIssuesFactory())
            else:
                return RetrievalResult(shouldRetry=False, retrievedIssues=abbreviatedGitIssuesFactory())

        except Exception as generalError:
            if self._progressDlg:
                self._progressDlg.destroy()
                
            self.logger.error(f'General Error during retrieval: {generalError}')
            return RetrievalResult(shouldRetry=False, retrievedIssues=abbreviatedGitIssuesFactory())

    def _progressStatusCallback(self, loop: AbstractEventLoop, intermediateStatus: IntermediateStatus) -> None:
        """

        Args:
            loop:                Needed to help us run on the UI thread
            intermediateStatus:  Reported by the asynch GitHub adapter as it processes each repository

        """
        
        msg: str = f'Processed {intermediateStatus.currentRepoCount}/{intermediateStatus.totalNumberOfRepos}: {intermediateStatus.nameOfRepoJustProcessed}'

        def updateUI(uiMsg: str, uiCount: float) -> None:
            if self._progressDlg:
                self._progressDlg.updateMessage(uiMsg)
                self._progressDlg.updateProgress = uiCount

        # Bridges the gap between multi-threading and asynchronous event loops.
        # Safely injects the updateUI function and its arguments into the event loop's internal queue.
        loop.call_soon_threadsafe(updateUI, msg, float(intermediateStatus.currentRepoCount))

        self.logger.info(f'{msg}')
