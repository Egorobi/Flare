import re
import math
from nicegui import ui
from modules.module import Module
from modules.listeners import ChargeListener, SpellslotListener
from modules.dialogs import RollContext
import session
import storage
import icons
from wrappers import Weapon, Armor
import colorschemes

class Tabs(Module):
    # TODO split into sub-modules
    def __init__(self):
        self.action_tab_buttons = {}
        self.total_gold_label = None
        self.coin_counts = {}
        self.coin_counts_small = {}

    def show_module(self):
        with ui.tabs().classes("w-full q-pa-none").props("dense shrink narrow-indicator") as tabs:
            actions_tab = ui.tab('Actions')
            spells_tab = ui.tab('Spells')
            inventory_tab = ui.tab("Inventory")
            features_tab = ui.tab("Features")
            background_tab = ui.tab("Background")
            extras_tab = ui.tab("Extra")
        with ui.tab_panels(tabs, value=actions_tab).classes('w-full h-full q-px-sm q-pb-xs transparent no-shadow'):
            # ACTIONS
            self.show_actions_tab(actions_tab)
            # SPELL LIST
            self.show_spells(spells_tab)
            # INVENTORY
            self.show_inventory(inventory_tab)
            # # FEATURES
            self.show_features(features_tab)
            # # BACKGROUND
            self.show_background(background_tab)
            # # EXTRAS
            self.show_extras(extras_tab)

    def show_actions_tab(self, actions_tab):
        char = session.char
        with ui.tab_panel(actions_tab).classes("w-full q-py-none q-px-xs"), ui.scroll_area().classes("h-full w-full q-pa-none"):
            all_features = char.get_class_features()[0] + char.get_racial_traits()[0] + char.get_feats()[0]
            # self.showAttacks()
            # self.showActions(allFeatures)
            # self.showBonusActions(allFeatures)
            # self.showReactions(allFeatures)
            # self.showCombatDetails()
            with ui.tabs().classes('w-full q-pa-none justify-start absolute-top').props("dense align=left").style("z-index:1;") as action_tabs:
                all_tab = ui.tab('ALL')
                attacks_tab = ui.tab("ATTACKS")
                just_actions_tab = ui.tab("ACTIONS")
                bonus_actions_tab = ui.tab("BONUS ACTIONS")
                reactions_tab = ui.tab("REACTIONS")
                other_tab = ui.tab("OTHER")
            tab_types = ["ALL", "ATTACKS", "ACTIONS", "BONUS ACTIONS", "REACTIONS", "OTHER"]
            self.action_tab_buttons = {}
            with ui.row().style("gap:0.3rem; z-index:1;").classes("absolute-top q-pl-md"):
                for tab_type in tab_types:
                    self.action_tab_buttons[tab_type] = ui.button(tab_type, on_click=lambda t=tab_type: action_tabs.set_value(t)).classes("q-px-sm").props("dense outline size=sm")
            self.action_tab_buttons["ALL"].props["outline"] = False
            self.action_tab_buttons["ALL"].update()
            with ui.tab_panels(action_tabs, value=all_tab, on_change=lambda e: self.update_action_tabs(e.value)).classes('w-full absolute-top transparent no-shadow').style("padding-top: 1.2rem; z-index:0;").props("content-class='q-pa-none'"):
                with ui.tab_panel(all_tab):
                    self.show_attacks()
                    self.show_actions(all_features)
                    self.show_bonus_actions(all_features)
                    self.show_reactions(all_features)
                    self.show_special(all_features)
                    self.show_combat_details()
                with ui.tab_panel(attacks_tab):
                    self.show_attacks()
                with ui.tab_panel(just_actions_tab):
                    self.show_attacks()
                    self.show_actions(all_features)
                with ui.tab_panel(bonus_actions_tab):
                    self.show_bonus_actions(all_features)
                with ui.tab_panel(reactions_tab):
                    self.show_reactions(all_features)
                with ui.tab_panel(other_tab):
                    self.show_special(all_features)
                    self.show_combat_details()
            action_tabs.set_visibility(False)

    def update_action_tabs(self, value):
        for button in self.action_tab_buttons.values():
            button.props["outline"] = True
            button.update()
        self.action_tab_buttons[value].props["outline"] = False
        self.action_tab_buttons[value].update()

    def show_attacks(self):
        char = session.char
        with ui.column().classes("text-primary font-bold w-full").style("gap:0.1rem;"):
            with ui.row().classes("items-center").style("gap:0.1rem;"):
                ui.label("ACTIONS •")
                ui.label(f"Attacks per Action: {session.char.attacks_per_action}").classes("font-normal text-xs text-slate-400")
            ui.separator().props("color=primary")
        with ui.column().classes("w-full"):
            with ui.row().classes("no-wrap w-full font-bold"):
                ui.label("ATTACK").classes("col-3")
                ui.label("RANGE").classes("col-2")
                ui.label("HIT/DC").classes("col-1")
                ui.label("DAMAGE").classes("col-2")
                ui.label("NOTES").classes("col-2")
            ui.separator()
            for attack in char.attacks:
                with ui.row().classes("no-wrap items-center").style("width:38rem;"):
                    ui.label(attack.name).on("click", lambda id=attack.identifier: self.show_item_info(id)).classes("col-3")
                    if re.match(".*/.*", attack.attack_range):
                        m = re.search(r"(.*)/(.*)", attack.attack_range)
                        ui.html(f"<b>{m.group(1)}</b><b class='text-slate-400 text-xs'> ({m.group(2)})</b>").classes("col-2")
                    else:
                        m = re.search(r"\d*", attack.attack_range)
                        ui.html(f"<b>{m.group()}</b><b class='text-slate-400 text-xs'> ft.</b>").classes("col-2")
                    attack_bonus = re.search(r"[-+]?\d+", attack.attack)
                    attack_bonus = int(attack_bonus.group()) if attack_bonus is not None else 0
                    attack_roll_name = f"{attack.name} Attack"
                    # ui.label(attack.attack).classes("col-2")
                    with ui.column().classes("items-center col-1"):
                        with ui.button(session.val_to_string(attack_bonus), on_click=lambda mod=attack_bonus, attack_roll_name=attack_roll_name: session.roll_dialog.wait_module(f"1d20 + {mod}", attack_roll_name)).classes(
                                "text-xl q-px-sm q-py-xs outline-btn").props("dense unelevated outline"):
                            context_menu = RollContext()
                            context_menu.show_module(attack_bonus)
                    if re.match(r"\d+d\d+[-\+]\d+", attack.damage):
                        m = re.search(r"(\d+)d(\d+)([-\+])(\d+) (\w*)", attack.damage)
                        num = int(m.group(1))
                        die = int(m.group(2))
                        mod = int(m.group(4))
                        plus = m.group(3)
                        polarity = 1 if m.group(3) == "+" else -1
                        damage_type = m.group(5)
                        damage_only = f"{num}d{die}{plus}{mod}"
                        damage_roll_name = f"{attack.name} Damage"
                        with ui.button(damage_only, on_click=lambda num=num, die=die, mod=mod*polarity, damage_roll_name=damage_roll_name: session.roll_dialog.wait_module(f"{num}d{die} + {mod}", damage_roll_name)).classes(
                                "q-px-sm font-normal q-py-xs outline-btn col-2").props("dense no-caps unelevated outline"):
                            if damage_type in icons.damage_type_map:
                                ui.html(icons.damage_type_map[damage_type]).classes("q-pl-xs adaptcolor")
                            ui.tooltip(damage_type.capitalize()).classes("adapttooltip")
                    else:
                        ui.label(attack.damage).classes("col-2")
                    ui.label(attack.notes).classes("col-2 text-xs text-slate-400")
                ui.separator()

    def show_actions(self, all_features):
        with ui.column().classes("w-full q-py-none").style("gap:0.8rem"):
            with ui.column().style("gap:0.3rem;"):
                ui.label("Actions in Combat").classes("font-bold")
                with ui.row().classes("w-full no-wrap"):
                    ui.separator().props("vertical")
                    ui.label("Attack, Dash, Disengage, Dodge, Grapple, Help, Hide, Improvise, Influence, Magic, Ready, Search, Shove, Study, Utilize")
                with ui.column().classes("w-full").style("gap:0.1rem"):
                    ui.label("Unarmed Strike").classes("font-bold")
                    unarmed_strike = """
                    <p>You make a melee attack that involves using your body to deal one of the following effects:</p>
                    <p><i><strong>Damage</strong></i>. You make an attack roll against the creature (Prof. Bonus + Str.), and on a hit, you deal 1 + STR Bludgeoning damage.</p>
                    <p><i><strong>Grapple</strong></i>. The target must succeed on a Str./Dex. (it chooses which) saving throw (DC = 8 + Prof. Bonus + Str.) or it has the Grappled condition.</p>
                    <p><i><strong>Shove</strong></i>. The target must succeed on a Str./Dex. (it chooses which) saving throw (DC = 8 + Prof. Bonus + Str.) or you can either push it 5 ft. away or cause it to have the Prone condition.</p>
                    """
                    ui.html(unarmed_strike).classes("text-xs")
            for feature in all_features:
                if feature.action == "Action":
                    feature_module = Feature(feature)
                    feature_module.show_module()

    def show_bonus_actions(self, all_features):
        with ui.column().classes("w-full q-py-none").style("gap:0.8rem"):
            with ui.column().classes("w-full").style("gap:0.1rem;"):
                ui.label("BONUS ACTIONS").classes("text-primary font-bold")
                ui.separator().props("color=primary")
            with ui.column().classes("w-full").style("gap:0.1rem"):
                ui.label("Actions in Combat").classes("font-bold")
                with ui.row().classes("w-full no-wrap"):
                    ui.separator().props("vertical")
                    ui.label("Two-Weapon Fighting")
            # bonusSpells = self.spellsByCast("bonus action")
            self.show_cast_spells("bonus action")
            for feature in all_features:
                if feature.action == "Bonus Action":
                    feature_module = Feature(feature)
                    feature_module.show_module()

    def show_cast_spells(self, cast):
        cast_spells = self.spells_by_cast(cast)
        if len(cast_spells) > 0:
            with ui.column().classes("w-full").style("gap:0.1rem"):
                ui.label("Spells").classes("font-bold")
                with ui.row().classes("w-full no-wrap"):
                    ui.separator().props("vertical")
                    with ui.row().classes("w-full").style("gap:0.3rem;"):
                        for i, spell in enumerate(cast_spells):
                            ui.html(f"<i>{spell.name}</i> <span class='text-slate-400'>({self.level_suffix_compact(spell.level)})</span>{',' if i < len(cast_spells) - 1 else ''}").on('click', lambda s=spell.spell_id: self.show_spell_info(s))

    def spells_by_cast(self, cast):
        cast_spells = []
        for spells_at_level in session.char.spells:
            for spell in spells_at_level:
                if cast in spell.cast:
                    cast_spells.append(spell)
        return cast_spells

    def spells_by_cast_formatted(self, cast):
        cast_spells = []
        for level, spells_at_level in enumerate(session.char.spells):
            for spell in spells_at_level:
                if cast in spell.cast:
                    cast_spells.append(f"<i>{spell.name}</i>" + f"<span class='text-slate-400'> ({self.level_suffix_compact(level)})</span>")
        return cast_spells

    def show_reactions(self, all_features):
        with ui.column().classes("w-full").style("gap:0.8rem"):
            with ui.column().classes("w-full").style("gap:0.1rem;"):
                ui.label("REACTIONS").classes("text-primary font-bold")
                ui.separator().props("color=primary")
            with ui.column().classes("w-full").style("gap:0.1rem"):
                ui.label("Actions in Combat").classes("font-bold")
                with ui.row().classes("w-full no-wrap"):
                    ui.separator().props("vertical")
                    ui.label("Opportunity Attack")
            self.show_cast_spells("reaction")
            for feature in all_features:
                if feature.action == "Reaction":
                    feature_module = Feature(feature)
                    feature_module.show_module()

    def show_special(self, all_features):
        with ui.column().classes("w-full").style("gap:0.8rem"):
            with ui.column().classes("w-full").style("gap:0.1rem;"):
                ui.label("SPECIAL").classes("text-primary font-bold")
                ui.separator().props("color=primary")
            for feature in all_features:
                if feature.action == "Other" or feature.action == "Special":
                    feature_module = Feature(feature)
                    feature_module.show_module()

    def show_combat_details(self):
        combat_details = session.char.get_combat_details()
        with ui.column().classes("text-primary font-bold w-full").style("gap:0.1rem"):
            ui.label("COMBAT DETAILS")
            ui.separator().props("color=primary")
        if combat_details is not None:
            ui.label(combat_details)

    def show_spells(self, spells_tab):
        char = session.char
        with ui.tab_panel(spells_tab).classes("q-pa-none"), ui.scroll_area().classes("h-full w-full q-pa-none"):
            with ui.column().classes("w-full no-wrap"):
                self.show_concentration()
                normal_spellcastings = [s for s in char.spellcastings if s.name != "Additional"]
                if len(normal_spellcastings) > 0:
                    with ui.row().classes("w-full items-center justify-center q-ma-none"):
                        for i, spellcasting in enumerate(normal_spellcastings):
                            if spellcasting.name == "Additional":
                                continue
                            with ui.column().classes("items-center").style("gap:0.1rem"):
                                if len(normal_spellcastings) > 1:
                                    ui.label(spellcasting.name).classes("little-text")
                                with ui.row().classes("justify-center items-center").style("gap:0.5rem"):
                                    with ui.column().classes("items-center").style("gap:0.1rem"):
                                        ui.label(session.val_to_string(spellcasting.modifier)).classes("font-bold")
                                        ui.label("MODIFIER").classes("little-text")
                                    ui.separator().props("vertical")
                                    with ui.column().classes("items-center").style("gap:0.1rem"):
                                        ui.label(session.val_to_string(spellcasting.attack)).classes("font-bold")
                                        ui.label("SPELL ATTACK").classes("little-text")
                                    ui.separator().props("vertical")
                                    with ui.column().classes("items-center").style("gap:0.1rem"):
                                        ui.label(spellcasting.dc).classes("font-bold")
                                        ui.label("SAVE DC").classes("little-text")
                            if i < len(normal_spellcastings)-1:
                                ui.separator().props("vertical color=primary")

                for i in range(10):
                    with ui.column().classes("w-full"):
                        # if len(char.spells[i]) == 0: continue
                        # if not char.getAvailableSpellslots()[i]: continue
                        if len(char.spells[i]) == 0 and not char.get_available_spellslots()[i]:
                            continue
                        label = ""
                        if i == 0:
                            label = "CANTRIP"
                        elif i == 1:
                            label = "1ST LEVEL"
                        elif i == 2:
                            label = "2ND LEVEL"
                        elif i == 3:
                            label = "3RD LEVEL"
                        else:
                            label = str(i) + "TH LEVEL"
                        with ui.row().classes("w-full no-wrap"):
                            ui.label(label).classes("font-bold text-l col-6 text-primary")
                            if char.get_available_spellslots()[i]:
                                with ui.row().classes("justify-end w-full col-5"):
                                    if i > 0:
                                        spellslot_buttons = SpellSlots(i)
                                        spellslot_buttons.show_module()

                        ui.separator().props("color=primary")

                        with ui.row().classes("font-bold w-full no-wrap text-xs"):
                            ui.label("NAME").classes("col-3")
                            ui.label("TIME").classes("col-1")
                            ui.label("RANGE").classes("col-2")
                            ui.label("HIT/DC").classes("col-1")
                            ui.label("DURATION").classes("col-2")
                            ui.label("NOTES").classes("col-2")

                        for spell in char.spells[i]:
                            with ui.row().classes("no-wrap w-full items-center") as spell_row:
                                if spell.concentration:
                                    self.concetrate_context(spell.spell_id, spell.level)
                                spell_row.on('click', lambda id=spell.spell_id: self.show_spell_info(id))
                                with ui.column().classes("w-full col-3 justify-start").style("gap: 0.1em"):
                                    with ui.row().classes("w-full").style("gap: 0.1em"):
                                        ui.label(spell.name).classes("italic")
                                        if spell.concentration:
                                            ui.icon("copyright").classes("q-pt-xs")
                                        if spell.ritual:
                                            ui.icon("book_2").classes("q-pt-xs q-pl-md")
                                    ui.label(spell.source).classes("tiny-text h-1 text-slate-400")
                                cast = ""
                                if "1 action" in spell.cast:
                                    cast = "1A"
                                elif "1 bonus action" in spell.cast:
                                    cast = "1BA"
                                elif "1 reaction" in spell.cast:
                                    cast = "1R"
                                else:
                                    cast = spell.cast
                                # casting time
                                ui.label(cast).classes("col-1")
                                # range
                                ui.label(spell.spell_range).classes("col-2")
                                # hit/dc
                                label = "--"
                                if spell.spell_type == "attack":
                                    label = "ATK"
                                    attack = char.read_variable(spell.source.lower() + ":spellcasting:attack")
                                    if attack != 0:
                                        # label = session.valToString(char.readVariable(attack))
                                        with ui.row().classes("col-1"):
                                            roll_name = f"{spell.name} Attack"
                                            with ui.button(session.val_to_string(attack)).classes(
                                                "little=text outline-btn q-pa-none").props("dense unelevated outline").style("width:2rem;").on("click.stop", lambda mod=attack, roll_name=roll_name: session.roll_dialog.wait_module(f"1d20 + {mod}", roll_name=roll_name)):
                                                context_menu = RollContext()
                                                context_menu.show_module(attack)
                                    else:
                                        ui.label("--").classes("text-slate-400 col-1")
                                elif spell.spell_type == "save":
                                    label = "SAVE"
                                    save = spell.source.lower() + ":spellcasting:dc"
                                    label = char.read_variable(save)
                                    if label != 0:
                                        with ui.column().classes("col-1 text-slate-400").style("gap:0.05rem;"):
                                            ui.label(spell.save_type).classes("little-text")
                                            ui.label(label).classes("little-text font-bold")
                                    else:
                                        with ui.column().classes("col-1 text-slate-400").style("gap:0.05rem;"):
                                            ui.label(spell.save_type).classes("little-text")
                                            ui.label("--").classes("little-text")
                                else:
                                    ui.label("--").classes("text-slate-400 col-1")
                                # duration
                                ui.label(spell.duration).classes("col-2")
                                notes = ""
                                icon = ""
                                if spell.shape is not None:
                                    shape = spell.shape[0]
                                    if shape == "cube":
                                        notes += spell.shape[1] + "ft"
                                        icon = icons.CUBE_SVG
                                    elif shape == "sphere":
                                        notes += spell.shape[1] + "ft"
                                        icon = icons.SPHERE_SVG
                                    elif shape == "square":
                                        notes += spell.shape[1] + "ft"
                                        # TODO nicer square icon
                                        icon = icons.SQUARE_SVG
                                    elif shape == "cone":
                                        notes += spell.shape[1] + "ft"
                                        icon = icons.CONE_SVG
                                    elif shape == "cylinder":
                                        notes += f"{spell.shape[1][0]}ft,{spell.shape[1][1]}ft"
                                        icon = icons.CYLINDER_SVG
                                notes += " " + spell.keywords
                                with ui.row().classes("text-slate-400 q-pr-sm").style("gap: 0.1em"):
                                    components = self.compile_spell_components(spell.components, None)
                                    ui.label(components)
                                    ui.html(icon)
                                    ui.label(notes)
                            ui.separator()

                        ui.space().classes("h-6")

    @ui.refreshable
    def show_concentration(self):
        spell_id, level = session.char.get_concentration()
        if spell_id != "":
            spell = storage.spell_id_map[spell_id]
            with ui.row().classes("w-full justify-center items-center").style("gap:0.3rem;"):
                ui.label("Concentrating on:").classes("text-bold")
                ui.label(spell.name)
                ui.label(f"({self.level_suffix_compact(level)})")
                ui.button(icon="close", on_click=lambda: self.clear_concentration()).props("size=xs dense outline")

    def clear_concentration(self):
        session.char.set_concentration("", 0)
        self.show_concentration.refresh()

    def set_concentration(self, spell_id, level):
        session.char.set_concentration(spell_id, level)
        self.show_concentration.refresh()

    def concetrate_context(self, spell_id, level):
        with ui.context_menu().classes("no-shadow items-center q-pa-sm adapttooltip").props(""):
            # ui.card().classes("frameborder absolute-center w-full h-full frame no-shadow transparent")
            # ui.menu_item("Concentrate", lambda: self.setConcentration(spellId, level), auto_close=True)
            ui.label("Concentrate at level:")
            ui.separator()
            available = session.char.get_available_spellslots()
            available[level] = True
            with ui.row().classes("justify-center"):
                if level == 0:
                    ui.menu_item("Cantrip", lambda: self.set_concentration(spell_id, 0), auto_close=True)
                else:
                    for i in range(level, 10):
                        if available[i]:
                            ui.menu_item(self.level_suffix_compact(i), lambda level=i: self.set_concentration(spell_id, level), auto_close=True)

    def level_suffix_compact(self, level):
        if level == 0:
            return "Cantrip"
        elif level == 1:
            return "1st"
        elif level == 2:
            return "2nd"
        elif level == 3:
            return "3rd"
        else:
            return str(level) + "th"

    def compile_spell_components(self, comps, material):
        components = ""
        if comps[0]:
            components += "V"
        if comps[0] and (comps[1] or comps[2]):
            components += "/"
        if comps[1]:
            components += "S"
        if comps[1] and comps[2]:
            components += "/"
        if comps[2]:
            components += "M"
        if material is not None and material != "":
            components += " (" + material + ")"
        return components

    def cast_spell(self, spell_id, level):
        spell = storage.spell_id_map[spell_id]
        if level > 0:
            session.set_spellslots(level, True)
        if spell.concentration:
            # a warning here if there is active concentration would be nice
            self.set_concentration(spell_id, level)

    def show_spell_info(self, spell_id):
        spell = storage.spell_id_map[spell_id]
        with ui.dialog().props("full-height") as dialog, ui.card() as card:
            card.classes("fixed-top-right w-2/5 h-full no-shadow q-pa-none").props("square bordered")
            with ui.scroll_area().classes("h-full w-full q-pa-none"):
                ui.label(spell.source).classes("text-xs")
                with ui.row().classes("w-full justify-between q-pr-md items-center"):
                    ui.label(spell.name).classes('text-xl font-bold text-primary')
                    with ui.row().classes("items-center").style("z-index: 1;"):
                        ui.button("CAST", on_click=lambda level=spell.level, id=spell_id: self.cast_spell(id, level)).props("outline")
                        if spell.level > 0:
                            ui.label("Spell slots:")
                            if session.char.get_available_spellslots()[spell.level]:
                                spellslot_buttons = SpellSlots(spell.level)
                                spellslot_buttons.show_module()
                            else:
                                ui.label("None")
                level_school = ""
                if spell.level == 0:
                    level_school = f"{spell.school} Cantrip"
                else:
                    if spell.level == 1:
                        level_school += "1st"
                    elif spell.level == 2:
                        level_school += "2nd"
                    elif spell.level == 3:
                        level_school += "3rd"
                    else:
                        level_school += f"{spell.level}th"
                    level_school += " Level " + spell.school
                if spell.ritual:
                    level_school += " (Ritual)"
                ui.label(level_school).classes("italic text-xs")
                ui.separator()
                ui.label("Casting Time: " + spell.cast)
                ui.label("Range: " + spell.spell_range)
                ui.label("Components: " + self.compile_spell_components(spell.components, spell.material))
                ui.label("Duration: " + spell.duration)
                ui.separator()
                # print(spell.description)
                ui.html(spell.description)
            ui.card().classes("frameborder absolute-center w-full h-full frame no-shadow transparent").style("z-index: -1;")

        dialog.open()

    def rarity_color(self, rarity):
        if rarity in colorschemes.rarity:
            return colorschemes.rarity[rarity]
        else:
            return "#FFFFFF"

    @ui.refreshable
    def money_dialog(self):
        char = session.char
        with ui.dialog() as dialog, ui.card() as card:
            card.classes("fixed-top-right w-1/4 h-full no-shadow").props("square")
            with ui.column().classes("w-full"):
                ui.label("Coins").classes('text-3xl font-bold text-primary')
                ui.separator().props("color=primary")
                with ui.row().classes("w-full justify-center q-pr-md items-center q-px-lg"):
                    ui.label("Total (gp):").classes("font-bold")
                    self.total_gold_label = ui.label(math.floor(char.calculate_total_coin_value(char.currency) / 100)).classes("text-lg font-bold")
                ui.separator()
                currency = char.currency
                input_boxes = {}
                self.coin_counts = {}
                for denom in storage.coin_denoms:
                    with ui.row().classes("w-full justify-between text-xl items-center"):
                        with ui.row().classes("items-center text-normal text-base q-pl-sm"):
                            self.show_coin_icon(denom)
                            with ui.column().classes("h-12 justify-center q-py-none items-start").style("gap:0rem;"):
                                ui.label(denom.capitalize() + f" ({denom[0]}p)").classes("q-py-none h-5")
                                if denom != "gold":
                                    ui.label(storage.coin_labels[denom]).classes("little-text text-slate-400 h-4")
                        with ui.row().classes("w-36 justify-between no-wrap items-center q-pr-md"):
                            input_boxes[denom] = ui.number(format='%d', precision=0, min=0).props("dense outlined").classes("w-20")
                            self.coin_counts[denom] = ui.label(currency[denom]).classes("font-bold text-lg")
                    ui.separator()
                with ui.row().classes("w-full justify-center"):
                    ui.button("Add", on_click=lambda: self.set_money(1, input_boxes)).props("outline")
                    ui.button("Remove", on_click=lambda: self.set_money(-1, input_boxes)).props("outline")
                ui.checkbox("Use electrum", value=False, on_change=lambda e: session.inventory_manager.set_use_electrum(e.value)).classes("w-full justify-center")
            ui.card().classes("frameborder absolute-center w-full h-full frame no-shadow transparent").style("z-index: -1;")
        dialog.open()

    def set_money(self, polarity, inputs):
        request = {}
        for _, (denom, money_input) in enumerate(inputs.items()):
            amount = int(money_input.value) if money_input.value is not None else 0
            request[denom] = amount
        if polarity < 0:
            # check if there is enough money
            if not session.inventory_manager.check_available_coins(request):
                ui.notify("Not enough coins")
                return
        for money_input in inputs.values():
            money_input.set_value(None)
        for _, (denom, amount) in enumerate(request.items()):
            amount *= polarity
            session.inventory_manager.edit_money(amount, denom)
        # self.moneyDialog.refresh()
        currency = session.char.currency
        for _, (denom, label) in enumerate(self.coin_counts.items()):
            label.set_text(currency[denom])
        # for _, (denom, label) in enumerate(self.coinCountsSmall.items()):
        #     label.set_text(currency[denom])
        self.show_coin_row.refresh()
        self.total_gold_label.set_text(math.floor(session.char.calculate_total_coin_value(session.char.currency) / 100))

    def show_coin_icon(self, coin):
        colors = {"platinum":"#e5e4e2", "gold":"#FFD700", "electrum":"#F2E279", "silver":"#C0C0C0", "copper":"#B87333"}
        coin_icons = {"platinum":"hexagon", "gold":"circle"}
        svgs = {"silver":icons.ROUNDED_SQUARE_SVG, "electrum":icons.DIAMOND_SVG, "copper":icons.HALF_CIRCLE_SVG}
        if coin in coin_icons:
            ui.icon(coin_icons[coin], color=colors[coin]).classes("q-pr-xs").props("size=1.2rem")
        else:
            ui.html(svgs[coin]).classes("q-pr-xs")

    @ui.refreshable
    def show_coin_row(self):
        currency = session.char.currency
        for c in currency:
            if currency[c] != 0:
                ui.label(currency[c]).classes("q-pl-xs text-slate-400 font-bold")
                self.show_coin_icon(c)

    def show_inventory(self, inventory_tab):
        char = session.char
        with ui.tab_panel(inventory_tab).classes("q-pa-none"), ui.scroll_area().classes("h-full w-full q-pa-none"):
            with ui.row().classes("w-full no-wrap absolute-top justify-center items-center").style("gap:0.1em").on("click", lambda: self.money_dialog()):
                self.coin_counts_small = {}
                self.show_coin_row()

            with ui.row().classes("w-full q-pt-md no-wrap font-bold text-slate-400 uppercase"):
                ui.label("Name").classes("col-4")
                ui.label("Weight").classes("col-1")
                ui.label("Cost").classes("col-1")
                ui.label("Notes").classes("col-4")

            storages = {}
            for inventory_item in char.inventory:
                item = inventory_item.item
                if not item.storage in storages:
                    storages[item.storage] = []
                storages[item.storage].append(inventory_item)

            storage_names = list(storages.keys())

            if None in storage_names:
                storage_names.remove(None)
                storage_names.insert(0, None)

            for location in storage_names:
                with ui.column().classes("w-full").style("gap: 0.1rem;"):
                    if location is None:
                        location_name = "Equipment"
                    else:
                        location_name = location
                    ui.label(location_name).classes("font-bold text-primary uppercase")
                    ui.separator().props("color=primary")
                for inventory_item in storages[location]:
                    item = inventory_item.item
                    if item.hidden:
                        continue
                    with ui.row().classes("no-wrap w-full") as item_row:
                        item_row.props(f"item-id={item.item_id}")
                        item_row.on('click', lambda id=inventory_item.identifier: self.show_item_info(id))
                        storage.items_id_map[inventory_item.identifier] = inventory_item
                        name = item.name
                        weight = item.weight * item.amount
                        if weight.is_integer():
                            weight = int(weight)
                        weight = str(weight)
                        if item.amount != 1:
                            name += f" ({item.amount})"
                            weight += f" ({item.weight})"
                        ui.label(name).classes("col-4").style(f"color: {self.rarity_color(item.rarity)};")
                        if item.weight == 0:
                            ui.label("--").classes("col-1 text-center text-slate-400")
                        else:
                            ui.html(f"<span>{weight}</span><span class='text-slate-400 text-xs'> lb.</span>").classes("col-1 text-center")
                        cost = item.cost
                        if re.match(r"\d*[pgesc]{2}", cost):
                            m = re.search(r"(\d*)([pgesc]{2})", cost)
                            cost = float(m.group(1)) * item.amount
                            if cost.is_integer():
                                cost = int(cost)
                            cost = str(cost)
                            if item.amount != 1:
                                cost += f" ({m.group(1)})"
                            if cost == "0":
                                ui.label("--").classes("col-1 text-center text-slate-400")
                            else:
                                ui.html(f"<span>{cost}</span><span class='text-slate-400 text-xs'> {m.group(2)}</span>").classes("col-1 text-center")
                        else:
                            if len(item.cost) == 0:
                                ui.label("--").classes("col-1 text-center text-slate-400")
                            ui.label(item.cost).classes("col-1 text-center")
                        notes = ""
                        if isinstance(item, Weapon):
                            for i, prop in enumerate(item.properties):
                                notes += prop
                                if i != len(item.properties)-1:
                                    notes += ", "
                        elif isinstance(item, Armor):
                            notes += item.armor_type
                        ui.label(notes).classes("text-xs")
                    ui.separator()
            # ui.separator()

            attunable_items = []
            for item in char.inventory:
                if item.item.attunement:
                    attunable_items.append(item)
            attuned_items = []
            for item in attunable_items:
                if item.attuned:
                    attuned_items.append(item)
            with ui.column().classes("text-primary font-bold w-full").style("gap:0.1rem"):
                ui.label("ATTUNEMENT")
                ui.separator().props("color=primary")
            ui.label(f"Attuned Items: {len(attuned_items)}/{char.query.get_variable_value("attunement:max")}").classes("text-slate-400 font-bold")
            with ui.column().classes("q-pl-none"):
                for item in attuned_items:
                    ui.label("- "+item.item.name).style(f"color: {self.rarity_color(item.item.rarity)};").classes("q-pl-none").on('click', lambda id=item.identifier: self.show_item_info(id))

            quest_items = char.get_quest_items()
            if quest_items is None:
                quest_items = ""
            with ui.column().classes("text-primary font-bold w-full").style("gap:0.1rem"):
                ui.label("QUEST ITEMS")
                ui.separator().props("color=primary")
            # ui.label(questItems).classes("text-xs")
            ui.textarea(value=quest_items, on_change=lambda e: session.inventory_manager.edit_quest_items(e.value)).classes("w-full").props("dense autogrow")

            treasure = char.get_treasure()
            # if treasure != None:
            with ui.column().classes("text-primary font-bold w-full").style("gap:0.1rem"):
                ui.label("TREASURE")
                ui.separator().props("color=primary")
            # ui.label(treasure).classes("text-xs")
            ui.textarea(value=treasure, on_change=lambda e: session.inventory_manager.edit_treasure(e.value)).classes("w-full").props("dense autogrow")

    def show_item_info(self, identifier):
        if identifier is None:
            return
        inventory_item = storage.items_id_map[identifier]
        item = inventory_item.item
        with ui.dialog().props("full-height")  as dialog, ui.card() as card:
            card.classes("fixed-top-right w-2/5 h-full no-shadow q-pa-none").props("square")
            with ui.scroll_area().classes("w-full h-full q-pa-none"):
                name = item.name
                if item.amount != 1:
                    name += f" ({item.amount})"
                with ui.row().classes("w-full justify-between q-pr-md items-center q-pt-sm"):
                    ui.label(name).classes('text-xl font-bold text-primary').style(f"color: {self.rarity_color(item.rarity)};")
                    with ui.row().classes("items-center"):
                        if item.charges is not None:
                            ui.label("Charges: ")
                            item_charges = ItemCharges(inventory_item)
                            item_charges.show_module()
                ui.label("Common" if item.rarity is None else item.rarity)
                ui.separator()
                if isinstance(item, Weapon):
                    properties = ""
                    for i, prop in enumerate(item.properties):
                        properties += prop
                        if i < len(item.properties)-1:
                            properties += ", "
                    ui.label("Properties: " + properties)
                    damage = item.damage
                    if item.versatile != "" and item.versatile is not None:
                        damage += f"({item.versatile})"
                    ui.label(f"Damage: {damage} {item.damage_type}")
                elif isinstance(item, Armor):
                    ui.label("Armor Type: " + item.armor_type)
                    ui.label("Armor Class: " + item.armor_class)
                ui.label("Category: " + item.category + (" (Attunement)" if item.attunement else ""))
                ui.label("Cost: " + item.cost)
                ui.label("Weight: " + str(item.weight) + " lbs")
                ui.separator()
                ui.html(item.description)
            ui.card().classes("frameborder absolute-center w-full h-full frame no-shadow transparent").style("z-index: -1;")

        dialog.open()

    def show_features(self, features_tab):
        char = session.char
        with ui.tab_panel(features_tab).classes("q-pa-none"), ui.scroll_area().classes("h-full w-full q-pa-none"):
            with ui.row().classes("w-full").style("gap:0.1em"):
                ui.label("CLASS FEATURES").classes("font-bold text-md text-primary")
                ui.separator().props("color=primary")
            features, child_dict = char.get_class_features()
            self.show_features_group(features, child_dict)
            with ui.row().classes("w-full").style("gap:0.1em"):
                ui.label("RACIAL FEATURES").classes("font-bold text-md text-primary")
                ui.separator().props("color=primary")
            # for trait in char.getRacialTraits():
            #     showFeature(trait)
            features, child_dict = char.get_racial_traits()
            self.show_features_group(features, child_dict)
            with ui.row().classes("w-full").style("gap:0.1em"):
                ui.label("FEATS").classes("font-bold text-md text-primary")
                ui.separator().props("color=primary")
            features, child_dict = char.get_feats()
            self.show_features_group(features, child_dict)
            with ui.column().classes("w-full").style("gap:0.1rem"):
                ui.label("ADDITIONAL FEATURES").classes("font-bold text-md text-primary")
                ui.separator().props("color=primary")
            ui.label(char.get_additional_features()).classes("text-xs")

    def show_features_group(self, features, child_dict):
        display_dict = {}
        for child_id in child_dict:
            feature = Feature(next((x for x in features if x.feature_id == child_id), None))
            if feature.display:
                display_dict[child_id] = child_dict[child_id]
        for display_id in display_dict:
            feature = Feature(next((x for x in features if x.feature_id == display_id), None))
            # skipping if sheet has disabled display
            # if feature.display == False: continue
            # skipping if child of another feature - this might block some features
            if session.char.query.check_if_child(display_id, display_dict):
                continue
            # if session.char.query.checkParentFeature(id): continue
            with ui.row().classes("w-full items-center justify-start").style("gap:0.1rem;"):
                feature = Feature(next((x for x in features if x.feature_id == display_id), None))
                feature.show_module()
                for child in child_dict[display_id]:
                    child_feature = next((x for x in features if x.feature_id == child), None)
                    if child_feature is not None:
                        with ui.row().classes("w-full no-wrap"):
                            ui.separator().props("vertical")
                            feature = Feature(child_feature)
                            feature.show_module()

    def show_background(self, background_tab):
        char = session.char
        with ui.tab_panel(background_tab).classes("q-pa-none"), ui.scroll_area().classes("h-full w-full q-pa-none"):
            with ui.column().classes("w-full").style("gap:0.1em"):
                ui.label("BACKGROUND").classes("font-bold text-md text-primary")
                ui.separator().props("color=primary")
            background = char.get_background()
            with ui.column().classes("text-sm").style("gap:0.1em"):
                ui.label(background.name).classes("font-bold text-md")
                ui.label(background.feature_name).classes("font-bold")
                ui.label(background.feature_description)

            with ui.column().classes("w-full").style("gap:0.1em"):
                ui.label("CHARACTERISTICS").classes("font-bold text-md text-primary")
                ui.separator().props("color=primary")

            with ui.grid(columns = '6.8rem '*5).classes(""):
                top_row = ["alignment", "gender", "eyes", "size", "height"]
                bottom_row = ["faith", "hair", "skin", "age", "weight"]
                for row in [top_row, bottom_row]:
                    for e in row:
                        ui.label(e.upper()).classes("font-bold h-2")
                    for e in row:
                        ui.label(char.characteristics[e]).classes("h-2")

            ui.separator().props("color=primary")

            traits = {"Personality Traits": background.traits,
                    "Ideals": background.ideals,
                    "Bonds": background.bonds,
                    "Flaws": background.flaws}

            for trait_name, trait in traits.items():
                with ui.column().classes("w-full text-sm").style("gap:0.2rem"):
                    ui.label(trait_name).classes("font-bold")
                    ui.label(trait).classes("").style('white-space: pre-wrap')

    def show_extras(self, extras_tab):
        char = session.char
        with ui.tab_panel(extras_tab).classes("q-pa-none"), ui.scroll_area().classes("h-full w-full q-pa-none"):
            profs = char.get_training()
            with ui.column().classes("w-full").style("gap:0.1rem"):
                ui.label("PROFICIENCIES & TRAINING").classes("font-bold text-md text-primary")
                ui.separator().props("color=primary")
            with ui.column().classes("w-full").style("gap:0.1rem"):
                ui.label("ARMOR").classes("font-bold")
                ui.label(", ".join(profs[1]))
            with ui.column().classes("w-full").style("gap:0.1rem"):
                ui.label("WEAPONS").classes("font-bold")
                ui.label(", ".join(profs[0]))
            with ui.column().classes("w-full").style("gap:0.1rem"):
                ui.label("TOOLS").classes("font-bold")
                ui.label(", ".join(profs[2]+profs[3]))
            with ui.column().classes("w-full").style("gap:0.1rem"):
                ui.label("LANGUAGES").classes("font-bold")
                ui.label(", ".join(profs[4]))

            if len(char.companions) > 0:
                with ui.column().classes("w-full").style("gap:0.1rem;"):
                    ui.label("COMPANIONS").classes("font-bold text-md text-primary")
                    ui.separator().props("color=primary")
                for comp in char.companions:
                    with ui.column().classes("w-full").style("gap:0.1rem;"):
                        # name
                        ui.label(comp.name).classes("font-bold text-xl")
                        # size, type, alignment
                        ui.label(f"{comp.size if comp.size is not None else ""} {comp.companion_type}, {comp.alignment.capitalize() if comp.alignment is not None else "Unaligned"}").classes('italic text-slate-400')
                        ui.separator()
                        # ac, hp, speed
                        ui.html(f"<b>Armor Class</b> {comp.ac}")
                        ui.html(f"<b>Hit Points</b> {comp.hp}")
                        ui.html(f"<b>Speed</b> {comp.speed}")
                        ui.separator()
                        # scores
                        with ui.row().classes("w-full"):
                            for score, value in comp.scores.items():
                                with ui.column().classes("items-center").style("gap:0.1rem;"):
                                    ui.label(score[:3].upper()).classes("font-bold")
                                    ui.label(f"{value} ({math.floor((int(value)-10)/2)})")
                        ui.separator()
                        # the everything section
                        if comp.condition_immunities is not None:
                            ui.html(f"<b>Condition Immunities</b> {comp.condition_immunities}")
                        if comp.skills is not None:
                            ui.html(f"<b>Skills</b> {comp.skills}")
                        if comp.saves is not None:
                            ui.html(f"<b>Saving Throws</b> {comp.saves}")
                        if comp.senses is not None:
                            ui.html(f"<b>Senses</b> {comp.senses}")
                        if comp.languages is not None:
                            ui.html(f"<b>Languages</b> {comp.languages}")
                        if comp.challenge is not None:
                            ui.html(f"<b>Challenge</b> {comp.challenge}")
                        # traits
                        for f in [("Traits", comp.traits), ("Actions", comp.actions)]:
                            if len(f[1]) > 0:
                                ui.separator()
                                ui.label(f[0]).classes("text-lg font-bold")
                                for t in f[1]:
                                    usage = (t.usage + f" ({t.action})" if t.action is not None else "") if t.usage is not None else None
                                    if t.sheet is None:
                                        continue
                                    ui.html(f"<b>{t.name}</b>. {f"<b>{usage}</b>. " if usage is not None else ""} {t.sheet}")

            with ui.column().classes("w-full").style("gap:0.1rem"):
                ui.label("NOTES").classes("text-primary font-bold text-md")
                ui.separator().props("color=primary")
            # for note in char.getNotes().split("\n"):
            #     ui.label(note)
            ui.textarea(value=char.get_notes(), on_change=lambda e: session.notes_manager.edit_notes(e.value)).classes("w-full").props("dense autogrow")

