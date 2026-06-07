
from typing import cast

from logging import Logger
from logging import getLogger

from toga import Box
from toga import Label
from toga import Selection

from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.MobileMultiSelect import MobileMultiSelect
from gitissue2todoist.MobileMultiSelect import MultiSelectValues
from gitissue2todoist.Preferences import Preferences
from gitissue2todoist.RepositoryIssues import RepositoryIssues
from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.adapters.HttpxGitHubAdapter import HttpxGitHubAdapter
from gitissue2todoist.adapters.IGitHubAdapter import MilestoneTitles
from gitissue2todoist.adapters.IGitHubAdapter import Slug

from gitissue2todoist.pubsubengine.MessageType import MessageType
from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine


class MilestoneGitHubPanel(Box):

    def __init__(self, pubSubEngine: IPubSubEngine):

        self.logger: Logger = getLogger(__name__)
        style: Pack = Pack(direction=COLUMN, flex=1, margin_left=UICommon.MARGIN_LEFT, margin_right=UICommon.MARGIN_RIGHT, gap=15)
        super().__init__(style=style)

        self._pubSubEngine:  IPubSubEngine = pubSubEngine
        self._preferences:   Preferences   = Preferences()
        self._githubAdapter: HttpxGitHubAdapter = cast(HttpxGitHubAdapter, None)        # noqa

        mileStonesLabel: Label = UICommon.createStandardSectionTitle('Repository Milestone Titles')
        self._mileStoneSelection: Selection = Selection(
            items=[],
            on_change=self._onSelectHandler
        )
        mileStonesBox: Box = Box(children=[mileStonesLabel, self._mileStoneSelection], style=Pack(direction=COLUMN))

        issuesLabel:      Label = UICommon.createStandardSectionTitle('Issues')
        repositoryIssues: RepositoryIssues = RepositoryIssues()
        # repositoryIssues: MobileMultiSelect = MobileMultiSelect()
        # repositoryIssues.setValues(
        #     MultiSelectValues([
        #         'hasii2011/pytrek',
        #         'hasii2011/py2appsigner',
        #         'hasii2011/umldiagrammer',
        #         'hasii2011/umlmodel',
        #         'hasii2011/umlio',
        #         'hasii2011/umlshapes',
        #     ])
        # )

        issuesBox: Box = Box(children=[issuesLabel, repositoryIssues], style=Pack(direction=COLUMN, flex=1))

        self.add(mileStonesBox)
        self.add(issuesBox)

        self._pubSubEngine.subscribe(messageType=MessageType.LOAD_MILESTONES, listener=self._loadMilestonesListener)

    def _loadMilestonesListener(self, repositoryName: Slug):
        """
        Delay getting the GitHub Adapter as long as possible in case the authentication token has
        changed

        Args:
            repositoryName:

        """

        self.logger.info(f'Time to load milestones for {repositoryName}')
        self._githubAdapter = HttpxGitHubAdapter(authenticationToken=self._preferences.gitHubAPIToken)

        milestoneTitles: MilestoneTitles = self._githubAdapter.getMileStoneTitles(repoName=repositoryName)

        self._mileStoneSelection.items = milestoneTitles

    def _onSelectHandler(self, arg1):
        pass
