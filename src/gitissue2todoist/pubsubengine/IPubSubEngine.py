
from typing import Callable

from abc import ABC
from abc import abstractmethod

from gitissue2todoist.pubsubengine.MessageType import MessageType


class IPubSubEngine(ABC):
    """
    Implement an interface using the standard Python library.  I found zope too abstract
    and python interface could not handle subclasses;
    We will register a topic on a eventType.frameId.DiagramName
    """
    @abstractmethod
    def subscribe(self, messageType: MessageType, listener: Callable):
        pass

    @abstractmethod
    def sendMessage(self, messageType: MessageType, **kwargs):
        pass
