from modules.module import Module
import session

class HealthListener(Module):

    def __init__(self):
        session.health_listeners.append(self)

    def health_callback(self, current, temp):
        pass

class HitDiceListener(Module):

    def __init__(self):
        session.hitdice_listeners.append(self)

    def hitdice_callback(self):
        pass

class SpellslotListener(Module):

    def __init__(self):
        session.spellslot_listeners.append(self)

    def spellslot_callback(self):
        pass

class ChargeListener(Module):

    def __init__(self):
        session.charge_listeners.append(self)

    def charge_callback(self):
        pass

class RollsListener(Module):

    def __init__(self):
        session.roll_listeners.append(self)

    def roll_callback(self):
        pass
