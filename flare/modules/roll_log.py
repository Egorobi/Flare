import re
from nicegui import ui
from modules.module import Module
from modules.listeners import RollsListener
import session

class RollLog(RollsListener):

    def __init__(self):
        super().__init__()
        self.pinned_toggle = None
        self.state = {"opened": False}
        self.dialog = None

        with ui.dialog().props("full-height seamless") as self.dialog, ui.card().classes("justify-end") as card:
            card.classes("fixed-top-right h-full no-shadow q-px-none square q-py-sm").props("square bordered").style("width: 20rem;")
            back_space = ui.space().style("height: 0.01rem;")
            self.show_roll_history()
            with ui.row().classes('items-center justify-between w-full q-pl-sm'):
                ui.button("Hide", icon="chevron_right", on_click=lambda: self.dialog.close()).props("outline dense size=sm")
                self.pinned_toggle = ui.checkbox("Show Pinned", value=session.char.get_pinned_rolls_shown(), on_change=lambda e: session.char.save_pinned_rolls_shown(e.value)).classes("q-my-none q-mx-md").props("unchecked-icon='bi-pin' checked-icon='close' dense").style("z-index: 3;")
                ui.button("Clear Log", on_click=lambda: self.clear_rolls()).classes("q-mr-md").props("outline dense size=sm")
            back_space.bind_visibility_from(self.pinned_toggle, "value")
            self.show_pinned_rolls()
            # ui.card().classes("frameborder absolute-center w-full h-full frame no-shadow transparent").style("z-index: -1;")

            # ui.button("add roll", on_click=lambda: self.test_func())
            ui.card().classes("frameborder absolute-center w-full h-full frame no-shadow transparent").style("z-index: -1;")
        
        self.dialog.bind_value_to(self.state, "opened")

    def show_module(self):
        self.roll_callback()
        self.dialog.open()

    def clear_rolls(self):
        session.char.clear_roll_history()
        self.roll_callback()

    @ui.refreshable
    def show_roll_history(self):
        roll_history = session.char.get_roll_history()
        if not roll_history:
            return
        with ui.scroll_area().classes("w-full h-full q-pa-none justify-end") as scroll:
            ui.space().classes("h-full")
            with ui.column().classes("w-full flex-col-reverse justify-end").style("gap:0.85rem;"):
                for roll in roll_history:
                    message = RollMessage(roll.attrib.get("roll", None), roll.attrib.get("result", None), roll.attrib.get("values", None), roll.attrib.get("name", None))
                    message.show_module()
                    ui.separator().classes("w-full")
        scroll.scroll_to(percent=100)

    @ui.refreshable
    def show_pinned_rolls(self):

        pinned_rolls = session.char.get_pinned_rolls()
        number_pinned = len(pinned_rolls)
        height = number_pinned*4 + max(0, number_pinned-1)*0.1 + (2 if number_pinned>0 else 0)
        with ui.card().classes("absolute-top q-pa-none").props("").style("margin: 0.85rem 0.45rem; box-shadow: 0px 30px 30px rgba(0, 0, 0, 0.5);") as card:
            if number_pinned <= 6:
                self.draw_pin_column(pinned_rolls)
            else:
                with ui.scroll_area().classes("").style(f"height: {height}rem; max-height: 55vh;").style("z-index: 2").props(""):
                    self.draw_pin_column(pinned_rolls)

        card.bind_visibility_from(self.pinned_toggle, 'value')

        # scroll.scroll_to(percent=100)
    
    def draw_pin_column(self, pinned_rolls):
        with ui.column().classes("w-full h-min q-ma-none").style("gap: 0.1rem;"):
            for i, roll in enumerate(pinned_rolls):
                message = RollPreset(roll.attrib.get("roll", None), roll.attrib.get("name", None), roll.attrib.get("id", None), position=i)
                message.show_module()

    def roll_callback(self):
        self.show_roll_history.refresh()
        self.show_pinned_rolls.refresh()

