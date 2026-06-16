
from typing import cast

from logging import Logger
from logging import getLogger


from toga import Box
from toga import Button
from toga import Divider
from toga import ErrorDialog
from toga import Widget
from toga import Position as TogaPosition

from toga.style import Pack

from toga.style.pack import COLUMN

from codeallybasic.Position import Position

from gitissue2todoist.Preferences import Preferences
from gitissue2todoist.UICommon import UICommon
from gitissue2todoist.ClonedIssuesDisplay import ClonedIssuesDisplay
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

        self._todoistCreation:  TodoistCreation  = TodoistCreation()
        self._cloneInformation: CloneInformation = cast(CloneInformation, None)     # noqa
        self._progressDlg:      ProgressDialog   = cast(ProgressDialog, None)       # noqa

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

    # noinspection PyUnusedLocal
    async def _onCreateTasks(self, widget: Widget):

        from asyncio import AbstractEventLoop
        from asyncio import get_running_loop
        from asyncio import to_thread
        from functools import partial

        self._progressDlg = self._setupProgressDialog()

        ci:                CloneInformation  = self._cloneInformation
        # Capture the Main Event Loop BEFORE leaving the main thread
        loop:              AbstractEventLoop = get_running_loop()

        def _threadSafeCallback(msg: str):
            self.logger.info(f'{msg}')
            # Use the captured loop reference
            loop.call_soon_threadsafe(self._progressDlg.updateMessage, msg)

        try:
            # Run heavy synchronous task creation in a background thread so the GUI does not freeze
            await to_thread(
                partial(self._todoistCreation.createTasks, info=ci, progressCb=_threadSafeCallback)
            )
            self._progressDlg.destroy()
        except AdapterAuthenticationError as e:
            self._progressDlg.destroy()
            self._handleAuthenticationError()
        except (TaskCreationError, NoteCreationError) as tce:
            self._progressDlg.destroy()
            errorHandler: ErrorHandler = ErrorHandler(widget)

            if errorHandler.isErrorHandled(tce.errorCode):
                await errorHandler.handleError(tce.message, tce.errorCode)
            else:
                # booBoo: MessageDialog = MessageDialog(parent=None, message=tce.message, caption='Task Creation Error!', style=OK | ICON_ERROR)
                # booBoo.ShowModal()
                dlg: ErrorDialog = ErrorDialog(
                    title='Task Creation Error!',
                    message=tce.message
                )
                await self._showDialog(dialog=dlg)
        except Exception as ue:
            # This path was manually verified when I was missing the _todoistCreation
            message: str = str(ue)

            dlg = ErrorDialog(
                title='General Error!',
                message=message
            )
            await self._showDialog(dialog=dlg)
        finally:
            self._resetPanel()
            self._pubSubEngine.sendMessage(messageType=MessageType.TASK_CREATION_COMPLETE)

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

    def _handleAuthenticationError(self):
        # TODO:   Pop up dialog for new authorization token
        pass

    def _setupProgressDialog(self) -> ProgressDialog:

        dlg: ProgressDialog = ProgressDialog('Creating Todoist Tasks...')

        position: Position = self._preferences.progressDialogPosition

        dlg.position = TogaPosition(x=position.x, y=position.y)

        dlg.show()

        return dlg
