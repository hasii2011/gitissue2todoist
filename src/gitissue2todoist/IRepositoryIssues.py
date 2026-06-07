from abc import abstractmethod
from typing import List
from typing import NewType

from abc import ABC

SelectedIssues    = NewType('SelectedIssues', List[str])

class IRepositoryIssues(ABC):

    @property
    @abstractmethod
    def selectedIssues(self) -> SelectedIssues:
        """
        Returns: A list of selected values
        """
        pass
