
from logging import Logger
from logging import getLogger

from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import Slug
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import Slugs

from gitissue2todoist.components.MobileMultiSelect import MobileMultiSelect
from gitissue2todoist.components.MobileMultiSelect import MultiSelectValues
from gitissue2todoist.components.MobileMultiSelect import SelectedValues

from gitissue2todoist.owner.IOwnerRepositoryList import IOwnerRepositoryList
from gitissue2todoist.owner.IOwnerRepositoryList import RepositoryDeselectedCb
from gitissue2todoist.owner.IOwnerRepositoryList import RepositorySelectedCb

from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine


class MobileOwnerRepositoryList(MobileMultiSelect, IOwnerRepositoryList):

    def __init__(self, pubSubEngine: IPubSubEngine, repositorySelectedCb: RepositorySelectedCb, repositoryDeselectedCb: RepositoryDeselectedCb):
        """

        Args:
            pubSubEngine:
            repositorySelectedCb:
            repositoryDeselectedCb:
        """

        self.logger: Logger = getLogger(__name__)

        super().__init__(itemSelectCallback=repositorySelectedCb, itemDeselectCallback=repositoryDeselectedCb)

        IOwnerRepositoryList.__init__(self, pubSubEngine=pubSubEngine)

    @property
    def selectedRepositories(self) -> Slugs:
        """
        TODO: Need to implement this for the switches

        Returns: A list of selected repositories
        """

        selectedValues: SelectedValues = self.selectedValues
        #
        #  LEARN THIS IDIOM !!!
        # repositories: Slugs = Slugs([])
        # for val in selectedValues:
        #     repositories.append(Slug(val))
        #
        # I am so Pythonic, I can puke
        repositories: Slugs = Slugs([Slug(val) for val in selectedValues])
        return repositories

    def setRepositories(self, slugs: Slugs) -> None:
        multiSelectValues: MultiSelectValues= MultiSelectValues([])

        for s in slugs:
            slug: Slug = s
            multiSelectValues.append(slug)

        self.setValues(values=multiSelectValues)

    def deSelectAll(self):
        """
        TODO:

        """
        pass
