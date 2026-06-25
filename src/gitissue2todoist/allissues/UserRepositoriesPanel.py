
from typing import Dict
from typing import List
from typing import NewType
from typing import Union
from typing import cast

from logging import Logger
from logging import getLogger


from toga import Box
from toga import Button
from toga import ErrorDialog
from toga import Label
from toga import Table

from toga.style import Pack
from toga.style.pack import ROW
from toga.style.pack import COLUMN

from toga.sources import Row

from gitissue2todoist.UICommon import UICommon
from gitissue2todoist.adapters.IGitHubAdapter import AbbreviatedGitIssues
from gitissue2todoist.adapters.IGitHubAdapter import IntermediateStatus
from gitissue2todoist.adapters.IGitHubAdapter import IssueOwner
from gitissue2todoist.adapters.IGitHubAdapter import Slug

from gitissue2todoist.adapters.IGitHubAdapter import Slugs
from gitissue2todoist.adapters.HttpxGitHubAdapter import HttpxGitHubAdapter
from gitissue2todoist.dialogs.IAuthenticationDialog import IAuthenticationDialog

from gitissue2todoist.preferences.Preferences import Preferences

from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine

from gitissue2todoist.general.exceptions.AdapterAuthenticationError import AdapterAuthenticationError
from gitissue2todoist.pubsubengine.MessageType import MessageType

REPOSITORY_TITLE_KEY: str = 'repository'

RepositoryDataRow = NewType('RepositoryDataRow', Dict[str, Union[str, Slug]])
RepositoryData    = NewType('RepositoryData', List[RepositoryDataRow])

SelectedRepositories = Slugs


