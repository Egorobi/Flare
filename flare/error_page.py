import traceback
from nicegui import ui
from modules.head_module import HeadModule
import session
from colorschemes import color_schemes
from saver import Saver

class ErrorPage():
    def __init__(self):
        self.saver = Saver()
        self.character_path = None
        self.traceback = ""
        self.exception = ""

    def show_error_page(self, exception: Exception):
        # ui.label("Custom oopsie")
        scheme = self.saver.get_menu_color()
        if scheme in color_schemes:
            session.color_scheme = color_schemes[scheme]

        add_head = HeadModule()
        add_head.add_head()

        ui.page_title('Flare')

        darkmode = ui.dark_mode()
        darkmode.set_value(self.saver.get_menu_dark_mode())

        with ui.card().classes("everything transparent no-shadow").style("max-width: 85rem; min-width:85rem;"):
            with ui.column().classes("w-full items-center"):
                ui.label("Internal Error").classes("text-xl font-bold text-primary")
                ui.image("data/assets/error_screen.png").classes("w-40 h-40").classes("frame")
                self.exception = "".join(traceback.format_exception(exception))
                ui.label("Refer to the Troubleshooting guide on the GitHub repository if the issue persists")
                ui.button("Return to Home", on_click=lambda: ui.navigate.to("/character_select")).props("outline")
                traceback_switch = ui.checkbox("Show Traceback").classes("text-slate-400").props("checked-icon='arrow_drop_down' unchecked-icon='arrow_drop_up'")
                # ui.markdown(f"```python\n{self.exception}\n```").bind_visibility_from(traceback_switch, 'value')
                ui.code(f"{self.exception.strip()}").bind_visibility_from(traceback_switch, 'value')
