from lxml import etree as et
from editors.editor import Editor

class Generator():

    def __init__(self, editor: Editor):
        self.editor = editor
        # self.scoreMap = {
        #     "str": "strength",
        #     "dex": "dexterity",
        #     "con": "constitution",
        #     "int": "intelligence",
        #     "wis": "wisdom",
        #     "cha": "charisma"
        # }
        # self.stats = {} # FIND CHARACTER STATS FROM SHEET
        # self.level = None # FIND CHARACTER LEVEL FROM SHEET
        self.query = editor.char.query

    def get_tree(self):
        return None

    def generate_sum(self):
        elements = self.query.query_elements_list()

        # create parent sum element
        element_sum = et.Element("sum")
        element_count = 0

        for _, elem in et.iterwalk(elements):
            # convert each element in elements to a sum element
            if elem.tag != "element":
                continue
            element_count += 1
            element = et.SubElement(element_sum, "element")
            element.attrib["id"] = elem.attrib.get("id", elem.attrib["registered"])
            element.attrib["type"] = elem.attrib["type"]

        element_sum.attrib["element-count"] = element_count

        return element_sum
