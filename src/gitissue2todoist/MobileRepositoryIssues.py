
from logging import Logger
from logging import getLogger

from gitissue2todoist.IRepositoryIssues import IRepositoryIssues
from gitissue2todoist.IRepositoryIssues import SelectedIssues
from gitissue2todoist.MobileMultiSelect import MobileMultiSelect


class MobileRepositoryIssues(MobileMultiSelect, IRepositoryIssues):
    def __init__(self):
        self.logger: Logger = getLogger(__name__)
        
        super().__init__()

    @property
    def selectedIssues(self) -> SelectedIssues:
        """

        Returns: A list of selected issues that  were toggled ON.
        """

        selectedValues: SelectedIssues = SelectedIssues(list(self.selectedValues))

        # for switch in self._switchWidgets:
        #     if switch.value:
        #         selectedValues.append(switch.text)
        #
        return selectedValues
