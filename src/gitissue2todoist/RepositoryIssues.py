
from typing import cast

from logging import Logger
from logging import getLogger

from toga import Box
from toga import Button
from toga import Table

from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.IRepositoryIssues import IRepositoryIssues
from gitissue2todoist.IRepositoryIssues import SelectedIssues
from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.adapters.IGitHubAdapter import Slug
from gitissue2todoist.pubsubengine.MessageType import MessageType
from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine


class RepositoryIssues(Box, IRepositoryIssues):
    """
    A container with single column Table with multiple_select enabled and a Button
    """
    def __init__(self, pubSubEngine: IPubSubEngine):
        self.logger: Logger = getLogger(__name__)

        style: Pack = Pack(direction=COLUMN, flex=1, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT, gap=15)
        super().__init__(style=style)

        IRepositoryIssues.__init__(self, pubSubEngine=pubSubEngine)

        self._selectionTable: Table = Table(
            columns=['Issues'],
            multiple_select=True,
            show_headings=False,
            style=Pack(flex=1),
        )
        buttonContainer, cloneButton = UICommon.createRightAlignedButton(buttonText='Clone', onPressHandler=self._onClone)

        # Disabled until issues are selected
        self._cloneButton: Button = cloneButton
        self._cloneButton.enabled = False

        self.add(self._selectionTable)
        self.add(buttonContainer)

        self._selectionTable.on_select = self._onSelectionChanged
        self._pubSubEngine.subscribe(messageType=MessageType.LOAD_ISSUES, listener=self._loadIssuesListener)

    @property
    def selectedIssues(self) -> SelectedIssues:
        """

        Returns: A list of selected values were toggled ON.
        """
        selectedValues: SelectedIssues = SelectedIssues([])
        selectedRows = cast(list, self.selection)

        if selectedRows:
            selectedValues = SelectedIssues([cast(str, getattr(row, 'issues')) for row in selectedRows])
            self.logger.warning(f'Currently selected: {selectedValues}')
        else:
            self.logger.warning('Nothing selected.')

        return selectedValues

    # noinspection PyUnusedLocal
    def _onSelectionChanged(self, widget, **kwargs):
        """
        Handle selection changes
        When multiple_select=True, widget.selection returns a list of Row objects
        You can access the data using getattr matching the heading (lowercased/underscored usually)
        or by indexing.

        Args:
            widget:
            **kwargs:

        """
        selectedRows = cast(list, widget.selection)
        if selectedRows:
            self._cloneButton.enabled = True
        else:
            self._cloneButton.enabled = False

    def _onClone(self, widget):
        pass

    def _loadIssuesListener(self, repositoryName: Slug, milestoneTitle: str):

        issueTitles = self._getAssociatedIssues(repositoryName=repositoryName, milestoneTitle=milestoneTitle)
        self._selectionTable.data = issueTitles
