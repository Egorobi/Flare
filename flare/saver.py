import glob
import os
import json
from lxml import etree as et

class Saver():

    save_directory = "./data/saves/"

    def __init__(self):
        self.parser = et.XMLParser(remove_blank_text=True)

    ### CHRACTER SETUP

    def save_pdf_file_path(self, name, pdf_path):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        root = tree.getroot()
        root.find("./pdf").text = pdf_path
        tree.write(filename, pretty_print=True)

    def save_character_file_path(self, name, aurora_file_path):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        root = tree.getroot()
        root.find("./aurora").text = aurora_file_path
        tree.write(filename, pretty_print=True)

    def save_source_path(self, name, source_path):
        print("saving source path")
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        root = tree.getroot()
        root.find("./source").text = source_path
        tree.write(filename, pretty_print=True)

    def save_portrait(self, name, portrait_path):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        root = tree.getroot()
        portrait = root.find("./portrait")
        if portrait is None:
            portrait = et.SubElement(root, "portrait")
        portrait.text = portrait_path
        tree.write(filename, pretty_print=True)

    def save_description(self, name, short):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        root = tree.getroot()
        description = root.find("./description")
        if description is None:
            description = et.SubElement(root, "description")
        description.text = short
        tree.write(filename, pretty_print=True)

    ### SETTINGS

    def get_global_settings(self):
        filename = self.save_directory + "settings.json"
        if os.path.isfile(filename):
            with open(filename) as f:
                settings = json.load(f)
            return settings
        settings = {}
        self.write_global_settings(settings)
        return settings

    def write_global_settings(self, settings):
        filename = self.save_directory + "settings.json"
        settings = json.dumps(settings)
        with open(filename, "w") as outfile:
            outfile.write(settings)

    def get_setting(self, setting, default):
        settings = self.get_global_settings()
        if setting in settings:
            return settings[setting]
        else: return default

    def save_global_content(self, content_path):
        settings = self.get_global_settings()
        settings["content"] = content_path
        self.write_global_settings(settings)

    def get_global_content(self):
        return self.get_setting("content", None)

    def save_background(self, background, dark=False):
        settings = self.get_global_settings()
        if dark:
            settings["darkmodeBackground"] = background
        else:
            settings["lightmodeBackground"] = background
        self.write_global_settings(settings)

    def get_background(self, dark=False):
        if dark:
            return self.get_setting("darkmodeBackground", "night")
        else:
            return self.get_setting("lightmodeBackground", "solid")

    def save_menu_color(self, scheme):
        settings = self.get_global_settings()
        settings["menuColor"] = scheme
        self.write_global_settings(settings)

    def get_menu_color(self):
        return self.get_setting("menuColor", "default")

    def save_menu_dark_mode(self, dark):
        # print(dark)
        settings = self.get_global_settings()
        settings["menuDarkMode"] = dark
        self.write_global_settings(settings)

    def get_menu_dark_mode(self):
        return self.get_setting("menuDarkMode", True)

    def save_frame_style(self, style):
        settings = self.get_global_settings()
        settings["frames"] = style
        self.write_global_settings(settings)

    def get_frame_style(self):
        return self.get_setting("frames", "flare")

    ### CUSTOM

    def write_custom_colors(self, colors):
        filename = self.save_directory + "colors.json"
        colors = json.dumps(colors)
        with open(filename, "w") as outfile:
            outfile.write(colors)

    def get_custom_colors(self):
        filename = self.save_directory + "colors.json"
        if os.path.isfile(filename):
            with open(filename) as f:
                colors = json.load(f)
            return colors
        colors = {}
        self.write_custom_colors(colors)
        return colors


    ### UTILITIES

    def read_file(self, name):
        file = self.find_save_file(name)
        tree = et.parse(file)
        print(tree)

    def find_save_file(self, name):
        for filename in glob.iglob(self.save_directory + '**/*.xml', recursive=True):
            if not filename.endswith('.xml'):
                continue
            tree = et.parse(filename, self.parser)
            root = tree.getroot()
            if root.attrib["name"] == name:
                return filename
        # if file not found
        filename = self.save_directory + name + ".xml"
        root = et.Element('character')
        root.attrib["name"] = name
        _ = et.SubElement(root, 'pdf')
        _ = et.SubElement(root, "aurora")
        _ = et.SubElement(root, "source")
        _ = et.SubElement(root, "spellSlots")
        hp = et.SubElement(root, "hitpoints")
        hp.attrib["temp"] = "0"
        _ = et.SubElement(root, "death_saves")
        _ = et.SubElement(root, "hitdice")
        _ = et.SubElement(root, "portrait")
        _ = et.SubElement(root, "description")
        inspiration = et.SubElement(root, "inspiration")
        inspiration.text = "false"
        darkmode = et.SubElement(root, "dark")
        darkmode.text = "true"
        concentration = et.SubElement(root, "concentration")
        concentration.attrib["id"] = ""
        concentration.attrib["level"] = "0"
        tree = et.ElementTree(root)
        print(filename)
        tree.write(filename, pretty_print=True)
        return filename

    def get_saves(self):
        saves = []
        for filename in glob.iglob(self.save_directory + '**/*.xml', recursive=True):
            if not filename.endswith('.xml'):
                continue
            tree = et.parse(filename, self.parser)
            root = tree.getroot()
            aurora_file = root.find("./aurora").text
            source_path = root.find("./source").text
            portrait = root.find("./portrait").text
            description = root.find("./description").text
            save = {"name": root.attrib["name"], "file": filename, "aurora": aurora_file, "source": source_path, "portrait": portrait, "description": description}
            saves.append(save)
        return saves

    def get_sub_element(self, name, default, tree):
        root = tree.getroot()
        element = root.find(f"./{name}")
        if element is None:
            element = et.SubElement(root, name)
            if default is not None:
                element.text = default
        return tree, element

    ### GETTERS SETTERS

    # SPELL SLOTS

    def get_spellslot(self, name, level: int):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        root = tree.getroot()
        spellslots = root.find(".//spellSlots")
        slot = spellslots.find(f"./slot[@level='{level}']")
        if slot is None:
            slot = et.SubElement(spellslots, "slot")
            slot.attrib["level"] = str(level)
            slot.attrib["usedSlots"] = str(0)
            tree.write(filename, pretty_print=True)
        return tree, slot

    def record_used_slots(self, name, level: int, uses: int):
        filename = self.find_save_file(name)
        tree, slot = self.get_spellslot(name, level)
        slot.set("usedSlots", str(uses))
        tree.write(filename, pretty_print=True)

    def get_used_slots(self, name, level: int):
        _, slot = self.get_spellslot(name, level)
        return int(slot.attrib["usedSlots"])

    # HIT DICE

    def get_hitdice(self, name, dice_class):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        root = tree.getroot()
        hitdice_parent = root.find(".//hitdice")
        if hitdice_parent is None:
            hitdice_parent = et.SubElement(root, "hitdice")
        hitdice = hitdice_parent.find(f"./hd[@class='{dice_class}']")
        if hitdice is None:
            hitdice = et.SubElement(hitdice_parent, "hd")
            hitdice.attrib["class"] = dice_class
            hitdice.attrib["usedDice"] = str(0)
        return tree, hitdice

    def record_used_hitdice(self, name: str, dice_class: str, uses: int):
        filename = self.find_save_file(name)
        tree, hitdice = self.get_hitdice(name, dice_class)
        hitdice.set("usedDice", str(uses))
        tree.write(filename, pretty_print=True)

    def get_used_hitdice(self, name: str, dice_class: str):
        _, hitdice = self.get_hitdice(name, dice_class)
        return int(hitdice.attrib["usedDice"])

    # HITPOINTS

    def record_hitpoints(self, name, current: int, temp: int):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        hitpoints = tree.getroot().find("./hitpoints")
        hitpoints.attrib["current"] = str(current)
        hitpoints.attrib["temp"] = str(temp)
        tree.write(filename, pretty_print=True)

    def get_hitpoints(self, name, max_hp: int):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        hitpoints = tree.getroot().find("./hitpoints")
        if hitpoints.attrib.get("current") is None:
            hitpoints.attrib["current"] = str(max_hp)
            tree.write(filename, pretty_print=True)
        current = int(hitpoints.attrib["current"])
        temp = int(hitpoints.attrib["temp"])
        return current, temp

    # DEATH SAVES

    def record_death_saves(self, name, successes: int, failures: int):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        tree, saves = self.get_sub_element("death_saves", None, tree)
        saves.attrib["successes"] = str(max(0, min(successes, 3)))
        saves.attrib["failures"] = str(max(0, min(failures, 3)))
        tree.write(filename, pretty_print=True)

    def get_death_saves(self, name):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        tree, death_saves = self.get_sub_element("death_saves", None, tree)
        return int(death_saves.attrib.get("successes", 0)), int(death_saves.attrib.get("failures", 0))

    # DARK MODE

    def save_dark_mode(self, name, dark: str):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        root = tree.getroot()
        darkmode = root.find("./dark")
        if darkmode is None:
            darkmode = et.SubElement(root, "dark")
        darkmode.text = dark
        tree.write(filename, pretty_print=True)

    def get_dark_mode(self, name):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        root = tree.getroot()
        darkmode = root.find("./dark")
        if darkmode is None:
            darkmode = et.SubElement(root, "dark")
            darkmode.text = "true"
            tree.write(filename, pretty_print=True)
        if darkmode.text == "true":
            return True
        else:
            return False

    # COLOR SCHEME

    def save_color(self, name, color: str):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        tree, color_scheme = self.get_sub_element("color", "default", tree)
        color_scheme.text = color
        tree.write(filename, pretty_print=True)

    def get_color(self, name):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        tree, color_scheme = self.get_sub_element("color", "default", tree)
        return color_scheme.text

    # FEATURE CHARGES

    def get_charges(self, name, feature_id, max_charges):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        tree, all_charges = self.get_sub_element("charges", None, tree)
        charges = all_charges.find(f"./charge[@id='{feature_id}']")
        if charges is None:
            charges = et.SubElement(all_charges, "charge")
            charges.attrib["id"] = feature_id
            charges.text = max_charges
        return int(charges.text)

    def save_charges(self, name, feature_id, num):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        tree, all_charges = self.get_sub_element("charges", None, tree)
        charges = all_charges.find(f"./charge[@id='{feature_id}']")
        if charges is None:
            charges = et.SubElement(all_charges, "charge")
            charges.attrib["id"] = feature_id
        charges.text = num
        tree.write(filename, pretty_print=True)

    # HEROIC INSPIRATION

    def get_inspiration(self, name) -> bool:
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        tree, inspiration = self.get_sub_element("inspiration", "false", tree)
        return inspiration.text == "true"

    def save_inspiration(self, name, value: bool):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        tree, inspiration = self.get_sub_element("inspiration", "false", tree)
        inspiration.text = "true" if value else "false"
        tree.write(filename, pretty_print=True)

    # CONCENTRATION

    def get_concentration(self, name):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        tree, concentration = self.get_sub_element("concentration", None, tree)
        spell_id = concentration.attrib.get("id", "")
        level = int(concentration.attrib.get("level", "0"))
        return spell_id, level

    def save_concentration(self, name, spell_id, level: int):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        tree, concentration = self.get_sub_element("concentration", None, tree)
        concentration.attrib["id"] = spell_id
        concentration.attrib["level"] = str(level)
        tree.write(filename, pretty_print=True)

    # CONDITIONS

    def get_conditions(self, name):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        tree, conditions = self.get_sub_element("conditions", "", tree)
        if conditions.text is None or len(conditions.text) == 0:
            return []
        active = conditions.text.split(",")
        active = list(set(active))
        return active

    def save_conditions(self, name, active):
        filename = self.find_save_file(name)
        tree = et.parse(filename, self.parser)
        tree, conditions = self.get_sub_element("conditions", "", tree)
        conditions.text = ",".join(active)
        tree.write(filename, pretty_print=True)
