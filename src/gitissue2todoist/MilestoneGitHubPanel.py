
from logging import Logger
from logging import getLogger

from toga import Box
from toga import Label
from toga import Table
from toga.style import Pack
from toga.style.pack import ROW
from toga.style.pack import COLUMN

from gitissue2todoist.Preferences import Preferences
from gitissue2todoist.adapters.GithubAdapter import GithubAdapter


class MilestoneGitHubPanel(Box):
    def __init__(self):

        self.logger: Logger = getLogger(__name__)
        super().__init__(style=Pack(direction=ROW))

        self._preferences: Preferences = Preferences()
        self._githubAdapter: GithubAdapter = GithubAdapter(
            userName=self._preferences.gitHubUserName,
            authenticationToken=self._preferences.gitHubAPIToken
        )

        repositoryLabel: Label = Label(
            'Repository Milestone Titles',
            style=Pack(margin=(2, 5)),
        )

        mileStoneTitlesTable: Table = Table(
            columns=['Issues'],
            data=[
                'Alice',
                'Bob',
                'Charlie',
                'Diana'
            ],
            multiple_select=True,
            show_headings=False,
            on_select=self._onSelectHandler
        )
        mileStoneTitlesBox: Box = Box(children=[repositoryLabel, mileStoneTitlesTable], style=Pack(direction=COLUMN))

        self.add(mileStoneTitlesBox)


    def _onSelectHandler(self, arg1):
        pass
