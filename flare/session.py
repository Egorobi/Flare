from nicegui import ui
from saver import Saver
from colorschemes import color_schemes

port = None

char = None

zoom = 1

inventory_manager = None
notes_manager = None

loader = None

name = None

saver = Saver()

color_scheme = color_schemes["default"]

health_listeners = []
hitdice_listeners = []
spellslot_listeners = []
charge_listeners = []
roll_listeners = []

# rest dialogs
short_rest_dialog = None
long_rest_dialog = None

# dice roller
roll_dialog = None

# stat info dialog
stat_info_dialog = None
stat_info_created = False

# charges
charges = {}

def change_health(change):
    assert char is not None, "Character not set"
    current, temp = char.get_hitpoints()
    # print("current {} temp {}".format(current, temp))
    # print(change)
    if change < 0:
        remain = min(temp + change, 0)
        print(remain)
        temp = max(0, temp + change)
        current = max(0, current + remain)
    else:
        current = min(char.max_hp, current + change)
    char.set_hitpoints(current, temp)
    # print("current {} temp {}".format(current, temp))
    # call health listeners
    for listener in health_listeners:
        listener.health_callback(current, temp)

async def set_temp_hitpoints(value):
    assert char is not None, "Character not set"
    current, _ = char.get_hitpoints()
    value = 0 if value is None else int(value)
    # tempHpLabel.text = value
    char.set_hitpoints(current, value)

def set_hitdice(props, value):
    assert char is not None, "Character not set"
    dice_class = props["class"]
    if value:
        char.set_used_hitdice(dice_class, char.get_used_hitdice(dice_class)+1)
    else:
        char.set_used_hitdice(dice_class, char.get_used_hitdice(dice_class)-1)
    # updateHitDiceButtons(diceClass)

    for listener in hitdice_listeners:
        listener.hitdice_callback()

def change_charges(charge_id, increment, max_uses):
    assert char is not None, "Character not set"
    feature_charges = char.get_charges(charge_id, max_uses)
    num = max(feature_charges+increment, 0)
    num = min(num, max_uses)
    char.set_charges(charge_id, num)

    for listener in charge_listeners:
        listener.charge_callback()

def set_spellslots(level, value):
    assert char is not None, "Character not set"
    used_slots = char.get_used_spellslots(level)
    if value:
        used_slots = min(used_slots+1, char.get_total_spellslots()[level])
    else:
        used_slots = max(0, used_slots-1)
    char.set_used_spellslots(level, used_slots)
    for listener in spellslot_listeners:
        listener.spellslot_callback()

async def perform_rest(rest_type):
    assert char is not None, "Character not set"
    assert long_rest_dialog is not None, "Long rest dialog not set"
    if rest_type == "long":
        if not await long_rest_dialog.wait_module() == "Confirm":
            return
    if rest_type == "short":
        if not await short_rest_dialog.wait_module() == "Confirm":
            return

    if rest_type == "short":
        # warlock regains spellslots
        for spellcast in char.spellcastings:
            if spellcast.name != "Warlock":
                continue
            for i, slot in enumerate(spellcast.slots):
                char.set_used_spellslots(i+1, max(char.get_used_spellslots(i+1) - slot, 0))

        # restore feature charges
        for charge_id, (max_uses, recharge) in charges.items():
            if recharge == "Short Rest":
                char.set_charges(charge_id, max_uses)
    if rest_type == "long":
        # reset spells
        for spellcast in char.spellcastings:
            for i, slot in enumerate(spellcast.slots):
                char.set_used_spellslots(i+1, max(char.get_used_spellslots(i+1) - slot, 0))
        # restore health
        change_health(char.max_hp)
        # regain hitdice
        for hd in char.hit_dice:
            char.set_used_hitdice(hd[0], max(char.get_used_hitdice(hd[0]) - max(1, hd[1] // 2), 0))

        # restore feature charges
        for charge_id, (max_uses, recharge) in charges.items():
            if recharge == "Short Rest" or recharge == "Long Rest":
                char.set_charges(charge_id, max_uses)

    # call spellslot and feature charge listeners
    for listener in spellslot_listeners:
        listener.spellslot_callback()
    for listener in charge_listeners:
        listener.charge_callback()

def set_page_color(scheme):
    assert char is not None, "Character not set"
    saver.save_color(char.name, scheme)
    ui.run_javascript('location.reload();')

def set_background():
    # NOTE this does not work, changes both backgrounds not just dark or light mode
    dark_back_mode = saver.get_background(dark = True)
    print(dark_back_mode)
    dark_body = ui.query('body')
    if dark_back_mode == "match":
        dark_body.style("background-image: linear-gradient(0.25turn, var(--q-backtint), #141414, #141414, var(--q-backtint));")
    elif dark_back_mode == "night":
        dark_body.style("background-image: linear-gradient(0.25turn, #151c24, #141414, #141414, #151c24);")
    else:
        dark_body.style("background-image: '';")
        dark_body.style("background-color: black;")
    light_back_mode = saver.get_background()
    print(light_back_mode)
    light_body = ui.query("body")
    if light_back_mode == "match":
        light_body.style("background-image: linear-gradient(0.25turn, var(--q-backtint), white, white, var(--q-backtint));")
    else:
        light_body.style("background-image: '';")
        light_body.style("background-color: white;")

def val_to_string(val):
    return f"{val:+d}"

def show_stat_info(stat, stat_name=None):
    assert stat_info_dialog is not None, "Stat info dialog not set"
    if not stat_info_created:
        stat_info_dialog.show_module(stat, stat_name)
    else:
        stat_info_dialog.show_module.refresh(stat, stat_name)

def update_roll_listeners():
    for listener in roll_listeners:
        listener.roll_callback()
