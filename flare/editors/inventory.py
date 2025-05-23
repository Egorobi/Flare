from editors.editor import Editor

class InventoryManager():

    use_electrum = False

    money_values = {"platinum": 10, "gold": 1, "electrum": 0.5, "silver": 0.1, "copper": 0.01}
    money_order = list(money_values.keys())
    if not use_electrum:
        money_order.remove("electrum")

    full_denoms = ["platinum", "gold", "electrum", "silver", "copper"]

    def __init__(self, editor: Editor):
        self.editor = editor

    def edit_money(self, amount, denom="gold"):
        root = self.editor.get_root()
        current = self.editor.char.query.query_currency().copy()

        current = self.change_money(current, amount, denom)

        currency = root.find("./build/input/currency")

        for d in self.full_denoms:
            currency.find("./"+d).text = str(current[d])
        self.editor.apply_edits(scope = "coins")

    def check_available_coins(self, request):
        request_total = self.editor.char.calculate_total_coin_value(request)
        available_total = self.editor.char.calculate_total_coin_value(self.editor.char.currency)
        # print(requestTotal)
        # print(availableTotal)
        if request_total <= available_total:
            return True
        else:
            return False

    def set_use_electrum(self, use):
        self.use_electrum = use
        self.money_order = list(self.money_values.keys())
        if not use:
            self.money_order.remove("electrum")

    def change_money(self, current, amount, denom):
        if amount >= 0 or current[denom] >= abs(amount):
            # just add lol
            current[denom] += int(amount)
        else:
            # pain
            # use whats possible of this denomination
            # convert amount to absolute to make it easier
            amount = abs(amount)
            amount -= current[denom]
            current[denom] = 0
            # figure out how many cp are needed
            needed_cp = amount * (self.money_values[denom] / 0.01)
            # convert until enough cp is available
            # if highest necessary currency is X, convert all of X and lower to cp, remove needed amount,
            # then convert remainder back to up to X and remainder of that to the next lowest and so on
            highest_denom = "copper"
            available = current[highest_denom]
            while available < needed_cp:
                next_largest = self.money_order.index(highest_denom) - 1
                highest_denom = self.money_order[next_largest]
                available += current[highest_denom] * (self.money_values[highest_denom] / 0.01)
                current[highest_denom] = 0
            current["copper"] = 0
            remaining_cp = available - needed_cp
            # convert to hightest and move down if there is remainder
            conversion_to_highest = remaining_cp // (self.money_values[highest_denom] / 0.01)
            current[highest_denom] = int(conversion_to_highest)
            remainder = remaining_cp % (self.money_values[highest_denom] / 0.01)
            next_highest = highest_denom
            while remainder != 0:
                next_highest = self.money_order[self.money_order.index(next_highest) + 1]
                conversion_to_next = remainder // (self.money_values[next_highest] / 0.01)
                remainder = remainder % (self.money_values[next_highest] / 0.01)
                current[next_highest] = int(conversion_to_next)

        return current

    def edit_quest_items(self, text):
        if text is None:
            text = ""
        root = self.editor.get_root()
        notes = root.find("./build/input/quest")

        # notes.text = et.CDATA(text)
        notes.text = text
        self.editor.apply_edits(scope=None)

    def edit_treasure(self, text):
        if text is None:
            text = ""
        root = self.editor.get_root()
        notes = root.find("./build/input/currency/treasure")

        notes.text = text
        self.editor.apply_edits(scope=None)


if __name__ == "__main__":
    dummy_editor = Editor("dummy")
    inv = InventoryManager(dummy_editor)
    # inv.setUseElectrum(True)
    inv.change_money({"pp": 10, "gp": 0, "ep": 0, "sp": 0, "cp": 0}, -1, "ep")