class Feature(Module):
    def __init__(self, feature):
        super().__init__()
        self.feature = feature
        self.empty = self.feature.sheet is None
        self.display = feature.display

    def show_module(self):
        feature = self.feature
        with ui.column().style("gap:0.1em"):
            usage = feature.usage
            if feature.action is not None:
                if usage is None:
                    usage = f"({feature.action})"
                else:
                    usage += f" ({feature.action})"
            with ui.row().classes("w-full items-center justify-start"):
                ui.label(feature.name).classes("font-bold").on('click', lambda feature=feature: self.show_feature_info(feature))
                if usage is not None and "/" in usage:
                    feature_charges = FeatureCharges(feature)
                    feature_charges.show_module()
            ui.label(usage).classes("text-sm")
            if feature.sheet is not None:
                ui.html(feature.sheet).classes("text-xs")

    def show_feature_info(self, feature):
        with ui.dialog().props("full-height") as dialog, ui.card() as card:
            card.classes("fixed-top-right w-2/5 q-pa-none h-full no-shadow").props("square bordered")
            with ui.scroll_area().classes("w-full h-full q-pa-none"):
                ui.label(feature.name).classes('text-xl font-bold text-primary')
                usage = feature.usage
                if feature.action is not None:
                    if usage is None:
                        usage = "({feature.action})"
                    else:
                        usage += f" ({feature.action})"
                if usage != "" and not usage is None:
                    ui.label(usage).classes("italic")
                ui.separator()
                ui.html(feature.description)
            ui.card().classes("frameborder absolute-center w-full h-full frame no-shadow transparent").style("z-index: -1;")

        dialog.open()

