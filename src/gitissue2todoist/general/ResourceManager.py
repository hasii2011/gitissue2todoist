
from logging import Logger
from logging import getLogger

from os import sep as osSep

from pathlib import Path

from importlib.resources import as_file
from importlib.resources import files

from gitissue2todoist.general.ResourceTextType import ResourceTextType


class ResourceManager:
    """
    Static class
    """
    CANONICAL_APPLICATION_NAME: str = 'gitissue2todoist'
    RESOURCES_PACKAGE_NAME:     str = 'gitissue2todoist.resources'
    RESOURCES_PATH:             str = f'gitissue2todoist{osSep}resources'

    # noinspection SpellCheckingInspection
    RESOURCE_ENV_VAR:       str = 'RESOURCEPATH'

    clsLogger: Logger = getLogger(__name__)

    @classmethod
    def retrieveResourceText(cls, textType: ResourceTextType) -> str:
        """
        Look up and retrieve the text associated with the resource type

        Args:
            textType:  The text type from the 'well known' list

        Returns:  A long string
        """
        textFileName: Path = ResourceManager.retrieveResourcePath(textType.value)
        cls.clsLogger.debug(f'text filename: {textFileName}')

        with open(textFileName, 'r') as fd:

            # objRead = open(textFileName, 'r')
            # requestedText: str = objRead.read()
            # objRead.close()
            requestedText: str = fd.read()

        return requestedText

    @classmethod
    def retrieveResourcePath(cls, bareFileName: str) -> Path:
        """
        Use this local code until codeallybasic is updated;  I will update to return Path
        Args:
            bareFileName:

        Returns:

        """
        # noinspection SpellCheckingInspection
        """
        fqFileName: str = ResourceManager.retrieveResourcePath(bareFileName=bareFileName,
                                                               packageName=Resources.RESOURCES_PACKAGE_NAME)
        """

        # Obtains a real filesystem path (extracting from packages/zips if necessary)
        with as_file(files(ResourceManager.RESOURCES_PACKAGE_NAME) / bareFileName) as filePath:
            # filePath is now a standard pathlib.Path object representing a real file on disk
            pass

        return filePath
