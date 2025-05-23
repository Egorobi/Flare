from lxml import etree as et
from editors.editor import Editor

class NotesManager():

    def __init__(self, editor: Editor):
        self.editor = editor

    def edit_notes(self, text):
        if text is None:
            text = ""
        root = self.editor.get_root()
        # just save everyting in the left column
        notes = root.find("./build/input/notes")
        note = notes.find("./note[@column='left']")
        if note is None:
            note = et.SubElement(notes, "note")
            note.attrib["column"] = "left"

        # notes.text = et.CDATA(text)
        note.text = text
        self.editor.apply_edits(scope=None)
