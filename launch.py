

from types import ModuleType
from typing import List, Callable
from imgui_bundle import imgui, hello_imgui, immapp
from imgui_bundle.immapp import static
import imgui_windows.download_window as download_window



def make_params() -> tuple[hello_imgui.RunnerParams, immapp.AddOnsParams]:
    
    
    runner_params = hello_imgui.RunnerParams()
    
    runner_params.app_window_params.window_title = (
        "Timeline Generation"
    )
    runner_params.app_window_params.window_geometry.size = (1400, 950)
    
    runner_params.imgui_window_params.show_menu_bar = False
    runner_params.imgui_window_params.show_status_bar = False
    
    
    runner_params.imgui_window_params.default_imgui_window_type = (
        hello_imgui.DefaultImGuiWindowType.provide_full_screen_dock_space
    )
    
    runner_params.imgui_window_params.enable_viewports = False


    dockable_windows: List[hello_imgui.DockableWindow] = []

    def add_dockable_window(label: str, gui_func):
        window = hello_imgui.DockableWindow()
        window.label = label
        window.dock_space_name = "MainDockSpace"
        
        def win_fn() -> None:
            
            if imgui.get_frame_count() < 2:  # cf https://github.com/pthom/imgui_bundle/issues/293
                return
            gui_func()

        window.gui_function = win_fn
        dockable_windows.append(window)

    windows = [
        ["Download", download_window.gui]
    ]

    for window in windows:
        add_dockable_window(window[0],window[1])

    runner_params.docking_params.dockable_windows = dockable_windows

    # the main gui is only responsible to give focus to ImGui Bundle dockable window
    @static(nb_frames=0)
    def show_gui():
        if show_gui.nb_frames == 1:
            # Focus cannot be given at frame 0, since some additional windows will
            # be created after (and will steal the focus)
            runner_params.docking_params.focus_dockable_window("Download")
        show_gui.nb_frames += 1

    runner_params.callbacks.show_gui = show_gui
    
    ################################################################################################
    # Part 3: Run the app
    ################################################################################################
    addons = immapp.AddOnsParams()
    addons.with_markdown = True
    addons.with_implot = True
    addons.with_implot3d = True
    addons.with_tex_inspect = True

    return runner_params, addons


def main():
    runner_params, addons = make_params()
    immapp.run(runner_params=runner_params, add_ons_params=addons)


if __name__ == "__main__":
    main()