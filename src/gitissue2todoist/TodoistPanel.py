
from typing import cast

from logging import Logger
from logging import getLogger

from sys import platform as sysPlatform

from toga import Box
from toga import Button
from toga import Divider
from toga import ErrorDialog
from toga import Widget
from toga import Position as TogaPosition

from toga.style import Pack

from toga.style.pack import COLUMN

from codeallybasic.Position import Position

from gitissue2todoist.AppCommon import AppCommon
from gitissue2todoist.dialogs.IAuthenticationDialog import IAuthenticationDialog
from gitissue2todoist.dialogs.AuthenticationDialog import AuthenticationDialog
from gitissue2todoist.dialogs.IOSAuthenticationDialog import IOSAuthenticationDialog

from gitissue2todoist.Preferences import Preferences
from gitissue2todoist.UICommon import UICommon
from gitissue2todoist.ClonedIssuesDisplay import ClonedIssuesDisplay
from gitissue2todoist.dialogs.IOSProgressDialog import IOSProgressDialog
from gitissue2todoist.dialogs.IProgressDialog import IProgressDialog
from gitissue2todoist.dialogs.ProgressDialog import ProgressDialog

from gitissue2todoist.general.exceptions.AdapterAuthenticationError import AdapterAuthenticationError
from gitissue2todoist.adapters.ErrorHandler import ErrorHandler
from gitissue2todoist.adapters.IGitHubAdapter import MilestoneTitle
from gitissue2todoist.adapters.IGitHubAdapter import Slug

from gitissue2todoist.general.exceptions.NoteCreationError import NoteCreationError
from gitissue2todoist.general.exceptions.TaskCreationError import TaskCreationError

from gitissue2todoist.pubsubengine.MessageType import MessageType
from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine
from gitissue2todoist.strategy.TodoistCreation import TodoistCreation

from gitissue2todoist.strategy.TodoistStrategyTypes import CloneInformation

DONT_JAM_ME_MARGIN: int = 20


