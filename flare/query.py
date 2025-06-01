import re
import math
# from ast import literal_eval
from lxml import etree as et
from wrappers import Attack, Spellcasting, Armor, Background, InventoryItem
from compendium_query import CompendiumQuery

class Query:

    variables = {}
    variable_bonus = {}

    def __init__(self, source_path, character_path):
        self.parser = et.XMLParser(remove_blank_text=False, compact=False, strip_cdata=False)
        self.character_file = character_path
        self.compendium = CompendiumQuery(source_path)
        self.compendium.level = Query.query_level_from_file(character_path)
        self.variables = {}
        self.variable_bonus = {} # (stat, bonus) -> value
        self.contributions = {} # stat -> [(stat, alt/element, value, bonus=None)]
        self.smart_vars = {}
        self.compute_variables()

    def get_character_attacks(self):
        tree = et.parse(self.character_file, self.parser)
        root = tree.getroot()

        attacks = []

        for attack in root.findall(".//attacks/attack"):
            attack_wrapped = Attack(attack.attrib.get("name", None), attack.attrib.get("range", None), attack.attrib.get("attack", None), attack.attrib.get("damage", None), attack.attrib.get("ability", None),
                                   attack.find("./description").text, identifier=attack.attrib.get("identifier", None))
            attacks.append(attack_wrapped)

        return attacks

    def get_character_spells(self):
        character_tree = et.parse(self.character_file, self.parser)
        character_root = character_tree.getroot()

        spellcastings = []

        # add spells from granted spellcasting
        for spellcasting in character_root.findall(".//magic/spellcasting"):
            spells = []
            for spell in spellcasting.findall(".//spell"):
                # NOTE aurora has weird prepared tags
                # it seems spells that aren't prepared have the always-prepared attribute no matter what
                # for non-prepare casters unprepared spells will have neither tag
                # spells from classes that are not prepared have neither the prepared or always-prepared attribute
                # this will break something in the future for sure
                if spell.attrib["level"] != "0":
                    if ("always-prepared" in spell.attrib and not "prepared" in spell.attrib) or ((not "prepared" in spell.attrib) and (not "known" in spell.attrib)):
                        continue
                spells.append(self.compendium.query_spell(spell, source=spellcasting.attrib["name"]))
            slots = self.get_spellcasting_slots(spellcasting)
            attack =int(spellcasting.attrib["attack"])
            dc = int(spellcasting.attrib["dc"])
            ability = spellcasting.attrib["ability"]
            modifier = int(self.get_variable_value(ability.lower() + ":modifier"))
            spellcasting_wrapped = Spellcasting(spellcasting.attrib["name"], "Long Rest", spells, slots, attack, dc, ability, modifier)
            spellcastings.append(spellcasting_wrapped)

        additonal = character_root.find(".//magic/additional")

        # add spells from additional
        if additonal is not None:
            spells = []
            for spell in additonal.findall("./spell"):
                if "always-prepared" in spell.attrib and not "prepared" in spell.attrib:
                    continue
                spells.append(self.compendium.query_spell(spell))
            additional_spells = Spellcasting("Additional", "Long Rest", spells, [], 0, 0, "", 0)
            spellcastings.append(additional_spells)

        return spellcastings

    def get_character_spellslots(self):
        slots = []
        for i in range(9):
            slots.append(0)

        tree = et.parse(self.character_file, self.parser)
        root = tree.getroot()
        for i in range(1, 10):
            for slot in root.findall(".//magic//slots"):
                slots[i-1] += int(slot.attrib["s" + str(i)])
        return slots

    def get_spellcasting_slots(self, spellcasting):
        slots = []
        for i in range(9):
            slots.append(0)
        for i in range(1, 10):
            for slot in spellcasting.findall("./slots"):
                slots[i-1] = int(slot.attrib["s" + str(i)])
        return slots

    def get_inventory(self):
        inventory = []
        ids = []
        items = []
        for item in self.find_character_elements(".//equipment/item"):
            items.append(item)
            ids.append(item.attrib["id"])
        item_entries = self.compendium.query_item_batch(ids)

        for item in items:
            entry = next((x for x in item_entries if item.attrib["id"] == x.attrib["id"]), None)
            if entry is None:
                continue
            item_wrapped = self.compendium.wrap_item(entry)
            adorner = item.find("./items/adorner")
            name_override = item.find("./details/name")
            if name_override is not None and re.search(r"[\w]", name_override.text) is not None:
                item_wrapped.name = name_override.text
            description_override = item.find("./details/notes")
            if description_override is not None and re.search(r"[\w]", description_override.text) is not None:
                item_wrapped.description += f"<br><i>{description_override.text}</i>"
            if adorner is not None:
                item_wrapped = self.compendium.process_magic_item(item_wrapped, adorner.attrib["id"])
            # if itemWrapped != None:
            #     inventory.append(itemWrapped)
            item_wrapped.hidden = item.attrib.get("hidden", "") == "true"
            if "amount" in item.attrib:
                item_wrapped.amount = int(item.attrib["amount"])
            # item storage container
            storage = item.find("./storage/location")
            if storage is not None:
                item_wrapped.storage = storage.text
            if item_wrapped is not None:
                inventory_item = InventoryItem(item_wrapped, item.attrib["identifier"])
                if item.find("./attunement") is not None:
                    inventory_item.attuned = item.find("./attunement").text == "true"
                inventory.append(inventory_item)

        # for item in self.findCharacterElements(".//equipment/item"):
        #     itemWrapped = self.compendium.queryItem(item.attrib["id"])
        #     adorner = item.find("./items/adorner")
        #     nameOverride = item.find("./details/name")
        #     if nameOverride != None and re.search(r"[\w]", nameOverride.text) != None:
        #         itemWrapped.name = nameOverride.text
        #     descriptionOverride = item.find("./details/notes")
        #     if descriptionOverride != None and re.search(r"[\w]", descriptionOverride.text) != None:
        #         itemWrapped.description += "<br><i>{}</i>".format(descriptionOverride.text)
        #     if adorner != None:
        #         itemWrapped = self.compendium.processMagicItem(itemWrapped, adorner.attrib["id"])
        #     if itemWrapped != None:
        #         inventory.append(itemWrapped)
        return inventory

    def find_character_element(self, query):
        tree = et.parse(self.character_file, self.parser)
        root = tree.getroot()
        return root.find(query)

    def find_character_elements(self, query):
        tree = et.parse(self.character_file, self.parser)
        root = tree.getroot()
        elements = root.xpath(query)
        return elements

    def get_racial_traits(self):
        ids = []
        for element in self.find_character_elements("./build/sum/element[@type='Racial Trait']"):
            ids.append(element.attrib["id"])
        return self.wrap_features(ids, "[@type='Racial Trait']")

    def get_class_features(self):
        ids = []
        for element in self.find_character_elements("./build/sum/element[@type='Class Feature']") + self.find_character_elements(".//sum/element[@type='Archetype Feature']") + self.find_character_elements(".//sum/element[@type='Archetype']"):
            ids.append(element.attrib["id"])
        return self.wrap_features(ids, "[@type='Class Feature' or @type='Archetype Feature' or @type='Archetype']")

    def get_feats(self):
        ids = []
        for element in self.find_character_elements("./build/sum/element[@type='Feat']") + self.find_character_elements(".//sum/element[@type='Feat Feature']"):
            ids.append(element.attrib["id"])
        return self.wrap_features(ids, "[@type='Feat' or @type='Feat Feature']")

    def wrap_features(self, ids, typequery):
        if len(ids) == 0:
            return [], {}
        features = []
        wrapped = self.compendium.query_features_batch(ids, typequery)
        child_dict = {}
        for feature in wrapped:
            children = self.get_children_features(feature.feature_id)
            if len(children) > 0:
                if feature.feature_id in child_dict:
                    child_dict[feature.feature_id] += children
                else:
                    child_dict[feature.feature_id] = children
            if feature.sheet is not None:
                feature.sheet = self.format_variables(feature.sheet)
                if feature.usage is not None:
                    feature.usage = self.format_variables(feature.usage)
                if feature.feature_id not in child_dict:
                    child_dict[feature.feature_id] = []
                features.append(feature)
            elif len(children) > 0 or self.check_parent_feature(feature.feature_id):
                features.append(feature)
        return features, child_dict

    def check_parent_feature(self, feature_id):
        # name is confusing, checks if feature has a parent
        feature = self.find_character_element(f"./build/elements//element[@registered='{feature_id}']")
        if feature is None:
            return False
        else:
            return True

    def check_if_child(self, feature_id, child_dict):
        for child_id in child_dict:
            if feature_id in child_dict[child_id]:
                return True
        return False

    def get_parent_feature(self, feature_id):
        parent = self.find_character_element(f"./build/elements//element[@registered='{feature_id}']")
        if parent is None:
            return None
        else:
            return parent.attrib.get("id")

    def get_children_features(self, feature_id):
        feature = self.find_character_element(f"./build/elements//element[@id='{feature_id}']")
        if feature is None:
            return []
        else:
            children = [c.attrib["registered"] for c in feature.findall("./element") if "registered" in c.attrib]
            return children

