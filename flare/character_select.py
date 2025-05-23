import tkinter.filedialog as fd
from tkinter import Tk
import urllib.parse
import os
from nicegui import ui, run
from modules.head_module import HeadModule
from modules.loader import LoadingDialog
from saver import Saver
import frames
from query import Query
import session
from colorschemes import color_schemes

class SelectPage():
    def __init__(self):
        self.saver = Saver()
        self.character_path = None

    def show_select_page(self):
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
                # ui.image("data/assets/banner_thick.png").classes("frame").style("height: 8rem; width: 26.6rem;")
                # ui.label("Character Sheet").classes("text-xl font-bold text-primary text-center")
                # ui.separator()
                ui.space()
                saves = self.saver.get_saves()
                with ui.grid(columns=3):
                    for save in saves:
                        with ui.card().classes("no-shadow transparent"):
                            frames.show_frame("select")
                            with ui.row().classes('w-full items-center no-wrap justify-end').style("gap:0.5rem;"):
                                with ui.row().classes("w-full justify-start items-center no-wrap"):
                                    ui.image(save["portrait"]).classes("size-16")
                                    with ui.column().style("gap:0.2rem").style("width:13.25rem;"):
                                        ui.label(save["name"]).classes("text-xl font-bold")
                                        ui.label(save["description"]).classes("text-xs")
                                name = save["name"]
                                ui.button(icon="o_delete").on("click", lambda name=name: self.delete_character_dialog(name)).props("outline color=primary dense size=0.75rem")
                                ui.button("OPEN").on("click", lambda name=name: self.open_character_button(name)).props("outline")
                ui.button("Load Character", on_click=self.start_character_creation).style("width:12rem; height:3rem;").props("outline")
                ui.button("Settings", icon="settings", on_click=lambda: ui.navigate.to("/settings")).props("outline")
                # lil credit
                ui.link("Built by Egorobi", "https://github.com/Egorobi", new_tab=True).classes("italic text-sm text-white text-center").style("opacity: 0.4;")

    def open_character_button(self, name):
        # ui.navigate.to("/character_sheet/"+urllib.parse.quote(name))
        self.open_character(name)

    @ui.refreshable
    def create_character_dialog(self):
        with ui.dialog().classes("dicedialog") as dialog, ui.card().classes("transparent no-shadow frameborder frame items-center"):
            ui.label("Create Character").classes("text-bold")
            # nameInput = ui.input(label="Name")
            # auroraInput = ui.input(label='Path to Aurora File', placeholder='/character.dnd5e')
            # sourceInput = ui.input(label='Path to Aurora Content', placeholder=r"5e Character Builder/custom/")
            # ui.button("Create", on_click=lambda: createCharacter(nameInput.value, auroraInput.value, sourceInput.value))
            ui.label("Path to aurora character file:")
            ui.label(self.character_path)
            ui.label("If the file selection dialog doesn't appear try to alt+tab to it").classes("italic")
            # createButton = ui.button("Create", on_click=lambda: self.createCharacter(auroraPath.text)).props("outline")
            # if self.characterPath == "":
            #     createButton.disable()
        dialog.open()

    async def start_character_creation(self):
        self.character_path = ""
        self.create_character_dialog()
        await run.io_bound(self.set_aurora_path_dialog)
        # prevent dialog from reopening on cancel
        if self.character_path is not None and self.character_path != "":
            self.create_character_dialog.refresh()
            self.create_character(self.character_path)

    def set_aurora_path_dialog(self):
        root = Tk()
        filetypes = [('aurora fles', '*.dnd5e')]
        root.withdraw()
        file = fd.askopenfilename(filetypes=filetypes, title="Choose aurora character file", initialdir="/", parent=root)
        root.attributes('-topmost', True)
        root.after_idle(root.attributes, '-topmost', False)
        # label.set_text(file)
        self.character_path = file
        # label.update()

    def create_character(self, aurora):
        source = self.saver.get_global_content()
        if not self.check_file_paths(aurora):
            return
        print(f"Creating character with {aurora} and {source}")
        name = Query.query_name_from_file(aurora)
        self.saver.save_character_file_path(name, aurora)
        # self.saver.saveSourcePath(name, source)
        self.open_character(name)

    def open_character(self, name):
        loading = LoadingDialog()
        loading.wait_module()
        saves = [s for s in self.saver.get_saves() if s["name"]==name]
        if len(saves) < 1:
            ui.notify("Character does not exist")
            loading.close()
            return
        save = saves[0]
        aurora = save["aurora"]
        if not self.check_file_paths(aurora):
            loading.close()
            return
        name = Query.query_name_from_file(aurora)
        ui.navigate.to("/character_sheet/"+urllib.parse.quote(name))

    def check_file_paths(self, aurora):
        if not os.path.isfile(aurora):
            ui.notify("Aurora file not found")
            return False
        content = self.saver.get_global_content()
        if content is None or not os.path.isdir(content):
            ui.notify("Content directory not found, check settings")
            return False
        return True

    async def delete_character_dialog(self, name):
        with ui.dialog().classes("dicedialog") as dialog, ui.card().classes("transparent no-shadow frameborder frame items-center"):
            ui.label(f"Are you sure you want to delete character \"{name}\"?").classes("font-bold")
            ui.label("Note: this will delete the Flare save file, not the aurora character")
            ui.button("DELETE", on_click=lambda: self.delete_save(name)).props("outline color=red")
        dialog.open()

    def delete_save(self, name):
        save = [s for s in self.saver.get_saves() if s["name"]==name][0]
        file = save["file"]
        os.remove(file)
        ui.navigate.to("/character_select")
