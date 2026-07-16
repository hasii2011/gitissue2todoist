
from typing import List
from typing import Tuple
from typing import cast

from logging import Logger
from logging import getLogger

from sys import platform as sysPlatform

from os import linesep as osLineSep

from toga import Box
from toga import Window
from toga import Label
from toga import Switch
from toga import Widget
from toga import TextInput
from toga import Selection
from toga import OptionItem
from toga import InfoDialog
from toga import OptionContainer

from toga.style import Pack
from toga.style.pack import COLUMN
from toga.style.pack import LEFT
from toga.style.pack import ROW

from gitissue2todoist.UICommon import UICommon
from gitissue2todoist.AppCommon import AppCommon

from gitissue2todoist.preferences.Preferences import Preferences
from gitissue2todoist.preferences.SecureTokenManager import SecureTokenManager

from gitissue2todoist.strategy.TodoistTaskCreationStrategy import TodoistTaskCreationStrategy
from gitissue2todoist.general.GitHubURLOption import GitHubURLOption

IOS_LAYOUT_POLLER_INTERVAL: float = 0.25

URL_OPTION_MARGIN_BOTTOM: int = 15

TOKEN_ROW_MARGIN_BOTTOM: int = 10
TOKEN_LABEL_WIDTH:       int = 150
TOKEN_INPUT_WIDTH:       int = 250

GITHUB_TAB_NAME: str = 'GitHub'


