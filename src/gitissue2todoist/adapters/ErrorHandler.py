
from typing import List
from typing import NewType

from logging import Logger
from logging import getLogger

from os import getenv
from os import path as osPath

from shutil import rmtree

from toga import InfoDialog
from toga import QuestionDialog
from toga import Window

from gitissue2todoist.Preferences import Preferences

INVALID_TEMP_ID: int = 16
MAX_PROJECTS:    int = 50

HandledErrors = NewType('HandledErrors', List[int])


class ErrorHandler:

    TODOIST_CACHE_DIRECTORY_NAME: str = '.todoist-sync'

    def __init__(self, window: Window):
        """

        Args:
            window:
        """

        self.logger: Logger = getLogger(__name__)

        self._window:      Window      = window
        self._preferences: Preferences = Preferences()

        self._errorsHandled: HandledErrors = HandledErrors([INVALID_TEMP_ID])

    def isErrorHandled(self, errorCode: int) -> bool:
        """
        Determine if we can handle this type of error.  Currently only applies to
        the Todoist API

        Args:
            errorCode: Error code to check

        Returns: `True` if we do else `False`

        """

        ans: bool = False

        if errorCode in self._errorsHandled:
            ans = True

        return ans

    async def handleError(self, errorMessage: str, errorCode: int):
        """
        Assumes caller has validated we can handle

        Args:
            errorMessage:
            errorCode:
        """

        assert errorCode in self._errorsHandled, 'Developer made  boo boo'

        if self._preferences.cleanTodoistCache is False:
            await self._informUserOfOptions(errorMessage)
        else:
            await self._doRemedialAction()

    async def _doRemedialAction(self):

        msg: str = (
            f'You opted to allow us to clean up certain types of errors by '
            f'removing the Todoist cache. '
            f'I am just double confirming you want to do this?'
        )
        # msgDlg: MessageDialog = MessageDialog(parent=None,
        #                                       message=msg,
        #                                       caption='Question',
        #                                       style=YES | NO | NO_DEFAULT | ICON_QUESTION)
        #
        # answer: int = msgDlg.ShowModal()
        # msgDlg.Destroy()
        # if answer == ID_YES:
        #     self.__removeTodoistCache()

        # 2. Replaces wx.MessageDialog(wx.YES_NO)
        questionDlg: QuestionDialog = QuestionDialog(
            title='Question',
            message=msg
        )
        userClickedYes: bool = await self._window.dialog(questionDlg)
        if userClickedYes:
            await self._removeTodoistCache()

    async def _informUserOfOptions(self, errorMessage: str):
        msg: str = (
            f'Error: "{errorMessage}"   '
            f'This error can usually be handled by deleting the '
            f'Todoist cache.  However, you have that preference turned off '
            f'Turn the preference on and retry your operation'
        )
        # msgDlg: MessageDialog = MessageDialog(parent=None,
        #                                       message=msg,
        #                                       caption='Information',
        #                                       style=OK | ICON_INFORMATION)
        # msgDlg.ShowModal()
        # msgDlg.Destroy()
        dlg: InfoDialog = InfoDialog(
            title='Information',
            message=msg
        )
        await self._window.dialog(dlg)

    async def _removeTodoistCache(self):

        homeDir: str = getenv('HOME')   # type: ignore

        directoryToDelete: str = osPath.join(homeDir, ErrorHandler.TODOIST_CACHE_DIRECTORY_NAME)

        rmtree(directoryToDelete)

        # msgDlg: MessageDialog = MessageDialog(parent=None,
        #                                       message='Now quit and restart PyGitIssue2Todoist',
        #                                       caption='Restart',
        #                                       style=OK | ICON_INFORMATION)
        #
        # msgDlg.ShowModal()
        # msgDlg.Destroy()

        dlg: InfoDialog = InfoDialog(
            title='Restart',
            message='Now quit and restart GitIssue2Todoist'
        )
        await self._window.dialog(dlg)
