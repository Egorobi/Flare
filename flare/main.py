import urllib.parse
from nicegui import ui, native, app
from sheet import Sheet
from character_select import SelectPage
from settings import Settings
from saver import Saver
import colorschemes
try:
    import pyi_splash # type: ignore
except:
    print("pyi_splash unavailable")

@ui.page("/character_sheet/{name}")
def character_sheet_page(name):
    name = urllib.parse.unquote(name)
    sheet_saver = Saver()
    # print(saver.getSaves("./saves/"))
    save = [s for s in sheet_saver.get_saves() if s["name"]==name][0]

    print(save)

    sheet = Sheet(save["aurora"])
    sheet.show_sheet()

@ui.page("/character_select")
def character_select():
    select = SelectPage()
    select.show_select_page()

@ui.page("/settings")
def settings_page():
    settings = Settings()
    settings.show_settings()

# app.add_static_files("/assets", "./data/assets")
# ui.navigate.to("/character_select")
# ui.run()

try:
    app.add_static_files("/assets", "./data/assets")

    try:
        pyi_splash.close()
    except:
        print("pyi_splash unavailable")

    ui.navigate.to("/character_select")

    f = open("data/assets/d20pure.svg")
    svg = f.read()

    # add custom colors
    character_saver = Saver()
    colorschemes.color_schemes.update(character_saver.get_custom_colors())

    app.native.window_args["maximized"] = True
    app.native.window_args["zoomable"] = True
    app.native.window_args["text_select"] = True
    app.native.start_args["icon"] = r"data\assets\border.png"
    ui.run(favicon=svg, reload=False, port=native.find_open_port(), native=True, reconnect_timeout=0)
except Exception as Argument:
    # creating/opening a file
    f = open("errorlog.txt", "a")

    # writing in the file
    f.write(str(Argument))

    # closing the file
    f.close()
