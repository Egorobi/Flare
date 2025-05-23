import random
import re
from nicegui import ui
from modules.listeners import HitDiceListener
from modules.module import Module
import session

class ShortRestDialog(HitDiceListener):

    hitdice_buttons = {}

    def __init__(self):
        session.hitdice_listeners.append(self)

    async def wait_module(self):
        char = session.char

        with ui.dialog() as dialog, ui.card().classes("no-shadow transparent items-center").props("square"):
            dialog.classes("dicedialog")
            ui.card().classes("absolute-center w-full h-full frameborder frame no-shadow transparent")
            ui.label("Short Rest").classes("text-bold text-l")
            with ui.column().classes("w-full items-start"):
                for hd in char.hit_dice:
                    self.hitdice_buttons[hd[0]] = []
                    ui.label(f"{hd[0]} (Hit Die 1d{hd[2]} - Total {hd[1]})")
                    with ui.row().classes("w-full justify-center"):
                        for _ in range(hd[1]):
                            box = ui.checkbox().on("click", lambda e: session.set_hitdice(e.sender.props, e.sender.value)
                                                                            ).props(f"unchecked-icon=check_box_outline_blank checked-icon=disabled_by_default class={hd[0]} size=xl dense").classes("w-3 h-3")
                            self.hitdice_buttons[hd[0]].append(box)
                        self.set_hitdice_buttons()
            with ui.row():
                ui.button('Yes', on_click=lambda: dialog.submit('Confirm')).props("outline")
                ui.button('Cancel', on_click=lambda: dialog.submit('Cancel')).props("outline")
        return await dialog

    def set_hitdice_buttons(self):
        for hd in session.char.hit_dice:
            dice_class = hd[0]
            if not dice_class in self.hitdice_buttons:
                return
            for i in range(len(self.hitdice_buttons[dice_class])):
                self.hitdice_buttons[dice_class][i].set_value(True if i < session.char.get_used_hitdice(dice_class) else False)

    def hitdice_callback(self):
        self.set_hitdice_buttons()

class LongRestDialog(Module):

    async def wait_module(self):
        with ui.dialog() as dialog, ui.card().classes("no-shadow transparent items-center").props("square"):
            dialog.classes("dicedialog")
            ui.card().classes("absolute-center w-full h-full frameborder frame no-shadow transparent")
            ui.label("Complete Long Rest?")
            with ui.row():
                ui.button('Yes', on_click=lambda: dialog.submit('Confirm')).props("outline")
                ui.button('Cancel', on_click=lambda: dialog.submit('Cancel')).props("outline")
        return await dialog

