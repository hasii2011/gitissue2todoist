
from logging import Logger
from logging import getLogger

from toga import Box
from toga import Table
from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.UICommon import UICommon
from gitissue2todoist.adapters.IGitHubAdapter import Slugs
from gitissue2todoist.preferences.Preferences import Preferences
from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine
from gitissue2todoist.pubsubengine.MessageType import MessageType


class MultiRepositoryIssues(Box):

    def __init__(self, pubSubEngine: IPubSubEngine):

        style: Pack = Pack(direction=COLUMN, flex=1, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT, gap=15)
        super().__init__(style=style)

        self.logger: Logger = getLogger(__name__)

        self._pubSubEngine: IPubSubEngine = pubSubEngine
        self._preferences:  Preferences   = Preferences()

        self._issueTable: Table = Table(
            columns=['Repository', 'Issue'],
            multiple_select=True,
            show_headings=False,
            style=Pack(flex=1),
            data=[
                ('hasii2011/pytrek', 'Game is AI smart'),
                ('hasii2011/umldiagrammer', 'True round trip engineering'),
                ('hasii2011/umlshapes', 'Super smart shapes'),
            ]
        )

        self.add(self._issueTable)

        # self._pubSubEngine.subscribe(MessageType.MULTIPLE_REPOSITORIES_SELECTED, repositories=selectedRepositories)
        self._pubSubEngine.subscribe(MessageType.RETRIEVE_OWNER_ISSUES, listener=self._retrieveOwnerIssuesListener)


    def _retrieveOwnerIssuesListener(self, repositories: Slugs):
        pass
