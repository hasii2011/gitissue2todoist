
from typing import Iterator
from typing import List

from logging import Logger
from logging import getLogger

from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Project

from gitissue2todoist.Preferences import Preferences

ProjectName = str
ProjectId   = str

DeleteList = List[ProjectId]


class TodoistCleanup:
    """
    Used by the unit test to clean up bogus project it created

    Usage:

        projectsToDelete = [PROJECT_SAFE_TO_DELETE, BOGUS_SAFE_TO_DELETE, MOCK_REPO_SAFE_TO_DELETE]

        cleanup: TodoistCleanup = TodoistCleanup(projectsToDelete=projectsToDelete)
        cleanup.deleteProjects()

    """
    def __init__(self, projectsToDelete: List[str]):
        """

        Args:
            projectsToDelete:
        """

        self.logger: Logger = getLogger(__name__)

        self._projectsToDelete: List[str] = projectsToDelete

        api_token:     str        = Preferences().todoistAPIToken
        self._todoist: TodoistAPI = TodoistAPI(api_token)

    def deleteProjects(self):

        projectsToDelete: DeleteList = self._getProjectsToDelete()

        for projectId in projectsToDelete:
            self.logger.info(f' Bye Bye --- {projectId=}')
            self._todoist.delete_project(project_id=projectId)

    def _getProjectsToDelete(self) -> DeleteList:

        deleteList: DeleteList = []

        projectIter: Iterator = self._todoist.get_projects()
        for projects in projectIter:
            for p in projects:
                project: Project = p
                if project.name in self._projectsToDelete:
                    self.logger.info(f'{project.name:25} - {project.id=}')
                    deleteList.append(project.id)

        return deleteList

