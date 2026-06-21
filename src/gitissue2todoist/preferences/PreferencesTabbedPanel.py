
from typing import List
from typing import cast

from toga import Box
from toga import Label
from toga import Switch
from toga import TextInput
from toga import Selection
from toga import OptionItem
from toga import OptionContainer

from gitissue2todoist.preferences.Preferences import Preferences
from gitissue2todoist.strategy.TodoistTaskCreationStrategy import TodoistTaskCreationStrategy
from gitissue2todoist.general.GitHubURLOption import GitHubURLOption

from toga.style import Pack
from toga.style.pack import COLUMN
from toga.style.pack import LEFT
from toga.style.pack import ROW

URL_OPTION_MARGIN_BOTTOM: int = 15

TOKEN_ROW_MARGIN_BOTTOM: int = 10
TOKEN_LABEL_WIDTH:       int = 150


class PreferencesTabbedPanel(OptionContainer):
    def __init__(self) -> None:
        super().__init__()

        self._preferences: Preferences = Preferences()

        self.tokensBox:  Box = Box(style=Pack(direction=COLUMN, margin=10))
        self.todoistBox: Box = Box(style=Pack(direction=COLUMN, margin=10))
        self.githubBox:  Box = Box(style=Pack(direction=COLUMN, margin=10))
        
        self._todoistToken:         TextInput
        self._githubToken:          TextInput
        self._taskCreationStrategy: Selection
        self._githubUrlOption:      Selection
        self._todoistProjectName:   TextInput
        self._cacheCleanupSwitch:   Switch

        self._buildTokensTab()
        self._buildTodoistTab()
        self._buildGitHubTab()
        
        self.content.append(OptionItem('Tokens', self.tokensBox))
        self.content.append(OptionItem('Todoist', self.todoistBox))
        self.content.append(OptionItem('GitHub', self.githubBox))

        self._setDialogValues()

    @property
    def gitHubAPIToken(self) -> str:
        return self._githubToken.value

    def savePreferences(self):

        preferences: Preferences = self._preferences

        preferences.gitHubAPIToken  = self._githubToken.value
        preferences.todoistAPIToken = self._todoistToken.value

        preferences.cleanTodoistCache    = self._cacheCleanupSwitch.value
        preferences.todoistProjectName   = self._todoistProjectName.value
        preferences.taskCreationStrategy = TodoistTaskCreationStrategy(cast(str, self._taskCreationStrategy.value))

        preferences.gitHubURLOption = GitHubURLOption(cast(str, self._githubUrlOption.value))

    def _buildTokensTab(self) -> None:
        """
        Builds the Tokens tab.
        
        Modifies instance variables:
            - self._todoistTokenInput
            - self._githubTokenInput
        """
        # Todoist Token
        todoistTokenRow:   Box       = Box(style=Pack(direction=ROW, margin_bottom=TOKEN_ROW_MARGIN_BOTTOM))
        todoistTokenLabel: Label     = Label('Todoist Token', style=Pack(width=TOKEN_LABEL_WIDTH, text_align=LEFT))
        self._todoistToken = TextInput(style=Pack(flex=1))
        todoistTokenRow.add(todoistTokenLabel, self._todoistToken)

        # GitHub Token
        githubTokenRow:   Box           = Box(style=Pack(direction=ROW, margin_bottom=TOKEN_ROW_MARGIN_BOTTOM))
        githubTokenLabel: Label         = Label('GitHub Token', style=Pack(width=TOKEN_LABEL_WIDTH, text_align=LEFT))
        self._githubToken = TextInput(style=Pack(flex=1))
        githubTokenRow.add(githubTokenLabel, self._githubToken)

        self.tokensBox.add(todoistTokenRow, githubTokenRow)

    def _buildTodoistTab(self) -> None:
        """
        Builds the Todoist tab.
        
        Modifies instance variables:
            - self._strategySelection
            - self._cacheCleanupSwitch
            - self_.projectNameInput
        """
        # Allow Todoist Cache Cleanup
        self._cacheCleanupSwitch = Switch('Allow Todoist Cache Cleanup', style=Pack(margin_bottom=15))
        self._cacheCleanupSwitch.value = True
        self.todoistBox.add(self._cacheCleanupSwitch)

        # Todoist Task Creation Strategy
        strategyLabel: Label = Label('Todoist Task Creation Strategy', style=Pack(margin_bottom=5, font_weight='bold'))
        self.todoistBox.add(strategyLabel)
        
        strategyItems: List[str] = [
            strategy.value for strategy in TodoistTaskCreationStrategy
            if strategy != TodoistTaskCreationStrategy.NOT_SET
        ]
        self._taskCreationStrategy = Selection(items=strategyItems, style=Pack(margin_bottom=15))
        self.todoistBox.add(self._taskCreationStrategy)

        # Todoist Project Name
        projectNameRow:   Box       = Box(style=Pack(direction=ROW, margin_bottom=10))
        projectNameLabel: Label     = Label('Todoist Project Name', style=Pack(width=150, text_align=LEFT))

        self._todoistProjectName = TextInput(style=Pack(flex=1))
        self._todoistProjectName.value = 'Development'
        projectNameRow.add(projectNameLabel, self._todoistProjectName)

        self.todoistBox.add(projectNameRow)

    def _buildGitHubTab(self) -> None:
        """
        Builds the GitHub tab.
        
        Modifies instance variables:
            - self._githubUrlSelection
        """
        urlLabel: Label = Label('Include GitHub Issue URL', style=Pack(margin_bottom=5, font_weight='bold'))
        self.githubBox.add(urlLabel)

        urlOptions: List[str] = [option.value for option in GitHubURLOption]
        self._githubUrlOption = Selection(items=urlOptions, style=Pack(margin_bottom=URL_OPTION_MARGIN_BOTTOM))
        
        # Default to Hyper Linked Task Name
        self._githubUrlOption.value = GitHubURLOption.HyperLinkedTaskName.value
        
        self.githubBox.add(self._githubUrlOption)

    def _setDialogValues(self):

        preferences: Preferences = self._preferences

        self._githubToken.value  = preferences.gitHubAPIToken
        self._todoistToken.value = preferences.todoistAPIToken

        self._cacheCleanupSwitch.value   = preferences.cleanTodoistCache
        self._todoistProjectName.value   = preferences.todoistProjectName
        self._taskCreationStrategy.value = preferences.taskCreationStrategy.value

        self._githubUrlOption.value = preferences.gitHubURLOption.value
