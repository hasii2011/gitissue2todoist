
from typing import cast
from typing import Iterator

from abc import ABCMeta

from logging import INFO
from logging import Logger
from logging import getLogger

from todoist_api_python.api import TodoistAPI
from todoist_api_python.api_async import TodoistAPIAsync

from todoist_api_python.models import Task
from todoist_api_python.models import Project
from todoist_api_python.models import Comment

from gitissue2todoist.strategy.ITodoistCreationStrategy import ITodoistCreationStrategy

from gitissue2todoist.general.GitHubURLOption import GitHubURLOption

from gitissue2todoist.preferences.Preferences import Preferences
from gitissue2todoist.preferences.SecureTokenManager import SecureTokenManager

from gitissue2todoist.AppCommon import AppCommon

from gitissue2todoist.strategy.TodoistStrategyTypes import CloneInformation
from gitissue2todoist.strategy.TodoistStrategyTypes import TodoistProgress
from gitissue2todoist.strategy.TodoistStrategyTypes import TodoistProgressCB

from gitissue2todoist.strategy.TodoistStrategyTypes import Tasks
from gitissue2todoist.strategy.TodoistStrategyTypes import TaskId
from gitissue2todoist.strategy.TodoistStrategyTypes import TaskInfo
from gitissue2todoist.strategy.TodoistStrategyTypes import TaskName
from gitissue2todoist.strategy.TodoistStrategyTypes import ProjectName
from gitissue2todoist.strategy.TodoistStrategyTypes import TaskNameMap
from gitissue2todoist.strategy.TodoistStrategyTypes import ProjectDictionary

from gitissue2todoist.general.exceptions.NoteCreationError import NoteCreationError


