
from logging import Logger
from logging import getLogger
from typing import Dict
from typing import List
from typing import NewType

from toga import Table
from toga.style import Pack

from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import Slug
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import Slugs
from gitissue2todoist.owner.IRepositoryList import IRepositoryList
from gitissue2todoist.owner.IRepositoryList import RepositoryDeselectedCb
from gitissue2todoist.owner.IRepositoryList import RepositorySelectedCb

from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine

REPOSITORY_TITLE_KEY: str = 'repository'

RepoDataRow = NewType('RepoDataRow', Dict[str, Slug])
RepoData    = NewType('RepoData',  List[RepoDataRow])
IssueKey    = NewType('IssueKey', str)

REPO_SLUG_KEY:  IssueKey = IssueKey('repository')
# ISSUE_TITLE_KEY: IssueKey = IssueKey('issueTitle')

class RepositoryList(Table, IRepositoryList):

    def __init__(self, pubSubEngine: IPubSubEngine, repositorySelectedCb: RepositorySelectedCb, repositoryDeselectedCb: RepositoryDeselectedCb):

        super().__init__(
            columns=[REPOSITORY_TITLE_KEY],
            multiple_select=True,
            show_headings=False,
            style=Pack(flex=1),
            on_select=self._onRepositorySelected
        )
        self.logger: Logger = getLogger(__name__)
        IRepositoryList.__init__(self, pubSubEngine=pubSubEngine, repositorySelectedCb=repositorySelectedCb, repositoryDeselectedCb=repositoryDeselectedCb)

    @property
    def selectedRepositories(self) -> Slugs:
        """
        Returns: A list of selected repositories
        """
        repositories: Slugs = Slugs([])

        return repositories

    def setValues(self, slugs: Slugs) -> None:

        if slugs is not None:

            self.logger.info(f'Setting {len(slugs)} repositories')

            issueData: RepoData = RepoData([])
            for s in slugs:

                slug: Slug = s
                repoDataRow: RepoDataRow = RepoDataRow({})

                repoDataRow[REPOSITORY_TITLE_KEY] = slug

                issueData.append(repoDataRow)

            self.data = issueData

    def selectAll(self):
        """
        Access the underlying native macOS NSTableView and call selectAll_

        Safely grab the native NSTableView and trigger the OS-level 'Select All' action

        This OSX specific

        """
        # noinspection PyProtectedMember
        self._impl.native.documentView.selectAll_(None)

    def deSelectAll(self):
        """
        Safely grab the native NSTableView and trigger the OS-level 'Select All' action

        This OSX specific
            The None parameter is being passed as the sender argument to the underlying macOS Objective-C method.
            The sender represents the UI component (like a button, menu item, or keyboard shortcut) that triggered the action.
            Passing None translates to nil in Objective-C
            Safe way to tell macOS, I am triggering this action programmatically; there is no sender.

        """
        self._impl.native.documentView.deselectAll_(None)

    # noinspection PyUnusedLocal
    def _onRepositorySelected(self, widget):
        self._repositorySelectedCb()
