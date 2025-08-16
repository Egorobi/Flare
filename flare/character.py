# from pdfminer.pdfparser import PDFParser
# from pdfminer.pdfdocument import PDFDocument
# from pdfminer.pdftypes import resolve1
from query import Query
from saver import Saver
import storage
# from editors.editor import Editor
# from editors.inventory import InventoryManager

class Character:

    save_file_path = ""
    pdf_path = ""
    pdf_fields = {}

    name = ""
    build = ""

    proficiency_bonus = 0
    speed = [0, 0, 0, 0]
    initiative = 0
    armor_class = 0

    current_hp = None
    max_hp = None
    temp_hp = None

    hit_dice = []

    # (score, modifier)
    ability_scores = {
        "Strength": None,
        "Dexterity": None,
        "Constitution": None,
        "Intelligence": None,
        "Wisdom": None,
        "Charisma": None
    }

    # (proficiency, modifier)
    saving_throws = {
        "STR": 0,
        "DEX": 0,
        "CON": 0,
        "INT": 0,
        "WIS": 0,
        "CHA": 0
    }

    # (proficiency, expertise, modifier)
    skills = {
    }

    # passive, perception, investiation, insight
    passive_skills = []

    # senses (sense, range)
    senses = []

    attacks = []
    attacks_per_action = 1

    # one array per level of spells, 0 for cantrips
    spells = [[],
              [],
              [],
              [],
              [],
              [],
              [],
              [],
              [],
              []]

    spellcastings = []

    inventory = []

    currency = {}

    conditions = []

    variables = {}

    characteristics = {}

    companions = []

    def __init__(self, character_path):
        self.saver = Saver()
        source_path = self.saver.get_global_content()
        self.query = Query(source_path, character_path)
        # set path to aurora savefile
        self.save_file_path = character_path
        # set path to character sheet pdf
        # self.pdfPath = pdfPath

        # read fields from pdf
        # self.readPdf()
        # self.pdfFields = self.cleanFields(self.pdfFields)

        self.update()


    # SETUP

    def update(self):
        self.set_name()

        self.saver.save_character_file_path(self.name, self.save_file_path)

        self.set_details()

        self.saver.save_portrait(self.name, self.get_portrait())
        self.saver.save_description(self.name, self.build)

        # self.saver.savePdfFilePath(self.name, self.pdfPath)

        self.set_ability_scores()
        self.set_saving_throws()
        self.set_skill_modifiers()

        self.attacks = self.query.get_character_attacks()
        self.attacks_per_action = max(1, self.query.get_variable_value("extra attack:count"))
        self.spellcastings = self.query.get_character_spells()
        self.compile_spells()

        self.inventory = self.query.get_inventory()

        self.companions = self.query.query_companions()

    def set_save_file(self, path):
        # set path to aurora savefile
        self.save_file_path = path

        self.saver.save_character_file_path(self.name, path)

        self.attacks = self.query.get_character_attacks()

        self.spellcastings = self.query.get_character_spells()
        self.compile_spells()

        self.inventory = self.query.get_inventory()

    def compile_spells(self):
        # reset spell list
        self.spells = [[] for _ in range(10)]
        # put all spells into one list for ease of iterating
        for spellcasting in self.spellcastings:
            # print(spellcasting.spells)
            for spell in spellcasting.spells:
                self.spells[spell.level].append(spell)

    def read_variable(self, variable):
        return self.query.get_variable_value(variable)

    def set_name(self):
        self.name = self.query.find_character_element(".//display-properties/name").text

    def set_details(self):
        self.build = f"Level {self.read_variable("level")} {self.query.find_character_element(".//display-properties/race").text} {self.query.find_character_element(".//display-properties/class").text}"

        self.proficiency_bonus = self.read_variable("proficiency")
        self.initiative = self.read_variable("initiative")
        # TODO initiative advantage
        self.armor_class = self.read_variable("ac:calculation")
        # TODO armor conditions
        self.speed = [
            self.read_variable("speed"),
            self.read_variable("speed:climb"),
            self.read_variable("speed:fly"),
            self.read_variable("speed:swim"),
            self.read_variable("speed:burrow")
        ]

        self.senses = self.query.query_senses()

        self.conditions = self.query.query_conditions()

        self.currency = self.query.query_currency()

        self.max_hp = self.read_variable("hp")

        self.set_characteristics()

        self.hit_dice = self.query.query_hitdice()

    def set_ability_scores(self):
        self.ability_scores["Strength"] = (self.read_variable("strength:score"), self.read_variable("strength:modifier"))
        self.ability_scores["Dexterity"] = (self.read_variable("dexterity:score"), self.read_variable("dexterity:modifier"))
        self.ability_scores["Constitution"] = (self.read_variable("constitution:score"), self.read_variable("constitution:modifier"))
        self.ability_scores["Intelligence"] = (self.read_variable("intelligence:score"), self.read_variable("intelligence:modifier"))
        self.ability_scores["Wisdom"] = (self.read_variable("wisdom:score"), self.read_variable("wisdom:modifier"))
        self.ability_scores["Charisma"] = (self.read_variable("charisma:score"), self.read_variable("charisma:modifier"))

        self.passive_skills = [self.read_variable("perception:passive"), self.read_variable("investigation:passive"), self.read_variable("insight:passive")]

    def set_saving_throws(self):
        scores = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        for score in scores:
            self.saving_throws[score[:3].upper()] = (True if self.read_variable(score+":save:proficiency") == self.proficiency_bonus else False,
                                       self.read_variable(score+":save"))

    def set_skill_modifiers(self):
        skills = ["Acrobatics", "Animal Handling", "Arcana", "Athletics", "Deception", "History", "Insight", "Intimidation", "Investigation",
                  "Medicine", "Nature", "Perception", "Performance", "Persuasion", "Religion", "Sleight of Hand", "Stealth", "Survival"]
        for skill in skills:
            self.skills[skill] = (True if self.read_variable(skill.lower()+":proficiency") == self.proficiency_bonus else False,
                                  True if self.read_variable(skill.lower()+":proficiency") == 2 * self.proficiency_bonus else False,
                                  self.read_variable(skill.lower()))

    # UPDATERS

    def update_coins(self):
        self.currency = self.query.query_currency()

    # GETTERS SETTERS

    def set_characteristics(self):
        self.characteristics = self.query.query_characteristics()

    def set_used_spellslots(self, level, uses):
        self.saver.record_used_slots(self.name, level, uses)

    def get_used_spellslots(self, level):
        return self.saver.get_used_slots(self.name, level)

    def get_hitpoints(self):
        return self.saver.get_hitpoints(self.name, self.max_hp)

    def set_hitpoints(self, current, temp):
        self.saver.record_hitpoints(self.name, current, temp)

    def get_used_hitdice(self, dice_class):
        return self.saver.get_used_hitdice(self.name, dice_class)

    def set_used_hitdice(self, dice_class, uses):
        self.saver.record_used_hitdice(self.name, dice_class, uses)

    def get_death_saves(self):
        return self.saver.get_death_saves(self.name)

    def set_death_saves(self, successes, failures):
        self.saver.record_death_saves(self.name, successes, failures)

    def get_roll_history(self):
        return self.saver.get_rolls(self.name)

    def add_roll_history(self, roll_formula, result, values=None, roll_name=None):
        self.saver.record_roll(self.name, roll_formula, result, values=values, roll_name=roll_name)

    def clear_roll_history(self):
        self.saver.clear_rolls(self.name)

    def get_pinned_rolls(self):
        return self.saver.get_pinned_rolls(self.name)

    def add_pinned_roll(self, roll_formula, roll_name=None, position=None):
        self.saver.pin_roll(self.name, roll_formula, roll_name, position)

    def remove_pinned_roll(self, pin_id):
        self.saver.remove_pinned_roll(self.name, pin_id)
    
    def get_pinned_rolls_shown(self):
        return self.saver.get_show_pinned_rolls(self.name)

    def move_pinned_roll(self, pin_id, direction):
        self.saver.move_pinned_roll(self.name, pin_id, direction)
    
    def save_pinned_rolls_shown(self, value):
        self.saver.save_show_pinned_rolls(self.name, value)

    def get_racial_traits(self):
        return self.query.get_racial_traits()

    def get_class_features(self):
        return self.query.get_class_features()

    def get_feats(self):
        return self.query.get_feats()

    def get_additional_features(self):
        return self.query.query_additional_features()

    def get_portrait(self):
        return self.query.query_portrait()

    def get_background(self):
        return self.query.query_background()

    def get_notes(self):
        notes = self.query.query_notes()
        if notes[0] != "" and notes[1] != "":
            notes_joined = "\n".join(notes)
        else:
            notes_joined = "".join(notes)
        notes_joined = notes_joined.strip()
        return notes_joined

    def get_quest_items(self):
        return self.query.query_quest_items()

    def get_treasure(self):
        return self.query.query_treasure()

    def get_combat_details(self):
        return self.query.query_combat_details()

    def get_training(self):
        return self.query.query_proficiency_hierarchy()

    def get_dark_mode(self):
        return self.saver.get_dark_mode(self.name)

    def set_dark_mode(self, dark: bool):
        if dark:
            self.saver.save_dark_mode(self.name, "true")
        else:
            self.saver.save_dark_mode(self.name, "false")

    def get_charges(self, charge_id, max_charges: int) -> int:
        return self.saver.get_charges(self.name, charge_id, str(max_charges))

    def set_charges(self, charge_id, num: int):
        self.saver.save_charges(self.name, charge_id, str(num))

    def get_inspiration(self) -> bool:
        return self.saver.get_inspiration(self.name)

    def set_inspiration(self, value: bool):
        self.saver.save_inspiration(self.name, value)

    def get_concentration(self):
        return self.saver.get_concentration(self.name)

    def set_concentration(self, spell_id, level: int):
        self.saver.save_concentration(self.name, spell_id, level)

    def get_available_spellslots(self):
        available = [False for _ in range(10)]
        available[0] = True
        for i in range(1, 10):
            for spellcasting in self.spellcastings:
                if len(spellcasting.slots) >= i:
                    available[i] = spellcasting.slots[i-1] > 0 or available[i]
        return available

    def get_total_spellslots(self):
        total = [0 for _ in range(10)]
        for i in range(1, 10):
            for spellcasting in self.spellcastings:
                if len(spellcasting.slots) >= i:
                    total[i] += spellcasting.slots[i-1]
        return total

    def calculate_total_coin_value(self, currency):
        # returns total coins in copper
        total = 0
        for _, (denom, amount) in enumerate(currency.items()):
            total += amount * (storage.coin_values[denom] / 0.01)
        return total

    def get_conditions(self):
        return self.saver.get_conditions(self.name)

    def set_conditions(self, conditions):
        self.saver.save_conditions(self.name, conditions)

    # def computeVariables(self):
    #     self.variables = self.query.computeVariables(self.variables)
