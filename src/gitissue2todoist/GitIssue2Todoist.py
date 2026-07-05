from typing import cast

from logging import Logger
from logging import getLogger
from logging import shutdown as loggingShutdown

import logging.config


from json import load as jsonLoad

from pathlib import Path

from asyncio import create_task

from sys import platform as sysPlatform

from toga import App
from toga import Box
from toga import Button
from toga import Command
from toga import Group
from toga import MainWindow

from toga.style import Pack
from toga.style.pack import COLUMN
from toga.style.pack import ROW

from gitissue2todoist.AppCommon import AppCommon
from gitissue2todoist.MilestoneGitHubPanel import MilestoneGitHubPanel
from gitissue2todoist.RepositorySelector import RepositorySelector
from gitissue2todoist.TodoistPanel import TodoistPanel
from gitissue2todoist.owner.OwnerIssuesGitHubPanel import OwnerIssuesGitHubPanel
from gitissue2todoist.preferences.IOSPreferencesDialog import IOSPreferencesDialog
from gitissue2todoist.preferences.IPreferencesDialog import IPreferencesDialog

from gitissue2todoist.preferences.Preferences import Preferences

from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine
from gitissue2todoist.pubsubengine.PubSubEngine import PubSubEngine

from gitissue2todoist.strategy.TodoistTaskCreationStrategy import TodoistTaskCreationStrategy

from gitissue2todoist.preferences.PreferencesDialog import PreferencesDialog


class GitIssue2Todoist(App):
    JSON_LOGGING_CONFIG_FILENAME: str = "loggingConfiguration.json"

    def __init__(self):

        # Make sure this matches pyproject.toml
        super().__init__(
            formal_name='GitIssue2Todoist',
            app_id='org.gitissue2todoist.gitissue2todoist'
        )
        self._setupSystemLogging()

        self.logger: Logger = getLogger(__name__)

        self._preferences:  Preferences   = Preferences()
        self._pubSubEngine: IPubSubEngine = PubSubEngine()

        self._repositorySelector:     RepositorySelector     = cast(RepositorySelector, None)
        self._milestoneGithubPanel:   MilestoneGitHubPanel   = cast(MilestoneGitHubPanel, None)
        self._ownerIssuesGitHubPanel: OwnerIssuesGitHubPanel = cast(OwnerIssuesGitHubPanel, None)
        self._todoistPanel:           TodoistPanel           = cast(TodoistPanel, None)

    def startup(self):
        """
        Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """

        self.main_window = MainWindow(title=self.formal_name)
        assert self.main_window is not None
        assert not isinstance(self.main_window, str)

        try:
            mainContainer:   Box = Box(style=Pack(direction=ROW, flex=1, margin_left=5, gap=10))


            if self._preferences.taskCreationStrategy == TodoistTaskCreationStrategy.SINGLE_TODOIST_PROJECT or \
                    self._preferences.taskCreationStrategy == TodoistTaskCreationStrategy.PROJECT_BY_REPOSITORY:

                self._repositorySelector = RepositorySelector(pubSubEngine=self._pubSubEngine)

                gitHubContainer: Box = Box(style=Pack(direction=COLUMN, flex=1, margin_left=5, gap=10))

                self._milestoneGithubPanel = MilestoneGitHubPanel(pubSubEngine=self._pubSubEngine)
                gitHubContainer.add(self._repositorySelector)
                gitHubContainer.add(self._milestoneGithubPanel)
                mainContainer.add(gitHubContainer)

            elif self._preferences.taskCreationStrategy == TodoistTaskCreationStrategy.ALL_ISSUES_ASSIGNED_TO_USER:
                if sysPlatform == AppCommon.PLATFORM_MAC:
                    newWindowWidth:  int = self._preferences.startupSize.width
                    newWindowHeight: int = self._preferences.startupSize.height
                    self.main_window.size = (newWindowWidth, newWindowHeight)

                self._ownerIssuesGitHubPanel = OwnerIssuesGitHubPanel(pubSubEngine=self._pubSubEngine)
                mainContainer.add(self._ownerIssuesGitHubPanel)
            else:
                assert False, 'Not yet implemented'

            self._todoistPanel = TodoistPanel(pubSubEngine=self._pubSubEngine)

            # Only render this button on mobile platforms where menus don't exist
            if sysPlatform == AppCommon.PLATFORM_IOS:
                settingsButton = Button(
                    '⚙️ Settings',
                    on_press=self._actionPreferences,
                    style=Pack(margin=5)
                )
                mainContainer.add(settingsButton)

            mainContainer.add(self._todoistPanel)

            self.main_window.content = mainContainer

            preferencesCommand: Command = Command(
                self._actionPreferences,
                text='Preferences...',
                group=Group.APP  # Group.APP places it specifically in the macOS app menu!
            )
            self.commands.add(preferencesCommand)
            # noinspection PyUnresolvedReferences
            self.main_window.show()

            self.logger.info(f'*************************** GitIssue2Todist Started ***************************')
            
        except Exception as e:
            print(f"FATAL ERROR IN STARTUP: {e}")
            import traceback
            traceback.print_exc()
            raise e

    def on_exit(self) -> bool:
        self.logger.info(f'*************************** GitIssue2Todist Ended ***************************')
        loggingShutdown()
        return True

    async def on_running(self):
        if self._preferences.taskCreationStrategy == TodoistTaskCreationStrategy.ALL_ISSUES_ASSIGNED_TO_USER:
            await self._ownerIssuesGitHubPanel.loadRepositories()
        else:
            await self._repositorySelector.loadRepositoriesSelectionList()

    # noinspection PyUnusedLocal
    def _actionPreferences(self, command: Command, **kwargs) -> bool:
        """
        The pure synchronous action handler that perfectly satisfies Toga's ActionHandler Protocol
        Args:

        """
        create_task(self._showPreferencesDialog())

        return True

    async def _showPreferencesDialog(self) -> None:
        """
        The async background task that actually halts execution to wait for the dialog
        """
        if self._preferences.debugMobilePreferencesDialog:
            dialog: IPreferencesDialog = IOSPreferencesDialog()
        else:
            if sysPlatform == AppCommon.PLATFORM_IOS:
                dialog = IOSPreferencesDialog()
            elif sysPlatform == AppCommon.PLATFORM_MAC:
                dialog = PreferencesDialog()
            else:
                assert False, 'Unsupported platform'

        await dialog.showDialog()

    def _setupSystemLogging(self):
        """

        PosixPath('/Users/humberto.a.sanchez.ii/Library/Application Support/org.gitissue2todoist.gitissue2todoist/gitissue2todoist.log')
        """

        configFilePath: Path = self.paths.app / 'resources' / GitIssue2Todoist.JSON_LOGGING_CONFIG_FILENAME

        with open(configFilePath, 'r') as loggingConfigurationFile:
            configurationDictionary = jsonLoad(loggingConfigurationFile)

        safeLogPath: Path = self.paths.data / 'gitissue2todoist.log'
        #
        # Hacky way to override the file name from the configuration file
        # names must EXACTLY match what is in the configuration file
        #
        configurationDictionary['handlers']['rotatingFileHandler']['filename'] = str(safeLogPath)

        logging.config.dictConfig(configurationDictionary)
        logging.logProcesses = False
        logging.logThreads   = False

def main():
    return GitIssue2Todoist()
