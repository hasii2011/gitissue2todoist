
from logging import Logger
from logging import getLogger

from toga import Box
from toga import Button
from toga import Widget
from toga.style import Pack
from toga.style.pack import COLUMN


from gitissue2todoist.UICommon import UICommon
from gitissue2todoist.components.ReadOnlyList import ListItems
from gitissue2todoist.components.ReadOnlyList import ReadOnlyList


class TodoistPanel(Box):
    """
    TODO:  Once I add more code I will ask Gemini to generate me some
    documentation that I can then edit
    """
    def __init__(self):
        
        self.logger: Logger = getLogger(__name__)

        style: Pack = Pack(direction=COLUMN, flex=1, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT, gap=15)

        super().__init__(style=style)

        # Just provide the title, no icons or subtitles
        items: ListItems = ListItems([
            'hasii2011/pytrek',
            'hasii2011/umlio',
            'hasii2011/umlshapes',
            'hasii2011/umlmodel',
            'hasii2011/gitissue2todoist',
            'hasii2011/umlextensions',
            'hasii2011/umldiagrammer',
            ]
        )
        items.sort()
        # Without an on_select handler, tapping a row does nothing
        self._clonedIssues: ReadOnlyList = ReadOnlyList(
            items=items,
            style=Pack(flex=1)
        )
        buttonContainer, createTasksButton = UICommon.createRightAlignedButton(buttonText='Create Tasks', onPressHandler=self._onCreateTasks)

        buttonContainer.style.margin_right = 20  # Don't jam the button on the app right side
        # Disabled tasks are loaded
        self._createTasksButton: Button = createTasksButton
        self._createTasksButton.enabled = False

        self.add(self._clonedIssues)
        self.add(buttonContainer)

    def _onCreateTasks(self, widget: Widget):
        pass
