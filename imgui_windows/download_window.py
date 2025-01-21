from imgui_bundle import imgui
from imgui_bundle.immapp import static



def gui():
    
    if imgui.button("Print"):
        print("pressed")