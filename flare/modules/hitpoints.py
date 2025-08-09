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
        self.death_saves_card = None
        self.char = session.char

    def show_module(self):
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
                    self.main_hitpoints()
                with ui.column().classes("items-center h-full w-16 justify-between q-pt-sm q-pb-lg").style("gap: 0em;"):
                    with ui.row().classes("w-full no-wrap q-pt-sm q-pb-none").style("gap:0em"):
                        ui.label("TEMP").classes("little-text text-center w-full h-4")
                        ui.space().classes("w-3")
                    self.temp_input = ui.number(format='%d', prefix=" ", precision=0, min=0, on_change=lambda e: session.set_temp_hitpoints(e.value)).props(
                        "borderless item-aligned input-class=text-center dense").classes("w-24 h-16 text-3xl text-center temp-input q-pb-sm q-pt-none")
                    self.temp_input.value = self.char.get_hitpoints()[1]

    @ui.refreshable
    def main_hitpoints(self):
        current_hp = self.char.get_hitpoints()[0]
        if current_hp > 0:
            with ui.row().classes("little-text h-2 justify-between q-pt-sm"):
                ui.label("CURRENT")
                ui.label("MAX").classes("w-12 text-center")
            with ui.row().classes("text-3xl vertical-middle no-wrap"):
                self.current_hp_label = ui.label(current_hp)
                ui.label(" / ")
                ui.label(self.char.max_hp)
        else:
            # ui.slider(min=0, max=3, step=1).props("track-size='10px' markers")
            with ui.column().classes("items-center justify-end").style("gap:0.1rem; height: 4rem; width:10rem;"):
                with ui.row().classes("items-center").style("gap:0.0rem;"):
                    ui.label("SUCCESSES").classes("text-center").style("width:3rem; font-size: 0.6rem;")
                    ui.space().style("width:0.8rem;")
                    self.success_boxes()
                ui.separator().props("color=primary")
                with ui.row().classes("items-center").style("gap:0.0rem;"):
                    ui.label("FAILURES").classes("text-center").style("width:3rem; font-size: 0.6rem;")
                    ui.space().style("width:0.8rem;")
                    self.failure_boxes()

    def make_boxes(self, result, active, callback):
        color = "primary"
        icon = "circle"
        if result == "failure":
            icon = "disabled_by_default"
            color = "red"
        elif result == "success":
            icon = "check_box"
            color = "green"
        # ui.icon(icon)
        for i in range(1, 4):
            ui.checkbox(value=i<=active, on_change=lambda e: callback(e.value)).props(f"size=lg dense color='{color}' checked-icon='{icon}'")

    @ui.refreshable
    def failure_boxes(self):
        self.make_boxes("failure", self.char.get_death_saves()[1], self.update_failures)

    @ui.refreshable
    def success_boxes(self):
        self.make_boxes("success", self.char.get_death_saves()[0], self.update_successes)

    def update_failures(self, value: bool):
        successes, failures = self.char.get_death_saves()
        if value:
            failures = min(3, failures+1)
        else:
            failures = max(0, failures-1)
        self.char.set_death_saves(successes, failures)
        self.failure_boxes.refresh()
    
    def update_successes(self, value: bool):
        successes, failures = self.char.get_death_saves()
        if value:
            successes = min(3, successes+1)
        else:
            successes = max(0, successes-1)
        self.char.set_death_saves(successes, failures)
        self.success_boxes.refresh()

    async def set_health_input(self, value):
        if value is not None and value != "":
            self.health_input = int(value)

    def apply_health_input(self, polarity):
        self.input_box.value = None
        self.input_box.update()
        session.change_health(self.health_input * polarity)
        self.health_input = 0

    def health_callback(self, current, temp):
        self.temp_input.value = temp
        self.main_hitpoints.refresh()
        if current > 0:
            self.char.set_death_saves(0, 0)
