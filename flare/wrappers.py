import re

class Attack:

    def __init__(self, name, attack_range, attack, damage, ability, notes, identifier=None):
        self.name = name
        self.attack_range = attack_range
        self.attack = attack
        self.damage = damage
        self.ability = ability
        self.notes = notes
        self.identifier = identifier


class Spell:

    # V/S/M
    components = (False, False, False)

    # [type, (dimensions, ...)]
    shape = None

    def __init__(self, spell_id, name, level, school, cast, ritual, duration, concentration, spell_range, components, material, description, source, keywords, spell_type=None, save_type=None):
        self.spell_id = spell_id
        self.name = name
        self.level = int(level)
        self.school = school
        self.cast = cast
        self.ritual = ritual == "true"
        self.duration = duration
        self.concentration = concentration == "true"
        self.spell_range = spell_range
        self.components = (components[0] == "true", components[1] == "true", components[2] == "true")
        self.material = material
        self.description = description.replace("indent", "indent-4")
        self.source = source
        self.keywords = str(keywords if keywords is not None else "")
        self.keywords = re.sub(r"(\w),(\w)", lambda m: f"{m.group(1)}, {m.group(2)}", self.keywords)
        # try find spell shape
        # sphere
        cylinder_parse = re.search(r"[\d]*[- ]foot[- ]radius*[,\s]*[\d]*[- ]foot[- ]high", self.description)
        sphere_parse = re.search(r"[\d]*[- ]foot[- ]radius", self.description)
        square_parse = re.search(r"[\d]*[- ]foot square", self.description)
        cube_parse = re.search(r"[\d]*[- ]foot cube", self.description)
        cone_parse = re.search(r"[\d]*[- ]foot cone", self.description)

        if cylinder_parse is not None:
            dims = cylinder_parse.group().split(" ")
            self.shape = ["cylinder", (dims[0].split("-")[0], dims[1].split("-")[0])]
        elif sphere_parse is not None:
            self.shape = ["sphere", (sphere_parse.group().split("-")[0])]
        elif square_parse is not None:
            self.shape = ["square", (square_parse.group().split("-")[0])]
        elif cube_parse is not None:
            self.shape = ["cube", (cube_parse.group().split("-")[0])]
        elif cone_parse is not None:
            self.shape = ["cone", (cone_parse.group().split("-")[0])]
        # 10-foot radius, 40-foot-high

        self.spell_type = spell_type
        self.save_type = save_type

class Spellcasting:

    def __init__(self, name, refresh, spells, slots, attack, dc, ability, modifier):
        self.name = name
        self.refresh = refresh
        self.spells = spells
        self.slots = slots
        self.attack = attack
        self.dc = dc
        self.ability = ability
        self.modifier = modifier

class Item:

    def __init__(self, item_id, name, category, cost, weight, description, storage=None, charges=None, attunement=False, rarity=None):
        self.item_id = item_id
        self.name = name
        self.category = category
        # cost contains currency
        self.cost = cost
        # weight in pounds
        if weight != "":
            self.weight = float(weight)
        else:
            self.weight = 0
        self.description = description.replace("indent", "indent-4")
        self.rarity = rarity
        self.attunement = attunement
        self.hidden = False
        self.amount = 1
        self.storage = storage
        self.charges = charges

class Weapon(Item):

    def __init__(self, weapon_id, name, category, cost, weight, description, properties, damage, damage_type, versatile):
        super().__init__(weapon_id, name, category, cost, weight, description)
        # list of parsed properties
        self.properties = properties
        self.damage = damage
        self.damage_type = damage_type
        self.versatile = versatile

class Armor(Item):

    def __init__(self, armor_id, name, category, cost, weight, description, armor_type, armor_class):
        super().__init__(armor_id, name, category, cost, weight, description)
        self.armor_type = armor_type
        self.armor_class = armor_class

class RacialTrait():

    def __init__(self, trait_id, name, description, sheet, usage, action):
        self.trait_id = trait_id
        self.name = name
        self.description = description
        self.sheet = sheet
        self.usage = usage
        self.action = action

class ClassFeature():

    def __init__(self, feature_id, name, description, sheet, usage, action):
        self.feature_id = feature_id
        self.name = name
        self.description = description
        self.sheet = sheet
        self.usage = usage
        self.action = action

class Feature():

    def __init__(self, feature_id, name, description, sheet, usage, action, display):
        self.feature_id = feature_id
        self.name = name
        self.description = description
        self.sheet = sheet
        self.usage = usage
        self.action = action
        self.display = display

    def get_id(self):
        return self.feature_id

class CharacterClass():

    def __init__(self, class_id, name, hit_dice):
        self.class_id = class_id
        self.name = name
        self.hit_dice = hit_dice

class Background():

    def __init__(self, name, trinket, traits, ideals, bonds, flaws, feature_name, feature_description):
        self.name = name
        self.trinket = trinket
        self.traits = traits
        self.ideals = ideals
        self.bonds = bonds
        self.flaws = flaws
        self.feature_name = feature_name
        self.feature_description = feature_description

class InventoryItem():

    def __init__(self, item: Item, identifier, attuned=False):
        self.item = item
        self.identifier = identifier
        self.attuned = attuned

class Companion():

    def __init__(self, companion_id=None, name=None, description=None, scores=None, ac=None, hp=None, speed=None, senses=None, languages=None, condition_immunities=None,
                 skills=None, saves=None, companion_type=None, size=None, alignment=None, challenge=None, traits=None, actions=None):
        self.companion_id = companion_id
        self.name = name
        self.description = description
        self.scores = scores
        self.ac = ac
        self.hp = hp
        self.speed = speed
        self.senses = senses
        self.languages = languages
        self.condition_immunities = condition_immunities
        self.skills = skills
        self.saves = saves
        self.companion_type = companion_type
        self.size = size
        self.alignment = alignment
        self.challenge = challenge
        self.traits = traits
        self.actions = actions



class CompanionFeature():
    # used for both companion traits and actions as they seem the same

    def __init__(self, companion_feature_id, name=None, description=None, sheet=None, usage=None, action=None):
        self.companion_feature_id = companion_feature_id
        self.name = name
        self.description = description
        self.sheet = sheet
        self.usage = usage
        self.action = action

class Variable():
    # a more flexible implementation of stats to avoid order of operation issues

    # calc format:
    # value of 4-tuples (value, bonus, requirements, equipped, level)
    # stat can be a string referring to another variable, or an int giving a number, or a string value if bonus=inline

    def __init__(self, name, calc=None):
        if calc is None:
            calc = []
        self.name = name
        self.calc = calc
        self.finalized = False
        self.value = None

    def add_to_calc(self, value, bonus=None, requirements=None, equipped=None, level=None):
        self.calc.append((value, bonus, requirements, equipped, level))
