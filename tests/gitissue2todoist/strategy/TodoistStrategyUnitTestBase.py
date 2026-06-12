
from typing import List

from gitissue2todoist.strategy.TodoistStrategyTypes import TaskInfo
from gitissue2todoist.strategy.TodoistStrategyTypes import TaskInfoList

from tests.ProjectTestBase import ProjectTestBase


class TodoistStrategyUnitTestBase(ProjectTestBase):
    """
    Base class for the todoist adapter unit tests.  Capture common code here
    """

    EXPECTED_NUMBER_OF_CALLBACKS: int = 6

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self._cbInvoked:     bool = False
        self._cbInvokeCount: int = 0

    def _sampleCallback(self, statusMsg: str):

        self.logger.warning(f'{statusMsg=}')

        self._cbInvoked     = True
        self._cbInvokeCount += 1

    def _createTasksToClone(self) -> TaskInfoList:
        taskList: TaskInfoList = TaskInfoList([])

        taskNames: List[str] = ['TaskOpie', 'TaskGabby10Meows', 'TaskFranny']

        for taskName in taskNames:
            taskInfo: TaskInfo = TaskInfo()

            taskInfo.gitIssueName = taskName
            taskInfo.gitIssueURL  = f'https://{taskName}.org'

            taskList.append(taskInfo)

        return taskList
