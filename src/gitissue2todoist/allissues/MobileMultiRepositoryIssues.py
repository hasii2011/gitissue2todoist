
from logging import Logger
from logging import getLogger

from toga import Box
from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.UICommon import UICommon
from gitissue2todoist.allissues.MobileMultiRepositorySelect import MobileMultiRepositorySelect
from gitissue2todoist.preferences.Preferences import Preferences
from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine


class MobileMultiRepositoryIssues(Box):
    def __init__(self, pubSubEngine: IPubSubEngine):

        style: Pack = Pack(direction=COLUMN, flex=1, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT, gap=15)
        super().__init__(style=style)

        self.logger:        Logger        = getLogger(__name__)
        self._pubSubEngine: IPubSubEngine = pubSubEngine
        self._preferences:  Preferences   = Preferences()


        issueSelector: MobileMultiRepositorySelect = MobileMultiRepositorySelect(
            pubSubEngine=self._pubSubEngine,
            itemSelectCallback=self._itemSelectCallback,
            itemDeselectCallback=self._itemDeselectCallback
        )

        self.add(issueSelector)

    def _itemSelectCallback(self) -> None:
        pass

    def _itemDeselectCallback(self, hasNoSelections: bool) -> None:
        pass