class TodoistPanel(Box):
    """
    TODO:  Once I add more code I will ask Gemini to generate me some
    documentation that I can then edit
    """
    def __init__(self, pubSubEngine: IPubSubEngine):
        
        self.logger: Logger = getLogger(__name__)

        style: Pack = Pack(direction=COLUMN, flex=1, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT, gap=15)

        super().__init__(style=style)

        self._pubSubEngine:        IPubSubEngine       = pubSubEngine
        self._preferences:         Preferences         = Preferences()
        self._clonedIssuesDisplay: ClonedIssuesDisplay = ClonedIssuesDisplay(style=Pack(flex=1))

        buttonContainer, createTasksButton = UICommon.createRightAlignedButton(
            buttonText='Create Tasks',
            onPressHandler=self._onCreateTasks,     # type: ignore
        )

        buttonContainer.style.margin_right = DONT_JAM_ME_MARGIN

        self._createTasksButton: Button = createTasksButton
        self._createTasksButton.enabled = False             # Disabled until tasks are loaded

        topDivider:    Divider = Divider(style=Pack(margin_bottom=5, margin_top=15))
        bottomDivider: Divider = Divider(style=Pack(margin_top=5, margin_bottom=10))

        self.add(topDivider)
        self.add(self._clonedIssuesDisplay)
        self.add(bottomDivider)
        self.add(buttonContainer)

        self._pubSubEngine.subscribe(MessageType.CLONE_ISSUES, self._cloneIssuesListener)
        self._pubSubEngine.subscribe(messageType=MessageType.SELECTED_REPOSITORY_CHANGED, listener=self._selectedRepositoryChangedListener)
        self._pubSubEngine.subscribe(messageType=MessageType.SELECTED_MILESTONE_CHANGED,  listener=self._selectedMilestoneChangedListener)

        self._todoistCreation:  TodoistCreation  = cast(TodoistCreation, None)      # noqa
        self._cloneInformation: CloneInformation = cast(CloneInformation, None)     # noqa
        self._progressDlg:      IProgressDialog  = cast(IProgressDialog, None)      # noqa

    def _cloneIssuesListener(self, cloneInformation: CloneInformation):
        """

        Args:
            cloneInformation
        """
        self.logger.debug(f'Cloning: {cloneInformation=}')      # TODO: pretty print this so I can log it
        self._clonedIssuesDisplay.clonedInformation = cloneInformation
        self._cloneInformation = cloneInformation
        self._createTasksButton.enabled = True

    # noinspection PyUnusedLocal
    def _selectedMilestoneChangedListener(self, repositoryName: Slug, milestoneTitle: MilestoneTitle):
        """

        Args:
            repositoryName:
            milestoneTitle:
        """
        self._resetPanel()

    # noinspection PyUnusedLocal
    def _selectedRepositoryChangedListener(self, repositoryName: Slug):
        """

        Args:
            repositoryName:
        """
        self._resetPanel()

    async def _onCreateTasks(self, widget: Widget):
        """
        Executes the task creation process. This uses a while loop for retries 
        (e.g., prompting for a new API token upon authentication failure) 
        rather than recursion, avoiding iOS strictly enforced view hierarchy crashes.
        
        Use local imports to hide to the multi-thread magic and
        the toga UI event loop machinations
        Args:
            widget:
        """
        from asyncio import AbstractEventLoop
        from asyncio import get_running_loop
        from asyncio import to_thread
        from functools import partial

        ci:   CloneInformation  = self._cloneInformation
        loop: AbstractEventLoop = get_running_loop()

        while True:
            # We instantiate this every time so it grabs the freshest API token
            self._todoistCreation = TodoistCreation()
            self._progressDlg     = self._setupProgressDialog()

            def _threadSafeCallback(msg: str):
                self.logger.info(f'{msg}')
                loop.call_soon_threadsafe(self._progressDlg.updateMessage, msg)

            try:
                # Execute task creation in a background thread; We don't need a frozen UI
                await to_thread(
                    partial(self._todoistCreation.createTasks, info=ci, progressCb=_threadSafeCallback)
                )
                self._progressDlg.destroy()
                break  # Exit loop on success
                
            except AdapterAuthenticationError:
                self._progressDlg.destroy()
                
                authDialog: IAuthenticationDialog = await self._createAppropriateAuthenticationDialog()
                okPressed: bool = await authDialog.showDialog()
                
                if okPressed:
                    # Save the new token into preferences and retry the loop
                    self._preferences.todoistAPIToken = authDialog.apiToken
                    continue
                else:
                    break  # User canceled, exit loop
                    
            except (TaskCreationError, NoteCreationError) as tce:
                self._progressDlg.destroy()
                await self._handleTaskCreationError(error=tce, widget=widget)
                break
                
            except Exception as ue:
                self._progressDlg.destroy()
                await self._handleGeneralError(error=ue)
                break

        self._resetPanel()
        self._pubSubEngine.sendMessage(messageType=MessageType.TASK_CREATION_COMPLETE)

    async def _handleTaskCreationError(self, widget: Widget, error):
        """
        Encapsulates the complex logic of resolving known task errors

        Args:
            widget:
            error:
        """
        errorHandler: ErrorHandler = ErrorHandler(widget)

        if errorHandler.isErrorHandled(error.errorCode):
            await errorHandler.handleError(error.message, error.errorCode)
        else:
            dlg: ErrorDialog = ErrorDialog(
                title='Task Creation Error!',
                message=error.message
            )
            await self._showDialog(dialog=dlg)

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

    async def _showDialog(self, dialog: ErrorDialog):
        """
        Convenience method to avoid the dipsy do we have to do to avoid
        a PyCharm warning

        Args:
            dialog:
        """
        _win = self.window
        if _win is not None:
            await _win.dialog(dialog)
        else:
            assert False, 'This should not happen'

    def _resetPanel(self):
        """
        Remove clones and disables create tasks button
        """
        self._createTasksButton.enabled = False
        self._clonedIssuesDisplay.clearCloneInformation()

        self._cloneInformation = cast(CloneInformation, None)  # noqa

    async def _createAppropriateAuthenticationDialog(self) -> IAuthenticationDialog:
        """

        Returns:  The platform specific dialog
        """

        dialogTitle:   str = 'Todoist Authentication'
        dialogMessage: str = 'Authentication Failed. Please enter your Todoist API Token:'
        initialToken:  str = self._preferences.todoistAPIToken

        if sysPlatform == AppCommon.PLATFORM_IOS:
            authDialog: IAuthenticationDialog = IOSAuthenticationDialog(
                title=dialogTitle,
                message=dialogMessage,
                initialToken=initialToken
            )
        elif sysPlatform == AppCommon.PLATFORM_MAC:
            authDialog = AuthenticationDialog(
                title=dialogTitle,
                message=dialogMessage,
                initialToken=initialToken
            )
        else:
            assert False, 'Unsupported platform'

        return authDialog

    def _setupProgressDialog(self) -> IProgressDialog:
        """

        Returns:  The platform specific dialog
        """
        commonTitle: str = 'Creating Todoist Tasks...'
        if sysPlatform == AppCommon.PLATFORM_MAC:

            dlg:      IProgressDialog = ProgressDialog(title=commonTitle)
            position: Position       = self._preferences.progressDialogPosition

            dlg.position = TogaPosition(x=position.x, y=position.y)
        elif sysPlatform == AppCommon.PLATFORM_IOS:
            dlg  = IOSProgressDialog(title=commonTitle)
        else:
            assert False, 'Unsupported platform'

        dlg.showDialog()

        return dlg
