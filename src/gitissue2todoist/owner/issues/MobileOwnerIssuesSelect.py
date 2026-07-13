
from typing import Any
from typing import Dict
from typing import List

from logging import Logger
from logging import getLogger

import textwrap

from toga import Box
from toga import Label
from toga import Switch
from toga import ScrollContainer

from toga.style import Pack
from toga.style.pack import ROW
from toga.style.pack import COLUMN

from gitissue2todoist.owner.IOwnerIssuesSelect import IOwnerIssuesSelect
from gitissue2todoist.owner.IOwnerIssuesSelect import ItemDeselectCallback
from gitissue2todoist.owner.IOwnerIssuesSelect import ItemSelectCallback
from gitissue2todoist.owner.IOwnerIssuesSelect import SelectedIssues

from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine

from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import AbbreviatedGitIssue
from gitissue2todoist.adapters.IAsyncHttpxGitHubAdapter import AbbreviatedGitIssues

ISSUE_MAX_TITLE_WIDTH: int = 40

REPO_LABEL_FIXED_WIDTH:  int = 100  # Fixed width so switches align nicely
REPO_LABEL_RIGHT_MARGIN: int = 10


class MobileOwnerIssuesSelect(ScrollContainer, IOwnerIssuesSelect):
    """
    iOS compatible component for selecting issues across multiple repositories.
    Replaces the toga.Table used on the desktop application.
    """
    def __init__(self, pubSubEngine: IPubSubEngine, itemSelectCallback: ItemSelectCallback, itemDeselectCallback: ItemDeselectCallback):
        """

        Args:
            pubSubEngine:
            itemSelectCallback:
            itemDeselectCallback:
        """
        self.logger:        Logger        = getLogger(__name__)
        self._pubSubEngine: IPubSubEngine = pubSubEngine

        super().__init__(style=Pack(flex=1))
        IOwnerIssuesSelect.__init__(self, pubSubEngine=pubSubEngine, itemSelectCallback=itemSelectCallback, itemDeselectCallback=itemDeselectCallback)


        self._listContainer: Box = Box(style=Pack(direction=COLUMN, margin=10))
        self.content = self._listContainer

        self._switchWidgets: List[Dict[str, Any]] = []

    def _switchChangedHandler(self, widget: Switch) -> None:
        if widget.value:
            self._itemSelectCallback()
        else:
            hasNoSelections: bool = (len(self.selectedIssues) == 0)
            self._itemDeselectCallback(hasNoSelections)

    @property
    def selectedIssues(self) -> SelectedIssues:
        """
        Returns: A list of selected issues that were toggled ON.
        """
        selectedIssues: SelectedIssues = SelectedIssues([])

        for item in self._switchWidgets:
            switchWidget: Switch = item['switch']
            gitIssue: AbbreviatedGitIssue = item['issue']
            if switchWidget.value:
                selectedIssues.append(gitIssue)

        return selectedIssues

    def setValues(self, issues: AbbreviatedGitIssues) -> None:
        """
        Clears existing elements and replaces them with a new set of issues
        """

        # Clear existing rows from the UI container
        for item in self._switchWidgets:
            clearRowBox: Box = item['rowBox']
            self._listContainer.remove(clearRowBox)
            
        # 2. Clear our tracking list
        self._switchWidgets.clear()

        # Build and add the new row elements
        for gitIssue in issues:
            # Create a horizontal box for each issue row
            rowBox: Box = Box(style=Pack(direction=ROW, margin_bottom=10))

            # Strip off the username
            userNameRepo = gitIssue.slug.split('/')
            # Label showing the repository slug
            repoLabel: Label = Label(
                text=userNameRepo[1],
                style=Pack(margin_right=REPO_LABEL_RIGHT_MARGIN, width=REPO_LABEL_FIXED_WIDTH)
            )

            displayTitle = self._elideIssueTitle(gitIssue.issueTitle)
            # Switch with the issue title
            selectionSwitch: Switch = Switch(
                text=displayTitle,
                on_change=self._switchChangedHandler
            )

            rowBox.add(repoLabel)
            rowBox.add(selectionSwitch)

            self._switchWidgets.append({
                'rowBox': rowBox,
                'switch': selectionSwitch,
                'issue': gitIssue
            })
            self._listContainer.add(rowBox)

        # Force the container to recalculate its layout with the new items
        self._listContainer.refresh()

    def selectAll(self):
        for w in self._switchWidgets:
            switch: Switch = w['switch']
            switch.value = True

    def _elideIssueTitle(self, issueTitle: str) -> str:
        """
        Use textwrap to shorten it cleanly; avoids cutting words in half

        Args:
            issueTitle:

        Returns:  An elided string
        """
        displayTitle: str = textwrap.shorten(
            text=issueTitle,
            width=ISSUE_MAX_TITLE_WIDTH,
            placeholder='...'
        )
        return displayTitle
