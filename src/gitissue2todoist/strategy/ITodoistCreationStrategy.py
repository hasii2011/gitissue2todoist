
from typing import Callable

from abc import ABC
from abc import abstractmethod

from gitissue2todoist.strategy.TodoistStrategyTypes import CloneInformation
from gitissue2todoist.strategy.TodoistStrategyTypes import TodoistProgressCB


class ITodoistCreationStrategy(ABC):
    """
    TODO:  Once I add more code I will ask Gemini to generate me some
    documentation that I can then edit
    """

    def __init__(self):
        pass

    @abstractmethod
    def createTasks(self, info: CloneInformation, progressCb: TodoistProgressCB):
        """
        Abstract method;  Subclass must implement
        Args:
            info:           The Clone information from the GitHub calls
            progressCb:     The callback to report information
        """
        pass

    @abstractmethod
    def _determineTopLevelProjectId(self, info: CloneInformation, progressCb: TodoistProgressCB) -> str:
        """
        Either gets a project ID from the repo name or one for the user specified project

        Args:
            info:  The cloned information
            progressCb: A progress callback to return status

        Returns:  An appropriate parent ID for newly created tasks
        """
        pass
