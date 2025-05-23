from nicegui import ui
from modules.module import Module

class LoadingDialog(Module):
    def __init__(self):
        with ui.dialog() as self.dialog:
            ui.spinner(size='lg', color='primary').props("no-esc-dismiss")

    def wait_module(self):
        self.dialog.open()

    def close(self):
        self.dialog.close()
