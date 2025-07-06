import re
from nicegui import ui
from modules.module import Module
from modules.listeners import RollsListener
import session

class RollLog(RollsListener):

    def __init__(self):
        super().__init__()
        self.pinned_toggle = None

    def show_module(self):
        with ui.dialog().props("full-height") as dialog, ui.card() as card:
            card.classes("fixed-top-right w-1/5 h-full no-shadow q-px-none square q-py-sm").props("square bordered")
            back_space = ui.space().style("height: 0.01rem;")
            self.show_roll_history()
            self.pinned_toggle = ui.checkbox("Show Pinned", value=session.char.get_pinned_rolls_shown(), on_change=lambda e: session.char.save_pinned_rolls_shown(e.value)).classes("q-my-none q-mx-md").props("unchecked-icon='bi-pin' checked-icon='close' dense").style("z-index: 3;")
            back_space.bind_visibility_from(self.pinned_toggle, "value")
            self.show_pinned_rolls()
            # ui.card().classes("frameborder absolute-center w-full h-full frame no-shadow transparent").style("z-index: -1;")

            # ui.button("add roll", on_click=lambda: self.test_func())
            ui.card().classes("frameborder absolute-center w-full h-full frame no-shadow transparent").style("z-index: -1;")

        dialog.open()

    @ui.refreshable
    def show_roll_history(self):
        roll_history = session.char.get_roll_history()
        if not roll_history:
            return
        with ui.scroll_area().classes("w-full h-full q-pa-none") as scroll:
            with ui.column().classes("w-full flex-col-reverse").style("gap:0.85rem;"):
                for roll in roll_history:
                    message = RollMessage(roll.attrib.get("roll", None), roll.attrib.get("result", None), roll.attrib.get("values", None))
                    message.show_module()
                    ui.separator().classes("w-full")
        scroll.scroll_to(percent=100)

    @ui.refreshable
    def show_pinned_rolls(self):

        pinned_rolls = session.char.get_pinned_rolls()
        number_pinned = len(pinned_rolls)
        height = number_pinned*4 + max(0, number_pinned-1)*0.1 + (2 if number_pinned>0 else 0)
        with ui.card().classes("absolute-top q-pa-none").props("square").style("margin: 0.85rem 0.45rem; box-shadow: 0px 30px 30px black;") as card:
            if number_pinned <= 6:
                self.draw_pin_column(pinned_rolls)
            else:
                with ui.scroll_area().classes("").style(f"height: {height}rem; max-height: 55vh;").style("z-index: 2").props(""):
                    self.draw_pin_column(pinned_rolls)

        card.bind_visibility_from(self.pinned_toggle, 'value')

        # scroll.scroll_to(percent=100)
    
    def draw_pin_column(self, pinned_rolls):
        with ui.column().classes("w-full h-min q-ma-none").style("gap: 0.1rem;"):
            for roll in pinned_rolls:
                message = RollPreset(roll.attrib.get("roll", None), roll.attrib.get("name", None), roll.attrib.get("id", None))
                message.show_module()

    async def test_func(self):
        await session.roll_dialog.roll_from_formula("1d6 10d10 +2 -4")
        session.char.add_roll_history("4d8", "1")
        self.show_roll_history.refresh()

    def roll_callback(self):
        self.show_roll_history.refresh()
        self.show_pinned_rolls.refresh()

