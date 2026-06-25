
from logging import Logger
from logging import getLogger

from sys import platform as sysPlatform

from toga import Box
from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.AppCommon import AppCommon
from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.MobileSingleRepositoryIssues import MobileSingleRepositoryIssues
from gitissue2todoist.allissues.MultiRepositoryIssues import MultiRepositoryIssues

from gitissue2todoist.allissues.UserRepositoriesPanel import UserRepositoriesPanel
from gitissue2todoist.preferences.Preferences import Preferences
from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine


class OwnerIssuesGitHubPanel(Box):

    def __init__(self, pubSubEngine: IPubSubEngine):

        style: Pack = Pack(direction=COLUMN, flex=1, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT, gap=15)
        super().__init__(style=style)

        self.logger: Logger = getLogger(__name__)

        self._pubSubEngine: IPubSubEngine = pubSubEngine
        self._preferences:  Preferences   = Preferences()

        if sysPlatform == AppCommon.PLATFORM_MAC:
            self._allUserRepositories = UserRepositoriesPanel(pubSubEngine=self._pubSubEngine)
        # elif sysPlatform == AppCommon.PLATFORM_IOS:
        #     allUserRepositories = MobileAllUserRepositories(pubSubEngine=self._pubSubEngine)
        else:
            assert False, 'Unsupported platform'

        if self._preferences.debugMobileIssueSelector:
            repositoryIssues = MobileSingleRepositoryIssues(pubSubEngine=self._pubSubEngine)  # temp so I can test it
        else:
            if sysPlatform == AppCommon.PLATFORM_MAC:
                repositoryIssues = MultiRepositoryIssues(pubSubEngine=self._pubSubEngine)
            elif sysPlatform == AppCommon.PLATFORM_IOS:
                repositoryIssues = MobileSingleRepositoryIssues(pubSubEngine=self._pubSubEngine)
            else:
                assert False, 'Unsupported platform'

        self.add(self._allUserRepositories)
        self.add(repositoryIssues)

    async def loadRepositories(self):
        await self._allUserRepositories.loadRepositories()
