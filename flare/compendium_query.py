import glob
import re
from copy import deepcopy
from lxml import etree as et
from wrappers import Spell, Item, Weapon, Armor, Feature, CharacterClass, Companion, CompanionFeature
import storage

class CompendiumQuery:
    def __init__(self, source_path):
        self.source_path = source_path

        self.level = None # used only when querying for a character

        if len(storage.compendium) == 0:
            self.fill_compendium()

    def fill_compendium(self):
        compendium = {}
        for filename in list(glob.iglob(self.source_path + '**/*.xml', recursive=True)) + ["./data/elements/internal_elements.xml"]:
            if not filename.endswith('.xml'):
                continue
            tree = et.parse(filename)
            for element in tree.getroot().iter():
                if not "id" in element.attrib or element.tag != "element":
                    continue
                compendium[element.attrib["id"]] = element
        storage.compendium = compendium

    def quick_query_id(self, query_id):
        return storage.compendium.get(query_id, None)

    def quick_query_parse(self, query):
        ids = re.findall(r"id='(\w*)'", query)
        elements = []
        for element_id in ids:
            element = self.quick_query_id(element_id)
            if element is not None:
                elements.append(element)
        return elements

    def read_setter(self, entry, field):
        if entry.find(f"./setters/set[@name='{field}']") is not None:
            return entry.find(f"./setters/set[@name='{field}']").text
        # if something breaks try changing this back to return ""
        return None

    def read_setter_attribs(self, entry, setter):
        if entry.find(f"./setters/set[@name='{setter}']") is not None:
            return entry.find(f"./setters/set[@name='{setter}']").attrib
        return {}

    def find_element(self, query=None, element_id=None):
        if query is not None:
            # parse id from query
            elements = self.quick_query_parse(query)
            if len(elements) > 0:
                return elements[0]
            return None
        elif element_id is not None:
            # query by id directly
            element = self.quick_query_id(element_id)
            if element is not None:
                return element
        return None
        # for filename in glob.iglob(self.source_path + '**/*.xml', recursive=True):
        #     if not filename.endswith('.xml'): continue
        #     tree = et.parse(filename)
        #     root = tree.getroot()
        #     element  = root.xpath(query)
        #     if len(element) > 0:
        #         return element[0]

    def find_all_elements(self, query):
        return self.quick_query_parse(query)
        # elements = []
        # for filename in glob.iglob(self.source_path + '**/*.xml', recursive=True):
        #     if not filename.endswith('.xml'): continue
        #     tree = et.parse(filename)
        #     root = tree.getroot()
        #     element  = root.xpath(query)
        #     if not element == None and len(element) != 0:
        #         elements += element
        # return elements

    def query_spell(self, spell, source=None):
        # NOTE aurora has weird prepared tags
        # it seems spells that aren't prepared have the always-prepared attribute no matter what
        # spells from classes that are not prepared have neither the prepared or always-prepared attribute
        # this will break something in the future for sure

        spell_id = spell.attrib["id"]
        for filename in glob.iglob(self.source_path + '**/*.xml', recursive=True):
            if not filename.endswith('.xml'):
                continue
            tree = et.parse(filename)
            root = tree.getroot()

            entry = root.find(f".//element[@type='Spell'][@id='{spell_id}']")
            if entry is None:
                continue

            components = (self.read_setter(entry, "hasVerbalComponent"), self.read_setter(entry, "hasSomaticComponent"), self.read_setter(entry, "hasMaterialComponent"))

            supports = entry.find("supports")
            spell_type = None
            if supports is not None:
                supports = supports.text.split(", ")
                if "Spell Saving Throw" in supports:
                    spell_type = "save"
                elif "Spell Attack" in supports:
                    spell_type = "attack"
                else:
                    spell_type = None

            description = et.tostring(entry.find("./description"), method='xml',with_tail=False).decode('UTF-8')

            save_type = None
            if spell_type == "save":
                save = re.search("(Intelligence|Wisdom|Charisma|Strength|Dexterity|Constitution) saving throw", description)
                if save is not None:
                    save_type = save.group(1)[:3].upper()

            spell_wrapped = Spell(spell_id,
                                entry.attrib["name"],
                                self.read_setter(entry, "level"),
                                self.read_setter(entry, "school"),
                                self.read_setter(entry, "time"),
                                self.read_setter(entry, "isRitual"),
                                self.read_setter(entry, "duration"),
                                self.read_setter(entry, "isConcentration"),
                                self.read_setter(entry, "range"),
                                deepcopy(components),
                                self.read_setter(entry, "materialComponent") if self.read_setter(entry, "hasMaterialComponent") == "true" else None,
                                description,
                                spell.attrib.get("source") if source is None else source,
                                self.read_setter(entry, "keywords"),
                                spell_type = spell_type,
                                save_type=save_type)
            # print(self.readSetter(spell, "keywords"))
            return spell_wrapped

    def query_item(self, item_id):
        for filename in glob.iglob(self.source_path + '**/*.xml', recursive=True):
            if not filename.endswith('.xml'):
                continue
            tree = et.parse(filename)
            root = tree.getroot()
            # NOTE this structure might not always hold
            item  = root.find(f"./element[@id='{item_id}']")
            if item is None:
                continue
            if item.attrib["type"] == "Weapon":
                return self.process_weapon(item)
            elif item.attrib["type"] == "Armor":
                return self.process_armor(item)
            else:
                return self.process_item(item)

    def query_item_batch(self, ids):
        if len(ids) == 0:
            return []
        id_string = "["
        id_string += " or ".join(f"@id='{i}'" for i in ids)
        id_string += "]"
        query = ".//element" + id_string
        return self.find_all_elements(query)

    def wrap_item(self, item):
        if item.attrib["type"] == "Weapon":
            return self.process_weapon(item)
        elif item.attrib["type"] == "Armor":
            return self.process_armor(item)
        else:
            return self.process_item(item)

    def process_magic_item(self, item, adorner_id):
        adorner = self.find_element(f".//element[@type='Magic Item'][@id='{adorner_id}']")
        # set up name
        name_format = self.read_setter(adorner, "name-format")
        name_format = re.sub(r"{{parent}}", item.name, name_format)
        # print(re.search())
        name_format = re.sub(r"{{([a-z \-]*)}}", lambda m: self.read_setter(adorner, m.group(1)), name_format)
        item.name = name_format
        # set up rarity
        item.rarity = self.read_setter(adorner, "rarity")
        # set up category
        item.category = self.read_setter(adorner, "category")
        # set up description
        item.description += et.tostring(adorner.find("./description"), method='xml',with_tail=False).decode('UTF-8')
        # set up attunement
        item.attunement = True if self.read_setter(adorner, "attunement") == "true" else False
        return item

    def process_item(self, item):
        cost = self.read_setter(item, "cost")
        return Item(item.attrib["id"], item.attrib["name"], self.read_setter(item, "category"),
                        cost if cost is not None else "" + self.read_setter_attribs(item, "cost").get("currency", ""),
                        self.read_setter_attribs(item, "weight").get("lb", ""),
                        et.tostring(item.find("./description"), method='xml',with_tail=False).decode('UTF-8'),
                        charges=int(self.read_setter(item, "charges")) if self.read_setter(item, "charges") is not None else None,
                        attunement=self.read_setter(item,"attunement") == "true",
                        rarity=self.read_setter(item, "rarity"))

    def process_weapon(self, weapon):
        supports = weapon.find("./supports").text
        properties = []
        for support in supports.split(","):
            support = support.strip()
            # try to query support name
            support_element = self.find_element(element_id=support)
            if support_element is not None:
                support_name = support_element.attrib.get("name", "SUPPORT MISSING NAME")
                # skip weapon group
                if "Weapon Group" in support_name:
                    continue
                properties.append(support_name)
            else:
                # fall back to id format
                words = support.split("_")
                if "CATEGORY" in words:
                    properties.append(words[-2].capitalize() + " " + words[-1].capitalize())
                elif "TYPE" in words:
                    properties.append(words[-1].capitalize())
                elif "PROPERTY" in words:
                    properties.append(words[-1].capitalize())

        base = self.process_item(weapon)

        return Weapon(base.item_id, base.name, base.category,
                      base.cost,
                      base.weight,
                      base.description,
                      properties,
                      self.read_setter(weapon, "damage"), self.read_setter_attribs(weapon, "damage").get("type", ""),
                      self.read_setter(weapon, "versatile"))

    def process_armor(self, armor):
        base = self.process_item(armor)

        return Armor(base.item_id, base.name, base.category, base.cost, base.weight, base.description,
                     self.read_setter(armor, "armor"), self.read_setter(armor, "armorClass"))

    def format_feature(self, feature):
        name = feature.attrib["name"]
        feature_id = feature.attrib["id"]
        # print(name)
        description = et.tostring(feature.find("./description"), method='xml',with_tail=False).decode('UTF-8')
        usage = None
        action = None
        display = True
        if feature.find("./sheet") is not None:
            usage = feature.find("./sheet").attrib.get("usage", None)
            action = feature.find("./sheet").attrib.get("action", None)
            name = feature.find("./sheet").attrib.get("alt", name)
            display = feature.find("./sheet").attrib.get("display", "true") == "true"
        sheet_descriptions = feature.findall("./sheet/description")
        if len(sheet_descriptions) == 1:
            sheet_description = sheet_descriptions[0].text
        elif len(sheet_descriptions) > 1:
            highest_level = 0
            sheet_description = None
            for desc in sheet_descriptions:
                description_level = int(desc.attrib.get("level", 0))
                if description_level <= self.level and description_level > highest_level:
                    highest_level = description_level
                    sheet_description = desc.text
        else:
            sheet_description = None

        if sheet_description is not None:
            sheet_description = re.sub("[\n]", "<br />", sheet_description)
            if action is None:
                if re.search("[Yy]ou can take an action", sheet_description):
                    action = "Action"
                elif re.search("[Yy]ou can take a bonus action", sheet_description):
                    action = "Bonus Action"
                elif re.search("[Oo]nce on your turn", sheet_description):
                    action = "Special"
                elif re.search("[Oo]nce per turn", sheet_description):
                    action = "Special"
                elif re.search("[Oo]nce on each of your turn", sheet_description):
                    action = "Special"
                elif re.search("[Ww]hen you cast a spell", sheet_description):
                    action = "Special"

        return Feature(feature_id, name, description, sheet_description, usage, action, display)

    def query_racial_trait(self, trait_id):
        trait = self.find_element(f".//element[@id='{trait_id}'][@type='Racial Trait']")
        # print(trait.attrib["name"])
        return self.format_feature(trait)

    def query_class_feature(self, feature_id):
        if "ID_INTERNAL_CLASS" in feature_id:
            return None
        feature = self.find_element(f".//element[@id='{feature_id}'][@type='Class Feature' or @type='Archetype Feature' or @type='Archetype']")
        return self.format_feature(feature)

    def query_class_features_batch(self, ids):
        id_string = "["
        id_string += " or ".join(f"@id='{i}'" for i in ids)
        id_string += "]"
        query = ".//element" + id_string + "[@type='Class Feature' or @type='Archetype Feature' or @type='Archetype']"
        features = []
        for feature in self.find_all_elements(query):
            if feature is not None:
                features.append(self.format_feature(feature))
        return features

    def query_features_batch(self, ids, typequery):
        id_string = "["
        id_string += " or ".join(f"@id='{i}'" for i in ids)
        id_string += "]"
        query = ".//element" + id_string + typequery
        features = []
        for feature in self.find_all_elements(query):
            if feature is not None:
                features.append(self.format_feature(feature))
        return features

    def query_feat(self, feat_id):
        feat = self.find_element(f".//element[@id='{feat_id}'][@type='Feat' or @type='Feat Feature']")
        return self.format_feature(feat)

    def query_class(self, class_id):
        class_info = self.find_element(f".//element[@type='Class'][@id='{class_id}']")
        hitdice = int(self.read_setter(class_info, "hd")[1:])
        name = class_info.attrib["name"]
        return CharacterClass(class_id, name, hitdice)

    def query_deity(self, deity_id):
        deity = self.find_element(f"./element[@id='{deity_id}']")
        return deity.attrib.get("name", None)

    def query_companion(self, companion_id):
        # NOTE: currently not using the companion variables (not sure if they are needed)
        companion = self.find_element(f"./element[@type='Companion' and @id='{companion_id}']")
        name = companion.attrib["name"]
        if companion.find("./description") is not None:
            description = et.tostring(companion.find("./description"), method='xml',with_tail=False).decode('UTF-8')
        else:
            description = None
        score_names = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        scores = {}
        for n in score_names:
            scores[n] = self.read_setter(companion, n)
        ac = self.read_setter(companion, "ac")
        hp = self.read_setter(companion, "hp")
        speed = self.read_setter(companion, "speed")
        senses = self.read_setter(companion, "senses")
        languages = self.read_setter(companion, "languages")
        condition_immunities = self.read_setter(companion, "conditionImmunities")
        skills = self.read_setter(companion, "skills")
        saves = self.read_setter(companion, "saves")
        companion_type = self.read_setter(companion, "type")
        size = self.read_setter(companion, "size")
        alignment = self.read_setter(companion, "alignment")
        challenge = self.read_setter(companion, "challenge")
        traits = self.read_setter(companion, "traits")
        traits = traits.split(",")
        actions = self.read_setter(companion, "actions")
        actions = actions.split(",")
        traits, actions = self.query_companion_features_batch(traits, actions)
        return Companion(companion.attrib["name"],
                         name=name,
                         description=description,
                         scores = scores,
                         ac = ac,
                         hp = hp,
                         speed=speed,
                         senses=senses,
                         languages=languages,
                         condition_immunities=condition_immunities,
                         skills=skills,
                         saves=saves,
                         companion_type=companion_type,
                         size=size,
                         alignment=alignment,
                         challenge=challenge,
                         traits=traits,
                         actions=actions)

    def query_companion_features_batch(self, traits, actions):
        id_string = "["
        id_string += " or ".join(f"@id='{i}'" for i in traits+actions)
        id_string += "]"
        query = ".//element" + id_string + "[@type='Companion Trait' or @type='Companion Action']"
        traits = []
        actions = []
        for feature in self.find_all_elements(query):
            if feature is not None:
                feature_wrapped = self.wrap_companion_feature(feature)
                if feature.attrib["type"] == "Companion Trait":
                    traits.append(feature_wrapped)
                elif feature.attrib["type"] == "Companion Action":
                    actions.append(feature_wrapped)
        return traits, actions

    def wrap_companion_feature(self, feature):
        description = et.tostring(feature.find("./description"), method='xml',with_tail=False).decode('UTF-8')
        sheet = feature.find("./sheet")
        action, usage = None, None
        if sheet is not None:
            action = sheet.attrib.get("action", None)
            usage = sheet.attrib.get("usage", None)
            sheet = et.tostring(sheet.find("./description"), method='xml',with_tail=False).decode('UTF-8')
        return CompanionFeature(feature.attrib["id"], name=feature.attrib["name"], description=description, sheet=sheet, action=action, usage=usage)
