
from logging import Logger
from logging import getLogger
from typing import Callable

from codeallybasic.BasePubSubEngine import BasePubSubEngine
from codeallybasic.BasePubSubEngine import Topic

from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine
from gitissue2todoist.pubsubengine.MessageType import MessageType


class PubSubEngine(IPubSubEngine, BasePubSubEngine):

    def subscribe(self, messageType: MessageType, listener: Callable):
        self._subscribe(topic=self._toTopic(messageType), listener=listener)

    def sendMessage(self, messageType: MessageType, **kwargs):
        self._sendMessage(topic=self._toTopic(messageType), **kwargs)

    def __init__(self):
        super().__init__()
        self.logger: Logger = getLogger(__name__)

    def _toTopic(self, eventType: MessageType) -> Topic:

        topic: Topic = Topic(f'{eventType.value}')
        return topic
