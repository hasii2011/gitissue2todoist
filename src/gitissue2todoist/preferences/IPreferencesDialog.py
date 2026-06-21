
from abc import ABC
from abc import abstractmethod

from toga import Box
from toga import Button

from toga.style import Pack

from toga.style.pack import ROW
from toga.style.pack import COLUMN

from gitissue2todoist.preferences.PreferencesTabbedPanel import PreferencesTabbedPanel


class IPreferencesDialog(ABC):

    def __init__(self):
        # By adding flex=1, iOS knows to expand the tabbed panel down to the buttons!
        self._configPanel:  PreferencesTabbedPanel = PreferencesTabbedPanel(style=Pack(flex=1))

    @abstractmethod
    async def showDialog(self) -> bool:
        pass

    @abstractmethod
    def _onOk(self, widget) -> None:
        pass

    @abstractmethod
    def _onCancel(self, widget) -> None:
        pass

    def _createDialogContent(self) -> Box:

        okButton:     Button = Button('OK', on_press=self._onOk)
        cancelButton: Button = Button('Cancel', on_press=self._onCancel, style=Pack(margin_right=10))

        spacerBox: Box = Box(style=Pack(flex=1))
        buttonBox: Box = Box(children=[spacerBox, cancelButton, okButton], style=Pack(direction=ROW, margin_top=10))

        mainBox: Box = Box(
            children=[
                self._configPanel,
                buttonBox
            ],
            style=Pack(direction=COLUMN, margin=20)
        )
        return mainBox
