
from codeallybasic.Dimensions import Dimensions
from codeallybasic.Position import Position
from gitissue2todoist.general.GitHubURLOption import GitHubURLOption
from gitissue2todoist.strategy.TodoistTaskCreationStrategy import TodoistTaskCreationStrategy


class Preferences:
    startupPosition: Position
    startupSize: Dimensions
    progressDialogPosition: Position
    gitHubUserName: str
    maxReposToRetrieve: int
    gitHubURLOption: GitHubURLOption
    cleanTodoistCache: bool
    todoistProjectName: str
    taskCreationStrategy: TodoistTaskCreationStrategy
    debugMobileIssueSelector: bool
    debugMobilePreferencesDialog: bool
    debugMobileAuthorizationDialog: bool
