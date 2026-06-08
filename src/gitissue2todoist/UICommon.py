from typing import Callable
from typing import Tuple

from sys import platform as sysPlatform

from toga import Box
from toga import Button
from toga import Label
from toga import Selection

from toga.style import Pack
from toga.style.pack import ROW


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
