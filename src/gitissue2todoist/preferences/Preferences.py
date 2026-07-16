
from logging import Logger
from logging import getLogger

from codeallybasic.IConfigurationLocator import IConfigurationLocator
from codeallybasic.ConfigurationLocator import ConfigurationLocator

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

from toga import App

from gitissue2todoist.general.TogaConfigurationLocator import TogaConfigurationLocator
from gitissue2todoist.general.GitHubURLOption import GitHubURLOption

from gitissue2todoist.general.ResourceManager import ResourceManager
from gitissue2todoist.strategy.TodoistTaskCreationStrategy import TodoistTaskCreationStrategy

UNSPECIFIED_GITHUB_USERNAME: str = 'Put Your GitHub User Name Here'

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
        KeyName('gitHubUserName'):     ValueDescription(defaultValue=UNSPECIFIED_GITHUB_USERNAME),
        KeyName('maxReposToRetrieve'): ValueDescription(defaultValue=DEFAULT_MAX_REPOS, deserializer=SecureConversions.secureInteger),
        KeyName('gitHubURLOption'):    ValueDescription(defaultValue=GitHubURLOption.HyperLinkedTaskName.value, deserializer=GitHubURLOption, enumUseValue=True),
    }
)

TODOIST_SECTION: ValueDescriptions = ValueDescriptions(
    {
        KeyName('cleanTodoistCache'):    ValueDescription(defaultValue='True', deserializer=SecureConversions.secureBoolean),
        KeyName('todoistProjectName'):   ValueDescription(defaultValue=DEFAULT_TODOIST_PROJECT_NAME),
        KeyName('taskCreationStrategy'): ValueDescription(defaultValue=DEFAULT_TASK_CREATION_STRATEGY, deserializer=TodoistTaskCreationStrategy, enumUseValue=True),
    }
)
DEBUG_SECTION: ValueDescriptions = ValueDescriptions(
    {
        KeyName('debugMobileIssueSelector'):         ValueDescription(defaultValue='False', deserializer=SecureConversions.secureBoolean),
        KeyName('debugMobilePreferencesDialog'):     ValueDescription(defaultValue='False', deserializer=SecureConversions.secureBoolean),
        KeyName('debugMobileAuthorizationDialog'):   ValueDescription(defaultValue='False', deserializer=SecureConversions.secureBoolean),
        KeyName('debugMobileMultiRepositoryIssues'): ValueDescription(defaultValue='False', deserializer=SecureConversions.secureBoolean),
        KeyName('debugMobileRepositoryList'):        ValueDescription(defaultValue='False', deserializer=SecureConversions.secureBoolean),

    }
)

CONFIGURATION_SECTIONS: Sections = Sections(
    {
        SectionName('Main'):    SECTION_MAIN,
        SectionName('GitHub'):  SECTION_GITHUB,
        SectionName('Todoist'): TODOIST_SECTION,
        SectionName('Debug'):   DEBUG_SECTION,
    }
)


class Preferences(DynamicConfiguration, metaclass=SingletonV3):
    """
    This updated class runs on both macOS and IOS

    On macOS as a BeeWare app:
        <home>/Library/Preferences/org.gitissue2todoist.gitissue2todoist
    for unit testting
        <home>/.config/gitissue2todoist
    """
    def __init__(self):
        self._logger: Logger = getLogger(__name__)

        baseFileName: str = f'{ResourceManager.CANONICAL_APPLICATION_NAME.lower()}.ini'
        moduleName:   str = f'{ResourceManager.CANONICAL_APPLICATION_NAME.lower()}'

        if App.app is None:
            configurationLocator: IConfigurationLocator = ConfigurationLocator()
        else:
            configurationLocator = TogaConfigurationLocator()

        super().__init__(baseFileName=baseFileName, moduleName=moduleName, sections=CONFIGURATION_SECTIONS, configurationLocator=configurationLocator)
