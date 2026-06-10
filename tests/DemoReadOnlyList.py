
from typing import Any
from toga import Box
from toga import App
from toga import MainWindow
from toga.style import Pack
from toga.style.pack import COLUMN

from gitissue2todoist.components.ReadOnlyList import ListItems
from gitissue2todoist.components.ReadOnlyList import ReadOnlyList


class CustomListApp(App):
    def __init__(self, *args: Any, **kwargs: Any) -> None:

        super().__init__(*args, **kwargs)

        self.customList: ReadOnlyList = ReadOnlyList(style=Pack(flex=1))

    def startup(self) -> None:
        self.customList.items = ListItems(["First item", "Second item", "Third item"])

        mainBox: Box = Box(style=Pack(direction=COLUMN))
        mainBox.add(self.customList)

        mainWindow: MainWindow = MainWindow(title=self.formal_name)
        mainWindow.content = mainBox

        mainWindow.show()

        # Finally, assign it to Toga's required property
        self.main_window = mainWindow


def main() -> CustomListApp:
    return CustomListApp("Custom List", "org.hasii.customlist")


if __name__ == "__main__":
    main().main_loop()
