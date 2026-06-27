
from logging import Logger
from logging import getLogger

from toga import Box
from toga import Table
from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.UICommon import UICommon
from gitissue2todoist.adapters.AsyncHttpxGitHubAdapter import AsyncHttpxGitHubAdapter
from gitissue2todoist.adapters.IAsyncGitHubAdapter import AbbreviatedGitIssues
from gitissue2todoist.adapters.IAsyncGitHubAdapter import IntermediateStatus
from gitissue2todoist.adapters.IAsyncGitHubAdapter import IssueOwner
from gitissue2todoist.adapters.IAsyncGitHubAdapter import Slugs
from gitissue2todoist.dialogs.IAuthenticationDialog import IAuthenticationDialog
from gitissue2todoist.general.exceptions.AdapterAuthenticationError import AdapterAuthenticationError
from gitissue2todoist.preferences.Preferences import Preferences
from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine
from gitissue2todoist.pubsubengine.MessageType import MessageType

from typing import Callable
from dataclasses import dataclass
from asyncio import AbstractEventLoop

@dataclass
class RetrievalResult:
    shouldRetry:     bool
    retrievedIssues: AbbreviatedGitIssues | None


class MultiRepositoryIssues(Box):

    def __init__(self, pubSubEngine: IPubSubEngine):

        style: Pack = Pack(direction=COLUMN, flex=1, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT, gap=15)
        super().__init__(style=style)

        self.logger: Logger = getLogger(__name__)

        self._pubSubEngine: IPubSubEngine = pubSubEngine
        self._preferences:  Preferences   = Preferences()

        self._issueTable: Table = Table(
            columns=['Repository', 'Issue'],
            multiple_select=True,
            show_headings=False,
            style=Pack(flex=1),
            data=[
                ('hasii2011/pytrek', 'Game is AI smart'),
                ('hasii2011/umldiagrammer', 'True round trip engineering'),
                ('hasii2011/umlshapes', 'Super smart shapes'),
            ]
        )

        self.add(self._issueTable)

        self._pubSubEngine.subscribe(MessageType.RETRIEVE_OWNER_ISSUES, listener=self._retrieveOwnerIssuesListener)

    def _retrieveOwnerIssuesListener(self, repositories: Slugs):
        """
        The listener that knows how to retrieve all issues across the published
        repositories
        Spawns an async task

        Args:
            repositories:
        """
        from asyncio import create_task

        async def _runAndProcess():
            retrievedIssues: AbbreviatedGitIssues | None = await self._doRetrieval(repositories)
            
            if retrievedIssues is not None:
                self.logger.info(f"Successfully captured {len(retrievedIssues)} issues!")
                # TODO: Update UI with retrievedIssues
                pass

        create_task(_runAndProcess())

    async def _doRetrieval(self, repositories: Slugs) -> AbbreviatedGitIssues | None:
        """
        This method is the outer loop that contains the base and retry logic to actually attempt the
        issue retrieval
        It instantiates the progress dialog

        Args:
            repositories:

        """
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
        githubAdapter = AsyncHttpxGitHubAdapter(authenticationToken=self._preferences.gitHubAPIToken)
        
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
                apiToken=self._preferences.gitHubAPIToken,
                gitHubUserName=self._preferences.gitHubUserName
            )
            okPressed: bool = await authDialog.showDialog()

            if okPressed:
                self._preferences.gitHubAPIToken = authDialog.apiToken
                return RetrievalResult(shouldRetry=True, retrievedIssues=None)
            else:
                return RetrievalResult(shouldRetry=False, retrievedIssues=None)

        except Exception as ue:
            self._progressDlg.destroy()
            await self._handleGeneralError(error=ue)
            return RetrievalResult(shouldRetry=False, retrievedIssues=None)

    def _progressStatusCallback(self, loop: AbstractEventLoop, status: IntermediateStatus):
        """
        Updates the UI progress bar safely from a background thread.
        """
        msg: str = f'Processed {status.currentRepoCount}/{status.totalNumberOfRepos}: {status.nameOfRepoJustProcessed}'

        def updateUI(uiMsg: str, uiCount: float):
            self._progressDlg.updateMessage(uiMsg)
            self._progressDlg.updateProgress = uiCount

        loop.call_soon_threadsafe(updateUI, msg, float(status.currentRepoCount))
        self.logger.info(f'{msg}')
