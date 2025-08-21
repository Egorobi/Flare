import random
import re
import asyncio
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

    # work in progress
    USE_HISTORY = False

    def __init__(self):
        super().__init__()
        self.ctrl_modifier = False
        self.shift_modifier = False
        self.state = {"opened": False}

    async def wait_module(self, roll_formula, roll_name = None):
        if self.shift_modifier:
            roll_formula = re.sub(r"\d*d(\d+) ", lambda m: f"2d{m.group(1)}kh1 ", roll_formula)
        elif self.ctrl_modifier:
            roll_formula = re.sub(r"\d*d(\d+) ", lambda m: f"2d{m.group(1)}kl1 ", roll_formula)

        result = self.process_formula(roll_formula)
        if result is None:
            return

        if len(result["history"]) > 50 or not self.USE_HISTORY:
            result["history"] = []

        with ui.dialog().props("") as dialog, ui.card().classes("items-center") as card:
            dialog.classes("dicedialog w-full")
            dialog.style("outline: dotted;")
            card.classes("no-shadow transparent")
            card.props("square")
            if roll_name is not None:
                ui.label(roll_name).classes("text-md font-bold")
            message = f"Rolled {roll_formula}"
            ui.label(message)

            if len(result["history"]) > 0:
                history = result["history"]
                self.draw_dice_in_dialog(history[0])
            else:
                self.draw_dice_in_dialog(result["rolls"])

            ui.label(f"= {result["total"]}").classes("text-xl font-bold")

            values = []
            for roll in result["rolls"]:
                values.append(roll[1])
                values.append(roll[0])

            session.char.add_roll_history(roll_formula, result["total"], values, roll_name)

            ui.card().classes("absolute-center w-full h-full frameborder frame no-shadow transparent")

            session.update_roll_listeners()

            dialog.bind_value_to(self.state, "opened")
            dialog.open()

            if len(result["history"]) > 0:
                await asyncio.sleep(min(0.2, 1/len(history)))
                for i, h in enumerate(history):
                    if not self.state["opened"]: break
                    if i == 0: continue
                    self.draw_dice_in_dialog.refresh(h)
                    await asyncio.sleep(min(0.2, 1/len(history)))
                self.draw_dice_in_dialog.refresh(result["rolls"])


    @ui.refreshable
    def draw_dice_in_dialog(self, rolls):
        with ui.row().classes("items-center w-full justify-center"):
            for roll in rolls:
                if roll[2] is None:
                    with ui.card().classes("transparent no-shadow"):
                        self.show_die(roll[1], roll[0])
                else:
                    if roll[2] == "high":
                        highlight_color = "#a1793a, rgba(161, 121, 58, 0)"
                    else:
                        highlight_color = "red, rgba(255, 255, 255, 0)"
                    with ui.card().classes("transparent no-shadow"):
                        ui.element().classes("absolute-center w-full h-full").style(f"background-image: radial-gradient(closest-corner, {highlight_color});")
                        self.show_die(roll[1], roll[0])

    def process_formula(self, roll_formula):
        # return format
        # {total: x, rolls: [(sides, result, highlight), ...], history: state at every roll}

        roll_formula = self.pad_symbols(roll_formula)

        if not self.check_formula(roll_formula):
            ui.notify("Invalid roll formula")
            return None

        rolls = []

        history = []

        # find and replace parentheses
        while True:
            group = re.search(r"\(([^\(\)]*)\)", roll_formula)
            if group is None:
                break
            result = self.process_formula(group.group(1))
            # rolls += result["rolls"]
            roll_formula = roll_formula[0:group.span()[0]] + str(result["total"]) + roll_formula[group.span()[1]:]
            history += result["history"]

        # handle dice
        while True:
            dice = re.search(r"(\d*)d(\d+)(r\d+|rr\d+|min\d+|x\d*|kh\d+|kl\d+)?", roll_formula)
            if dice is None:
                break
            batch_rolls = []
            history_step = []
            roll_total = 0
            extra = dice.group(3)
            if int(dice.group(2)) not in [4, 6, 8, 10, 12, 20, 100]:
                ui.notify("Invalid dice in formula")
                return
            for _ in range(int(dice.group(1) if len(dice.group(1)) > 0 else 1)):
                die_size = int(dice.group(2))
                roll = random.randint(1, int(dice.group(2)))
                history_step.append((die_size, roll, None))
                history.append(history_step.copy())
                if extra is not None:
                    if re.match(r"^rr?\d+", extra):
                        threshold = int(re.search(r"\d+", extra).group())
                        if threshold < int(dice.group(2)):
                            while roll <= threshold:
                                roll = random.randint(1, int(dice.group(2)))
                                history_step[-1] = (die_size, roll, None)
                                history.append(history_step.copy())
                                if not re.match("rr", extra):
                                    # not recursive
                                    break
                    if re.match(r"min?\d+", extra):
                        threshold = int(re.search(r"\d+", extra).group())
                        if roll < threshold:
                            roll = threshold
                            history_step[-1] = (die_size, threshold, None)
                            history.append(history_step.copy())
                roll_total += roll
                batch_rolls.append((int(dice.group(2)), roll, None))
                if extra is not None and re.match(r"x\d*", extra):
                    # exploding dice
                    threshold = re.search(r"x(\d*)", extra).group(1)
                    if len(threshold) == 0:
                        threshold = int(dice.group(2))
                    else:
                        threshold = int(threshold)
                        if threshold == 1:
                            # prevent infinite exploding
                            threshold = int(dice.group(2))
                    while roll >= threshold:
                        roll = random.randint(1, int(dice.group(2)))
                        roll_total += roll
                        batch_rolls.append((int(dice.group(2)), roll, None))
                        history_step.append((die_size, roll, None))
                        history.append(history_step.copy())
            if extra is not None and re.match(r"k([hl])(\d+)", extra):
                # keep
                keep = re.search(r"k([hl])(\d+)", extra)
                mode = keep.group(1)
                threshold = int(keep.group(2))
                batch_sorted = sorted(batch_rolls, key = lambda r: r[1], reverse = True if mode == "h" else False)
                for i, s in enumerate(batch_sorted):
                    if i >= threshold:
                        roll_total -= s[1]
                    else:
                        i, m = next(((i, r) for i, r in enumerate(batch_rolls) if r[1] == s[1] and r[2] is None), None)
                        batch_rolls[i] = (m[0], m[1], "high" if mode == "h" else "low")
                history_step = batch_rolls.copy()
                history.append(history_step)
            rolls += batch_rolls
            roll_formula = roll_formula[0:dice.span()[0]] + str(roll_total) + roll_formula[dice.span()[1]:]

        # evaluating manually
        terms = roll_formula.split(" ")
        sign = "+"
        total = 0
        for term in terms:
            # supporting only addition and subtraction currently
            if term == "+" or term == "-":
                sign = term
            elif term.isdigit():
                total += int(sign + term)

        return {"total": total, "rolls": rolls, "history": history}

    def show_die(self, roll, die, size=10):
        f = open(f"data/assets/d{die}.svg")
        svg = f.read()
        # svg = re.sub("fill:none","fill:#000000",svg)
        # svg = re.sub("stroke:#FFC360","stroke:#808080",svg)
        # svg = re.sub("fill:none","fill:none",svg)
        svg = re.sub("stroke:#FFC360",f"stroke:{session.color_scheme[0]}",svg)
        svg = re.sub("<svg", f"<svg class='size-{size}'", svg)
        font_size = 1.5 * (size/10)
        with ui.card().classes("no-shadow transparent q-pa-none"):
            ui.html(svg).classes("absolute-center")
            color = "var(--q-adaptcolor)"
            outline = ""
            if int(roll) == 1:
                color = "#C73032"
            elif roll == die:
                color = "#d4af37"
            if color != "var(--q-adaptcolor)":
                outline = f"-webkit-text-stroke: 0.5px var(--q-adaptcolor);"
                # outline = f"text-shadow: 0px 0px 10px {color};"
            color = "var(--q-adaptcolor)"
            if die == 100:
                # ui.label(str(roll)).classes("text-xl mix-blend-difference absolute-center").style("color: {};".format(color))
                # ui.label(str(roll)).classes("text-xl absolute-center").style("color: {}; background-color: rgba(0, 0, 0, 0.3); border-radius: 5px;".format(color))
                ui.label(str(roll)).classes("absolute-center").style(f"font-size: {font_size}rem; color: {color}; backdrop-filter: blur(3px); border-radius: 5px;")
                # ui.label(str(roll)).classes("text-xl absolute-center").style("color: {}; border-radius: 5px;".format(color))
            else:
                # ui.label(str(roll)).classes("font-bold absolute-center").style(f"font-size: {font_size}rem; color: {color};")
                ui.label(str(roll)).classes("font-bold absolute-center").style(f"font-size: {font_size}rem; color: {color};")

    def roll_to_formula(self, rolls):
        formula = ""
        for roll in rolls:
            if roll[0] > 0:
                formula += f"{roll[0]}d{roll[1]} "
            if roll[2] != 0:
                formula += f"{roll[2]:+} "
        return formula

    def show_dice_values(self, values, size):
        if len(values) < 2:
            return
        for i in range(0, len(values), 2):
            self.show_die(values[i], values[i+1], size=size)

    def pad_symbols(self, roll_formula):
        roll_formula = re.sub(r"(\S)\+", lambda m: m.group(1) + " +", roll_formula)
        roll_formula = re.sub(r"\+(\S)", lambda m: "+ " + m.group(1), roll_formula)
        roll_formula = re.sub(r"(\S)-", lambda m: m.group(1) + " -", roll_formula)
        roll_formula = re.sub(r"-(\S)", lambda m: "- " + m.group(1), roll_formula)
        return roll_formula

    def check_formula(self, roll_formula):
        roll_formula = self.pad_symbols(roll_formula)

        while True:
            group = re.search(r"\(([^\(\)]*)\)", roll_formula)
            if group is None:
                break
            if not self.check_formula(group.group(1)):
                return False
            # rolls += result["rolls"]
            roll_formula = roll_formula[0:group.span()[0]] + roll_formula[group.span()[1]:]

        # no parentheses left here
        for term in roll_formula.split(" "):
            if len(term) == 0:
                continue
            if re.match(r"^(\+)|(-)|(\d+)$", term):
                continue
            if re.match(r"^(\d*)d(\d+)(r\d+|rr\d+|min\d+|x\d*|kh\d+|kl\d+)?$", term):
                if int(re.search(r"(\d*)d(\d+)", term).group(2)) not in [4, 6, 8, 10, 12, 20, 100]:
                    return False
                continue
            return False

        return True

class RollContext(Module):

    def show_module(self, modifier, roll_name=None):
        with ui.context_menu().classes("no-shadow adapttooltip").props(""):
            # ui.card().classes("frameborder absolute-center w-full h-full frame no-shadow transparent")
            ui.menu_item('Advantage', lambda: session.roll_dialog.wait_module(f"2d20kh1 + {modifier}", roll_name=roll_name), auto_close=False)
            ui.separator().classes("w-full")
            ui.menu_item('Disadvantage', lambda: session.roll_dialog.wait_module(f"2d20kl1 + {modifier}", roll_name=roll_name), auto_close=False)

class StatInfo(Module):

    @ui.refreshable
    def show_module(self, stat, name=None):
        if name is None:
            name = stat.title()
        # print(session.char.query.formatContributors(stat))
        contributors = session.char.query.format_contributors(stat)
        # print(session.char.query.get_all_contributors(stat))
        # print(contributors)
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
