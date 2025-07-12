from nicegui import ui
from modules.module import Module

class HelpScreen(Module):

    base = "'#FFC360'"

    def __init__(self):
        pass

    def show_module(self):
        with ui.dialog() as dialog, ui.card() as card:
            # dialog.classes("dicedialog")
            card.classes("no-shadow q-pa-none items-center").props("square bordered")
            card.style("max-width: none; width: 60vw; height: 90vh; z-index: -1;")

            with open("data/tips.md") as tips:
                tips_content = tips.read()

            with ui.scroll_area().classes("h-full transparent q-my-xs"):
                    ui.markdown(tips_content).classes("q-px-md")

            ui.card().classes("frameborder absolute-center w-full h-full frame no-shadow transparent").style("z-index: -1;")

        dialog.open()