# VARIABLES

    def get_variable_value(self, s):
        # return value directly
        if s.isdigit() or ((s.startswith('-') or s.startswith('+')) and s[1:].isdigit()):
            return int(s)
        # calculate half
        if s.endswith(":half"):
            return self.get_variable_value(re.sub(":half$", "", s)) // 2
        elif s.endswith(":half:up"):
            return -(self.get_variable_value(re.sub(":half:up$", "", s)) // -2)
        # return variable
        if s in self.variables:
            return self.variables[s]
        # calculate ability modifier
        if s.endswith(":modifier"):
            return (self.get_variable_value(s.split(":")[0]+":score") - 10) // 2
        # calculate score
        # max of (score capped by max score) and set score
        if s.endswith(":score"):
            score = s.split(":")[0]
            return max(min(self.variables[score], self.variables[score+":max"]), self.get_variable_value(score+":score:set"))
        return 0

    def format_variables(self, string):
        try:
            string = re.sub(r"{{([a-z: \-]*)}}", lambda m: str(self.get_variable_value(m.group(1))), string)
        except:
            print("Failed to find variable for: " + string)
        return string

    def set_basic_variables_2(self):
        # level
        self.variables["level"] = int(self.find_character_element(".//level").text)
        self.variables["level:half"] = self.variables["level"] // 2
        self.variables["level:half:up"] = -(self.variables["level"] // -2)
        # scores
        scores = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        for score in scores:
            self.variables[score] = int(self.find_character_element(f"./build/abilities/{score}").text)

    def set_basic_variables(self):
        # NOTE deprecated with internal elements - not yet
        # Need to do manually:
        # level, proficiency

        # level
        self.variables["level"] = int(self.find_character_element(".//level").text)
        # self.variables["level:half"] = self.variables["level"] // 2
        # self.variables["level:half:up"] = -(self.variables["level"] // -2)
        class_text = self.find_character_element(".//class").text
        class_names = []
        class_levels = []
        if not "(" in class_text:
            class_names = [class_text.lower()]
            class_levels = [self.variables["level"]]
        else:
            for cls in class_text.split("/ "):
                class_names.append(re.search("[a-zA-Z]*", cls).group().lower())
                class_levels.append(int(re.search(r"\(.*\)", cls).group().strip("()")))

        for i, class_name in enumerate(class_names):
            self.variables["level:" + class_name] = class_levels[i]
            # self.variables["level:" + classNames[i] + ":half"] = classLevels[i] // 2
            # self.variables["level:" + classNames[i] + ":half:up"] = -(classLevels[i] // -2)
        # proficiency
        if self.variables["level"] <= 4:
            self.variables["proficiency"] = 2
        elif self.variables["level"] <= 8:
            self.variables["proficiency"] = 3
        elif self.variables["level"] <= 12:
            self.variables["proficiency"] = 4
        elif self.variables["level"] <= 16:
            self.variables["proficiency"] = 5
        else:
            self.variables["proficiency"] = 6
        # self.variables["proficiency:half"] = self.variables["proficiency"] // 2
        # self.variables["proficiency:half:up"] = -(self.variables["proficiency"] // -2)

        # max scores and attunement
        self.process_element("ID_INTERNAL_FLARE_GRANTS_CHARACTER_BASE")

        # ability scores
        scores = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        for score in scores:
            base_score = int(self.find_character_element(f"./build/abilities/{score}").text)
            self.variables[score] = base_score
            self.contributions.setdefault(score, []).append((None, f"{score.capitalize()} Score", base_score, None))
            # self.variables[score+":max"] = 20
        # attunement
        # self.variables["attunement"] = 3
        # proficiencies
        # for prof in proficiencies:
        #     skillMatch = re.search("ID_PROFICIENCY_SKILL_([A-Z]*)", prof)
        #     saveMatch = re.search("ID_PROFICIENCY_SAVINGTHROW_([A-Z]*)", prof)
        #     if skillMatch != None:
        #         self.variables[skillMatch.group(1).lower() + ":proficiency"] = self.variables["proficiency"]
        #     elif saveMatch != None:
        #         self.variables[saveMatch.group(1).lower() + ":save:proficiency"] = self.variables["proficiency"]

    def translate_operators(self, string):
        string = string.replace("||", " or ")
        string = string.replace("&&", " and ")
        string = string.replace(",", " and ")
        string = string.replace("!", "not ")
        return string

    def check_requirements(self, requirements, all_ids):
        print_debug = False
        # convert aurora operators to python operators
        requirements = self.translate_operators(requirements)
        if print_debug:
            print(requirements)
        # convert ids to bools
        requirements = re.sub(r"(ID_[A-Z_]*)", lambda m: str(m.group(1) in all_ids), requirements)
        score_map = {
            "str": "strength",
            "dex": "dexterity",
            "con": "constitution",
            "int": "intelligence",
            "wis": "wisdom",
            "cha": "charisma"
        }
        # convert stat requirements to bools
        requirements = re.sub(r"\[([a-z ]*):(\d*)\]", lambda m: str(self.variables[score_map[m.group(1)]] >= int(m.group(2)) if m.group(1) in score_map else self.get_variable_value(m.group(1)) >= int(m.group(2))), requirements)
        # convert type requirements to bools
        requirements = re.sub(r"\[type:([a-z ]*)\]", lambda m: str(self.find_character_element(f".//element[@type='{m.group(1)}']") is not None), requirements)
        # convert level requirements to bools
        requirements = re.sub(r"\[level:(\d*)\]", lambda m: str(self.variables["level"] >= int(m.group(1))), requirements)
        if print_debug:
            print(requirements)
            print(eval(requirements))
        # NOTE: literal_eval can't handle boolean expressions like "not False"
        try:
            return eval(requirements)
        except:
            return False

    # def computeSmartStat(self, stat):
    #     # UNUSED
    #     # check if variable is new
    #     statName = stat.attrib["name"]
    #     if not statName in self.smartVars:
    #         statVar = Variable(statName)
    #     bonus = stat.attrib.get("bonus")

    #     value = stat.attrib["value"]
    #     if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
    #         value = int(value)

    #     requirements = stat.attrib.get("requirements")


    def compute_stat(self, stat, contributor):
        if not stat.attrib["name"] in self.variables:
            self.variables[stat.attrib["name"]] = 0
        # types of bonus
        # base, double, proficiency, calculation
        bonus = stat.attrib.get("bonus")
        name = stat.attrib["name"]
        if stat.attrib.get("inline") == "true":
            # used for string values, always overrides previous value
            self.variables[name] = stat.attrib["value"]
            return
        value = self.get_variable_value(stat.attrib["value"])
        # stat maximum
        if "maximum" in stat.attrib:
            value = min(value, self.get_variable_value(stat.attrib["maximum"]))

        contribs = self.contributions.get(name, [])
        alt = contributor
        contributor = None
        if stat.attrib["value"] in self.contributions:
            contributor = stat.attrib["value"]

        if bonus is not None:
            current_bonus = self.variable_bonus.get((name, bonus))
            if current_bonus is None:
                self.variables[name] = self.get_variable_value(name) + value
                self.variable_bonus[(name, bonus)] = value
                # store contribution with bonus
                contribs.append((contributor, alt, value, bonus))
            else:
                # compare and keep higher bonus
                if value > current_bonus:
                    self.variable_bonus[(name, bonus)] = value
                    # current bonus is replaced with new one
                    self.variables[name] = self.get_variable_value(name) - current_bonus + value
                    # replace old contributor with new one
                    for index, contrib in enumerate(contribs):
                        if contrib[3] == bonus:
                            contribs[index] = (contributor, alt, value, bonus)
            # store contribution
            self.contributions[name] = contribs
        else:
            self.variables[name] = self.get_variable_value(name) + value
            # store contribution
            contribs.append((contributor, alt, value, None))
            self.contributions[name] = contribs

    def add_to_variable(self, variable, value):
        if not variable in self.variables:
            self.variables[variable] = 0
        self.variables[variable] += value

    def check_equipped(self, equipped, requirement):
        requirement = self.translate_operators(requirement)
        # armor type check
        # TODO: dont count shield as armor?
        requirement = re.sub(r"\[armor:none\]", lambda m: str(len([1 for i in equipped if isinstance(i, Armor)]) == 0), requirement)
        requirement = re.sub(r"\[armor:any\]", lambda m: str(len([1 for i in equipped if isinstance(i, Armor)]) > 0), requirement)
        requirement = re.sub(r"\[armor:([a-z- ]*)\]", lambda m: str(len([1 for i in equipped if isinstance(i, Armor) and i.armor_type.lower() == m.group(1).lower()]) > 0), requirement)
        # shield check TODO improve
        requirement = re.sub(r"\[shield:none\]", lambda m: str(len([1 for i in equipped if isinstance(i, Armor) and i.armor_type.lower() == "shield"]) == 0), requirement)
        requirement = re.sub(r"\[shield:any\]", lambda m: str(len([1 for i in equipped if isinstance(i, Armor) and i.armor_type.lower() == "shield"]) > 0), requirement)
        # weapon check
        # this list should be computed elsewhere
        equipped_with_location = []
        for equip in equipped:
            info = self.find_character_element(f".//item[@id='{equip.item_id}']/equipped")
            equipped_with_location.append((equip, info.attrib.get("location", "none").split()[0].lower() and info.text == "true"))
        for slot in ["primary", "secondary"]:
            requirement = re.sub(r"\["+slot+r":none\]", lambda m, s=slot: str(next((e for e in equipped_with_location if e[1] == s), None) is None), requirement)
            requirement = re.sub(r"\["+slot+r":any\]", lambda m, s=slot: str(next((e for e in equipped_with_location if e[1] == s), None) is not None), requirement)
            requirement = re.sub(r"\["+slot+r":([a-z- ])\]", lambda m, s=slot: str(next((e for e in equipped_with_location if e[1] == s and m.group(1).capitalize() in e[0].properties), None) is not None), requirement)
        # requirement = re.sub

        try:
            return eval(requirement)
        except:
            return False

    def apply_final_variables(self):
        # NOTE deprecated with internal elements - not yet
        # Can get from file:
        # con from level, skills, generic spellcasting
        # Done: AC, speeds, initiative

        # speeds
        self.process_element("ID_INTERNAL_FLARE_GRANTS_SPEED")
        # self.addToVariable("speed", self.getVariableValue("innate speed"))
        # for s in ["climb", "fly", "swim", "burrow"]:
        #     if "innate speed:"+s in self.variables:
        #         self.addToVariable("speed:"+s, self.variables["innate speed:"+s])
        #     else:
        #         self.addToVariable("speed:"+s, 0)

        # hp
        health = 0
        rand_hp = {}
        class_count = {}
        average_hp = self.find_character_element("./build/sum/element[@id='ID_INTERNAL_OPTION_ALLOW_AVERAGE_HP']") is not None
        for rand in self.find_character_elements(".//element[@type='Level'][@rndhp]"):
            rand_hp[rand.attrib.get("class", "base")] = rand.attrib["rndhp"].split(",")
            class_count[rand.attrib.get("class", "base")] = 0
        for i in range(self.get_variable_value("level")):
            health_change = 0
            health_change += self.get_variable_value("constitution:modifier")
            lvl = self.find_character_element(f".//element[@type='Level'][@name='{i+1}']")
            if lvl.attrib.get("multiclass") == "true":
                class_count[lvl.attrib["class"]] += 1
                if average_hp:
                    health_change += int(math.ceil(int(rand_hp[lvl.attrib["class"]][0])/2 + 0.5))
                else:
                    health_change += int(rand_hp[lvl.attrib["class"]][class_count[lvl.attrib["class"]]-1])
            else:
                class_count["base"] += 1
                if average_hp and class_count["base"] != 1:
                    health_change += int(math.ceil(int(rand_hp["base"][0])/2 + 0.5))
                else:
                    health_change += int(rand_hp["base"][class_count["base"]-1])
            health += max(health_change, 1)
        # print(f"CURRENT HP: {health}")
        self.variables["hp"] = self.get_variable_value("hp") + health

        # initiative
        self.process_element("ID_INTERNAL_FLARE_GRANTS_INITIATIVE")
        # self.variables["initiative"] = self.getVariableValue("dexterity:modifier") + self.getVariableValue("initiative:misc")

        # saves
        scores = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        # for score in scores:
        #     self.variables[score + ":save"] = self.get_variable_value(score+":save:proficiency") + self.get_variable_value(score+":save:misc") + self.get_variable_value(score+":modifier")
        self.process_element("ID_INTERNAL_FLARE_GRANTS_SAVING_THROWS")
        # skills
        str_skills = ["athletics"]
        dex_skills = ["acrobatics", "sleight of hand", "stealth"]
        int_skills = ["arcana", "history", "investigation", "nature", "religion"]
        wis_skills = ["animal handling", "insight", "medicine", "perception", "survival"]
        cha_skills = ["deception", "intimidation", "performance", "persuasion"]
        for skill in str_skills + dex_skills + int_skills + wis_skills+ cha_skills:
            self.variables[skill] = self.get_variable_value(skill + ":proficiency") + self.get_variable_value(skill + ":misc")
            self.contributions[skill] = [(skill+":proficiency", None, self.get_variable_value(skill + ":proficiency"), None),
                                               (skill+":misc", None, self.get_variable_value(skill + ":misc"), None)]
        for str_skill in str_skills:
            self.variables[str_skill] += self.get_variable_value("strength:modifier")
            self.contributions.setdefault(str_skill, []).append((None, "Strength Modifier", self.get_variable_value("strength:modifier"), None))
        for dex_skill in dex_skills:
            self.variables[dex_skill] += self.get_variable_value("dexterity:modifier")
            self.contributions.setdefault(dex_skill, []).append((None, "Dexterity Modifier", self.get_variable_value("dexterity:modifier"), None))
        for int_skill in int_skills:
            self.variables[int_skill] += self.get_variable_value("intelligence:modifier")
            self.contributions.setdefault(int_skill, []).append((None, "Intelligence Modifier", self.get_variable_value("intelligence:modifier"), None))
        for wis_skill in wis_skills:
            self.variables[wis_skill] += self.get_variable_value("wisdom:modifier")
            self.contributions.setdefault(wis_skill, []).append((None, "Wisdom Modifier", self.get_variable_value("wisdom:modifier"), None))
        for cha_skill in cha_skills:
            self.variables[cha_skill] += self.get_variable_value("charisma:modifier")
            self.contributions.setdefault(cha_skill, []).append((None, "Charisma Modifier", self.get_variable_value("charisma:modifier"), None))
        for skill in str_skills + dex_skills + int_skills + wis_skills+ cha_skills:
            self.variables[skill+":passive"] = 10 + self.get_variable_value(skill+":passive") + self.get_variable_value(skill)
            self.contributions.setdefault(skill+":passive", []).append((None, "Base", 10, None))
            self.contributions.setdefault(skill+":passive", []).append((skill, f"{skill.capitalize()} Modifier", self.get_variable_value(skill), None))
        # ac
        self.process_element("ID_INTERNAL_FLARE_GRANTS_ARMOR_CLASS")
        # check equipped armor type
        # armor = None
        # for item in equipped:
        #     if type(item) == Armor and item.armorType != "Shield":
        #         armor = item
        # if armor == None and not "ac:calculation" in self.variables:
        #     # default ac
        #     self.variables["ac"] = 10 + self.getVariableValue("dexterity:modifier") + self.getVariableValue("ac:shield")
        # elif armor == None and "ac:calculation" in self.variables:
        #     self.variables["ac"] = self.getVariableValue("ac:calculation")
        # elif "ac:calculation" in self.variables:
        #     self.variables["ac"] = self.getVariableValue("ac:calculation")
        # else:
        #     self.variables["ac"] = 0
        #     if armor.armorType.lower() == "light":
        #         self.variables["ac"] = self.getVariableValue("dexterity:modifier")
        #     elif armor.armorType.lower() == "medium":
        #         self.variables["ac"] = min(self.getVariableValue("dexterity:modifier"), 2)
        #     self.variables["ac"] += (self.getVariableValue("ac:misc") + self.getVariableValue("ac:shield") + self.getVariableValue("ac:calculation")
        #                             + self.getVariableValue("ac:armored:armor") + self.getVariableValue("ac:armored:enhancement") + + self.getVariableValue("ac:armored:misc"))

        # spellcasting from class
        character_tree = et.parse(self.character_file, self.parser)
        character_root = character_tree.getroot()
        for spellcasting in character_root.findall(".//magic/spellcasting"):
            casting_class = spellcasting.attrib["name"].lower()
            casting_ability = spellcasting.attrib["ability"].lower()
            self.add_to_variable(f"{casting_class}:spellcasting:dc", 8+self.get_variable_value("proficiency")+self.get_variable_value(f"{casting_ability}:modifier"))
            self.add_to_variable(f"{casting_class}:spellcasting:attack", self.get_variable_value("proficiency")+self.get_variable_value(f"{casting_ability}:modifier"))
        # generic ability spellcasting
        for score in scores:
            self.add_to_variable(f"spellcasting:dc:{score[:3]}", 8+self.get_variable_value("proficiency")+self.get_variable_value(f"{score}:modifier"))
            self.add_to_variable(f"spellcasting:attack:{score[:3]}", self.get_variable_value("proficiency")+self.get_variable_value(f"{score}:modifier"))


    def compute_variables(self):
        elements = self.find_character_elements("./build/sum/element")
        all_ids = []
        id_string = "["
        proficiencies = []
        for element in elements:
            id_string += f"@id='{element.attrib["id"]}' or "
            all_ids.append(element.attrib["id"])
            if element.attrib["type"] == "Proficiency":
                proficiencies.append(element.attrib["id"])
        # proficiencies should only contribute once
        proficiencies = list(set(proficiencies))
        self.set_basic_variables()
        self.all_ids = all_ids

        if len(id_string) > 1:
            id_string = id_string[:-4]
        id_string += "]"
        query = ".//element" + id_string
        real_elements = []
        # unsorted list of elements in compendium
        for real_element in self.compendium.find_all_elements(query):
            real_elements.append(real_element)
        # sort elements from compendium
        sorted_elements = []
        for char_element in elements:
            for e in real_elements:
                if e.attrib["id"] == char_element.attrib["id"]:
                    sorted_elements.append(e)
                    break
        # print("SORTED ELEMENTS")
        # for e in sorted_elements:
        #     print(e.attrib["id"])

        equipped = []
        for item in self.find_character_elements(".//item"):
            equip = item.find("./equipped")
            if equip is None:
                continue
            item = self.compendium.query_item(item.attrib["id"])
            if item is not None:
                equipped.append(item)
        self.equipped = equipped

        for element in sorted_elements:
            for stat in element.findall("./rules/stat"):
                contribition_name = stat.attrib.get("alt", element.attrib.get("name", "unknown"))
                # contributionName = stat.attrib.get("alt", None)
                self.process_stat(stat, contribition_name)

        self.apply_final_variables()

        print(self.variables)
        print(self.contributions)

        # print(self.getContributors("ac:calculation"))
        # print(self.formatContributors("ac:calculation"))

    def process_stat(self, stat, contributor):
        print_debug = False
        if stat.attrib.get("requirements") is not None:
            if not self.check_requirements(stat.attrib["requirements"], self.all_ids):
                if print_debug:
                    print(f"Skippping (requirement) {stat.attrib["name"]}, {contributor}")
                return
        if stat.attrib.get("level") is not None:
            if int(stat.attrib["level"]) > self.variables["level"]:
                return
        equip_requirement = stat.attrib.get("equipped")
        if equip_requirement is not None:
            if not self.check_equipped(self.equipped, equip_requirement):
                if print_debug:
                    print(f"Skippping (equipped) {stat.attrib["name"]}")
                return
        self.compute_stat(stat, contributor)

    def process_element(self, element_id):
        element = self.compendium.find_element(f"[@id='{element_id}']")
        if element is not None:
            for stat in element.findall("./rules/stat"):
                self.process_stat(stat, stat.attrib.get("alt", element.attrib.get("name", "unknown")))

    def get_contributors(self, stat):
        all_contribs = []
        if not stat in self.contributions:
            return []
        for contrib in self.contributions[stat]:
            all_contribs.append((contrib[0], contrib[1], contrib[2], contrib[3]))
        return all_contribs

    def get_all_contributors(self, stat):
        all_contribs = []
        if not stat in self.contributions:
            return []
        for contrib in self.contributions[stat]:
            if contrib[0] is not None:
                all_contribs += self.get_contributors(contrib[0])
            else:
                all_contribs.append((contrib[0], contrib[1], contrib[2], contrib[3]))
        return all_contribs

    def format_contributors(self, stat):
        contributors = self.get_contributors(stat)
        contributor_list = []
        for contrib in contributors:
            if contrib[2] == 0:
                continue
            if contrib[0] is None:
                contributor_list.append((contrib[1] + (" " + str(contrib[3]) if contrib[3] else ""), contrib[2]))
            else:
                contributor_list.append((contrib[1], self.format_contributors(contrib[0])))
        same_name = {}
        for contrib in contributor_list:
            if not isinstance(contrib, tuple):
                continue
            if contrib[0] in same_name:
                same_name[contrib[0]] += contrib[1]
            else:
                same_name[contrib[0]] = contrib[1]
        combined_list = []
        for _, (contrib, source) in enumerate(same_name.items()):
            combined_list.append((contrib, source))
        return combined_list


# SPECIFIC ELEMENT QUERIES

    def query_senses(self):
        senses = []
        # for vis in self.findCharacterElements("./build/sum/element[@type='Vision']"):
        #     # sense = re.search(r"ID_VISION_([A-Z]*)", vis.attrib["id"]).group(1).lower()
        #     # senses.append((sense, self.getVariableValue(sense+":range")))
        sense_types = ["darkvision", "blindsight", "truesight", "tremorsense"]
        for sense in sense_types:
            sense_range = self.get_variable_value(sense + ":range")
            if sense_range > 0:
                senses.append((sense.capitalize(), sense_range))
        return senses

    def query_conditions(self):
        conditions = []
        for condition in self.find_character_elements("./build/sum/element[@type='Condition']"):
            condition_id = condition.attrib["id"]
            # try to query from internal file
            condition_element = self.compendium.find_element(element_id=condition_id)
            if condition_element is not None:
                if condition_element.attrib.get("name", None) is not None:
                    conditions.append(condition_element.attrib["name"])
                    continue

            # fall back to id format
            if condition_id.startswith("ID_INTERNAL_CONDITION_DAMAGE_RESISTANCE_"):
                conditions.append(condition_id.split("_")[-1].capitalize() + " Resistance")
            elif condition_id.startswith("ID_INTERNAL_CONDITION_DAMAGE_IMMMUNITY_"):
                conditions.append(condition_id.split("_")[-1].capitalize() + " Immunity")
        return conditions

    def query_currency(self):
        denoms = ["platinum", "gold", "electrum", "silver", "copper"]
        money = {}
        currency = self.find_character_element("./build/input/currency")
        for denom in denoms:
            money[denom] = int(currency.find("./"+denom).text)
        return money

    def query_portrait(self):
        return self.find_character_element("./display-properties/portrait/local").text

    def query_hitdice(self):
        # class, level, dice(no d)
        hd = []
        for char_class in self.find_character_elements("./build/sum/element[@type='Class']") + self.find_character_elements("./build/sum/element[@type='Multiclass']"):
            char_wrapped = self.compendium.query_class(re.sub("_MULTICLASS_", "_CLASS_", char_class.attrib["id"]))
            hd.append((char_wrapped.name, self.get_variable_value("level:"+char_wrapped.name.lower()), char_wrapped.hit_dice))
        return hd

    def query_background(self):
        name = self.find_character_element("./display-properties/background").text
        trinket = self.find_character_element("./build/input/background-trinket").text
        traits = self.find_character_element("./build/input/background-traits").text
        ideals = self.find_character_element("./build/input/background-ideals").text
        bonds = self.find_character_element("./build/input/background-bonds").text
        flaws = self.find_character_element("./build/input/background-flaws").text
        feature_name = self.find_character_element("./build/input/background/feature").attrib["name"]
        feature_name = self.find_character_element("./build/input/background/feature/description").text
        return Background(name, trinket, traits, ideals, bonds, flaws, feature_name, feature_name)

    def query_characteristics(self):
        characteristics = {}
        alignment_array = self.find_character_element(".//sum/element[@type='Alignment']")
        if alignment_array is not None:
            alignment_array = alignment_array.attrib["id"].split("_")
            alignment = alignment_array[2].capitalize()
            if len(alignment_array) > 3:
                alignment += " " + alignment_array[3].capitalize()
            characteristics["alignment"] = alignment
        else:
            characteristics["alignment"] = ""
        deity = self.find_character_element(".//sum/element[@type='Deity']")
        if deity is not None:
            characteristics["faith"] = self.compendium.query_deity(deity.attrib["id"])
        else:
            characteristics["faith"] = ""
        gender = self.find_character_element("./build/input/gender")
        characteristics["gender"] = gender.text if gender is not None else ""
        appearance = ["hair", "eyes", "skin", "age", "height", "weight"]
        for a in appearance:
            entry = self.find_character_element("./build/appearance/"+a)
            characteristics[a] = entry.text if entry is not None else ""
        size = self.find_character_element("./build/sum/element[@type='Size']").attrib.get("id", "")
        size = size.split("_")[-1].capitalize()
        characteristics["size"] = size
        return characteristics

    def query_additional_features(self):
        additional = self.find_character_element("./build/input/additional-features")
        if additional is None:
            return ""
        return additional.text

    def query_notes(self):
        notes = self.find_character_element("./build/input/notes")
        left_notes = notes.find("./note[@column='left']")
        right_notes = notes.find("./note[@column='right']")
        left_note_text = left_notes.text if left_notes is not None else ""
        if left_note_text is None:
            left_note_text = ""
        right_note_text = right_notes.text if right_notes is not None else ""
        if right_note_text is None:
            right_note_text = ""
        return [left_note_text, right_note_text]

    def query_quest_items(self):
        quest = self.find_character_element("./build/input/quest")
        if quest is not None and quest.text is not None and re.search(r"\w", quest.text) is not None:
            return quest.text
        return None

    def query_treasure(self):
        treasure = self.find_character_element("./build/input/currency/treasure")
        if treasure is not None and treasure.text is not None and re.search(r"\w", treasure.text) is not None:
            return treasure.text
        return None

    def query_combat_details(self):
        combat = self.find_character_element("./build/input/attacks/description")
        if combat is None or combat.text is None:
            return None
        if re.search(r"\w", combat.text) is not None:
            return combat.text
        return None

    def query_proficiency_hierarchy(self):
        top_profs = self.find_character_elements(".//element[@type!='Proficiency']/element[@type='Proficiency']")
        weapon_profs = []
        armor_profs = []
        tool_profs = []
        other_profs = []
        for prof in top_profs:
            if "registered" in prof.attrib:
                registered_id = prof.attrib["registered"]
            else:
                registered_id = prof.attrib["id"]
            if "Weapon Proficiency" in prof.attrib["name"]:
                weapon_profs.append(registered_id)
            elif "Armor Proficiency" in prof.attrib["name"]:
                armor_profs.append(registered_id)
            elif "Tool Proficiency" in prof.attrib["name"] or "Musical Instrument" in prof.attrib["name"]:
                tool_profs.append(registered_id)
            elif "Gaming Set" in prof.attrib["name"]:
                other_profs.append(registered_id)
        weapon_profs = list(set(weapon_profs))
        armor_profs = list(set(armor_profs))
        tool_profs = list(set(tool_profs))
        other_profs = list(set(other_profs))

        # for i, p in enumerate(weaponProfs):
        #     weaponProfs[i] = " ".join([s.capitalize() for s in re.sub(r"[A-Z_]*WEAPON_PROFICIENCY_", "", p).split("_")])
        # for i, p in enumerate(armorProfs):
        #     armorProfs[i] = " ".join([s.capitalize() for s in re.sub(r"[A-Z_]*ARMOR_PROFICIENCY_", "", p).split("_")])
        # for i, p in enumerate(toolProfs):
        #     toolProfs[i] = " ".join([s.capitalize() for s in re.sub(r"[A-Z_]*TOOL_PROFICIENCY_", "", p).split("_")])
        # for i, p in enumerate(otherProfs):
        #     otherProfs[i] = " ".join([s.capitalize() for s in re.sub(r"[A-Z_]*GAMING_SET_PROFICIENCY_", "", p).split("_")])
        # for i, p in enumerate(weaponProfs):
        #     weaponProfs[i] = " ".join([s.capitalize() for s in re.sub(r"[A-Z_]*PROFICIENCY_", "", p).split("_")])
        # for i, p in enumerate(armorProfs):
        #     armorProfs[i] = " ".join([s.capitalize() for s in re.sub(r"[A-Z_]*PROFICIENCY_", "", p).split("_")])
        # for i, p in enumerate(toolProfs):
        #     toolProfs[i] = " ".join([s.capitalize() for s in re.sub(r"[A-Z_]*PROFICIENCY_", "", p).split("_")])
        # for i, p in enumerate(otherProfs):
        #     otherProfs[i] = " ".join([s.capitalize() for s in re.sub(r"[A-Z_]*PROFICIENCY_", "", p).split("_")])

        # Try to query proficiency name
        for prociency_list in [weapon_profs, armor_profs, tool_profs, other_profs]:
            for i, p in enumerate(prociency_list):
                prof_element = self.compendium.find_element(element_id = p)
                if prof_element is None:
                    # Fall back on generic cprocessing
                    prociency_list[i] = " ".join([s.capitalize() for s in re.sub(r"[A-Z_]*PROFICIENCY_", "", p).split("_")])
                    continue
                else:
                    prof_name = prof_element.attrib.get("name", "PROFICIENCY NOT FOUND")
                    # this seems to be of the form [proficiency type] ([proficiency]) so it gets formatted
                    prof_name = re.search(r"\((.*)\)", prof_name).group(1)
                    prociency_list[i] = prof_name

        languages = self.find_character_elements(".//sum/element[@type='Language']")
        languages = [language.attrib["id"] for language in languages]
        for i, language in enumerate(languages):
            language_element = self.compendium.find_element(element_id = language)
            if language_element is None:
                languages[i] = " ".join([s.capitalize() for s in re.sub(r"[A-Z_]*LANGUAGE", "", language).split("_")])
            else:
                language_name = language_element.attrib.get("name", "LANGUAGE NOT FOUND")
                languages[i] = language_name

        return [weapon_profs, armor_profs, tool_profs, other_profs, languages]

    def query_companions(self):
        companions = self.find_character_elements("./build/sum/element[@type='Companion']")
        companion_list = []
        for c in companions:
            companion_list.append(self.compendium.query_companion(c.attrib["id"]))
        return companion_list

    def query_companion(self):
        # NOTE: only 1 companion is currently supported
        companion = self.find_character_element("./build/sum/element[@type='Companion']")
        if companion is None:
            return None
        companion_id = companion.attrib["id"]
        return self.compendium.query_companion(companion_id)

# GENERAL FILE QUERYING FOR GENERATION

    def query_elements_list(self):
        elements = self.find_character_element("./build/elements")
        return elements

# STATIC

    @staticmethod
    def query_name_from_file(character_file):
        tree = et.parse(character_file)
        root = tree.getroot()
        return root.find(".//display-properties/name").text

    @staticmethod
    def query_level_from_file(character_file):
        tree = et.parse(character_file)
        root = tree.getroot()
        return int(root.find(".//display-properties/level").text)