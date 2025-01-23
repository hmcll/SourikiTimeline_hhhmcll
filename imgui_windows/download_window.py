from imgui_bundle import imgui

import os


def gui():
    savePath = os.path.normpath(os.path.dirname(__file__) + "/../Projects")
    imgui.text("Workspace: " + savePath)
    
    if imgui.button("Print"):
        print("pressed")
    

#https://youtu.be/idZov-CjcHA