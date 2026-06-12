
from typing import List
from typing import NewType

from logging import Logger
from logging import getLogger

from toga import Box
from toga import Switch
from toga import ScrollContainer

from toga.style import Pack
from toga.style.pack import COLUMN

SwitchWidgets     = NewType('SwitchWidgets', List[Switch])
MultiSelectValues = NewType('MultiSelectValues', List[str])
SelectedValues    = NewType('SelectedValues', List[str])

class MobileMultiSelect(ScrollContainer):
    """
    Inherit from ScrollContainer to make the whole component scrollable

    # --- Usage Example ---

    # 1. Create the empty widget
    myMultiSelectList: MobileMultiSelect = MobileMultiSelect()

    # 2. Populate it with initial data
    myMultiSelectList.setOptions(['Label 1', 'Label 2', 'Label 3'])

    # 3. Later on, completely replace the data with new options!
    myMultiSelectList.setOptions(['New Option A', 'New Option B'])

    # 4. Read the selections at any time
    currentSelections = myMultiSelectList.selectedItems

    """
    def __init__(self, **kwargs):

        super().__init__(style=Pack(flex=1), **kwargs)

        self.logger: Logger = getLogger(__name__)

        self._switchContainer: Box = Box(style=Pack(direction=COLUMN, margin=10))

        self.content = self._switchContainer

        self._switchWidgets: SwitchWidgets = SwitchWidgets([])

    @property
    def selectedValues(self) -> SelectedValues:
        """

        Returns: A list of selected values were toggled ON.
        """

        selectedValues: SelectedValues = SelectedValues([])

        for switch in self._switchWidgets:
            if switch.value:
                selectedValues.append(switch.text)

        return selectedValues

    def setValues(self, values: MultiSelectValues):
        """
        Clears existing values and replaces them with a new set of values

        Args:
            values:
        """

        # 1. Remove all existing switches from the UI container
        for oldSwitch in self._switchWidgets:
            self._switchContainer.remove(oldSwitch)

        # 2. Clear our tracking list
        self._switchWidgets.clear()

        # 3. Build and add the new switches
        for itemText in values:
            selectionSwitch: Switch = Switch(
                text=itemText,
                style=Pack(margin=5)
            )
            self._switchWidgets.append(selectionSwitch)
            self._switchContainer.add(selectionSwitch)

        # Force the container to recalculate its layout with the new items
        self._switchContainer.refresh()

