
from logging import Logger
from logging import getLogger

from toga import Box

from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.owner.OwnerRepositoriesPanel import OwnerRepositoriesPanel
from gitissue2todoist.owner.OwnerRepositoryIssuesPanel import OwnerRepositoryIssuesPanel

from gitissue2todoist.preferences.Preferences import Preferences
from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine


class OwnerIssuesGitHubPanel(Box):

    def __init__(self, pubSubEngine: IPubSubEngine):

        style: Pack = Pack(direction=COLUMN, flex=1, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT, gap=15)
        super().__init__(style=style)

        self.logger: Logger = getLogger(__name__)

        self._pubSubEngine: IPubSubEngine = pubSubEngine
        self._preferences:  Preferences   = Preferences()
        #
        #  Selection of all a User's repositories &
        #  Selection of the GitHub Issues 'owned' by the user
        #
        self._allUserRepositories: OwnerRepositoriesPanel      = OwnerRepositoriesPanel(pubSubEngine=pubSubEngine)
        repositoryIssues:          OwnerRepositoryIssuesPanel = OwnerRepositoryIssuesPanel(pubSubEngine=pubSubEngine)

        self.add(self._allUserRepositories)
        self.add(repositoryIssues)

    async def loadRepositories(self):
        await self._allUserRepositories.loadRepositories()
