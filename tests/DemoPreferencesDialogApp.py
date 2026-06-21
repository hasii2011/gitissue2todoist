
from typing import cast

from logging import Logger
from logging import getLogger
import logging.config

from json import load as jsonLoad

from importlib.resources import files

from toga import App
from toga import Box
from toga import Button
from toga import MainWindow

from gitissue2todoist.preferences.PreferencesDialog import PreferencesDialog

from toga.style import Pack
from toga.style.pack import COLUMN


class DemoPreferencesDialogApp(App):

    def __init__(self, formal_name: str, app_id: str):

        self._setupSystemLogging()

        super().__init__(formal_name=formal_name, app_id=app_id)

        self.logger: Logger = getLogger('tests.DemoConfigTabbedPanelApp')

        self.configDialog: PreferencesDialog = cast(PreferencesDialog, None)      # noqa

    def startup(self) -> None:
        mainBox: Box = Box(style=Pack(direction=COLUMN, margin=10))
        
        openConfigBtn: Button = Button('Open Preferences Dialog', on_press=self._onOpenPreferencesDialog, style=Pack(margin=50))
        mainBox.add(openConfigBtn)

        mainWindow: MainWindow = MainWindow(title=self.formal_name, size=(400, 200))
        mainWindow.content = mainBox
        self.main_window = mainWindow
        mainWindow.show()

    # noinspection PyUnusedLocal
    async def _onOpenPreferencesDialog(self, widget) -> None:
        """"""
        self.configDialog = PreferencesDialog()
        result: bool = await self.configDialog.showDialog()
        
        if result:
            self.logger.info('Dialog OK clicked! Configuration state:')
        else:
            self.logger.info("Dialog Canceled.")


    def _setupSystemLogging(self):
        """

        """

        # 1. Target the package where your resources live
        resource_package = files('tests.resources')

        # 2. Join the path to the specific file
        config_file = resource_package.joinpath('testLoggingConfiguration.json')

        # 3. Open it directly as a text stream!
        # This works identically to a standard open() call, but safely reads from the app bundle.
        with config_file.open('r') as loggingConfigurationFile:
            configurationDictionary = jsonLoad(loggingConfigurationFile)

        logging.config.dictConfig(configurationDictionary)
        logging.logProcesses = False
        logging.logThreads = False

def main() -> App:
    return DemoPreferencesDialogApp(formal_name='Config Panel Demo', app_id='org.gitissue2todoist.gitissue2todoist')

if __name__ == '__main__':
    main().main_loop()