class FeatureCharges(ChargeListener):
    def __init__(self, feature):
        super().__init__()
        self.feature = feature
        self.max_uses = 0
        self.minus_button = None
        self.label = None
        self.plus_button = None

    def show_module(self):
        usage = self.feature.usage.split("/")
        numerical_usage = re.search(r"\d+", usage[0])
        if numerical_usage is None:
            return
        max_uses = int(numerical_usage.group())
        self.max_uses = max_uses
        recharge = usage[1]

        char = session.char
        feature = self.feature

        if feature.feature_id not in session.charges:
            session.charges[feature.feature_id] = (max_uses, recharge)

        charges = char.get_charges(feature.feature_id, max_uses)

        with ui.row().classes("items-center").style("gap:0.5rem;"):
            self.minus_button = ui.button(icon="remove", on_click=lambda id=feature.feature_id, max=max_uses: session.change_charges(id, -1, max)).classes("little-text q-py-none q-px-xs").props("outline size=0.5rem")
            label = ui.label(charges)
            self.label = label
            self.plus_button = ui.button(icon="add", on_click=lambda id=feature.feature_id, max=max_uses: session.change_charges(id, 1, max)).classes("little-text q-py-none q-px-xs").props("outline size=0.5rem")
        self.set_button_states(charges)

    def charge_callback(self):
        charges = session.char.get_charges(self.feature.feature_id, self.max_uses)
        self.label.text = charges
        self.label.update()
        self.set_button_states(charges)

    def set_button_states(self, charges):
        if charges == self.max_uses:
            self.plus_button.disable()
        else: self.plus_button.enable()
        if charges == 0:
            self.minus_button.disable()
        else: self.minus_button.enable()

