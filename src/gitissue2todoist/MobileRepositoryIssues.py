
from typing import cast

from logging import Logger
from logging import getLogger

from toga import Box
from toga import Button
from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.IRepositoryIssues import IRepositoryIssues
from gitissue2todoist.IRepositoryIssues import SelectedIssues

from gitissue2todoist.components.MobileMultiSelect import MobileMultiSelect
from gitissue2todoist.components.MobileMultiSelect import MultiSelectValues

from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.adapters.IGitHubAdapter import Slug

from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine
from gitissue2todoist.pubsubengine.MessageType import MessageType


class MobileRepositoryIssues(Box, IRepositoryIssues):

    def __init__(self, pubSubEngine: IPubSubEngine):

        self.logger: Logger = getLogger(__name__)

        style: Pack = Pack(direction=COLUMN, flex=1, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT, gap=15)
        super().__init__(style=style)
        IRepositoryIssues.__init__(self, pubSubEngine=pubSubEngine)

        self._mobileMultiSelect: MobileMultiSelect = MobileMultiSelect()
        buttonContainer, cloneButton = UICommon.createRightAlignedButton(buttonText='Clone', onPressHandler=self._onClone)

        # Disabled until issues are selected
        self._cloneButton: Button = cloneButton
        self._cloneButton.enabled = False

        self.add(self._mobileMultiSelect)
        self.add(self._cloneButton)

        self._pubSubEngine.subscribe(messageType=MessageType.LOAD_ISSUES, listener=self._loadIssuesListener)

    @property
    def selectedIssues(self) -> SelectedIssues:
        """

        Returns: A list of selected issues (toggled ON)
        """
        selectedValues: SelectedIssues = SelectedIssues(list(self._mobileMultiSelect.selectedValues))

        return selectedValues

    def _onClone(self, widget):
        pass

    def _loadIssuesListener(self, repositoryName: Slug, milestoneTitle: str):

        issues = self._getAssociatedIssues(repositoryName=repositoryName, milestoneTitle=milestoneTitle)

        self._mobileMultiSelect.setValues(MultiSelectValues(cast(list, issues)))
