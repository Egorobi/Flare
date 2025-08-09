import session
from nicegui import ui
from modules.module import Module
from modules.dialogs import RollDiceDialog

class DiceRoller(Module):

    base = "'#FFC360'"

    def __init__(self):
        self.last_roll = [0 for _ in range(7)]
        self.roll_dialog = RollDiceDialog()
        self.custom_roll = []
        self.rolling_menu = None
        self.confirm_button = None

    @ui.refreshable
    def show_module(self):
        dice = [20, 12, 100, 10, 8, 6, 4]
        self.custom_roll = [0 for _ in range(7)]
        # darkmode = session.char.getDarkMode()
        # for d in dice:
        #     svg = ""
        #     with open('data/assets/d{}.svg'.format(d)) as file:
        #         svg = file.read()
        #     with open("data/assets/temp/roller_d{}.svg".format(d), "w") as file:
        #         svg = re.sub("stroke:#......", "stroke:"+session.colorScheme[0], svg)
        #         file.write(svg)

        # with open('data/assets/temp/roller_d20.svg') as file:
        #         print(file.read())

        # couldnt use generated svgs on the fly so instead using default colors and frame filter on the whole dice roller
        with ui.element('q-fab').props('hide-icon hide-label color=theme direction=right outline').classes("fixed-bottom-left frame q-ml-md q-mb-md") as self.sideways:
            with ui.element('q-fab-action').props('icon=more_horiz color=theme outline label-position=left text-color=theme') \
                .classes("q-ml-md").on("click", lambda: self.roll_formula_dialog()):
                ui.tooltip("Custom formula").classes('text-sm').props("anchor='center right' self='center left'").classes("adapttooltip")

        with ui.element('q-fab').props('icon=img:/assets/d20.svg color=theme direction=up outline label-class=dice-icon').classes("fixed-bottom-left frame q-ml-md q-mb-md") as parent:
            parent.on("update:modelValue", lambda e: self.update_sideways_fab(e))
            count = [0 for i in range(7)]
            self.rolling_menu = parent
            self.confirm_button = ui.element('q-fab-action').props('icon=done outline color=theme').classes("q-ml-md") \
                .on('click', lambda: self.roll_custom_dice())
            for i, die in enumerate(dice):
                label = ""
                if count[i] != 0:
                    label = "label="+str(count[i])
                dice_icon = f"icon=img:/assets/d{die}.svg"
                with ui.element('q-fab-action').props(f'{dice_icon} color=theme outline label-position=left text-color=theme dietype={die} {label}') \
                    .on('click', lambda i=i, die=die: self.set_custom_dice_count(i, die)).classes("q-ml-md") \
                    .on('contextmenu', lambda i=i, die=die: self.set_custom_dice_count(i, die, False)).classes("q-ml-md"):
                    ui.tooltip(f"D{die}").classes('text-sm').props("anchor='center right' self='center left'").classes("adapttooltip")
            # formula_input = ui.input("Roll formula", validation={'Invalid formula': lambda value: session.roll_dialog.check_formula(value)}).props("outlined")

    async def update_sideways_fab(self, e):
        value = e.args
        self.sideways.props["model-value"] = value
        self.sideways.update()

    async def roll_formula_dialog(self):
        with ui.dialog() as dialog, ui.card().classes("items-center") as card:
            dialog.classes("dicedialog")
            card.classes("no-shadow transparent")
            card.props("square")
            with ui.column().classes("items-center"):
                ui.label("Roll Custom Formula").classes("font-bold")
                formula_input = ui.input("Roll formula", validation={'Invalid formula': lambda value: session.roll_dialog.check_formula(value)}).props("outlined")
                ui.button("Create", on_click=lambda: session.roll_dialog.wait_module(formula_input.value)).props("outline").bind_enabled_from(formula_input, "value", backward=lambda value: session.roll_dialog.check_formula(value))
        dialog.open()
        self.sideways.run_method("show")

    async def roll_custom_dice(self):
        dice = [20, 12, 100, 10, 8, 6, 4]
        roll_dialog = self.roll_dialog
        # roll previous dice if no new ones are chosen
        if sum(self.custom_roll) == 0 and sum(self.last_roll) > 0:
            self.custom_roll = self.last_roll.copy()
        # roll
        await roll_dialog.wait_module(" ".join([f"{self.custom_roll[i]}d{dice[i]}" for i in range(len(dice)) if self.custom_roll[i] > 0]))
        assert self.rolling_menu is not None, "Rolling menu not initialized"
        for d in self.rolling_menu.descendants():
            if "label" in d.props:
                d.props.pop("label")
                d.update()
        self.last_roll = self.custom_roll.copy()
        self.custom_roll = [0 for i in range(7)]
        # set confirm button to reroll icon
        assert self.confirm_button is not None, "Roll button not initialized"
        self.confirm_button.props["icon"] = "cached"
        self.confirm_button.update()

    def set_custom_dice_count(self, index, dice, increase=True):
        if increase:
            self.custom_roll[index] += 1
        else:
            self.custom_roll[index] = max(0, self.custom_roll[index]-1)
        label = str(self.custom_roll[index]) if self.custom_roll[index] > 0 else "\'\'"
        assert self.rolling_menu is not None, "Rolling menu not initialized"
        next(x for i,x in enumerate(self.rolling_menu.descendants()) if x.props.get("dietype") == str(dice)).props("label="+label)
        self.rolling_menu.run_method("show")
        assert self.confirm_button is not None, "Roll button not initialized"
        self.confirm_button.props["icon"] = "done"
        self.confirm_button.update()
