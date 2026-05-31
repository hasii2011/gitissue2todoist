
from logging import Logger
from logging import getLogger

from os import sep as osSep

from codeallybasic.ResourceManager import ResourceManager

from gitissue2todoist.general.ResourceTextType import ResourceTextType


class Resources:
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
        textFileName: str = Resources.retrieveResourcePath(textType.value)
        cls.clsLogger.debug(f'text filename: {textFileName}')

        objRead = open(textFileName, 'r')
        requestedText: str = objRead.read()
        objRead.close()

        return requestedText

    @classmethod
    def retrieveResourcePath(cls, bareFileName: str) -> str:

        fqFileName: str = ResourceManager.retrieveResourcePath(bareFileName=bareFileName,
                                                               packageName=Resources.RESOURCES_PACKAGE_NAME)
        return fqFileName
