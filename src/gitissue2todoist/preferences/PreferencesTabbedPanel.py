
from typing import List
from typing import Tuple
from typing import cast

from logging import Logger
from logging import getLogger

from sys import platform as sysPlatform

from toga import Box
from toga import Label
from toga import Switch
from toga import TextInput
from toga import Selection
from toga import OptionItem
from toga import OptionContainer
from toga import Widget

from toga.style import Pack
from toga.style.pack import COLUMN
from toga.style.pack import LEFT
from toga.style.pack import ROW

from gitissue2todoist.UICommon import UICommon
from gitissue2todoist.AppCommon import AppCommon

from gitissue2todoist.preferences.Preferences import Preferences
from gitissue2todoist.strategy.TodoistTaskCreationStrategy import TodoistTaskCreationStrategy
from gitissue2todoist.general.GitHubURLOption import GitHubURLOption

IOS_LAYOUT_POLLER_INTERVAL: float = 0.25

URL_OPTION_MARGIN_BOTTOM: int = 15

TOKEN_ROW_MARGIN_BOTTOM: int = 10
TOKEN_LABEL_WIDTH:       int = 150
TOKEN_INPUT_WIDTH:       int = 250


class PreferencesTabbedPanel(OptionContainer):
    def __init__(self, **kwargs) -> None:

        super().__init__(**kwargs)
        
        self.logger: Logger = getLogger(__name__)
        
        # self.on_select = self._onTabSelected

        self._preferences: Preferences = Preferences()

        if sysPlatform == AppCommon.PLATFORM_IOS:
            from asyncio import get_event_loop
            get_event_loop().create_task(self._iosLayoutPoller())

        tokensBox:  Box = Box(style=Pack(direction=COLUMN, flex=1, margin=10))
        todoistBox: Box = Box(style=Pack(direction=COLUMN, flex=1, margin=10))
        githubBox:  Box = Box(style=Pack(direction=COLUMN, flex=1, margin=10))
        
        if sysPlatform == AppCommon.PLATFORM_IOS:
            tokensBox.add(Box(style=Pack(height=100, width=300)))
            todoistBox.add(Box(style=Pack(height=100, width=300)))
            githubBox.add(Box(style=Pack(height=100, width=300)))

        self._todoistToken:         TextInput
        self._githubToken:          TextInput
        self._githubUrlOption:      Selection
        self._todoistProjectName:   TextInput
        self._cacheCleanupSwitch:   Switch

        self._buildTokensTab(container=tokensBox)
        self._buildTodoistTab(container=todoistBox)
        self._buildGitHubTab(container=githubBox)
        
        self.content.append(OptionItem('Tokens',  tokensBox))
        self.content.append(OptionItem('Todoist', todoistBox))
        self.content.append(OptionItem('GitHub',  githubBox))

        self._setDialogValues()

    def savePreferences(self):

        preferences: Preferences = self._preferences

        preferences.gitHubAPIToken  = self._githubToken.value
        preferences.todoistAPIToken = self._todoistToken.value

        preferences.cleanTodoistCache    = self._cacheCleanupSwitch.value
        preferences.todoistProjectName   = self._todoistProjectName.value
        preferences.taskCreationStrategy = TodoistTaskCreationStrategy(cast(str, self._taskCreationStrategy.value))

        preferences.gitHubURLOption = GitHubURLOption(cast(str, self._githubUrlOption.value))

    def _buildTokensTab(self, container: Box) -> None:
        """
        Builds the Tokens tab.
        
        Modifies instance variables:
            - self._todoistTokenInput
            - self._githubTokenInput

        Args:
            container:

        """
        # Todoist Token
        todoistTokenRow, self._todoistToken = self._buildTokenRow('Todoist Token')
        # GitHub Token
        githubTokenRow, self._githubToken = self._buildTokenRow('GitHub Token')

        container.add(todoistTokenRow, githubTokenRow)

    def _buildTodoistTab(self, container: Box) -> None:
        """
        Builds the Todoist tab.
        
        Modifies instance variables:
            - self._strategySelection
            - self._cacheCleanupSwitch
            - self_.projectNameInput

        Args:
            container:

        """
        # Allow Todoist Cache Cleanup
        self._cacheCleanupSwitch = Switch('Allow Todoist Cache Cleanup', style=Pack(margin_bottom=15))
        self._cacheCleanupSwitch.value = True
        container.add(self._cacheCleanupSwitch)

        # Todoist Task Creation Strategy
        strategyLabel: Label = Label('Todoist Task Creation Strategy', style=Pack(margin_bottom=5, font_weight='bold'))
        container.add(strategyLabel)
        
        strategyItems: List[str] = [
            strategy.value for strategy in TodoistTaskCreationStrategy
            if strategy != TodoistTaskCreationStrategy.NOT_SET
        ]
        self._taskCreationStrategy = Selection(items=strategyItems, style=Pack(width=300, margin_bottom=15))
        container.add(self._taskCreationStrategy)

        # Todoist Project Name
        projectNameRow:   Box       = Box(style=Pack(direction=ROW, margin_bottom=10))
        projectNameLabel: Label     = Label('Todoist Project Name', style=Pack(width=160, text_align=LEFT))

        self._todoistProjectName = TextInput(style=Pack(width=140, flex=1))
        self._todoistProjectName.value = 'Development'
        projectNameRow.add(projectNameLabel, self._todoistProjectName)

        container.add(projectNameRow)

        self._taskCreationStrategy.on_change = self._onTaskCreationStrategyChanged

    def _buildGitHubTab(self, container: Box) -> None:
        """
        Builds the GitHub tab.
        
        Modifies instance variables:
            - self._githubUrlSelection

        Args:
            container:

        """
        urlLabel: Label = Label('Include GitHub Issue URL', style=Pack(margin_bottom=5, font_weight='bold'))
        
        urlOptions: List[str] = [option.value for option in GitHubURLOption]
        self._githubUrlOption = Selection(items=urlOptions, style=Pack(width=300, margin_bottom=URL_OPTION_MARGIN_BOTTOM))
        
        # Default to Hyper Linked Task Name
        self._githubUrlOption.value = GitHubURLOption.HyperLinkedTaskName.value

        wrapperBox: Box = Box(style=Pack(direction=COLUMN))
        wrapperBox.add(urlLabel, self._githubUrlOption)
        
        container.add(wrapperBox)

        self._githubUrlOption.on_change = self._onGitHubUrlOptionChanged

    def _buildTokenRow(self, textLabel: str) -> Tuple[Box, TextInput]:

        tokenRow:   Box        = Box(style=Pack(direction=ROW, margin_bottom=TOKEN_ROW_MARGIN_BOTTOM))
        tokenLabel: Label      = Label(textLabel, style=Pack(width=TOKEN_LABEL_WIDTH, text_align=LEFT))
        
        inputStyle = Pack(width=400) if sysPlatform == AppCommon.PLATFORM_IOS else Pack(flex=1)
        tokenInput: TextInput = TextInput(style=inputStyle)

        tokenRow.add(tokenLabel, tokenInput)

        return  tokenRow, tokenInput

    def _setDialogValues(self):

        preferences: Preferences = self._preferences

        self._githubToken.value  = preferences.gitHubAPIToken
        self._todoistToken.value = preferences.todoistAPIToken

        self._cacheCleanupSwitch.value   = preferences.cleanTodoistCache
        self._todoistProjectName.value   = preferences.todoistProjectName
        self._taskCreationStrategy.value = preferences.taskCreationStrategy.value

        self._githubUrlOption.value = preferences.gitHubURLOption.value

    def _onTaskCreationStrategyChanged(self, selection: Selection):
        UICommon.popDownPicker(selection=selection)

    def _onGitHubUrlOptionChanged(self, selection: Selection):
        UICommon.popDownPicker(selection=selection)

    # noinspection PyUnusedLocal
    # def _onTabSelected(self, optionContainer: OptionContainer, **kwargs) -> None:
    #
    #     assert isinstance(optionContainer, OptionContainer)
    #
    #     optionItem: OptionItem = cast(OptionItem, optionContainer.current_tab)
    #
    #     if optionItem and optionItem.content:
    #         widget: Widget = optionItem.content
    #         self.logger.info(f'{widget}.refresh() firing')
    #         widget.refresh()

    async def _iosLayoutPoller(self) -> None:
        """
        This layout poller is a workaround for a Toga framework bug
        where `OptionContainer.on_select` fails to fire on iOS; Doing this refresh
        causes selected tab to refresh and correctly display
        """
        from asyncio import sleep
        while True:
            try:
                # Stop polling if the widget is removed from the window to prevent memory leaks
                if getattr(self, 'window', None) is None and getattr(self, '_startedPolling', False):
                    break
                self._startedPolling = True

                if getattr(self, 'current_tab', None) and getattr(self.current_tab, 'content', None):

                    optionItem: OptionItem = cast(OptionItem, self.current_tab)
                    widget: Widget = optionItem.content
                    widget.refresh()
                    # self.current_tab.content.refresh()

            except Exception as e:
                self.logger.error(f'{e}')
            await sleep(IOS_LAYOUT_POLLER_INTERVAL)