class RollDiceDialog(Module):

    async def wait_module(self, rolls, advantage=None):
        # print("rolling")
        if sum(r[0] for r in rolls) == 0 :
            return
        with ui.dialog() as dialog, ui.card().classes("items-center") as card:
            dialog.classes("dicedialog")
            card.classes("no-shadow transparent")
            card.props("square")
            message = ""
            if advantage is not None:
                result = 0
                if len(rolls) == 1:
                    roll = rolls[0]
                    two_rolls = (random.randint(1, roll[1]),random.randint(1, roll[1]))
                    highlight = 0
                    if advantage == "advantage":
                        result = max(two_rolls[0], two_rolls[1])
                        message = f"Rolled {roll[0]}d{roll[1]} {session.val_to_string(roll[2])} (Advantage)"
                        if two_rolls[0] > two_rolls[1]:
                            highlight = 1
                        elif two_rolls[1] > two_rolls[0]:
                            highlight = 2
                    elif advantage == "disadvantage":
                        result = min(two_rolls[0], two_rolls[1])
                        message = f"Rolled {roll[0]}d{roll[1]} {session.val_to_string(roll[2])} (Disadvantage)"
                        if two_rolls[0] < two_rolls[1]:
                            highlight = 1
                        elif two_rolls[1] < two_rolls[0]:
                            highlight = 2
                    ui.label(message)
                    if advantage == "advantage":
                        highlight_color = "#a1793a, rgba(161, 121, 58, 0)"
                    else:
                        highlight_color = "red, rgba(255, 255, 255, 0)"
                    with ui.row().classes("items-center w-full justify-center"):
                        for i in range(2):
                            if highlight == i+1:
                                with ui.card().classes("transparent no-shadow"):
                                    ui.element().classes("absolute-center w-full h-full").style(f"background-image: radial-gradient(closest-side, {highlight_color});")
                                    self.show_die(two_rolls[i], roll[1])
                            else:
                                with ui.card().classes("transparent no-shadow"):
                                    self.show_die(two_rolls[i], roll[1])
                    ui.label(f"= {result+roll[2]}").classes("text-xl font-bold")
            else:
                result = 0
                all_rolls = []
                for roll in rolls:
                    for _ in range(roll[0]):
                        all_rolls.append(random.randint(1, roll[1]))
                result = sum(all_rolls)
                all_dice = ",".join([f"{r[0]}d{r[1]}" for r in rolls if r[0] > 0])
                total_mod = sum([r[2] for r in rolls])
                message = f"Rolled {all_dice} {session.val_to_string(total_mod)}"
                ui.label(message)
                with ui.row().classes("items-center w-full justify-center"):
                    # dice = [20, 12, 100, 10, 8, 6, 4]
                    count = 0
                    for i, roll in enumerate(rolls):
                        for _ in range(roll[0]):
                            self.show_die(all_rolls[count], roll[1])
                            count += 1
                ui.label(f"= {result+total_mod}").classes("text-xl font-bold")
            ui.card().classes("absolute-center w-full h-full frameborder frame no-shadow transparent")


            dialog.open()

    def show_die(self, roll, die):
        f = open(f"data/assets/d{die}.svg")
        svg = f.read()
        # svg = re.sub("fill:none","fill:#000000",svg)
        # svg = re.sub("stroke:#FFC360","stroke:#808080",svg)
        # svg = re.sub("fill:none","fill:none",svg)
        svg = re.sub("stroke:#FFC360",f"stroke:{session.color_scheme[0]}",svg)
        svg = re.sub("<svg", "<svg class='size-10'", svg)
        with ui.card().classes("no-shadow transparent"):
            ui.html(svg).classes("absolute-center")
            color = "white"
            if roll == 1:
                color = "#C73032"
            elif roll == die:
                color = "#d4af37"
            if die == 100:
                # ui.label(str(roll)).classes("text-xl mix-blend-difference absolute-center").style("color: {};".format(color))
                # ui.label(str(roll)).classes("text-xl absolute-center").style("color: {}; background-color: rgba(0, 0, 0, 0.3); border-radius: 5px;".format(color))
                ui.label(str(roll)).classes("text-xl absolute-center").style(f"color: {color}; backdrop-filter: blur(3px); border-radius: 5px;")
                # ui.label(str(roll)).classes("text-xl absolute-center").style("color: {}; border-radius: 5px;".format(color))
            else:
                ui.label(str(roll)).classes("text-xl font-bold absolute-center").style(f"color: {color};")

class RollContext(Module):

    def show_module(self, modifier):
        with ui.context_menu().classes("no-shadow adapttooltip").props(""):
            # ui.card().classes("frameborder absolute-center w-full h-full frame no-shadow transparent")
            ui.menu_item('Advantage', lambda: session.roll_dialog.wait_module([(1, 20, modifier)], "advantage"), auto_close=False)
            ui.separator().classes("w-full")
            ui.menu_item('Disadvantage', lambda: session.roll_dialog.wait_module([(1, 20, modifier)], "disadvantage"), auto_close=False)


class StatInfo(Module):

    @ui.refreshable
    def show_module(self, stat, name=None):
        if name is None:
            name = stat.title()
        # print(session.char.query.formatContributors(stat))
        contributors = session.char.query.format_contributors(stat)
        print(session.char.query.get_all_contributors(stat))
        print(contributors)
        with ui.dialog().props("full-height") as dialog, ui.card() as card:
            card.classes("fixed-top-right w-2/5 q-pa-none h-full no-shadow").props("square bordered")
            with ui.scroll_area().classes("w-full h-full q-pa-none"):
                ui.label(f"{name} {session.char.query.get_variable_value(stat):+d}").classes('text-xl font-bold text-primary')
                ui.separator().classes("w-full font-bold").props("color=primary")
                for c in contributors:
                    self.recursive_indent(c)
            ui.card().classes("frameborder absolute-center w-full h-full frame no-shadow transparent").style("z-index: -1;")

        dialog.open()

    def recursive_indent(self, contributors):
        if isinstance(contributors[1], list):
            # with ui.column().classes("w-full"):
            #     ui.label(contributors[0])
            #     with ui.row().classes("w-full"):
            #         ui.separator().props("vertical")
            #         for c in contributors[1]:
            #             self.recursiveIndent(c)
            with ui.column().classes("w-full").style("gap:0.2rem;"):
                ui.label(contributors[0])
                with ui.list().classes("q-px-md" if contributors[0] is not None else ""):
                    for c in contributors[1]:
                        self.recursive_indent(c)
        else:
            ui.label(f"{contributors[1]:+d} {contributors[0]}")
