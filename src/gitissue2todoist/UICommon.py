
from typing import Tuple
from typing import Callable

from asyncio import Task
from asyncio import create_task

from sys import platform as sysPlatform

from toga import Box
from toga import Button
from toga import InfoDialog
from toga import Label
from toga import Selection

from toga import Position as TogaPosition
from toga import Widget
from toga import Window

from toga.style import Pack
from toga.style.pack import ROW

from codeallybasic.Position import Position

from gitissue2todoist.dialogs.IAuthenticationDialog import IAuthenticationDialog
from gitissue2todoist.dialogs.IProgressDialog import IProgressDialog


class UICommon:

    MARGIN_LEFT:  int = 5
    MARGIN_RIGHT: int = 5

    SECTION_LABEL_MARGIN: Tuple[int, int] = (2, 5)
    """
    2 integers are provided; 
    The first value is the margin for the top and bottom; 
    The second is the margin left and right;
    """
    SECTION_LABEL_WEIGHT: str = 'bold'
    SECTION_LABEL_SIZE:   int = 14

    @classmethod
    def createStandardSectionTitle(cls, titleText: str):

        stdLabel: Label = Label(
            titleText,
            style=Pack(
                margin=UICommon.SECTION_LABEL_MARGIN,
                font_weight=UICommon.SECTION_LABEL_WEIGHT,
                font_size=UICommon.SECTION_LABEL_SIZE,
            ),
        )

        return stdLabel

    @classmethod
    def createRightAlignedButton(cls, buttonText: str, onPressHandler: Callable[[Button], None]) -> Tuple[Box, Button]:
        """
        Give the button a natural size and right-align it. The standard "BeeWare Way" is to
            * Wrap it in a ROW box
            * Push it to the right using an empty invisible 'spacer' box
            * The 'spacer' box takes up all the remaining space.

        Args:
            buttonText:
            onPressHandler:

        Returns:  A tuple of the button container and the button
        """
        buttonContainer: Box    = Box(style=Pack(direction=ROW))
        spacer:          Box    = Box(style=Pack(flex=1))
        stdButton:       Button = Button(buttonText, on_press=onPressHandler, style=Pack(margin=5))

        buttonContainer.add(spacer)
        buttonContainer.add(stdButton)

        return buttonContainer, stdButton

    @classmethod
    def popDownPicker(cls, selection: Selection):
        """
        Hacky way to pop down the spinners on the IOS simulator

        Args:
            selection:  The IO Picker

        """
        from gitissue2todoist.AppCommon import AppCommon

        if sysPlatform == AppCommon.PLATFORM_IOS:
            # noinspection PyProtectedMember
            selection._impl.native.resignFirstResponder()

    @classmethod
    def setupProgressDialog(cls, title: str, maxProgressValue: float | None = None) -> IProgressDialog:
        """
        Creates, configures, and displays the platform-specific progress dialog.
        
        If a maxProgressValue is provided, the progress bar will be initialized as determinate
        before being shown, preventing it from getting locked into an indeterminate sweeping animation.

        Args:
            title: The text to display as the dialog's title.
            maxProgressValue: An optional maximum float value for the progress bar. If None, it initializes as indeterminate.

        Returns:  The platform specific dialog
        """
        from gitissue2todoist.AppCommon import AppCommon
        from gitissue2todoist.dialogs.ProgressDialog import ProgressDialog
        from gitissue2todoist.dialogs.IOSProgressDialog import IOSProgressDialog
        from gitissue2todoist.preferences.Preferences import Preferences

        preferences: Preferences = Preferences()
        dlg:         IProgressDialog
        if sysPlatform == AppCommon.PLATFORM_MAC:
            dlg = ProgressDialog(title=title)
            position: Position = preferences.progressDialogPosition
            dlg.position = TogaPosition(x=position.x, y=position.y)

        elif sysPlatform == AppCommon.PLATFORM_IOS:
            dlg = IOSProgressDialog(title=title)
        else:
            assert False, 'Unsupported platform'

        if maxProgressValue is not None:
            dlg.maxProgressValue = maxProgressValue

        dlg.showDialog()

        return dlg

    @classmethod
    async def setupAuthenticationDialog(cls, dialogTitle: str, dialogMessage: str, apiToken: str, gitHubUserName: str = '') -> IAuthenticationDialog:
        """
        For use with GitHub and Todoist authentication tokens

        Args:
            dialogTitle:
            dialogMessage:
            apiToken:
            gitHubUserName:  Populate only if you are authenticating for the all issues strategy

        Returns:  The platform specific dialog
        """
        from gitissue2todoist.AppCommon import AppCommon
        from gitissue2todoist.dialogs.AuthenticationDialog import AuthenticationDialog
        from gitissue2todoist.dialogs.IOSAuthenticationDialog import IOSAuthenticationDialog

        if sysPlatform == AppCommon.PLATFORM_IOS:
            authDialog: IAuthenticationDialog = IOSAuthenticationDialog(
                title=dialogTitle,
                message=dialogMessage,
                initialToken=apiToken
            )
        elif sysPlatform == AppCommon.PLATFORM_MAC:
            authDialog = AuthenticationDialog(
                title=dialogTitle,
                message=dialogMessage,
                initialToken=apiToken
            )
        else:
            assert False, 'Unsupported platform'

        return authDialog

    @classmethod
    def asyncDisplayInfoDialog(cls, widget: Widget, title: str, message: str):
        """
        Displays an async dialog

        Args:
            widget:
            title:
            message:

        """

        dlg: InfoDialog = InfoDialog(title=title, message=message)

        _w: Window | None = widget.window
        assert _w is not None, 'I know what I am doing'
        #
        # _w.dialog(dialog=dlg)
        # Schedule the coroutine to run without blocking the current thread
        dialogTask: Task = create_task(_w.dialog(dialog=dlg))
