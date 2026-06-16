
from typing import List
from typing import NewType
from typing import Optional

from logging import Logger
from logging import getLogger

from toga import Box
from toga import Label
from toga import Divider
from toga import ScrollContainer

from toga.style import Pack
from toga.style.pack import COLUMN

LABEL_MARGIN_LEFT: int = 15
LABEL_MARGIN_VERTICAL: int = 6

ListItems = NewType('ListItems', List[str])


class ReadOnlyList(ScrollContainer):
    """

    """
    def __init__(self, widgetId: Optional[str] = None, style: Optional[Pack] = None, items: Optional[ListItems] = None) -> None:
        """
        Initializes a read-only list component.

        Args:
            widgetId: A unique string identifier for the widget.
                If not provided, Toga automatically generates one.

            style: A Toga Pack style object that defines
                the layout properties (e.g., flex, margin) of this widget.

            items: An initial list of items to
                populate the component with upon creation.
        """
        self.logger: Logger = getLogger(__name__)

        super().__init__(id=widgetId, style=style, horizontal=False, vertical=True)

        self._listBox: Box = Box(style=Pack(direction=COLUMN))
        self.content = self._listBox

        self._items: ListItems = ListItems([])

        if items is not None:
            self.items = items

    def _setItems(self, newItems: ListItems) -> None:

        self.clearItems()
        self._items = newItems

        for index, item in enumerate(self._items):
            label: Label = Label(
                str(item),
                style=Pack(
                    margin_top=LABEL_MARGIN_VERTICAL,
                    margin_bottom=LABEL_MARGIN_VERTICAL,
                    margin_left=LABEL_MARGIN_LEFT
                )
            )
            self._listBox.add(label)

            if index < len(self._items) - 1:
                divider: Divider = Divider()
                self._listBox.add(divider)

    items = property(fset=_setItems, doc='Write-only property to set the items in the list.')

    def clearItems(self) -> None:
        """
        Removes all items and dividers from the list.
        """
        self._items = ListItems([])
        for child in list(self._listBox.children):
            self._listBox.remove(child)
