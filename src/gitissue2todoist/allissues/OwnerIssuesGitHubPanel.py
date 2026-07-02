
from logging import Logger
from logging import getLogger

from sys import platform as sysPlatform

from toga import Box
from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.AppCommon import AppCommon
from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.allissues.MobileMultiRepositoryIssuesPanel import MobileMultiRepositoryIssuesPanel
from gitissue2todoist.allissues.MultiRepositoryIssuesPanel import MultiRepositoryIssuesPanel

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
        #
        #  Selection of all the User's repositories
        if sysPlatform == AppCommon.PLATFORM_MAC:
            self._allUserRepositories = UserRepositoriesPanel(pubSubEngine=self._pubSubEngine)
        elif sysPlatform == AppCommon.PLATFORM_IOS:
            pass        # We don't have this yet
        else:
            assert False, 'Unsupported platform'
        #
        # Selection of the GitHub Issues
        #
        # Define the UI container as a Toga Box so it satisfies both Desktop and Mobile types
        repositoryIssues: Box
        
        if self._preferences.debugMobileMultiRepositoryIssues:
            repositoryIssues = MobileMultiRepositoryIssuesPanel(pubSubEngine=self._pubSubEngine)  # temp so I can test it
        else:
            if sysPlatform == AppCommon.PLATFORM_MAC:
                repositoryIssues = MultiRepositoryIssuesPanel(pubSubEngine=self._pubSubEngine)
            elif sysPlatform == AppCommon.PLATFORM_IOS:
                repositoryIssues = MobileMultiRepositoryIssuesPanel(pubSubEngine=self._pubSubEngine)
            else:
                assert False, 'Unsupported platform'

        self.add(self._allUserRepositories)
        # Add the widget directly, no cast needed since Box is a Widget
        self.add(repositoryIssues)

    async def loadRepositories(self):
        await self._allUserRepositories.loadRepositories()
