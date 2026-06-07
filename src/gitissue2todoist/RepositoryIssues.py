
from typing import List
from typing import NewType

from logging import Logger
from logging import getLogger

from typing import cast

from toga import Table

from toga.style import Pack

from gitissue2todoist.IRepositoryIssues import IRepositoryIssues
from gitissue2todoist.IRepositoryIssues import SelectedIssues


class RepositoryIssues(Table, IRepositoryIssues):
    """
    A single column Table with multiple_select enabled
    """

    def __init__(self):
        self.logger: Logger = getLogger(__name__)

        super().__init__(
            columns=['Issues'],
            multiple_select=True,
            show_headings=False,
            style=Pack(flex=1),
            data=[
                'hasii2011/pytrek',
                'hasii2011/py2appsigner',
                'hasii2011/umldiagrammer',
                'hasii2011/umlmodel',
                'hasii2011/umlio',
                'hasii2011/umlshapes',
            ],
        )
        self.on_select = self.onSelectionChanged

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
    def onSelectionChanged(self, widget, **kwargs):
        """
        Optional: Handle selection changes
        When multiple_select=True, widget.selection returns a list of Row objects
        You can access the data using getattr matching the heading (lowercased/underscored usually)
        or by indexing.

        Args:
            widget:
            **kwargs:

        """
        selectedRows = cast(list, widget.selection)
        if selectedRows:
            # Access the data using the lowercased column name: 'issues'
            selectedValues = SelectedIssues([cast(str, getattr(row, 'issues')) for row in selectedRows])
            self.logger.warning(f'Currently selected: {selectedValues}')
        else:
            self.logger.warning('Nothing selected.')