class ItemCharges(ChargeListener):
    def __init__(self, inventory_item):
        super().__init__()
        self.inventory_item = inventory_item
        self.max_uses = 0
        self.minus_button = None
        self.label = None
        self.plus_button = None

    def show_module(self):
        max_uses = self.inventory_item.item.charges
        self.max_uses = max_uses

        char = session.char
        identifier = self.inventory_item.identifier

        charges = char.get_charges(identifier, max_uses)

        with ui.row().classes("items-center").style("gap:0.5rem;"):
            self.minus_button = ui.button(icon="remove", on_click=lambda id=identifier, max=max_uses: session.change_charges(id, -1, max)).classes("little-text q-py-none q-px-xs").props("outline size=0.5rem")
            label = ui.label(charges)
            self.label = label
            self.plus_button = ui.button(icon="add", on_click=lambda id=identifier, max=max_uses: session.change_charges(id, 1, max)).classes("little-text q-py-none q-px-xs").props("outline size=0.5rem")
        self.set_button_states(charges)

    def charge_callback(self):
        charges = session.char.get_charges(self.inventory_item.identifier, self.max_uses)
        self.label.text = charges
        self.label.update()
        self.set_button_states(charges)

    def set_button_states(self, charges):
        if charges == self.max_uses:
            self.plus_button.disable()
        else: self.plus_button.enable()
        if charges == 0:
            self.minus_button.disable()
        else: self.minus_button.enable()

class SpellSlots(SpellslotListener):
    def __init__(self, level):
        super().__init__()
        self.level = level
        self.buttons = []

    def show_module(self):
        # array to store the buttons for this level
        self.buttons = []
        # number of slots of this level available among all classes
        total = 0
        level = self.level
        # for spellcasting in session.char.spellcastings:
        #     if len(spellcasting.slots) >= level:
        #         total += spellcasting.slots[level-1]
        total = session.char.get_total_spellslots()[level-1]
        for _ in range(0, total):
            box = ui.checkbox().on("click", lambda e, level=level: self.set_slots(level, e.sender.value)
                                ).props("unchecked-icon=check_box_outline_blank checked-icon=disabled_by_default size=xl dense").classes("w-3 h-3")
            self.buttons.append(box)
        self.update_buttons()

    def set_slots(self, level, value):
        session.set_spellslots(level, value)
        self.update_buttons()

    def update_buttons(self):
        for i, button in enumerate(self.buttons):
            button.set_value(True if i < session.char.get_used_spellslots(self.level) else False)

    def spellslot_callback(self):
        self.update_buttons()
