
from typing import cast

from logging import Logger
from logging import getLogger

from sys import platform as sysPlatform

from toga import Box
from toga import Widget
from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.AppCommon import AppCommon
from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.owner.UserRepositoriesPanel import UserRepositoriesPanel
from gitissue2todoist.owner.IMultiRepositorySelect import IMultiRepositorySelect
from gitissue2todoist.owner.MultiRepositoryIssuesPanel import MultiRepositoryIssuesPanel

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
        #  Selection of all the User's repositories
        if sysPlatform == AppCommon.PLATFORM_MAC:
            self._allUserRepositories = UserRepositoriesPanel(pubSubEngine=self._pubSubEngine)
        elif sysPlatform == AppCommon.PLATFORM_IOS:
            assert False, 'We do not have this yet'
        else:
            assert False, 'Unsupported platform'
        #
        # Selection of the GitHub Issues
        #
        repositoryIssues: IMultiRepositorySelect = MultiRepositoryIssuesPanel(pubSubEngine=pubSubEngine)

        self.add(self._allUserRepositories)
        self.add(cast(Widget, repositoryIssues))    # I know what I am doing

    async def loadRepositories(self):
        await self._allUserRepositories.loadRepositories()