class RollMessage(Module):

    def __init__(self, roll, result, values, roll_name):
        self.roll = roll
        self.result = result
        if values is not None:
            self.values = values.split(",")
        else:
            self.values = values
        self.roll_name = roll_name

    def show_module(self):
        with ui.card() as card:
            card.classes("items-center w-full q-py-xs transparent").props("")
            card.style("box-shadow: 0 0 5px var(--q-primary) inset;")
            with ui.column().classes("items-start q-pa-none w-full h-full no-wrap").style("gap: 0.2rem;"):
                if self.roll_name is not None:
                    ui.label(self.roll_name).classes("font-bold")
                with ui.row().classes("w-full h-full items-center no-wrap justify-between").style("gap: 0rem;"):
                    ui.label(self.result).classes("text-2xl font-bold q-pr-sm")
                    ui.separator().props("vertical")
                    ui.label(self.roll).classes("text-sm text-slate-400 q-px-xs")
                    with ui.button(on_click=lambda: session.roll_dialog.wait_module(self.roll)).props("flat").classes("q-mr-sm q-pa-md items-center").style("width: 6rem;"):
                        count = int(len(self.values) / 2)
                        with ui.grid(columns = count if count < 5 else 4).style("gap: 1.5rem;"):
                            session.roll_dialog.show_dice_values(values=self.values, size=5)
                        ui.tooltip("Re-roll").classes("adapttooltip")
                with ui.button(icon="bi-pin-angle", on_click=lambda: self.pin_dialog()).props("flat size=sm dense").classes("absolute-top-right"):
                    ui.tooltip("Pin as preset").classes("adapttooltip")

    def dice_count(self, roll_formula):
        matches = re.findall(r"(\d+)d(\d+)", roll_formula)
        total = 0
        for match in matches:
            total += int(match[0])
        return total

    def pin(self, name, formula):
        session.char.add_pinned_roll(formula, roll_name=name)
        session.update_roll_listeners()

    async def pin_dialog(self, name=None):
        with ui.dialog() as dialog, ui.card().classes("items-center") as card:
            dialog.classes("dicedialog")
            card.classes("no-shadow transparent")
            card.props("square")
            with ui.column().classes("items-center"):
                ui.label("Create Roll Preset").classes("font-bold")
                name_input = ui.input("Roll name").props("outlined")
                if name is not None:
                    name_input.value = name
                formula_input = ui.input("Roll formula", validation={'Invalid formula': lambda value: session.roll_dialog.check_formula(value)}).props("outlined")
                formula_input.value = self.roll
                ui.button("Create", on_click=lambda: self.pin(name_input.value, formula_input.value)).props("outline").bind_enabled_from(formula_input, "value", backward=lambda value: session.roll_dialog.check_formula(value))
        dialog.open()


class RollPreset(RollMessage):

    def __init__(self, roll, name, preset_id, position):
        self.roll = roll
        self.name = name
        self.preset_id = preset_id
        self.position = position

    def show_module(self):
        with ui.card() as card:
            card.classes("items-center w-full q-py-xs transparent").props("")
            card.style("box-shadow: 0 0 5px var(--q-primary) inset;")
            with ui.row().classes("w-full items-center no-wrap justify-between"):
                with ui.column().classes("items-center justify-between").style("width: 0.1rem;"):
                    ui.button(icon="arrow_drop_up", on_click=lambda: self.move_preset("up")).props("flat size=xs dense")
                    ui.button(icon="arrow_drop_down", on_click=lambda: self.move_preset("down")).props("flat size=xs dense")
                with ui.column().classes("w-full items-start no-wrap justify-start").style("gap:0.3rem;"):
                    ui.label(self.name).classes("text-md font-bold")
                    with ui.label(self.roll).classes("text-md text-slate-400").on("click", lambda: self.pin_dialog(self.name)):
                        ui.tooltip("Edit formula").classes("adapttooltip")
                with ui.row().classes("items-start no-wrap").style("gap:0.3rem;"):
                    roll_name = self.name
                    ui.button("Roll", on_click=lambda: session.roll_dialog.wait_module(self.roll, roll_name)).props("outline").classes("q-mr-sm")
                    with ui.button(icon="bi-pin-angle-fill", on_click=lambda: self.remove_preset()).props("flat size=sm dense").classes("absolute-top-right"):
                        ui.tooltip("Remove pin").classes("adapttooltip")

    def pin(self, name, formula):
        session.char.remove_pinned_roll(self.preset_id)
        session.char.add_pinned_roll(formula, roll_name=name, position=self.position)
        session.update_roll_listeners()

    def move_preset(self, direction):
        session.char.move_pinned_roll(self.preset_id, direction)
        session.update_roll_listeners()

    def remove_preset(self):
        session.char.remove_pinned_roll(self.preset_id)
        session.update_roll_listeners()
