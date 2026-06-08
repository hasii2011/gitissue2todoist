
from logging import Logger
from logging import getLogger
from typing import cast

from gitissue2todoist.IRepositoryIssues import IRepositoryIssues
from gitissue2todoist.IRepositoryIssues import SelectedIssues
from gitissue2todoist.MobileMultiSelect import MobileMultiSelect
from gitissue2todoist.MobileMultiSelect import MultiSelectValues
from gitissue2todoist.adapters.IGitHubAdapter import Slug
from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine
from gitissue2todoist.pubsubengine.MessageType import MessageType


class MobileRepositoryIssues(MobileMultiSelect, IRepositoryIssues):

    def __init__(self, pubSubEngine: IPubSubEngine):

        self.logger: Logger = getLogger(__name__)

        super().__init__()
        IRepositoryIssues.__init__(self, pubSubEngine=pubSubEngine)

        self._pubSubEngine.subscribe(messageType=MessageType.LOAD_ISSUES, listener=self._loadIssuesListener)

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

    def _loadIssuesListener(self, repositoryName: Slug, milestoneTitle: str):

        issues = self._getAssociatedIssues(repositoryName=repositoryName, milestoneTitle=milestoneTitle)

        self.setValues(MultiSelectValues(cast(list, issues)))
