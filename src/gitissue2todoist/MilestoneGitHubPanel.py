
from typing import cast

from logging import Logger
from logging import getLogger

from toga import Box
from toga import Label
from toga import Selection

from toga.style import Pack
from toga.style.pack import ROW
from toga.style.pack import COLUMN

from gitissue2todoist.Preferences import Preferences
from gitissue2todoist.adapters.HttpxGitHubAdapter import HttpxGitHubAdapter
from gitissue2todoist.adapters.IGitHubAdapter import MilestoneTitles
from gitissue2todoist.adapters.IGitHubAdapter import Slug

from gitissue2todoist.pubsubengine.MessageType import MessageType
from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine


class MilestoneGitHubPanel(Box):

    def __init__(self, pubSubEngine: IPubSubEngine):

        self.logger: Logger = getLogger(__name__)
        super().__init__(style=Pack(direction=ROW))

        self._pubSubEngine:  IPubSubEngine = pubSubEngine
        self._preferences:   Preferences   = Preferences()
        self._githubAdapter: HttpxGitHubAdapter = cast(HttpxGitHubAdapter, None)        # noqa

        repositoryLabel: Label = Label(
            'Repository Milestone Titles',
            style=Pack(margin=(2, 5)),
        )

        self._mileStoneTitlesSelection: Selection = Selection(
            items=[],
            on_change=self._onSelectHandler
        )
        mileStoneTitlesBox: Box = Box(children=[repositoryLabel, self._mileStoneTitlesSelection], style=Pack(direction=COLUMN))

        self.add(mileStoneTitlesBox)

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

        self._mileStoneTitlesSelection.items = milestoneTitles

    def _onSelectHandler(self, arg1):
        pass
