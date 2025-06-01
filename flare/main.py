import urllib.parse
from nicegui import ui, native, app, Client
from nicegui.page import page
from sheet import Sheet
from character_select import SelectPage
from settings import Settings
from error_page import ErrorPage
from requests import Request
from saver import Saver
import colorschemes
try:
    import pyi_splash # type: ignore
    SPLASH = True
except:
    SPLASH = False
import session

@ui.page("/")
def redirect_from_main():
    ui.navigate.to("/character_select")

@ui.page("/character_sheet/{name}")
def character_sheet_page(name):
    name = urllib.parse.unquote(name)
    sheet_saver = Saver()
    save = [s for s in sheet_saver.get_saves() if s["name"]==name][0]

    print(save)

    sheet = Sheet(save["aurora"])
    sheet.show_sheet()

@ui.page("/character_select")
def character_select():
    # raise Exception("oops error")
    # st = "oops" + 69
    select = SelectPage()
    select.show_select_page()

@ui.page("/settings")
def settings_page():
    settings = Settings()
    settings.show_settings()

@app.exception_handler(500)
def custom_error_page(request: Request, exception: Exception):
    with Client(page(''), request=request) as client:
        error_page = ErrorPage()
        error_page.show_error_page(exception)
    return client.build_response(request, 500)

try:
    app.add_static_files("/assets", "./data/assets")
    ui.navigate.to("/character_select")
    ui.page_title('Flare')

    f = open("data/assets/d20pure.svg")
    svg = f.read()

    # add custom colors
    character_saver = Saver()
    colorschemes.color_schemes.update(character_saver.get_custom_colors())

    app.native.window_args["maximized"] = True
    app.native.window_args["zoomable"] = True
    app.native.window_args["text_select"] = True
    app.native.start_args["icon"] = r"data\assets\border.png"
    port = native.find_open_port()
    session.port = port
    if SPLASH:
        pyi_splash.close()
    ui.run(favicon=svg, reload=False, port=port, native=True, reconnect_timeout=10)
except Exception as Argument:
    # creating/opening a file
    f = open("errorlog.txt", "a")

    # writing in the file
    f.write(str(Argument))

    # closing the file
    f.close()
