
from typing import Tuple

from toga import Label

from toga.style import Pack


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