class UserRepositoriesPanel(Box):

    def __init__(self, pubSubEngine: IPubSubEngine):

        self.logger: Logger = getLogger(__name__)

        self._pubSubEngine: IPubSubEngine = pubSubEngine
        self._preferences:  Preferences   = Preferences()

        style: Pack = Pack(direction=COLUMN, flex=1, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT, gap=15)

        super().__init__(style=style)

        allUserRepositoriesLabel: Label = UICommon.createStandardSectionTitle('All User Repositories')

        self._repositoryList: Table = Table(
            columns=[REPOSITORY_TITLE_KEY],
            multiple_select=True,
            show_headings=False,
            style=Pack(flex=1),
            on_select=self._onRepositorySelected
        )
        self._retrieveIssuesButton: Button = cast(Button, None)

        self.add(allUserRepositoriesLabel)
        self.add(self._repositoryList)
        self.add(self._createButtons())

    async def loadRepositories(self):
        from asyncio import to_thread
        # We instantiate this every time so it grabs the freshest API token
        while True:
            githubAdapter = HttpxGitHubAdapter(authenticationToken=self._preferences.gitHubAPIToken)

            try:
                repoNames: Slugs = await to_thread(githubAdapter.getRepositoryNames)
                repoNames.sort()

                self._repositoryList.data = repoNames
                break
            except AdapterAuthenticationError as e:
                self.logger.error(f'{e=}')
                authDialog: IAuthenticationDialog = await UICommon.setupAuthenticationDialog(
                    dialogTitle='Authentication Failed',
                    dialogMessage='Enter GitHub Credentials;  Only need the user name for strategy all',
                    apiToken=self._preferences.gitHubAPIToken,
                    gitHubUserName=self._preferences.gitHubUserName
                )
                okPressed:  bool = await authDialog.showDialog()

                if okPressed:
                    # Save the new token into preferences and retry the loop
                    self._preferences.gitHubAPIToken = authDialog.apiToken

                    continue
                else:
                    break  # User canceled, exit loop
            except Exception as ue:
                await self._handleGeneralError(error=ue)
                break

    def _createButtons(self) -> Box:
        """
        Modifies:
                self._retrieveIssuesButton

        Returns:  The container for appropriate display in parent
        """

        selectAllButton: Button = Button('Select All',      on_press=self._onSelectAll)
        retrieveButton:  Button = Button('Retrieve Issues', on_press=self._onRetrieve, style=Pack(margin_right=10))

        retrieveButton.enabled = False

        spacerBox: Box = Box(style=Pack(flex=1))
        buttonBox: Box = Box(children=[spacerBox, selectAllButton, retrieveButton], style=Pack(direction=ROW, margin_top=10))

        self._retrieveIssuesButton =retrieveButton

        return buttonBox

    @property
    def selectedRepositories(self) -> SelectedRepositories:
        """

        Returns: A list of selected repositories were toggled ON.
        """
        selectedRepositories: SelectedRepositories = SelectedRepositories([])

        # Cast explicitly informs type checkers that multiple_select=True returns a List[Row]
        selectedRows: List[Row] = cast(List[Row], self._repositoryList.selection)

        if selectedRows:
            for row in selectedRows:
                togaRow: Row = row
                # Use getattr to bypass static type checker warnings for dynamic Row attributes
                repoSlug: Slug = getattr(togaRow, REPOSITORY_TITLE_KEY)

                self.logger.debug(f'Currently selected: {repoSlug}')
                selectedRepositories.append(repoSlug)
        else:
            self.logger.warning('Nothing selected.')

        return selectedRepositories

    # noinspection PyUnusedLocal
    def _onRepositorySelected(self, repositoryList: Table):
        self._retrieveIssuesButton.enabled = True

    # noinspection PyUnusedLocal
    def _onSelectAll(self, widget):
        """
        Access the underlying native macOS NSTableView and call selectAll_

        Safely grab the native NSTableView and trigger the OS-level 'Select All' action

        This OSX specific
        Args:
            widget:

        """
        self._repositoryList._impl.native.documentView.selectAll_(None)
        selections = self._repositoryList.selection

        selectedRepositories: SelectedRepositories = self.selectedRepositories

        self._pubSubEngine.sendMessage(MessageType.RETRIEVE_OWNER_ISSUES, repositories=selectedRepositories)

    # noinspection PyUnusedLocal
    async def _onRetrieve(self, widget):
        """
        Calls the GitHub adapter with the issue owner name and a list of
        selected repositories to get the issues assigned to this owner.  Because this is
        a potentially expensive operation we run it async and update a progress dialog
        for the application user

        TODO: The code to retrieve the issues belongs MultiRepositoryIsses and it mobile
        companion.  We should just publish the selected repositories
        Args:
            widget:

        """

        selectedRepositories: SelectedRepositories = self.selectedRepositories

        from asyncio import AbstractEventLoop
        from asyncio import get_running_loop
        from asyncio import to_thread

        def _threadSafeCallback(status: IntermediateStatus):

            msg: str = f'Processed {status.currentRepoCount}/{status.totalNumberOfRepos}: {status.nameOfRepoJustProcessed}'

            def updateUI(uiMsg: str, uiCount: float):
                self._progressDlg.updateMessage(uiMsg)
                self._progressDlg.updateProgress = uiCount

            loop.call_soon_threadsafe(updateUI, msg, float(status.currentRepoCount))

            self.logger.info(f'{msg}')

        loop: AbstractEventLoop = get_running_loop()
        while True:
            # We instantiate this every time so it grabs the freshest API token
            githubAdapter = HttpxGitHubAdapter(authenticationToken=self._preferences.gitHubAPIToken)

            self._progressDlg = UICommon.setupProgressDialog(
                title='Retrieving Issues...',
                maxProgressValue=float(len(selectedRepositories))
            )

            try:
                # Execute task creation in a background thread; We don't need a frozen UI
                retrievedIssues: AbbreviatedGitIssues = await to_thread(
                    githubAdapter.getIssuesAssignedToOwner,
                        slugs = selectedRepositories,
                        issueOwner = IssueOwner(self._preferences.gitHubUserName),
                        callback = _threadSafeCallback
                )

                self._progressDlg.destroy()
                self.logger.debug(f'{retrievedIssues}')
                self._pubSubEngine.sendMessage(MessageType.RETRIEVE_OWNER_ISSUES, repositories=selectedRepositories)

                break  # Exit loop on success
            except AdapterAuthenticationError as e:
                self._progressDlg.destroy()
                self.logger.error(f'{e=}')

                authDialog: IAuthenticationDialog = await UICommon.setupAuthenticationDialog(
                    dialogTitle='GitHub Authentication Failed',
                    dialogMessage='Enter GitHub Credentials;  Only need the user name for strategy all',
                    apiToken=self._preferences.gitHubAPIToken,
                    gitHubUserName=self._preferences.gitHubUserName
                )
                okPressed:  bool = await authDialog.showDialog()

                if okPressed:
                    # Save the new token into preferences and retry the loop
                    self._preferences.gitHubAPIToken = authDialog.apiToken
                    continue
                else:
                    break  # User canceled, exit loop
            except Exception as ue:
                self._progressDlg.destroy()
                await self._handleGeneralError(error=ue)
                break

    async def _handleGeneralError(self, error: Exception):
        """
        Handles any unpredicted, catastrophic failures
        """
        message: str = str(error)

        dlg: ErrorDialog = ErrorDialog(
            title='General Error!',
            message=message
        )
        await self._showDialog(dialog=dlg)
