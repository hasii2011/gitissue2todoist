
import os

from pathlib import Path

from unittest import TestLoader
from unittest import TestSuite
from unittest import TextTestRunner


def run_tests():
    # Change to the project root directory
    project_path = Path(__file__).parent.parent
    os.chdir(project_path)

    # Discover and run all unittest tests in the 'tests' directory
    loader: TestLoader = TestLoader()
    suite:   TestSuite = loader.discover(start_dir='tests', pattern='Test*.py', top_level_dir='')

    # Run the tests with verbosity enabled
    runner: TextTestRunner = TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return code is 0 if tests passed, 1 if there were failures/errors
    returnCode = 0 if result.wasSuccessful() else 1

    # Briefcase monitors standard output for this exact string to determine success
    print(f">>>>>>>>>> EXIT {returnCode} <<<<<<<<<<")


if __name__ == "__main__":
    run_tests()