class AbstractTodoistStrategy(ITodoistCreationStrategy, metaclass=ABCMeta):
    """
    TODO:  Once I add more code I will ask Gemini to generate me some
    documentation that I can then edit
    """

    clsLogger: Logger = getLogger(__name__)

    def __init__(self):
        """
        Initialize common protected properties
        """
        super().__init__()

        self._preferences: Preferences = Preferences()

        apiToken: str = AppCommon.getAuthenticationToken(
            fallbackMessage=AppCommon.NO_TODOIST_TOKEN_MESSAGE,
            tokenRetrievalMethod=lambda: SecureTokenManager().todoistToken
        )
            
        self._todoist:      TodoistAPI      = TodoistAPI(apiToken)
        self._todoistAsync: TodoistAPIAsync = TodoistAPIAsync(apiToken)

        self._devTasks:          Tasks             = []
        self._projectDictionary: ProjectDictionary = {}

        self._completedTasks: int = 0
        self._totalTasks:     int = 0

    def _createTaskItem(self, taskInfo: TaskInfo, projectId: str, parentTaskItem: Task, progressCb: TodoistProgressCB):
        """
        Create a new task if it does not already exist in Todoist
        Assumes self._devTasks has all the project's tasks

        Args:
            taskInfo:       The task (with information) to potentially create
            projectId:      Project id of potential task
            parentTaskItem: parent item if task needs to be created
            progressCb:     Progress callback
        """
        assert self._devTasks is not None, 'Internal error should at least be empty'

        todoist: TodoistAPI = self._todoist

        foundTaskItem: Task = cast(Task, None)      # noqa
        devTasks:      Tasks = self._devTasks
        for devTask in devTasks:
            taskItem: Task = devTask
            # Might have name embedded as URL
            # if taskInfo.gitIssueName in taskItem['content']:
            if taskInfo.gitIssueName in taskItem.content:
                foundTaskItem = taskItem
                break
        #
        # To create subtasks first create in project then move them to the milestone task
        #
        if foundTaskItem is None:
            option: GitHubURLOption = self._preferences.gitHubURLOption
            match option:
                case GitHubURLOption.DoNotAdd:
                    todoist.add_task(project_id=projectId,
                                     parent_id=parentTaskItem.id,
                                     content=taskInfo.gitIssueName)

                case GitHubURLOption.AddAsDescription:
                    todoist.add_task(project_id=projectId,
                                     parent_id=parentTaskItem.id,
                                     content=taskInfo.gitIssueName,
                                     description=taskInfo.gitIssueURL)

                case GitHubURLOption.AddAsComment:
                    task: Task = todoist.add_task(project_id=projectId,
                                                  parent_id=parentTaskItem.id,
                                                  content=taskInfo.gitIssueName)
                    comment: Comment = todoist.add_comment(task_id=task.id, content=taskInfo.gitIssueURL)
                    AbstractTodoistStrategy.clsLogger.info(f'Comment added: {comment}')

                case GitHubURLOption.HyperLinkedTaskName:
                    linkedTaskName: str = f'[{taskInfo.gitIssueName}]({taskInfo.gitIssueURL})'
                    todoist.add_task(project_id=projectId,
                                     parent_id=parentTaskItem.id,
                                     content=linkedTaskName)
                case _:
                    self.clsLogger.error(f'Unknown URL option: {option}')       # noqa

            self._reportProgress(progressCb, f'Created task: {taskInfo.gitIssueName}', incCompletedTskCnt=True)

    def _addNoteToTask(self, itemId: str, noteContent: str) -> Comment:
        """
        Currently only support creating text notes

        Args:
            itemId:         The id of the task to add this note to
            noteContent:    The content of the note

        Returns:  The created Note time
        """
        todoist: TodoistAPI = self._todoist
        try:
            newComment = todoist.add_comment(task_id=itemId, content=noteContent)
        except Exception as e:
            eDict = e.args[1]
            eMsg: str = eDict['error']
            eCode: int = eDict['error_code']

            noteCreationError: NoteCreationError = NoteCreationError()
            noteCreationError.message   = eMsg
            noteCreationError.errorCode = eCode

            raise noteCreationError

        return newComment

    def _getProjectIdOfSingleProjectName(self, progressCb: TodoistProgressCB):
        """
        Some Todoist strategies place all the subtasks in a single project.  This common method
        returns the ID of that preferred project.

        Args:
            progressCb:  The progress reporting callback

        """
        self._reportProgress(progressCb, f'Using single project: {self._preferences.todoistProjectName}')

        self._projectDictionary = self._getCurrentProjects()

        projectName: ProjectName = ProjectName(self._preferences.todoistProjectName)
        projectId:   str         = self._getProjectId(projectName=projectName, projectDictionary=self._projectDictionary)

        return projectId

    def _getProjectId(self, projectName: ProjectName, projectDictionary: ProjectDictionary) -> str:
        """
        Either returns an existing project ID or creates a project and
        Args:
            projectName:        The project name we are searching for
            projectDictionary:  A pre-built dictionary

        Returns:
            A todoist project id
        """

        if projectName in projectDictionary:
            project: Project = projectDictionary[projectName]
            self.clsLogger.info(f'Using project: {projectName}')
        else:
            project = self._createProject(projectName)
            self.clsLogger.info(f'Created project: {projectName}')

        projectId: str = project.id

        return projectId

    def _getIdForRepoName(self, projectId: str, repoName: str) -> str:
        """
        Will either find a repo in the "development" task or create it in the "development" task
        Args:
            projectId:
            repoName:

        Returns: The Repo ID

        """
        taskIterator: Iterator = self._todoist.get_tasks(project_id=projectId)
        taskList:     Tasks    = self._todoistIteratorToTasks(taskIterator=taskIterator)
        itemNames: TaskNameMap = self._createTaskNameMap(taskList=taskList)

        # Either use the id of the one found or create it
        if repoName in itemNames:
            repoId: str = itemNames[TaskName(repoName)]
        else:
            todoist:  TodoistAPI = self._todoist
            repoTask: Task = todoist.add_task(project_id=projectId, content=repoName, description='Repo task created by GitIssue2Todoist')

            repoId = repoTask.id

        return repoId

    def _getCurrentProjects(self) -> ProjectDictionary:

        todoist: TodoistAPI = self._todoist

        iterProjectLists:  Iterator          = todoist.get_projects()
        projectDictionary: ProjectDictionary = {}

        for projectList in iterProjectLists:

            for aProject in projectList:
                project: Project = cast(Project, aProject)
                projectName: ProjectName = ProjectName(project.name)
                projectId:   str         = project.id

                AbstractTodoistStrategy.clsLogger.debug(f'{projectName:12} - {projectId=}')

                projectDictionary[projectName] = project

        return projectDictionary

    def _createProject(self, name: ProjectName) -> Project:

        project: Project = self._todoist.add_project(name=name)
        self.clsLogger.info(f'New project: {project.id}')
        return project

    def _synchronize(self, progressCb):
        # TODO: This method is unneeded
        self._reportProgress(progressCb, 'Done')

    def _infoLogCloneInformation(self, info: CloneInformation, progressCb: TodoistProgressCB):

        if AbstractTodoistStrategy.clsLogger.isEnabledFor(INFO):
            AbstractTodoistStrategy.clsLogger.info(f'{progressCb.__name__}')

            AbstractTodoistStrategy.clsLogger.info(f'{info.repositoryTask=} {info.milestoneNameTask=}')
            for t in info.tasksToClone:
                taskInfo: TaskInfo = t
                AbstractTodoistStrategy.clsLogger.info(f'{taskInfo.gitIssueName}')

    def _createTaskNameMap(self, taskList: Tasks) -> TaskNameMap:
        """

        Args:
            taskList:   An iterator for lists of tasks

        Returns: dictionary taskName -> id
        """
        taskMap: TaskNameMap = TaskNameMap({})

        for item in taskList:
            task:     Task     = item
            itemName: TaskName = TaskName(task.content)
            itemId:   TaskId   = TaskId(task.id)

            taskMap[itemName] = itemId
            AbstractTodoistStrategy.clsLogger.debug(f'TaskName: {task.content}')

        return taskMap

    def _todoistIteratorToTasks(self, taskIterator) -> Tasks:

        unpackedList: Tasks = []
        for taskList in taskIterator:
            for task in taskList:
                unpackedList.append(task)

        return unpackedList

    def _reportProgress(self, progressCb: TodoistProgressCB, message: str, incCompletedTskCnt: bool = False):
        """

        Args:
            progressCb:     Method to call
            message:        Message to report
            incCompletedTskCnt:  If `True` increment self._completedTasks and report that back
            via the TodoistProgress structure

        Returns:

        """
        if incCompletedTskCnt:
            self._completedTasks += 1
            
        progressInfo: TodoistProgress = TodoistProgress(
            message=message, 
            completedTasks=self._completedTasks, 
            totalTasks=self._totalTasks
        )
        progressCb(progressInfo)
