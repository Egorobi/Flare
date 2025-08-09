import re
from nicegui import ui
from modules.module import Module
from modules.loader import LoadingDialog
from modules.dialogs import RollContext
import session
import frames
import icons
import storage
from colorschemes import color_schemes

class CharacterDetails(Module):

    def __init__(self, char):
        super().__init__()
        self.char = char

    def show_module(self):
        char = self.char
        with ui.row().classes("w-full items-center no-wrap").style("max-width: 99%"):
        # character name
        # ui.image(char.getPortrait()).style("width: 4.5rem; height: 4.5rem;")
            with ui.column():
                ui.label(char.name).tailwind("text-3xl font-extrabold")
                ui.label(char.build)
            ui.space()
            # zoom
            # USE KEYBOARD SHORTCUTS INSTEAD
            # with ui.row().style("gap:0.5rem;"):
            #     ui.button(icon="zoom_in",on_click=lambda: self.zoom(1)).classes("w-5 h-4").props("outline dense size=sm")
            #     ui.button(icon="zoom_out",on_click=lambda: self.zoom(-1)).classes("w-5 h-4").props("outline dense size=sm")

            # dark mode switch
            darkmode = char.get_dark_mode()
            dark_mode_switch = ui.switch(on_change=lambda e: char.set_dark_mode(e.value)).props("unchecked-icon=light_mode checked-icon=dark_mode")
            dark_mode_switch.set_value(darkmode)
            dark = ui.dark_mode()
            dark.bind_value(dark_mode_switch, "value")
            # num_schemes = float(len(color_schemes))
            with ui.dropdown_button('', icon="palette", color="primary", auto_close=False).props("outline dense content-class=no-shadow"):
                # ui.card().classes("frameborder absolute-center w-full h-full frame no-shadow transparent")
                with ui.grid(columns=2).classes("q-px-sm adapttooltip"):
                    for scheme in color_schemes:
                        label = "Flare Gold" if scheme == "default" else scheme
                        with ui.row().classes("items-center justify-start px-1").style("gap:0rem;"):
                            ui.icon("square", color=color_schemes[scheme][0]).style("width:1rem;height:1rem;")
                            ui.item(label, on_click=lambda s=scheme: self.change_color_scheme(s)).classes("q-pa-none")
            # rest buttons
            ui.button("Long Rest", color="primary", on_click=lambda: session.perform_rest("long")).props("outline")
            ui.button("Short Rest", on_click=lambda: session.perform_rest("short")).props("outline")
            # settings button
            ui.button("",icon="o_settings", on_click=lambda: ui.navigate.to("/settings")).props("outline").classes("w-5 h-5")
            # reload button
            ui.button(icon="refresh", on_click=lambda: self.reload()).classes("w-5 h-5").props("outline")

    def reload(self):
        loader = LoadingDialog()
        loader.wait_module()
        ui.run_javascript('location.reload();')

    def zoom(self, direction):
        zoom = session.zoom
        zoom = max(0.1, zoom + 0.1*direction)
        session.zoom = zoom
        ui.run_javascript(f'document.body.style.zoom={zoom};')
        # ui.notify(f"{int(zoom*100)}%")

    def change_color_scheme(self, scheme):
        loader = LoadingDialog()
        loader.wait_module()
        session.set_page_color(scheme)

class MovementSpeed(Module):
    ac_size = 7
    def show_module(self):
        with ui.card().classes("col-2 items-center justify-center no-shadow transparent").style(f"width:{self.ac_size}rem; height:{self.ac_size}rem").props("border=true"):
            frames.show_frame("movement")
            with ui.column().classes("absolute-center justify-between w-full h-full items-center q-py-sm"):
                ui.label("Movement").classes("")
                ui.label("Speed")
                speed = session.char.speed
                ui.label(speed[0]).classes("text-xl font-bold absolute-center")
                with ui.column().classes("absolute-center w-full q-px-sm"):
                    with ui.row().classes("w-full no-wrap text-sm items-center justify-between").style("gap:0em"):
                        ui.html(icons.CLIMB_SVG)
                        ui.label(speed[1])
                        ui.space().classes("w-full")
                        ui.label(speed[2])
                        ui.html(icons.WING_SVG)
                    with ui.row().classes("w-full no-wrap text-sm items-center").style("gap:0em"):
                        ui.icon("pool")
                        ui.label(speed[3])
                        ui.space().classes("w-full")
                        ui.label(speed[4])
                        ui.html(icons.SHOVEL_SVG)

