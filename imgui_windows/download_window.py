from imgui_bundle import imgui
from imgui_bundle.immapp import static
import os
from scripts.media_utils import ydl_download, get_video_info

def CreateNewProject(link : str, ProjectFolderLink : str):
    title,  thumbnail_url = get_video_info(link)
    if title != "":
        ydl_download(link, ProjectFolderLink + "\\" + title + "\\video.mp4")


def gui():
    savePath = os.path.normpath(os.path.dirname(__file__) + "\\..\\Projects")
    imgui.text("Workspace: " + savePath)
    if not os.path.exists(savePath):
        os.mkdir(savePath)
    for name in os.walk(savePath).__next__()[1]:
        videoFile = False
        settingFile = False

        for file in os.walk(savePath + "\\" + name).__next__()[2]:
            if not videoFile:
                if file == "video.mp4":
                    videoFile = True
            if not settingFile:
                if file == "setting.ini":
                    settingFile = True
        if videoFile and settingFile:
            imgui.text(savePath + "\\" + name)
            continue
        

        

    if not hasattr(static, 'videoLinkToDownload'):
        static.videoLinkToDownload = "https://www.youtube.com/watch?v=idZov-CjcHA"#"Set Link Here"
    changed, static.videoLinkToDownload = imgui.input_text("Video Link", static.videoLinkToDownload)

    if imgui.button("Print"):

        CreateNewProject(static.videoLinkToDownload, savePath)
    

#https://www.youtube.com/watch?v=idZov-CjcHA