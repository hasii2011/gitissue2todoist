
from typing import cast
from typing import Optional

from logging import Logger
from logging import getLogger

from toga.style import Pack

from gitissue2todoist.components.ReadOnlyList import ReadOnlyList
from gitissue2todoist.components.ReadOnlyList import ListItems
from gitissue2todoist.strategy.TodoistStrategyTypes import CloneInformation
from gitissue2todoist.strategy.TodoistStrategyTypes import TaskInfo
from gitissue2todoist.strategy.TodoistStrategyTypes import TaskInfoList


class ClonedIssuesDisplay(ReadOnlyList):

    def __init__(self, widgetId: Optional[str] = None, style: Optional[Pack] = None, cloneInformation: Optional[CloneInformation] = None) -> None:
        """

        Args:
            widgetId:
            style:
            cloneInformation:
        """

        self.logger: Logger = getLogger(__name__)

        items: ListItems = cast(ListItems, None)        # noqa
        if cloneInformation is not None:
            items = self._toItems(tasksToClone=cloneInformation.tasksToClone)

        super().__init__(widgetId=widgetId, style=style, items=items)

        self._cloneInformation: Optional[CloneInformation] = cloneInformation

    def _setClonedInformation(self, cloneInformation: CloneInformation) -> None:

        self._cloneInformation = cloneInformation

        tasksToClone: TaskInfoList = cloneInformation.tasksToClone

        self.items = self._toItems(tasksToClone=tasksToClone)

    clonedInformation = property(fset=_setClonedInformation, doc="Write-only property to set the cloned information in the list.")

    def clearCloneInformation(self):

        self._cloneInformation = cast(CloneInformation, None)     # noqa
        self.clearItems()   # clear the underlying display

    def _toItems(self, tasksToClone: TaskInfoList) -> ListItems:

        listItems: ListItems = ListItems([])
        for tasks in tasksToClone:
            gitIssueInfo: TaskInfo = tasks
            listItems.append(gitIssueInfo.gitIssueName)

        return listItems
