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
        # cwd = os.getcwd()
        # print(cwd)
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

        ui.keyboard(self.handle_key)

        # spell id map
        for i in range(0, 10):
            for spell in session.char.spells[i]:
                storage.spell_id_map[spell.spell_id] = spell

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
        with ui.row().classes("w-full justify-center"):
            ui.button("Return to Home", on_click=lambda: ui.navigate.to("/character_select")).props("outline")

        # Help button
        help_screen = HelpScreen()
        with ui.page_sticky(x_offset=18, y_offset=18):
            ui.button(icon='question_mark', on_click=lambda: help_screen.show_module()) \
                .props('fab color=primary outline size=md')

    async def handle_key(self, e: KeyEventArguments):
        # print(e.key.name)
        if e.modifiers.ctrl and e.action.keydown:
            if e.key.name == "=":
                self.zoom(1)
            elif e.key.name == "-":
                self.zoom(-1)
        elif e.key.name == "r" and e.action.keydown:
            # try to roll selected dice
            await self.roll_selected()

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
        await self.dice_roller.roll_dice_from_string(selection)

    def zoom(self, direction):
        zoom = session.zoom
        zoom = max(0.1, zoom + 0.1*direction)
        session.zoom = zoom
        ui.run_javascript(f'document.body.style.zoom={zoom};')
