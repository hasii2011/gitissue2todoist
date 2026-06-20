
from logging import Logger
from logging import getLogger

from pathlib import Path

from toga import App

from codeallybasic.IConfigurationLocator import IConfigurationLocator


class TogaConfigurationLocator(IConfigurationLocator):
    """
    Used by BeeWare applications so that configuration files get stored
    in platform dependent locations
    """

    def __init__(self):

        self.logger: Logger = getLogger(__name__)

        assert App.app is not None, 'Only works in active BeeWare applications'
        self._togaConfigDir: Path = App.app.paths.config

    @property
    def configurationHome(self) -> Path:
        """

        Returns:  The base path for the configuration
        """
        return self._togaConfigDir

    def applicationPath(self, applicationName: str, create: bool = True) -> Path:

        """
        Args:
            applicationName:  The application's config directory
            create:           If True (default) this method creates the
            base directory for the configuration file

        Returns:  The fully qualified path name for the directory where the
        config file should reside
        """

        appPath: Path = self.configurationHome / applicationName

        if create:
            appPath.mkdir(parents=True, exist_ok=True)

        return appPath
