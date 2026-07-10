
from logging import Logger
from logging import getLogger

from toga import ScrollContainer
from toga.style import Pack

from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import Slugs
from gitissue2todoist.owner.IRepositoryList import IRepositoryList
from gitissue2todoist.owner.IRepositoryList import RepositoryDeselectedCb
from gitissue2todoist.owner.IRepositoryList import RepositorySelectedCb

from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine


class MobileRepositoryList(ScrollContainer, IRepositoryList):

    def __init__(self, pubSubEngine: IPubSubEngine, repositorySelectedCb: RepositorySelectedCb, repositoryDeselectedCb: RepositoryDeselectedCb):

        self.logger: Logger = getLogger(__name__)

        super().__init__(style=Pack(flex=1))

        IRepositoryList.__init__(self, pubSubEngine=pubSubEngine, repositorySelectedCb=repositorySelectedCb, repositoryDeselectedCb=repositoryDeselectedCb)

    @property
    def selectedRepositories(self) -> Slugs:
        """
        Returns: A list of selected repositories
        """
        repositories: Slugs = Slugs([])

        return repositories

    def setValues(self, slugs: Slugs) -> None:
        pass

    def deSelectAll(self):
        pass

    def selectAll(self):
        pass