class PreferencesTabbedPanel(OptionContainer):
    def __init__(self, **kwargs) -> None:

        super().__init__(**kwargs)
        
        self.logger: Logger = getLogger(__name__)
        
        # self.on_select = self._onTabSelected

        self._preferences:    Preferences = Preferences()
        self._startedPolling: bool        = False

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
        self._githubUserName:       TextInput
        self._taskCreationStrategy: Selection
        self._todoistProjectName:   TextInput
        self._cacheCleanupSwitch:   Switch

        self._buildTokensTab(container=tokensBox)
        self._buildTodoistTab(container=todoistBox)
        self._buildGitHubTab(container=githubBox)
        
        self.content.append(OptionItem('Tokens',  tokensBox))
        self.content.append(OptionItem('Todoist', todoistBox))
        self.content.append(OptionItem(GITHUB_TAB_NAME,  githubBox))

        self._setDialogValues()
        self._setWidgetHandlers()

    def savePreferences(self):

        preferences: Preferences = self._preferences

        tokenManager: SecureTokenManager = SecureTokenManager()
        tokenManager.gitHubToken  = self._githubToken.value
        tokenManager.todoistToken = self._todoistToken.value

        preferences.cleanTodoistCache    = self._cacheCleanupSwitch.value
        preferences.todoistProjectName   = self._todoistProjectName.value
        preferences.taskCreationStrategy = TodoistTaskCreationStrategy(cast(str, self._taskCreationStrategy.value))

        preferences.gitHubURLOption = GitHubURLOption(cast(str, self._githubUrlOption.value))
        preferences.gitHubUserName  = self._githubUserName.value

    def _buildTokensTab(self, container: Box) -> None:
        """
        Builds the Tokens tab.
        
        Modifies instance variables:
            - self._todoistToken
            - self._githubToken

        Args:
            container:

        """
        todoistTokenRow: Box
        githubTokenRow: Box
        todoistTokenRow, self._todoistToken = self._buildTextInputRow('Todoist Token')
        githubTokenRow, self._githubToken   = self._buildTextInputRow('GitHub Token')

        container.add(githubTokenRow, todoistTokenRow)

    def _buildTodoistTab(self, container: Box) -> None:
        """
        Builds the Todoist tab.
        
        Modifies instance variables:
            - self._cacheCleanupSwitch
            - self._taskCreationStrategy
            - self._todoistProjectName

        Args:
            container:

        """
        # Allow Todoist Cache Cleanup
        switchStyle: Pack
        if sysPlatform == AppCommon.PLATFORM_IOS:
            switchStyle = Pack(width=300, margin_bottom=15)
        else:
            switchStyle = Pack(margin_bottom=15)

        self._cacheCleanupSwitch = Switch('Allow Todoist Cache Cleanup', style=switchStyle)
        container.add(self._cacheCleanupSwitch)

        # Todoist Task Creation Strategy
        strategyLabel: Label = Label('Todoist Task Creation Strategy', style=Pack(margin_bottom=5, text_align=LEFT, font_weight='bold'))
        container.add(strategyLabel)
        
        self._taskCreationStrategy = Selection(items=self._getStrategySelections(), style=Pack(width=300, margin_bottom=15))
        container.add(self._taskCreationStrategy)

        # Todoist Project Name
        projectNameLabel: Label = Label('Todoist Project Name', style=Pack(margin_bottom=5, width=200, text_align=LEFT, font_weight='bold'))

        self._todoistProjectName = TextInput(style=Pack(width=200, flex=1))

        projectNameBox: Box   = Box(children=[projectNameLabel, self._todoistProjectName], style=Pack(direction=COLUMN, margin_bottom=10))

        container.add(projectNameBox)

    def _buildGitHubTab(self, container: Box) -> None:
        """
        Builds the GitHub tab.
        
        Modifies instance variables:
            - self._githubUrlOption
            - self._githubUserName

        Args:
            container:

        """
        urlLabel: Label = Label('Include GitHub Issue URL', style=Pack(margin_bottom=5, font_weight='bold'))
        
        self._githubUrlOption = Selection(items=self._getGitHubURLOptions(), style=Pack(width=300, margin_bottom=URL_OPTION_MARGIN_BOTTOM))
        
        # Default to Hyper Linked Task Name
        self._githubUrlOption.value = GitHubURLOption.HyperLinkedTaskName.value

        wrapperBox: Box = Box(style=Pack(direction=COLUMN))
        wrapperBox.add(urlLabel, self._githubUrlOption)

        githubUserNameRow: Box
        githubUserNameRow, self._githubUserName   = self._buildTextInputRow('GitHub User Name')

        container.add(wrapperBox)
        container.add(githubUserNameRow)

    def _buildTextInputRow(self, textLabel: str) -> Tuple[Box, TextInput]:
        """

        Args:
            textLabel:  The label for the text input

        Returns:  A tuple of the box containing the label and text input AND the text input

        """

        tokenRow:   Box        = Box(style=Pack(direction=ROW, margin_bottom=TOKEN_ROW_MARGIN_BOTTOM))
        tokenLabel: Label      = Label(textLabel, style=Pack(width=TOKEN_LABEL_WIDTH, text_align=LEFT))
        
        inputStyle = Pack(width=400) if sysPlatform == AppCommon.PLATFORM_IOS else Pack(flex=1)
        tokenInput: TextInput = TextInput(style=inputStyle)

        tokenRow.add(tokenLabel, tokenInput)

        return  tokenRow, tokenInput

    def _setDialogValues(self):

        preferences: Preferences = self._preferences

        tokenManager: SecureTokenManager = SecureTokenManager()
        githubToken:  str | None = tokenManager.gitHubToken
        todoistToken: str | None = tokenManager.todoistToken

        self._githubToken.value  = githubToken if githubToken else 'Put Your GitHub API Token Here'
        self._todoistToken.value = todoistToken if todoistToken else 'Put Your Todoist API Token Here'

        self._cacheCleanupSwitch.value   = preferences.cleanTodoistCache
        self._todoistProjectName.value   = preferences.todoistProjectName
        self._taskCreationStrategy.value = preferences.taskCreationStrategy.value

        self._githubUrlOption.value = preferences.gitHubURLOption.value
        self._githubUserName.value  = preferences.gitHubUserName

    def _setWidgetHandlers(self):

        self._taskCreationStrategy.on_change = self._onTaskCreationStrategyChanged
        self._githubUrlOption.on_change      = self._onGitHubUrlOptionChanged


    async def _onTaskCreationStrategyChanged(self, selection: Selection):

        UICommon.popDownPicker(selection=selection)

        taskCreationStrategy: TodoistTaskCreationStrategy = TodoistTaskCreationStrategy(cast(str, self._taskCreationStrategy.value))

        msg: str = 'You must restart GitIssue2Todoist for this to take effect.'
        if taskCreationStrategy == TodoistTaskCreationStrategy.ALL_ISSUES_ASSIGNED_TO_USER:
            msg = f'{msg}{osLineSep}For this option ensure you have a valid GitHub user name.'
            self.current_tab = GITHUB_TAB_NAME

        dlg: InfoDialog = InfoDialog(
            title='Warning',
            message=msg
        )

        _w: Window | None = selection.window
        assert _w is not None, 'I know what I am doing'

        await _w.dialog(dialog=dlg)

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
                # Have we been added to the screen yet?
                if self.window is not None:
                    self._startedPolling = True
                
                # We were on the screen, but now we aren't (dialog closed). Stop polling!
                elif self._startedPolling:
                    break

                if self.current_tab is not None:
                    optionItem: OptionItem = cast(OptionItem, self.current_tab)     # type: ignore

                    if optionItem.content is not None:
                        widget: Widget = optionItem.content
                        widget.refresh()

            except (AttributeError, RuntimeError, ValueError) as e:
                self.logger.error(f'Transient layout error: {e}')

            await sleep(IOS_LAYOUT_POLLER_INTERVAL)

    def _getStrategySelections(self) -> List[str]:

        strategyItems: List[str] = [
            strategy.value for strategy in TodoistTaskCreationStrategy
            if strategy != TodoistTaskCreationStrategy.NOT_SET
        ]
        return strategyItems

    def _getGitHubURLOptions(self) -> List[str]:

        urlOptions: List[str] = [option.value for option in GitHubURLOption]
        return urlOptions
