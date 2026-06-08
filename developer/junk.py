import toga
from toga.style import Pack
from toga.style.pack import COLUMN, CENTER


class GitIssue2Todoist(toga.App):

    # ... your existing __init__ and startup ...

    def about(self, widget=None):
        """Override the default Toga 'About' command"""

        # 1. Create a secondary window to act as the dialog
        about_window = toga.Window(
            title="About GitIssue2Todoist",
            size=(300, 200),
            resizable=False
        )

        # 2. Build your completely custom layout
        content = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER, padding=20))

        title = toga.Label("GitIssue2Todoist v0.0.1", style=Pack(padding_bottom=10))
        description = toga.Label("My completely custom about dialog!")

        # Add a close button
        close_btn = toga.Button(
            "Close",
            on_press=lambda w: about_window.close(),
            style=Pack(padding_top=20)
        )

        content.add(title)
        content.add(description)
        content.add(close_btn)

        # 3. Assign and show
        about_window.content = content
        about_window.show()
