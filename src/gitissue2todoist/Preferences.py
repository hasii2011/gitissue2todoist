
from logging import Logger
from logging import getLogger

from pathlib import Path

from toga import App

from codeallybasic.Position import Position
from codeallybasic.Dimensions import Dimensions
from codeallybasic.SingletonV3 import SingletonV3
from codeallybasic.DynamicConfiguration import DynamicConfiguration
from codeallybasic.DynamicConfiguration import KeyName
from codeallybasic.DynamicConfiguration import SectionName
from codeallybasic.DynamicConfiguration import Sections
from codeallybasic.DynamicConfiguration import ValueDescription
from codeallybasic.DynamicConfiguration import ValueDescriptions
from codeallybasic.SecureConversions import SecureConversions

from gitissue2todoist.general.GitHubURLOption import GitHubURLOption

from gitissue2todoist.general.ResourceManager import ResourceManager
from gitissue2todoist.strategy.TodoistTaskCreationStrategy import TodoistTaskCreationStrategy

DEFAULT_APP_WIDTH:    int        = 1024
DEFAULT_APP_HEIGHT:   int        = 768
DEFAULT_MAX_REPOS:    str        = '100'

DEFAULT_POSITION:     str        = Position(32, 32).__str__()
DEFAULT_STARTUP_SIZE: Dimensions = Dimensions(width=DEFAULT_APP_WIDTH, height=DEFAULT_APP_HEIGHT).__str__()

DEFAULT_PROGRESS_DIALOG_POSITION: Position = Position(10, 10).__str__()

DEFAULT_TASK_CREATION_STRATEGY: str = TodoistTaskCreationStrategy.PROJECT_BY_REPOSITORY.value
DEFAULT_TODOIST_PROJECT_NAME:   str = 'Development'


SECTION_MAIN: ValueDescriptions = ValueDescriptions(
    {
        KeyName('startupPosition'):        ValueDescription(defaultValue=DEFAULT_POSITION,                 deserializer=Position.deSerialize),
        KeyName('startupSize'):            ValueDescription(defaultValue=DEFAULT_STARTUP_SIZE,             deserializer=Dimensions.deSerialize),
        KeyName('progressDialogPosition'): ValueDescription(defaultValue=DEFAULT_PROGRESS_DIALOG_POSITION, deserializer=Position.deSerialize),
    }
)

SECTION_GITHUB: ValueDescriptions = ValueDescriptions(
    {
        KeyName('gitHubAPIToken'):     ValueDescription(defaultValue='Put Your GitHub API Token Here'),
        KeyName('gitHubUserName'):     ValueDescription(defaultValue='Put Your GitHub User Name Here'),
        KeyName('maxReposToRetrieve'): ValueDescription(defaultValue=DEFAULT_MAX_REPOS, deserializer=SecureConversions.secureInteger),
        KeyName('gitHubURLOption'):    ValueDescription(defaultValue=GitHubURLOption.HyperLinkedTaskName.value, deserializer=GitHubURLOption, enumUseValue=True),
    }
)

TODOIST_SECTION: ValueDescriptions = ValueDescriptions(
    {
        KeyName('todoistAPIToken'):      ValueDescription(defaultValue='Put Your Todoist API Token Here'),
        KeyName('cleanTodoistCache'):    ValueDescription(defaultValue='True', deserializer=SecureConversions.secureBoolean),
        KeyName('singleTodoistProject'): ValueDescription(defaultValue='True', deserializer=SecureConversions.secureBoolean),
        KeyName('todoistProjectName'):   ValueDescription(defaultValue=DEFAULT_TODOIST_PROJECT_NAME),
        KeyName('taskCreationStrategy'): ValueDescription(defaultValue=DEFAULT_TASK_CREATION_STRATEGY, deserializer=TodoistTaskCreationStrategy, enumUseValue=True),
    }
)

CONFIGURATION_SECTIONS: Sections = Sections(
    {
        SectionName('Main'):    SECTION_MAIN,
        SectionName('GitHub'):  SECTION_GITHUB,
        SectionName('Todoist'): TODOIST_SECTION,
    }
)


class Preferences(DynamicConfiguration, metaclass=SingletonV3):
    """
    This updated class runs on both macOS and IOS
        1. Let the original __init__ run. (On desktop it finds the file; on iOS it safely misses it)
        2. Check if we are running as Toga application
        3. Retrieve the strictly safe sandbox directory (iOS, macOS, Android, Windows)
        4. IOS requiest that the directory exists
        5. Override the internal file path
        6. Reload the configuration from the sandboxed path

    On macOS
        <home>/Library/Preferences/org.gitissue2todoist.gitissue2todoist
    """
    def __init__(self):
        self._logger: Logger = getLogger(__name__)

        baseFileName: str = f'{ResourceManager.CANONICAL_APPLICATION_NAME.lower()}.ini'
        moduleName:   str = f'{ResourceManager.CANONICAL_APPLICATION_NAME.lower()}'

        super().__init__(baseFileName=baseFileName, moduleName=moduleName, sections=CONFIGURATION_SECTIONS)     # 1

        if App.app is not None:                                                                                 # 2
            togaConfigDir: Path = App.app.paths.config                                                          # 3

            togaConfigDir.mkdir(parents=True, exist_ok=True)                                                    # 4
            self._fqFileName = togaConfigDir / baseFileName                                                     # 5
            self._loadConfiguration()                                                                           # 6
