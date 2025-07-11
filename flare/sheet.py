import re
from character import Character
from modules.character_info import CharacterDetails, MovementSpeed, Initiative, ArmorClass, Conditions, HeroicInspiration
from modules.head_module import HeadModule
from modules.dialogs import ShortRestDialog, LongRestDialog, RollDiceDialog, StatInfo
from modules.skills import AbilityScores, ProficiencyBonus, SavingThrows, PassiveSenses, Skills
from modules.hitpoints import Hitpoints
from modules.tabs import Tabs
from modules.dice_roller import DiceRoller
from modules.loader import LoadingDialog
from modules.help_screen import HelpScreen
from modules.roll_log import RollLog
from editors.editor import Editor
from editors.inventory import InventoryManager
from editors.notes import NotesManager
import session
import frames
import storage
from colorschemes import color_schemes
from nicegui import ui
from nicegui.events import KeyEventArguments

class Sheet():

    def __init__(self, aurora_file):
        # set saved zoom
        ui.run_javascript(f'document.body.style.zoom={session.zoom};')

        self.char = Character(aurora_file)
        session.char = self.char
        session.name = self.char.name

        session.loader = LoadingDialog()

        editor = Editor(aurora_file, self.char)
        session.inventory_manager = InventoryManager(editor)
        session.notes_manager = NotesManager(editor)

        color_scheme = session.saver.get_color(session.name)
        if color_scheme not in color_schemes:
            color_scheme = "default"
        session.color_scheme = color_schemes[color_scheme]

        # rest dialogs
        session.short_rest_dialog = ShortRestDialog()
        session.long_rest_dialog = LongRestDialog()

        # stat info dialog
        session.stat_info_dialog = StatInfo()

        # dice roller
        session.roll_dialog = RollDiceDialog()
        self.dice_roller = DiceRoller()

        # print(session.roll_dialog.process_formula("(2d4 kh1)"))
        # session.roll_dialog.wait_module("1d4x")

        ui.keyboard(self.handle_key)

        # spell id map
        for i in range(0, 10):
            for spell in session.char.spells[i]:
                storage.spell_id_map[spell.spell_id] = spell

        self.key_dice = ""

    def show_sheet(self):
        self.dice_roller.show_module() # type: ignore
        self.dice_roller.show_module.refresh()

        with ui.card().classes("everything transparent no-shadow").style("max-width: 85rem;"):
            add_head = HeadModule()
            add_head.add_head()
            character_description = CharacterDetails(self.char)
            character_description.show_module()

            with ui.row().classes("no-wrap justify-between items-center").style("gap:1.1rem;"):
                # ability scores
                ability_scores = AbilityScores()
                ability_scores.show_module()

                # proficiency bonus
                proficiency_bonus = ProficiencyBonus()
                proficiency_bonus.show_module()

                # hitpoints
                hitpoints = Hitpoints()
                hitpoints.show_module()

            with ui.row().classes("no-wrap justify-between q-gutter-md"):
                with ui.row().classes("no-wrap col-auto").style("height:45rem"):
                    with ui.column().classes("col-6 items-center"):
                        ui.image(session.char.get_portrait()).style("width: 14rem; height: 14rem;")

                        # saving throws
                        saving_throws = SavingThrows()
                        saving_throws.show_module()

                        # passive senses
                        senses = PassiveSenses()
                        senses.show_module()

                    # skills
                    skills = Skills()
                    skills.show_module()

                with ui.column().classes():
                    # ac and stuff
                    with ui.row().classes("no-wrap items-center justify-between").style("width:41rem;"):
                        # walking speed
                        movement_speed = MovementSpeed()
                        movement_speed.show_module()
                        with ui.card().classes("w-32 items-center transparent no-shadow q-pa-none").style("gap:0.1rem;"):
                            frames.show_frame("inspiration_initiative")
                            # initiative
                            initiative = Initiative()
                            initiative.show_module()
                            # inspiration
                            inspiration = HeroicInspiration()
                            inspiration.show_module()
                        # ac
                        armor_class = ArmorClass()
                        armor_class.show_module()
                        # conditions
                        conditions = Conditions()
                        conditions.show_module()

                    # all the tabs
                    with ui.card().classes("w-full q-pa-none transparent no-shadow").style("height: 37rem; width:41rem"):
                        frames.show_frame("tabs")
                        # tabs
                        tabs = Tabs()
                        tabs.show_module()
        with ui.row().classes("w-full justify-center items-center"):
            ui.button("Return to Home", on_click=lambda: ui.navigate.to("/character_select")).props("outline")
            help_screen = HelpScreen()
            ui.button(icon='question_mark', on_click=lambda: help_screen.show_module()).props('color=primary outline size=sm rounded').classes("q-pa-sm")

        # Roll log
        self.roll_log = RollLog()
        with ui.page_sticky(x_offset=18, y_offset=18):
            ui.button(icon='history', on_click=lambda: self.roll_log.show_module()).props('fab color=primary outline size=md')
        # Help button
        # help_screen = HelpScreen()
        # with ui.page_sticky(x_offset=18, y_offset=80):
        #     ui.button(icon='question_mark', on_click=lambda: help_screen.show_module()).props('fab color=primary outline padding=sm')

    async def handle_key(self, e: KeyEventArguments):
        # print(e.key.name)

        session.roll_dialog.ctrl_modifier = e.modifiers.ctrl
        session.roll_dialog.shift_modifier = e.modifiers.shift

        if e.modifiers.ctrl and e.action.keydown:
            if e.key.name == "=":
                self.zoom(1)
            elif e.key.name == "-":
                self.zoom(-1)
        elif e.key.name == "r" and e.action.keydown:
            # try to roll selected dice
            await self.roll_selected()
        elif e.key.name == "h" and e.action.keydown:
            if self.roll_log.state["opened"]:
                self.roll_log.dialog.close()
            else:
                self.roll_log.show_module()
        elif e.key.name.isdigit() and e.action.keydown:
            self.key_dice += e.key.name
        elif e.key.name == "d" and e.action.keydown:
            if "d" not in self.key_dice:
                self.key_dice += "d"
            else:
                self.key_dice = "d"
        elif e.key.name == "c" and e.action.keydown:
            dice = re.search(r"^(\d*)d(\d+)$", self.key_dice)
            if len(self.key_dice) == 0:
                self.key_dice = ""
                return
            if dice is None or int(dice.group(2)) not in [4, 6, 8, 10, 12, 20, 100]:
                ui.notify(f"Invalid dice entered: {self.key_dice}")
                self.key_dice = ""
            else:
                if dice.group(1) == "":
                    self.key_dice = "1" + self.key_dice
                await session.roll_dialog.wait_module(self.key_dice)
                self.key_dice = ""

    async def roll_selected(self):
        selection = await ui.run_javascript("""
        let text = "";

        if (window.getSelection) {
            text = window.getSelection().toString();
        } else if (document.selection && document.selection.type != "Control") {
            text = document.selection.createRange().text;
        }

        return text;
        """)
        if len(selection) == 0:
            return
        await session.roll_dialog.wait_module(selection)

    def zoom(self, direction):
        zoom = session.zoom
        zoom = max(0.1, zoom + 0.1*direction)
        session.zoom = zoom
        session.saver.save_zoom(zoom)
        ui.run_javascript(f'document.body.style.zoom={zoom};')
