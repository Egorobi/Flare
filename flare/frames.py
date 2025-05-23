from nicegui import ui
import session

def show_frame(frame_type):
    frame_pack = session.saver.get_frame_style()
    if frame_type == "initiative":
        ui.image(f"data/assets/frames/{frame_pack}/frame_initiative.png").classes("absolute-center frame").style("z-index:-1;")
    elif frame_type == "inspiration_initiative":
        ui.image(f"data/assets/frames/{frame_pack}/inspiration_initiative_frame.png").classes("absolute-center frame").style("width: 7.3rem; height: 7.3rem; z-index:-1;")
    elif frame_type == "ability score" or frame_type == "proficiency bonus":
        ui.image(f"data/assets/frames/{frame_pack}/ability_score_frame.png").classes("absolute-center frame").style("width: 7rem; height: 7rem; z-index:-1;")
    elif frame_type == "movement":
        ui.image(f"data/assets/frames/{frame_pack}/movement_frame.png").classes("absolute-center frame").style("width: 9rem; height: 9rem; z-index:-1;")
    elif frame_type == "ac":
        ui.image(f"data/assets/frames/{frame_pack}/ac_frame.png").classes("absolute-center frame").style("width: 7rem; height: 7rem z-index:-1;;")
    elif frame_type == "saves":
        ui.image(f"data/assets/frames/{frame_pack}/saves_frame.png").classes("absolute-center frame").style("width: 15.2rem; height: 15.2rem; z-index:-1;")
    elif frame_type == "skills":
        ui.image(f"data/assets/frames/{frame_pack}/skills_frame.png").classes("absolute-center frame").style("width: 46rem; height: 46rem; z-index:-1;")
    elif frame_type == "tabs":
        ui.image(f"data/assets/frames/{frame_pack}/tabs_frame.png").classes("absolute-center frame").style("width: 42rem; height: 42rem; z-index:-1;")
    elif frame_type == "hp":
        ui.image(f"data/assets/frames/{frame_pack}/hp_frame.png").classes("absolute-center frame").style("width: 23rem; height: 23rem; z-index:-1;")
    elif frame_type == "conditions":
        ui.image(f"data/assets/frames/{frame_pack}/conditions_frame.png").classes("absolute-center frame").style("width: 18rem; height: 18rem; z-index:-1;")
    elif frame_type == "senses":
        ui.image(f"data/assets/frames/{frame_pack}/senses_frame.png").classes("absolute-center frame").style("width: 16rem; height: 16rem; z-index:-1;")
    elif frame_type == "select":
        ui.image(f"data/assets/frames/{frame_pack}/select_frame.png").classes("absolute-center frame").style("width: 27rem; height: 27rem; z-index:-1;")
