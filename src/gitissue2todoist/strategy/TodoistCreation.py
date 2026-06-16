from typing import Callable

from logging import Logger
from logging import getLogger

from httpx import HTTPStatusError

from gitissue2todoist.general.exceptions.AdapterAuthenticationError import AdapterAuthenticationError
from gitissue2todoist.strategy.TodoistOwnerIssues import TodoistOwnerIssues
from gitissue2todoist.strategy.TodoistStrategyTypes import CloneInformation
from gitissue2todoist.strategy.ITodoistCreationStrategy import ITodoistCreationStrategy
from gitissue2todoist.strategy.TodoistCreateByRepository import TodoistCreateByRepository
from gitissue2todoist.strategy.TodoistCreateSingleProject import TodoistCreateSingleProject
from gitissue2todoist.strategy.TodoistTaskCreationStrategy import TodoistTaskCreationStrategy

from gitissue2todoist.Preferences import Preferences

UNAUTHORIZED_CODE: int = 401
FORBIDDEN_CODE:    int = 403
AUTHORIZED_FAILED: str = 'Authorization to todoist API failed.  Perhaps, the authorization token is invalid'

class TodoistCreation:
    def __init__(self):
        self.logger: Logger = getLogger(__name__)

        preferences: Preferences = Preferences()

        if preferences.taskCreationStrategy == TodoistTaskCreationStrategy.PROJECT_BY_REPOSITORY:
            self._taskCreationStrategy: ITodoistCreationStrategy = TodoistCreateByRepository()
        elif preferences.taskCreationStrategy == TodoistTaskCreationStrategy.SINGLE_TODOIST_PROJECT:
            self._taskCreationStrategy = TodoistCreateSingleProject()
        elif preferences.taskCreationStrategy == TodoistTaskCreationStrategy.ALL_ISSUES_ASSIGNED_TO_USER:
            self._taskCreationStrategy = TodoistOwnerIssues()
        else:
            assert False, 'Unknown task creation strategy'

    def createTasks(self, info: CloneInformation, progressCb: Callable):
        try:
            self._taskCreationStrategy.createTasks(info=info, progressCb=progressCb)
        except HTTPStatusError as e:
            self.logger.error(f'{e}')
            if e.response.status_code == UNAUTHORIZED_CODE or e.response.status_code == FORBIDDEN_CODE:
                raise AdapterAuthenticationError(AUTHORIZED_FAILED) from e
            else:
                raise e
