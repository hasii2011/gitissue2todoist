
from typing import Dict
from typing import List
from typing import NewType
from typing import Union
from typing import cast

from logging import Logger
from logging import getLogger

from sys import platform as sysPlatform

from asyncio import Task
from asyncio import create_task

from toga import Box
from toga import Button
from toga import ErrorDialog
from toga import InfoDialog
from toga import Label
from toga import Window

from toga.style import Pack
from toga.style.pack import ROW
from toga.style.pack import COLUMN

from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.AppCommon import AppCommon

from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import Slug
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import Slugs
from gitissue2todoist.adapters.AsyncHttpxGitHubAdapter import AsyncHttpxGitHubAdapter

from gitissue2todoist.dialogs.IAuthenticationDialog import IAuthenticationDialog

from gitissue2todoist.owner.IRepositoryList import IRepositoryList
from gitissue2todoist.owner.MobileRepositoryList import MobileRepositoryList
from gitissue2todoist.owner.RepositoryList import RepositoryList
from gitissue2todoist.owner.RepositoryList import SelectedRepositories

from gitissue2todoist.preferences.Preferences import Preferences
from gitissue2todoist.preferences.SecureTokenManager import SecureTokenManager

from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine

from gitissue2todoist.general.exceptions.AdapterAuthenticationError import AdapterAuthenticationError
from gitissue2todoist.pubsubengine.MessageType import MessageType

from gitissue2todoist.strategy.TodoistStrategyTypes import CloneInformation

REPOSITORY_TITLE_KEY: str = 'repository'

RepositoryDataRow = NewType('RepositoryDataRow', Dict[str, Union[str, Slug]])
RepositoryData    = NewType('RepositoryData', List[RepositoryDataRow])


class UserRepositoriesPanel(Box):

    def __init__(self, pubSubEngine: IPubSubEngine):

        self.logger: Logger = getLogger(__name__)

        self._pubSubEngine: IPubSubEngine = pubSubEngine
        self._preferences:  Preferences   = Preferences()

        style: Pack = Pack(direction=COLUMN, flex=1, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT, gap=15)

        super().__init__(style=style)

        allUserRepositoriesLabel: Label = UICommon.createStandardSectionTitle('All User Repositories')

        self._repositoryList: IRepositoryList
        if self._preferences.debugMobileRepositoryList:

            self._repositoryList = MobileRepositoryList(
                pubSubEngine=self._pubSubEngine,
                repositorySelectedCb=self._repositorySelectedCb,
                repositoryDeselectedCb=self._repositoryDeselectedCb
            )

        else:
            if sysPlatform == AppCommon.PLATFORM_MAC:

                self._repositoryList = RepositoryList(
                    pubSubEngine=self._pubSubEngine,
                    repositorySelectedCb=self._repositorySelectedCb,
                    repositoryDeselectedCb=self._repositoryDeselectedCb
                )
            elif sysPlatform == AppCommon.PLATFORM_IOS:

                self._repositoryList = MobileRepositoryList(
                    pubSubEngine=self._pubSubEngine,
                    repositorySelectedCb=self._repositorySelectedCb,
                    repositoryDeselectedCb=self._repositoryDeselectedCb
                )
            else:
                assert False, 'Unsupported platform'

        self._retrieveIssuesButton: Button = cast(Button, None)

        self.add(allUserRepositoriesLabel)
        self.add(self._repositoryList)
        self.add(self._createButtons())

        #
        # Going to listen to this so I can clear my selection
        #
        self._pubSubEngine.subscribe(MessageType.CLONE_ISSUES, self._cloneIssuesListener)

    async def loadRepositories(self):
        # We instantiate this every time so it grabs the freshest API token
        while True:
            apiToken: str = AppCommon.getAuthenticationToken(
                fallbackMessage=AppCommon.NO_GITHUB_TOKEN_MESSAGE,
                tokenRetrievalMethod=lambda: SecureTokenManager().gitHubToken
            )
            
            githubAdapter = AsyncHttpxGitHubAdapter(authenticationToken=apiToken)

            try:
                repoNames: Slugs = await githubAdapter.getRepositoryNames()
                repoNames.sort()

                self._repositoryList.setRepositories(repoNames)
                break
            except AdapterAuthenticationError as e:
                self.logger.error(f'{e=}')
                authDialog: IAuthenticationDialog = await UICommon.setupAuthenticationDialog(
                    dialogTitle='Authentication Failed',
                    dialogMessage='Enter GitHub Credentials;  Only need the user name for strategy all',
                    apiToken=apiToken,
                    gitHubUserName=self._preferences.gitHubUserName
                )
                okPressed:  bool = await authDialog.showDialog()

                if okPressed:
                    # Save the new token into preferences and retry the loop
                    SecureTokenManager().gitHubToken = authDialog.apiToken

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

    # noinspection PyUnusedLocal
    def _repositorySelectedCb(self) -> None:
        self._retrieveIssuesButton.enabled = True

    # noinspection PyUnusedLocal
    def _repositoryDeselectedCb(self, lastOne: bool) -> None:
        if lastOne:
            self._retrieveIssuesButton.enabled = False
        else:
            self._retrieveIssuesButton.enabled = True

    # noinspection PyUnusedLocal
    def _onSelectAll(self, widget):
        """
        """
        self._repositoryList.selectAll()

    # noinspection PyUnusedLocal
    def _onRetrieve(self, widget):
        """

        Args:
            widget:

        """
        selectedRepositories: SelectedRepositories = self._repositoryList.selectedRepositories

        if len(selectedRepositories) == 0:

            dlg: InfoDialog = InfoDialog(title='Warning', message='Selected repositories have no issues')
            _w: Window | None = self.window
            assert _w is not None, 'I know what I am doing'
            # _w.dialog(dialog=dlg)
            # Schedule the coroutine to run without blocking the current thread
            dialogTask: Task = create_task(_w.dialog(dialog=dlg))

        else:
            self._pubSubEngine.sendMessage(MessageType.RETRIEVE_OWNER_ISSUES, repositories=selectedRepositories)

    async def _handleGeneralError(self, error: Exception):
        """
        Handles any unpredicted, catastrophic failures
        """
        message: str = str(error)

        dlg: ErrorDialog = ErrorDialog(
            title='General Error!',
            message=message
        )
        _w: Window | None = self.window
        assert _w is not None, 'I know what I am doing'
        await _w.dialog(dialog=dlg)

    # noinspection PyUnusedLocal
    def _cloneIssuesListener(self, cloneInformation: CloneInformation) -> None:
        """
        Listening to this so I can clear my selection

        Access the underlying native macOS NSTableView and call selectAll_

        Safely grab the native NSTableView and trigger the OS-level 'Select All' action

        This OSX specific
            The None parameter is being passed as the sender argument to the underlying macOS Objective-C method.
            The sender represents the UI component (like a button, menu item, or keyboard shortcut) that triggered the action.
            Passing None translates to nil in Objective-C
            Safe way to tell macOS, I am triggering this action programmatically; there is no sender.
        Args:
            cloneInformation
        """
        # noinspection PyProtectedMember
        self._repositoryList.deSelectAll()
        # self._repositoryList._impl.native.documentView.deselectAll_(None)
