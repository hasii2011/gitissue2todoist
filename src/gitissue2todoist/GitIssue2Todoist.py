from typing import cast

import logging.config

from json import load as jsonLoad

from pathlib import Path

from toga import App
from toga import Box
from toga import MainWindow

from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.RepositorySelector import RepositorySelector
from gitissue2todoist.general.ResourceManager import ResourceManager
from gitissue2todoist.Preferences import Preferences


class GitIssue2Todoist(App):
    JSON_LOGGING_CONFIG_FILENAME: str = "loggingConfiguration.json"

    def __init__(self):

        super().__init__()
        self._setupSystemLogging()

        self._preferences: Preferences = Preferences()
        self._repositorySelector: RepositorySelector = cast(RepositorySelector, None)

    def startup(self):
        """
        Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """

        mainContainer: Box = Box(style=Pack(direction=COLUMN))

        self._repositorySelector: RepositorySelector = RepositorySelector()

        mainContainer.add(self._repositorySelector)
        self.main_window = MainWindow(title=self.formal_name)
        self.main_window.content = mainContainer

        # noinspection PyUnresolvedReferences
        self.main_window.show()

    async def on_running(self):
        await self._repositorySelector.populateRepositories()

    def _setupSystemLogging(self):

        configFilePath: Path = ResourceManager.retrieveResourcePath(GitIssue2Todoist.JSON_LOGGING_CONFIG_FILENAME)

        with open(configFilePath, 'r') as loggingConfigurationFile:
            configurationDictionary = jsonLoad(loggingConfigurationFile)

        logging.config.dictConfig(configurationDictionary)
        logging.logProcesses = False
        logging.logThreads   = False

def main():
    return GitIssue2Todoist()
