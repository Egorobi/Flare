import re
import colorsys
import session
from nicegui import ui, app
from modules.module import Module

class HeadModule(Module):

    def add_head(self):
        color_scheme = session.color_scheme

        # print(colorScheme)

        base = "#FFC360"

        ui.colors(primary=color_scheme[0], theme="#FFA000", dark="#151c24")
        # hueRotation = colorScheme[1]
        # saturation= colorScheme[2]
        # brightness= colorScheme[3]
        # generate dice for colorscheme
        dice = [20, 12, 100, 10, 8, 6, 4]
        for d in dice:
            svg = ""
            with open(f'data/assets/d{d}.svg') as file:
                svg = file.read()
            with open(f"data/assets/temp/roller_d{d}.svg", "w") as file:
                svg = re.sub("stroke:#......", "stroke:"+color_scheme[0], svg)
                file.write(svg)
        app.add_static_files("/assets", "./data/assets")

        frame_pack = session.saver.get_frame_style()

        dark_back_mode = session.saver.get_background(dark = True)
        light_back_mode = session.saver.get_background()

        r, g, b = tuple(int(color_scheme[0].strip("#")[i:i+2], 16) for i in (0, 2, 4))
        primaryhsv = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        # print(primaryhsv)
        backhsv = (primaryhsv[0], 0.1, 1)
        darkbackrgb = (primaryhsv[0], 0.5, 0.1)
        backrgb = colorsys.hsv_to_rgb(backhsv[0], backhsv[1], backhsv[2])
        darkbackhsv = colorsys.hsv_to_rgb(darkbackrgb[0], darkbackrgb[1], darkbackrgb[2])

        goalhsv = (color_scheme[1]/360, color_scheme[2]/100, color_scheme[3]/100)

        r, g, b = tuple(int(base.strip("#")[i:i+2], 16) for i in (0, 2, 4))
        basehsv = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        hue_rotation = 0 if goalhsv[0] == 0 else (goalhsv[0] - basehsv[0]) * 360
        saturation= 0 if goalhsv[1] == 0 else 100 + (goalhsv[1] - basehsv[1]) * 100
        brightness = 0 if goalhsv[2] == 0 else 100 + (goalhsv[2] - basehsv[2]) * 100

        if dark_back_mode == "match":
            darkback = "background-image: linear-gradient(0.25turn, var(--q-dark-backtint), #141414, #141414, var(--q-dark-backtint));"
        elif dark_back_mode == "night":
            darkback = "background-image: linear-gradient(0.25turn, #151c24, #141414, #141414, #151c24);"
        else:
            darkback = "background-color: black;"

        if light_back_mode == "match":
            lightback = "background-image: linear-gradient(0.25turn, var(--q-light-backtint), white, white, var(--q-light-backtint));"
        elif light_back_mode == "paper":
            lightback = """
            background-color: #FCF5E5;
            background-image: radial-gradient(#cfc7b6 0.8px, #FCF5E5 0.8px);
            background-size: 30px 30px;"""
        else:
            lightback = "background-color: white;"

        # background-image: linear-gradient(0.25turn, #0B1026, black, black, #0B1026)
        # linear-gradient(0.25turn, #151c24, black, black, #151c24);
        # background-color: rgb({backrgb[0]*255}, {backrgb[1]*255}, {backrgb[2]*255});
        # background-image: linear-gradient(0.25turn, #151c24, #141414, #141414, #151c24);
        # filter: hue-rotate({hueRotation}deg) saturate({saturation}%) brightness({brightness}%);
        ui.add_head_html(f'''
        <script>
        window.onload = () => {{
            emitEvent('content_loaded');
        }};
        </script>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.3.0/font/bootstrap-icons.css">
        <style type="text/tailwindcss" lang="scss">     
            body{{
                font-family: "Roboto", sans-serif;
                -ms-overflow-style: none;  /* Internet Explorer 10+ */
                scrollbar-width: none;  /* Firefox */
                --q-adaptcolor: black;
                --q-adaptbg: white;
                --q-light-backtint: rgb({backrgb[0]*255}, {backrgb[1]*255}, {backrgb[2]*255});
                --q-dark-backtint: rgb({darkbackhsv[0]*255}, {darkbackhsv[1]*255}, {darkbackhsv[2]*255});
                zoom: 1.0;
            }}
            body.body--light{{
                --q-adaptcolor: black;
                --q-adaptbg: white;
                --q-backtint: var(--q-light-backtint);
                {lightback}
            }}
            body.body--dark{{
                --q-adaptcolor: white;
                --q-adaptbg: #151c24;
                --q-backtint: var(--q-dark-backtint);
                {darkback}
            }}
            ::-webkit-scrollbar {{
                display: none;  /* Safari and Chrome */
            }}
            .everything{{
                margin: auto;
            }}
            .tiny-text{{
                font-size: 8px;
            }}
            .little-text{{
                font-size: 12px;
            }}
            .health-input{{
                max-height: 10px;
            }}
            .temp-input{{
                max-height: 80px;
            }}
            .health-button{{
                margin-top: 0px;
                margin-bottom: 0px;
            }}
            .ability-label{{
                font-size: 10px;
            }}
            .dice-icon{{
                color: #000000;
            }}
            .frame{{
                filter: hue-rotate({hue_rotation}deg) saturate({saturation}%) brightness({brightness}%);
            }}
            .frameborder {{
                border: 40px solid transparent;
                padding: 0px;
                border-image: url(/assets/frames/{frame_pack}/border_frame.png);
                border-image-slice: 49%;
                border-image-outset: 10px;
            }}
            .dicedialog{{
                backdrop-filter: blur(10px);
                max-width: none;
                max-height: none;
            }}
            .debug{{
                outline-style: dotted;
            }}
            .customtab{{
                padding-right: 0px;
                padding-left: 0px;
                color: green;
            }}
            .outline-btn .q-btn__content *{{
                color: var(--q-adaptcolor);
            }}
            .glossy::before{{
                content: '';
                z-index: 1;
                width: 100%;
                height: 100%;
                display: block;
                position: absolute;
                background: linear-gradient(rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0.5) 50%, rgba(0, 0, 0, 0) 50%, rgba(0, 0, 0, 0));
            }}
            .adapttooltip{{
                background-color: var(--q-adaptbg);
                border: 1px solid var(--q-adaptcolor);
                color: var(--q-adaptcolor)
            }}
            div {{
                -moz-osx-font-smoothing: grayscale;
                -webkit-font-smoothing: antialiased !important;
                -moz-font-smoothing: antialiased !important;
                text-rendering: optimizelegibility !important;
                letter-spacing: .03em;
            }}
            p {{
                margin-bottom: 10px;
            }}
            ul {{
                list-style-type: disc;
                list-style-position: inside;
                margin-bottom: 10px;
            }}
            ol {{
                list-style-type: decimal;
                list-style-position: inside;
                margin-bottom: 10px;
            }}
            ul ul, ol ul {{
                list-style-type: circle;
                list-style-position: inside;
                margin-left: 15px;
            }}
            ol ol, ul ol {{
                list-style-type: lower-latin;
                list-style-position: inside;
                margin-left: 15px;
            }}
        </style>
    ''')

