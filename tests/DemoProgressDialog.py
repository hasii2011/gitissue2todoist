import asyncio
import toga

from toga import Box
from toga import MainWindow
from toga import Button
from toga.style import Pack
from toga.style.pack import COLUMN, CENTER

from gitissue2todoist.dialogs.ProgressDialog import ProgressDialog

class DemoProgressDialog(toga.App):
    
    def startup(self):
        mainBox: Box = Box(style=Pack(direction=COLUMN, align_items=CENTER, margin=50))
        
        startBtn: Button = Button(
            'Run Heavy Task',
            on_press=self._onRunTask,
            style=Pack(margin=20)
        )
        
        mainBox.add(startBtn)
        
        mainWindow: MainWindow = MainWindow(title='Desktop Progress Demo', size=(400, 200))
        mainWindow.content = mainBox

        # Assign to the expected toga property
        self.main_window = mainWindow

        mainWindow.show()

    async def _onRunTask(self, widget: Button):
        # Prevent spam-clicking the button while running
        widget.enabled = False
        
        # 1. Instantiate and show the popup overlay
        progressDialog: ProgressDialog = ProgressDialog('Cloning Tasks...')
        progressDialog.showDialog()
        
        try:
            # 2. Simulate multistep heavy work (e.g. cloning 10 tasks)
            # Using asyncio.sleep to simulate network latency without freezing the UI thread!
            
            i: int
            for i in range(1, 11):
                progressDialog.updateMessage(f'Processing task {i} of 10...')
                await asyncio.sleep(0.5) 
                
            progressDialog.updateMessage('Wrapping up...')
            await asyncio.sleep(0.8)
            
        finally:
            # 3. Always guarantee the dialog is destroyed
            progressDialog.destroy()
            widget.enabled = True


def main() -> DemoProgressDialog:
    
    app: DemoProgressDialog = DemoProgressDialog(
        'Progress Demo', 
        'com.hasii2011.progressdemo'
    )
    return app

if __name__ == '__main__':
    main().main_loop()
