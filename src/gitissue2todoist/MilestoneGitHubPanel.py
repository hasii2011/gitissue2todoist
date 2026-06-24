
from typing import cast

from logging import Logger
from logging import getLogger

from sys import platform as sysPlatform

from toga import Box
from toga import Label
from toga import Widget
from toga import Selection

from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.AppCommon import AppCommon
from gitissue2todoist.IRepositoryIssues import IRepositoryIssues
from gitissue2todoist.SingleRepositoryIssues import SingleRepositoryIssues
from gitissue2todoist.MobileSingleRepositoryIssues import MobileSingleRepositoryIssues

from gitissue2todoist.preferences.Preferences import Preferences
from gitissue2todoist.UICommon import UICommon

from gitissue2todoist.adapters.IGitHubAdapter import Slug
from gitissue2todoist.adapters.IGitHubAdapter import MilestoneTitles
from gitissue2todoist.adapters.HttpxGitHubAdapter import HttpxGitHubAdapter

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
            on_change=self._onMilestoneSelectedHandler
        )
        mileStonesBox: Box = Box(children=[mileStonesLabel, self._mileStoneSelection], style=Pack(direction=COLUMN))

        issuesLabel:      Label = UICommon.createStandardSectionTitle('Issues')
        repositoryIssues: IRepositoryIssues

        if self._preferences.debugMobileIssueSelector:
            repositoryIssues = MobileSingleRepositoryIssues(pubSubEngine=self._pubSubEngine)  # temp so I can test it
        else:
            if sysPlatform == AppCommon.PLATFORM_MAC:
                repositoryIssues = SingleRepositoryIssues(pubSubEngine=self._pubSubEngine)
            elif sysPlatform == AppCommon.PLATFORM_IOS:
                repositoryIssues = MobileSingleRepositoryIssues(pubSubEngine=self._pubSubEngine)
            else:
                assert False, 'Unsupported platform'

        issuesBox: Box = Box(
            children=[issuesLabel, cast(Widget, repositoryIssues)],
            style=Pack(direction=COLUMN, flex=1)
        )

        self.add(mileStonesBox)
        self.add(issuesBox)

        self._pubSubEngine.subscribe(messageType=MessageType.SELECTED_REPOSITORY_CHANGED, listener=self._selectedRepositoryChangedListener)

        self._repositoryName: Slug = Slug('')         # set by ._loadMilestonesListener

    def _selectedRepositoryChangedListener(self, repositoryName: Slug):
        """
        We need to load some new milestones

        Delay getting the GitHub Adapter as long as possible in case the authentication token has
        changed

        Args:
            repositoryName:

        """
        self._repositoryName = repositoryName
        self.logger.info(f'Time to load milestones for {repositoryName}')
        self._githubAdapter = HttpxGitHubAdapter(authenticationToken=self._preferences.gitHubAPIToken)

        milestoneTitles: MilestoneTitles = self._githubAdapter.getMileStoneTitles(repoName=repositoryName)

        self._mileStoneSelection.items = milestoneTitles

    def _onMilestoneSelectedHandler(self, widget):

        selection: Selection = cast(Selection, widget)
        mileStone: str = cast(str, selection.value)

        self._pubSubEngine.sendMessage(messageType=MessageType.SELECTED_MILESTONE_CHANGED, repositoryName=self._repositoryName, milestoneTitle=mileStone)
        UICommon.popDownPicker(selection=self._mileStoneSelection)

