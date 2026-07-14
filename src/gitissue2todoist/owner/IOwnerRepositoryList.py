
from typing import Callable

from abc import ABC
from abc import abstractmethod

from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import Slugs

from gitissue2todoist.preferences.Preferences import Preferences
from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine

RepositorySelectedCb   = Callable[[], None]
RepositoryDeselectedCb = Callable[[bool], None]

class IOwnerRepositoryList(ABC):

    def __init__(self, pubSubEngine: IPubSubEngine):

        self._pubSubEngine:           IPubSubEngine          = pubSubEngine
        self._preferences:  Preferences   = Preferences()

    @property
    @abstractmethod
    def selectedRepositories(self) -> Slugs:
        """
        Returns: A list of selected repositories
        """
        pass

    @abstractmethod
    def setRepositories(self, slugs: Slugs) -> None:
        """
        Clears existing elements and replaces them with a new set of issues
        """
        pass

    @abstractmethod
    def selectAll(self):
        pass

    @abstractmethod
    def deSelectAll(self):
        pass
