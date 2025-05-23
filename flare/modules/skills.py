from nicegui import ui
from modules.module import Module
from modules.dialogs import RollContext
import session
import frames

class AbilityScore(Module):
    score_size = 6

    def __init__(self, score):
        self.score = score

    def show_module(self):
        char = session.char
        with ui.card().classes("items-center no-shadow transparent").style(f"gap: 0em; width:{self.score_size}rem; height: {self.score_size}rem"):
            frames.show_frame("ability score")
            with ui.column().classes("items-center justify-between absolute-center q-pt-sm q-pb-xs h-full"):
                ui.label(self.score.upper()).classes("ability-label")
                ui.label(char.ability_scores[self.score][0]).classes("").on("click", lambda : session.show_stat_info(self.score.lower(), self.score.title()))
            # ui.label(valToString(char.abilityScores[score][1])).classes("text-2xl font-bold absolute-center")
            with ui.button(session.val_to_string(char.ability_scores[self.score][1]), on_click=lambda mod=char.ability_scores[self.score][1]: session.roll_dialog.wait_module([(1, 20, mod)])).classes(
                            "text-2xl font-bold q-pa-none absolute-center width").props("size=xl dense unelevated flat text-color=adaptcolor padding=sm"):
                context_menu = RollContext()
                context_menu.show_module(char.ability_scores[self.score][1])

class AbilityScores(Module):

    def show_module(self):
        for score in session.char.ability_scores:
            ability_score = AbilityScore(score)
            ability_score.show_module()

class ProficiencyBonus(Module):
    score_size = 6

    def show_module(self):
        with ui.card().classes("items-center no-shadow transparent").style(f"gap: 0.5em; width: {self.score_size}rem; height: {self.score_size}rem"):
            frames.show_frame("proficiency bonus")
            ui.label(session.val_to_string(session.char.proficiency_bonus)).classes("text-2xl font-bold h-8 absolute-center q-pb-lg")
            with ui.column().classes("items-center justify-between absolute-center q-pt-sm q-pb-xs h-full"):
                ui.label("Proficiency").classes("")
                ui.label("Bonus").classes("")

class SavingThrows(Module):

    def show_module(self):
        char = session.char
        with ui.card().classes("items-center no-shadow transparent"):
            frames.show_frame("saves")
            with ui.grid(columns=2).classes("q-gutter-xs items-center"):
                scores = {"str": "strength", "dex": "dexterity", "con": "constitution", "int": "intelligence", "wis": "wisdom", "cha": "charisma"}
                for save in char.saving_throws:
                    with ui.row().classes("no-wrap items-center justify-center"):
                        if char.saving_throws[save][0]:
                            ui.icon("circle").classes("col-1")
                        else:
                            ui.icon("radio_button_unchecked").classes("col-1")
                        ui.label(save).classes("col-2").on("click", lambda s=scores[save.lower()]: session.show_stat_info(s.lower()+":save", f"{s.capitalize()} Saving Throw"))
                        with ui.button(session.val_to_string(char.saving_throws[save][1]), on_click=lambda mod=char.saving_throws[save][1]: session.roll_dialog.wait_module([(1, 20, mod)])).classes(
                            "col-4 font-bold q-pa-none ").props("size=md unelevated flat text-color=adaptcolor"):
                            context_menu = RollContext()
                            context_menu.show_module(char.saving_throws[save][1])
            ui.label("SAVING THROWS").classes("font-bold")

class PassiveSenses(Module):

    def show_module(self):
        char = session.char
        with ui.card().classes("items-center w-full no-shadow transparent").style("gap:0.3rem; height:15.5rem;"):
            frames.show_frame("senses")
            passives = ["perception", "investigation", "insight"]
            for i, passive in enumerate(passives):
                with ui.row().classes("w-full"):
                    ui.label(char.passive_skills[i])
                    ui.label("PASSIVE " + passive.upper()).on("click", lambda s=passive: session.show_stat_info(s.lower()+":passive", f"Passive {s.title()}"))
                ui.separator()
            ui.label("SENSES").classes("font-bold")
            with ui.column().classes("w-full items-center").style("gap:0.1rem;"):
                for sense in char.senses:
                    ui.label(f"{sense[0].capitalize()} {sense[1]} ft.")

class Skills(Module):
    def show_module(self):
        char = session.char
        with ui.card().classes("col-6 h-max no-shadow transparent"):
            frames.show_frame("skills")
            with ui.column().classes("q-gutter-xs items-center w-full").style("gap:0.1rem"):
                for skill in char.skills:
                    with ui.row().classes("w-full no-wrap q-pr-md items-center"):
                        if char.skills[skill][1]:
                            ui.icon("radio_button_checked").classes("col-2")
                        elif char.skills[skill][0]:
                            ui.icon("circle").classes("col-2")
                        else:
                            ui.icon("radio_button_unchecked").classes("col-2")
                        ui.label(skill).classes("col-7").on("click", lambda s=skill: session.show_stat_info(s.lower()))
                        # ui.label(valToString(char.skills[skill][2])).classes("col-2")
                        with ui.button(session.val_to_string(char.skills[skill][2]), on_click=lambda mod=char.skills[skill][2]: session.roll_dialog.wait_module([(1, 20, mod)])).classes(
                            "col-2 text-md q-pa-none").props("size=0.9rem dense unelevated flat text-color=adaptColor padding=none"):
                            context_menu = RollContext()
                            context_menu.show_module(char.skills[skill][2])
                    ui.separator()
                ui.label("SKILLS").classes("font-bold")