class Initiative(Module):
    ac_size = 7
    def show_module(self):
        char = session.char
        with ui.card().classes("items-center no-shadow transparent q-pa-none").style(f"width: {self.ac_size}rem; gap: 0rem;"):
            # frames.showFrame("initiative")
            ui.label("Initiative")
            # ui.label(valToString(char.initiative)).classes("text-xl font-bold absolute-center")
            ui.space().classes("h-8")
            with ui.column().classes("absolute-center pt-3"):
                with ui.button(session.val_to_string(char.initiative), on_click=lambda mod=char.initiative: session.roll_dialog.wait_module(f"1d20 + {mod}")).classes(
                                "text-xl font-bold h-8 w-12").props("dense flat unelevated text-color=adaptcolor padding='0px 0px 0px 0px'"):
                    context_menu = RollContext()
                    context_menu.show_module(char.initiative)

class HeroicInspiration(Module):
    ac_size = 7
    def __init__(self):
        char = session.char
        self.inspiration = char.get_inspiration()

    def show_module(self):
        with ui.card().classes("items-center no-shadow transparent q-pa-none").style(f"width: {self.ac_size}rem; gap: 0.1rem;"):
            with ui.row().classes("w-full justify-center").style("padding-left: 0.45rem;"):
                ui.checkbox(value=self.inspiration, on_change=lambda e: self.set_inspiration(e.value)).classes("absolute-top-center q-ma-none q-pa-none").props("size=lg dense checked-icon=flare unchecked-icon=none")
            # ui.space().classes("h-6")
            ui.label("Heroic Inspiration").classes("text-xs")

    def set_inspiration(self, value):
        session.char.set_inspiration(value)


class ArmorClass(Module):
    ac_size = 7
    def show_module(self):
        with ui.card().classes("items-center no-shadow transparent").style(f"width: {self.ac_size}rem; height: {self.ac_size}rem;").on("click", lambda: session.show_stat_info("ac:calculation", "Armor Class")):
            frames.show_frame("ac")
            ui.label(session.char.armor_class).classes("text-xl font-bold absolute-center")
            with ui.column().classes("items-center justify-between absolute-center q-pt-sm q-pb-sm h-full"):
                ui.label("Armor").classes("h-2")
                ui.label("Class")

