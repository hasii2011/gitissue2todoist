
from typing import List
from typing import NewType
from typing import Callable

from abc import ABC
from abc import abstractmethod

from gitissue2todoist.preferences.Preferences import Preferences

from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine

from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import AbbreviatedGitIssue
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import AbbreviatedGitIssues

SelectedIssues = NewType('SelectedIssues', List[AbbreviatedGitIssue])

ItemSelectCallback   = Callable[[], None]
ItemDeselectCallback = Callable[[bool], None]


class IMultiRepositorySelect(ABC):

    def __init__(self, pubSubEngine: IPubSubEngine, itemSelectCallback: ItemSelectCallback, itemDeselectCallback: ItemDeselectCallback):

        self._pubSubEngine:         IPubSubEngine        = pubSubEngine
        self._itemSelectCallback:   ItemSelectCallback   = itemSelectCallback
        self._itemDeselectCallback: ItemDeselectCallback = itemDeselectCallback

        self._preferences: Preferences = Preferences()

    @property
    @abstractmethod
    def selectedIssues(self) -> SelectedIssues:
        """
        Returns: A list of selected issues that were toggled ON.
        """
        pass

    @abstractmethod
    def setValues(self, issues: AbbreviatedGitIssues) -> None:
        """
        Clears existing elements and replaces them with a new set of issues
        """
        pass

    @abstractmethod
    def selectAll(self):
        pass
