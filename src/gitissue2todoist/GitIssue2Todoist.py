from typing import cast

import logging.config

from json import load as jsonLoad

from pathlib import Path

from toga import App
from toga import Box
from toga import MainWindow

from toga.style import Pack
from toga.style.pack import COLUMN
from toga.style.pack import ROW

from gitissue2todoist.MilestoneGitHubPanel import MilestoneGitHubPanel
from gitissue2todoist.RepositorySelector import RepositorySelector
from gitissue2todoist.TodoistPanel import TodoistPanel
from gitissue2todoist.general.ResourceManager import ResourceManager

from gitissue2todoist.Preferences import Preferences

from gitissue2todoist.pubsubengine.IPubSubEngine import IPubSubEngine
from gitissue2todoist.pubsubengine.PubSubEngine import PubSubEngine

from gitissue2todoist.strategy.TodoistTaskCreationStrategy import TodoistTaskCreationStrategy


class GitIssue2Todoist(App):
    JSON_LOGGING_CONFIG_FILENAME: str = "loggingConfiguration.json"

    def __init__(self):

        super().__init__()
        self._setupSystemLogging()

        self._preferences:  Preferences   = Preferences()
        self._pubSubEngine: IPubSubEngine = PubSubEngine()

        self._repositorySelector:   RepositorySelector   = cast(RepositorySelector, None)
        self._milestoneGithubPanel: MilestoneGitHubPanel = cast(MilestoneGitHubPanel, None)
        self._todoistPanel:         TodoistPanel         = cast(TodoistPanel, None)

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
            mainContainer: Box = Box(style=Pack(direction=ROW, flex=1, margin_left=5, gap=10))

            gitHubContainer: Box = Box(style=Pack(direction=COLUMN, flex=1, margin_left=5, gap=10))

            self._repositorySelector = RepositorySelector(pubSubEngine=self._pubSubEngine)

            if self._preferences.taskCreationStrategy == TodoistTaskCreationStrategy.SINGLE_TODOIST_PROJECT or \
                    self._preferences.taskCreationStrategy == TodoistTaskCreationStrategy.PROJECT_BY_REPOSITORY:
                self._milestoneGithubPanel = MilestoneGitHubPanel(pubSubEngine=self._pubSubEngine)
            else:
                assert False, 'Not yet implemented'

            self._todoistPanel = TodoistPanel()

            gitHubContainer.add(self._repositorySelector)
            gitHubContainer.add(self._milestoneGithubPanel)

            mainContainer.add(gitHubContainer)
            mainContainer.add(self._todoistPanel)

            self.main_window.content = mainContainer

            # noinspection PyUnresolvedReferences
            self.main_window.show()
            
        except Exception as e:
            print(f"FATAL ERROR IN STARTUP: {e}")
            import traceback
            traceback.print_exc()
            raise e

    # noinspection PyUnusedLocal
    def _actionExit(self, widget, **kwargs) -> None:
        self.exit()

    async def on_running(self):
        await self._repositorySelector.loadRepositoriesSelectionList()

    def _setupSystemLogging(self):

        configFilePath: Path = ResourceManager.retrieveResourcePath(GitIssue2Todoist.JSON_LOGGING_CONFIG_FILENAME)

        with open(configFilePath, 'r') as loggingConfigurationFile:
            configurationDictionary = jsonLoad(loggingConfigurationFile)

        logging.config.dictConfig(configurationDictionary)
        logging.logProcesses = False
        logging.logThreads   = False

def main():
    return GitIssue2Todoist()
