from nicegui import ui
from modules.module import Module

class HelpScreen(Module):

    base = "'#FFC360'"

    def __init__(self):
        pass

    def show_module(self):
        with ui.dialog() as dialog, ui.card().classes("items-center") as card:
            # dialog.classes("dicedialog")
            card.classes("no-shadow q-pa-none").props("square bordered")
            card.props("square")

            with open("data/tips.md") as tips:
                tips_content = tips.read()

            ui.markdown(tips_content).classes("q-pa-lg")

            ui.card().classes("absolute-center w-full h-full frameborder frame no-shadow transparent")

        dialog.open()
