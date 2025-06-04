import os
import tkinter.filedialog as fd
from tkinter import Tk
from packaging.version import Version
from modules.head_module import HeadModule
from modules.loader import LoadingDialog
from nicegui import ui, run
from saver import Saver
from colorschemes import color_schemes
import session
from version import VERSION

class Settings():

    frame_directory = "./data/assets/frames"

    def __init__(self):
        self.saver = Saver()
        self.dark_back_buttons = {}
        self.light_backgrounds = {}
        self.content_label = None
        self.frame_buttons = {}

    def show_settings(self):
        scheme = self.saver.get_menu_color()
        if scheme in color_schemes:
            session.color_scheme = color_schemes[scheme]
        add_head = HeadModule()
        add_head.add_head()

        ui.page_title('Flare')

        darkmode = ui.dark_mode()
        darkmode.enable()

        dark_backgrounds = {
            "night": "background-image: linear-gradient(0.25turn, #151c24, #141414, #141414, #151c24);",
            "match": "background-image: linear-gradient(0.25turn, var(--q-dark-backtint), #141414, #141414, var(--q-dark-backtint));",
            "solid": "background-color: black;"
        }
        self.dark_back_buttons = {}
        light_backgrounds = {
            "paper": "background-color: #FCF5E5;",  
            "match": "background-image: linear-gradient(0.25turn, var(--q-light-backtint), white, white, var(--q-light-backtint));",
            "solid": "background-color: white;"
        }
        self.light_backgrounds = {}

        with ui.card().classes("everything transparent no-shadow items-center").style("max-width: 85rem; min-width:85rem;"):
            with ui.column().classes("justify-left"):
                ui.button(icon="arrow_back", on_click=lambda: self.go_back()).props("outline")

                ui.label("Content Directory").classes("font-bold text-primary text-xl")
                with ui.row().classes("items-center"):
                    with ui.card().classes("w-min").classes("no-shadow no-wrap q-py-sm").props("bordered").style("min-height: 2.2rem;"):
                        content = self.saver.get_global_content()
                        if content is None or content == "":
                            content = "..."
                        self.content_label = ui.label(content).classes("text-nowrap")
                    ui.button(icon="edit", on_click=lambda: self.open_content_dialog()).props("outline dense").classes("text-sm w-9 h-9")
                    with ui.icon("question_mark").classes("text-primary").props("size=sm"):
                        ui.tooltip(r"The topmost folder of the aurora additional content directory (5e Character Builder\custom)").classes("adapttooltip")

                ui.label("Main Menu Color").classes("font-bold text-primary text-xl")
                ui.label("(Character sheet colors are set from the sheet itself)").classes("italic text-xs")
                label = self.saver.get_menu_color()
                label = "Flare Gold" if label == "default" else label
                with ui.row().classes("items-center"):
                    with ui.dropdown_button(label, icon="palette", color="primary", auto_close=False).props("outline content-class=no-shadow no-caps"):
                        ui.card().classes("frameborder absolute-center w-full h-full frame no-shadow transparent")
                        with ui.grid(columns=2).classes("q-px-sm"):
                            for scheme_name, scheme in color_schemes.items():
                                label = "Flare Gold" if scheme_name == "default" else scheme_name
                                with ui.row().classes("items-center justify-start px-1").style("gap:0rem;"):
                                    ui.icon("square", color=scheme[0]).style("width:1rem;height:1rem;")
                                    ui.item(label, on_click=lambda s=scheme_name: self.change_menu_color(s)).classes("q-pa-none")
                    dark_mode_switch = ui.switch(on_change=lambda e: self.change_menu_dark_mode(e.value)).props("unchecked-icon=light_mode checked-icon=dark_mode")
                    dark_mode_switch.set_value(self.saver.get_menu_dark_mode())
                    dark = ui.dark_mode()
                    dark.bind_value(dark_mode_switch, "value")

                ui.label("Dark Mode Background").classes("font-bold text-primary text-xl")
                with ui.row().classes("items-center"):
                    for background_name, background in dark_backgrounds.items():
                        with ui.column().classes("items-center").style("gap:0.5rem;"):
                            self.dark_back_buttons[background_name] = ui.card().style(background).on("click", lambda b=background_name: self.update_background(b, True)).classes("w-20 h-20").props("flat bordered")
                            ui.label(background_name.capitalize())
                    self.update_background_select(self.saver.get_background(dark=True), dark=True)
                ui.label("Light Mode Background").classes("font-bold text-primary text-xl")
                with ui.row().classes("items-center"):
                    for background_name, background in light_backgrounds.items():
                        with ui.column().classes("items-center").style("gap:0.5rem;"):
                            self.light_backgrounds[background_name] = ui.card().style(background).on("click", lambda b=background_name: self.update_background(b, False)).classes("w-20 h-20").props("flat bordered")
                            ui.label(background_name.capitalize())
                    self.update_background_select(self.saver.get_background(dark=False), dark=False)

                # frames = [x for x in os.walk(self.frameDirectory)]
                frames = os.listdir(self.frame_directory)

                self.frame_buttons = {}

                ui.label("Frame Style").classes("font-bold text-primary text-xl")
                with ui.row().classes("items-center"):
                    for f in frames:
                        with ui.column().classes("items-center").style("gap:0.5rem;"):
                            self.frame_buttons[f] = ui.image(f"data/assets/frames/{f}/border_frame.png").on("click", lambda f=f: self.update_frames(f)).classes("w-20 h-20").props("flat bordered")
                            ui.label(f.capitalize())
                    self.update_frame_select(self.saver.get_frame_style())
                
                ui.label("Update Reminders").classes("font-bold text-primary text-xl")
                ui.checkbox("Remind me about new Flare releases", value=Version(self.saver.get_version_reminder()) < Version(VERSION), on_change=lambda e: self.set_version_reminder(e.value))

                ui.label("Miscellaneous").classes("font-bold text-primary text-xl")
                
                with ui.row().classes("items-center"):
                    ui.label("App running on: ").classes("text-slate-400")
                    ui.code(f"http://localhost:{session.port}")

                ui.button("Report a Problem", on_click=lambda: ui.navigate.to('https://github.com/Egorobi/Flare', new_tab=True)).props("outline")

    def go_back(self):
        loading = LoadingDialog()
        loading.wait_module()
        ui.run_javascript("history.back();")

    def update_frames(self, frames):
        self.saver.save_frame_style(frames)
        ui.run_javascript('location.reload();')

    def update_frame_select(self, frame):
        for _, button in self.frame_buttons.items():
            button.style("border: 1px solid gray;")
            # self.darkBackButtons[b].update()
        self.frame_buttons[frame].style("border: 3px solid var(--q-primary);")

    def change_menu_dark_mode(self, dark):
        self.saver.save_menu_dark_mode(dark)

    def change_menu_color(self, scheme):
        self.saver.save_menu_color(scheme)
        ui.run_javascript('location.reload();')

    def update_background_select(self, background, dark):
        if dark:
            back_dict = self.dark_back_buttons
        else:
            back_dict = self.light_backgrounds
        for _, back in back_dict.items():
            back.style("border: 1px solid gray;")
            # self.darkBackButtons[b].update()
        back_dict[background].style("border: 3px solid var(--q-primary);")
        # self.darkBackButtons[background].update()

    def update_background(self, background, dark):
        self.saver.save_background(background, dark)
        ui.run_javascript('location.reload();')

    async def open_content_dialog(self):
        ui.notify("If no dialog appears, try using alt+tab")
        await run.io_bound(self.set_source_directory)

    def set_source_directory(self):
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        root.after_idle(root.attributes, '-topmost', False)
        default = os.path.expanduser(r"~\Documents\5e Character Builder\custom")
        directory = fd.askdirectory(title="Choose Aurora custom content directory (/5e Character Builder/custom)", initialdir=default)
        if directory == "" or directory is None:
            return
        assert self.content_label is not None, "Settings content label not initialized"
        self.content_label.set_text(directory + "/")

        self.saver.save_global_content(directory + "/")

    async def set_version_reminder(self, value):
        # the current version is saved in the reminder so that when the application updates reminders are re-enabled
        if value:
            self.saver.save_version_reminder("0.0.1")
        else:
            self.saver.save_version_reminder(Version(VERSION).base_version)