class RollMessage(Module):

    def __init__(self, roll, result, values):
        self.roll = roll
        self.result = result
        if values is not None:
            self.values = values.split(",")
        else:
            self.values = values

    def show_module(self):
        with ui.card() as card:
            card.classes("items-center w-full q-py-xs transparent").props("")
            card.style("box-shadow: 0 0 5px var(--q-primary) inset; backdrop-filter: brightness(90%);")
            with ui.row().classes("w-full h-full items-center no-wrap justify-between").style("gap: 0rem;"):
                ui.label(self.result).classes("text-2xl font-bold q-pr-sm")
                ui.separator().props("vertical")
                ui.label(self.roll).classes("text-sm text-slate-400 q-px-xs")
                with ui.button(on_click=lambda: session.roll_dialog.roll_from_formula(self.roll)).props("flat").classes("q-mr-sm q-pa-md items-center").style("width: 6rem;"):
                    count = self.dice_count(self.roll)
                    if "adv" in self.roll or "dis" in self.roll:
                        count = 2
                    with ui.grid(columns = count if count < 5 else 4).style("gap: 1.5rem;"):
                        session.roll_dialog.show_dice_in_formula(self.roll, size=5, values=self.values)
                    ui.tooltip("Re-roll").classes("adapttooltip")
            with ui.button(icon="bi-pin-angle", on_click=lambda: self.pin_dialog()).props("flat size=sm dense").classes("absolute-top-right"):
                ui.tooltip("Pin as preset").classes("adapttooltip")

    def dice_count(self, roll_formula):
        matches = re.findall(r"(\d+)d(\d+)", roll_formula)
        total = 0
        for match in matches:
            total += int(match[0])
        return total

    def pin(self, name, bonus=""):
        if bonus == "adv" or bonus == "dis":
            bonus = " " + bonus
        elif len(bonus) > 0:
            bonus = f" {int(bonus):+}"
        session.char.add_pinned_roll(self.roll+bonus, roll_name=name)
        session.update_roll_listeners()

    async def pin_dialog(self):
        with ui.dialog() as dialog, ui.card().classes("items-center") as card:
            dialog.classes("dicedialog")
            card.classes("no-shadow transparent")
            card.props("square")
            with ui.column().classes("items-center"):
                ui.label("Create Roll Preset").classes("font-bold")
                name_input = ui.input("Roll name").props("outlined")
                bonus_input = ui.input("(optional) Extra bonus", validation={'Not an integer': lambda value: re.search(r"-?\d+", value) is not None or len(value)==0 or value in ["adv", "dis"]}).props("outlined")
                ui.button("Create", on_click=lambda: self.pin(name_input.value, bonus_input.value)).props("outline")
        dialog.open()

class RollPreset(Module):

    def __init__(self, roll, name, preset_id):
        self.roll = roll
        self.name = name
        self.preset_id = preset_id

    def show_module(self):
        with ui.card() as card:
            card.classes("items-center w-full q-py-xs transparent").props("")
            card.style("box-shadow: 0 0 5px var(--q-primary) inset; backdrop-filter: brightness(90%);")
            with ui.row().classes("w-full items-center no-wrap justify-between"):
                with ui.column().classes("items-center justify-between").style("width: 0.1rem;"):
                    ui.button(icon="arrow_drop_up", on_click=lambda: self.move_preset("up")).props("flat size=xs dense")
                    ui.button(icon="arrow_drop_down", on_click=lambda: self.move_preset("down")).props("flat size=xs dense")
                with ui.column().classes("w-full items-start no-wrap justify-start").style("gap:0.3rem;"):
                    ui.label(self.name).classes("text-md font-bold")
                    ui.label(self.roll).classes("text-md text-slate-400")
                with ui.row().classes("items-start no-wrap").style("gap:0.3rem;"):
                    ui.button("Roll", on_click=lambda: session.roll_dialog.roll_from_formula(self.roll)).props("outline").classes("q-mr-sm")
                    with ui.button(icon="bi-pin-angle-fill", on_click=lambda: self.remove_preset()).props("flat size=sm dense").classes("absolute-top-right"):
                        ui.tooltip("Remove pin").classes("adapttooltip")

    def move_preset(self, direction):
        session.char.move_pinned_roll(self.preset_id, direction)
        session.update_roll_listeners()

    def remove_preset(self):
        session.char.remove_pinned_roll(self.preset_id)
        session.update_roll_listeners()
