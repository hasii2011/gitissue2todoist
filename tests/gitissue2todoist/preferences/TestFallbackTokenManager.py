from unittest import TestCase
from unittest import main
from unittest.mock import patch
from unittest.mock import MagicMock

from pathlib import Path

from gitissue2todoist.preferences.FallbackTokenManager import FallbackTokenManager
from gitissue2todoist.preferences.FallbackTokenManager import FallbackFailedError

INVALID_JSON:    str = 'I am not JSON'
NONEXISTENT_KEY: str = 'nonexistent_key'

TEST_KEY:       str = 'TestToken'
TEST_TOKEN:     str = 'SecretToken1776'
TEST_DIR:       Path = Path('/tmp')
TEST_FILE_PATH: Path = Path('/tmp/secure_tokens.json')

class TestFallbackTokenManager(TestCase):

    def setUp(self):
        
        self.manager: FallbackTokenManager = FallbackTokenManager()

    @patch('toga.App')
    def testGetFallbackFilePathReturnsTmp(self, mockTogaApp: MagicMock) -> None:
        
        # Make togaApp.paths.config return /tmp
        mockTogaApp.app.paths.config = TEST_DIR
        
        resultPath: Path = self.manager._getFallbackFilePath()
        
        self.assertEqual(resultPath, TEST_FILE_PATH)

    @patch('toga.App')
    def testWriteFallbackAndReadFallbackSuccess(self, mockTogaApp: MagicMock) -> None:
        
        # Set up the mock to use /tmp
        mockTogaApp.app.paths.config = TEST_DIR
        testFilePath: Path           = TEST_FILE_PATH

        # Ensure we start with a clean state
        if testFilePath.exists():
            testFilePath.unlink()

        try:
            # Test writing
            self.manager.writeFallback(key=TEST_KEY, token=TEST_TOKEN)
            
            self.assertTrue(testFilePath.exists())
            
            # Test reading
            retrievedToken: str | None = self.manager.readFallback(key=TEST_KEY)
            
            self.assertEqual(retrievedToken, TEST_TOKEN)
            
        finally:
            # Clean up the test file
            if testFilePath.exists():
                testFilePath.unlink()

    @patch('toga.App')
    def testReadFallbackReturnsNoneIfNoFile(self, mockTogaApp: MagicMock) -> None:
        
        mockTogaApp.app.paths.config = TEST_DIR
        testFilePath: Path           = TEST_FILE_PATH

        if testFilePath.exists():
            testFilePath.unlink()

        retrievedToken: str | None = self.manager.readFallback(key=NONEXISTENT_KEY)
        
        self.assertIsNone(retrievedToken)

    @patch('toga.App')
    def testReadFallbackRaisesFallbackFailedErrorOnInvalidJson(self, mockTogaApp: MagicMock) -> None:
        
        mockTogaApp.app.paths.config = TEST_DIR
        testFilePath: Path           = TEST_FILE_PATH

        with testFilePath.open('w') as fileHandle:
            fileHandle.write(INVALID_JSON)

        try:
            with self.assertRaises(FallbackFailedError):
                self.manager.readFallback(key=TEST_KEY)
        finally:
            if testFilePath.exists():
                testFilePath.unlink()


if __name__ == '__main__':
    main()
