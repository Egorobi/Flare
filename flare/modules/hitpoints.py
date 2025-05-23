from nicegui import ui
from modules.listeners import HealthListener
import session
import frames

class Hitpoints(HealthListener):

    health_input = 0
    score_size = 6
    hitpoints_width = 23

    def __init__(self):
        super().__init__()
        self.input_box = None
        self.current_hp_label = None
        self.temp_input = None

    def show_module(self):
        char = session.char
        with ui.card().classes("items-center transparent no-shadow").style(f"height:{self.score_size}rem; width:{self.hitpoints_width}rem"):
            frames.show_frame("hp")
            with ui.row().classes("items-center justify-between h-full w-full absolute-center q-px-md no-wrap").style("gap:0em"):
                with ui.column().classes("w-16").style("gap: 0.2em"):
                    ui.button("Heal", on_click=lambda: self.apply_health_input(1)).classes("w-16 h-4 tiny-text health-button").props("outline")
                    self.input_box = ui.number(format='%d', precision=0, min=0,
                            on_change=lambda e: self.set_health_input(e.value)).props("dense outlined").classes("health-input w-16")
                    ui.space().classes("h-7")
                    ui.button("Damage", on_click=lambda: self.apply_health_input(-1)).classes("w-16 h-4 tiny-text").props("outline")
                with ui.column().classes("items-center h-full justify-between q-pt-sm q-pb-lg w-36"):
                    with ui.row().classes("little-text h-2 justify-between q-pt-sm"):
                        ui.label("CURRENT")
                        ui.label("MAX").classes("w-12 text-center")
                    with ui.row().classes("text-3xl vertical-middle"):
                        self.current_hp_label = ui.label(char.get_hitpoints()[0])
                        ui.label(" / ")
                        ui.label(char.max_hp)
                with ui.column().classes("items-center h-full w-16 justify-between q-pt-sm q-pb-lg").style("gap: 0em;"):
                    with ui.row().classes("w-full no-wrap q-pt-sm q-pb-none").style("gap:0em"):
                        ui.label("TEMP").classes("little-text text-center w-full h-4")
                        ui.space().classes("w-3")
                    self.temp_input = ui.number(format='%d', prefix=" ", precision=0, min=0, on_change=lambda e: session.set_temp_hitpoints(e.value)).props(
                        "borderless item-aligned input-class=text-center dense").classes("w-24 h-16 text-3xl text-center temp-input q-pb-sm q-pt-none")
                    self.temp_input.value = char.get_hitpoints()[1]

    async def set_health_input(self, value):
        if value is not None and value != "":
            self.health_input = int(value)

    def apply_health_input(self, polarity):
        self.input_box.value = None
        self.input_box.update()
        session.change_health(self.health_input * polarity)
        self.health_input = 0

    def health_callback(self, current, temp):
        self.current_hp_label.text = current
        self.temp_input.value = temp