class Conditions(Module):
    ac_size = 7
    conditions_width = 17

    active_conditions = []

    def __init__(self):
        self.switches = {}
        self.conditions_label = None
        self.exhaustion_label = None

    def show_module(self):
        self.active_conditions = session.char.get_conditions()
        with ui.card().classes("q-py-sm q-px-sm transparent no-shadow items-center").style(f"width: {self.conditions_width}rem; height: {self.ac_size}rem; gap:0.1rem;"):
            frames.show_frame("conditions")
            # ui.label("CONDITIONS").classes("text-bold")
            # ui.separator().classes("w-full")
            # with ui.row().classes("w-full"):
            #     ui.label(", ".join(char.conditions)).classes("col-6 little-text")
            #     ui.separator().classes("h-full").props("vertical")
            #     ui.space().classes("col-6")
            # with ui.row().classes("w-full h-full no-wrap").style("gap:1rem;"):
            #     with ui.column().classes("col-6").style("width:7rem; gap:0.1rem;"):
            #         ui.label("DEFENSES").classes("text-bold")
            #         ui.label(", ".join(char.conditions)).classes("little-text")
            #     ui.separator().classes("").props("vertical")
            #     with ui.column().classes("").style("width:7rem; gap:0.1rem;"):
            #         ui.label("CONDITIONS").classes("text-bold")
            #         ui.label(", ".join(char.conditions)).classes("little-text")
            conditions = ["Blinded", "Charmed", "Deafened", "Frightened", "Grappled", "Incapacitated", "Invisible", "Paralyzed", "Petrified", "Poisoned", "Prone", "Restrained", "Stunned", "Unconscious"]
            self.switches = {}
            with ui.row().classes("w-full no-wrap h-full").style("gap:0rem;"):
                with ui.column().classes("col-6").style("gap:0.1rem;"):
                    ui.label("DEFENSES").classes("text-bold")
                    ui.separator().classes("w-full")
                    ui.label(", ".join(session.char.conditions)).classes("little-text")
                ui.separator().classes("h-full").props("vertical")
                # with ui.column().classes("col-6").style("gap:0.1rem;"):
                #     ui.label("CONDITIONS").classes("text-bold q-pl-sm")
                #     ui.separator().classes("w-full")
                #     # ui.label(", ".join(session.char.conditions)).classes("little-text q-pl-sm")
                #     selection = ui.select(conditions, multiple=True).props("borderless hide-bottom-space hide-dropdown-icon").classes("q-pl-sm w-full h-full little-text").style("height:4.5rem;")
                #     selection.props["popup-content-class"] = "frameborder frame q-pa-none"
                #     selection.update()
                with ui.column().classes("col-6 h-full").style("gap:0.1rem;"):
                    ui.label("CONDITIONS").classes("text-bold q-pl-sm")
                    ui.separator().classes("w-full")
                    self.conditions_label = ui.label().classes("q-pl-sm little-text")
                    with ui.dropdown_button('', split=False).props("outline").classes("absolute w-32 h-24 items-center").style("opacity: 0.0;"):
                        # ui.card().classes("absolute-center w-full h-full frameborder frame no-shadow transparent")
                        ui.card().classes("absolute-center w-full h-full adapttooltip frame no-shadow transparent")
                        with ui.grid(columns=2).classes("q-pa-sm"):
                            for condition in conditions:
                                with ui.row().classes("items-center").style("gap:0.1rem;"):
                                    switch = ui.switch(on_change=lambda e, name=condition: self.change_condition(name, e.value))
                                    self.switches[condition] = switch
                                    with ui.label(condition).style("z-index:1;"):
                                        # ui.tooltip(storage.conditionDefinitons[condition]).classes("text-sm")
                                        with ui.tooltip().classes("text-sm adapttooltip"):
                                            definition = storage.condition_definitions[condition]
                                            definition = definition.split("\n")[1:-1]
                                            definition = "".join([f"<li>{d}</li>" for d in definition])
                                            ui.html(f"<ul>{definition}</ul>")
                        with ui.row().classes("justify-center q-pb-sm"):
                            ui.label("Exhaustion:")
                            ui.button(icon="remove", on_click=lambda: self.change_exhaustion(-1)).classes("little-text q-py-none q-px-xs").props("outline size=0.5rem")
                            self.exhaustion_label = ui.label(str(self.get_exhaustion()))
                            ui.button(icon="add", on_click=lambda: self.change_exhaustion(1)).classes("little-text q-py-none q-px-xs").props("outline size=0.5rem")

                self.update_conditions_label()

    def change_condition(self, name, active):
        if active:
            self.active_conditions.append(name)
        else:
            self.active_conditions.remove(name)
        self.active_conditions = list(set(self.active_conditions))
        session.char.set_conditions(self.active_conditions)
        self.update_conditions_label()

    def change_exhaustion(self, increment):
        level = 0
        dest = None
        for i,c in enumerate(self.active_conditions):
            if "Exhaustion" in c:
                level = int(re.search(r"(\d+)", c).group())
                dest = i
                break
        if dest is not None:
            self.active_conditions.pop(dest)
        level = max(0, level+increment)
        if level > 0:
            self.active_conditions.append(f"Exhaustion({level})")
        session.char.set_conditions(self.active_conditions)
        self.exhaustion_label.set_text(level)
        self.update_conditions_label()

    def get_exhaustion(self):
        level = 0
        for c in self.active_conditions:
            if "Exhaustion" in c:
                level = int(re.search(r"(\d+)", c).group())
                break
        return level

    def update_conditions_label(self):
        text = ""
        if len(self.active_conditions) >= 5:
            text = ", ".join(self.active_conditions[:4]) + " ..."
        else:
            text = ", ".join(self.active_conditions)
        self.conditions_label.set_text(text)
        for condition in self.active_conditions:
            if not condition in self.switches:
                continue
            self.switches[condition].set_value(True)
