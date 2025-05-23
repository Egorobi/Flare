from lxml import etree as et
from character import Character

class Editor():
    def __init__(self, file, character: Character):
        self.file = file
        self.parser = et.XMLParser(remove_blank_text=False, compact=False, strip_cdata=False)
        self.char = character
        self.tree = None

    def get_root(self):
        self.tree = et.parse(self.file, self.parser)
        root = self.tree.getroot()
        return root

    def apply_edits(self, scope="all"):
        # self.tree.write(self.file, pretty_print=True)
        self.tree.write(self.file, method="c14n", pretty_print=True)
        if scope == "all":
            self.char.update()
            return
        elif scope == "coins":
            self.char.update_coins()
