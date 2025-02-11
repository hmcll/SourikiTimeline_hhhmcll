from imgui_bundle import imgui
from imgui_bundle.immapp import static
from imgui_bundle import immvision
import os
import json
import cv2
import numpy as np
import requests
import decord

from scripts.media_utils import ydl_download, get_video_info

selectedProject = ""

def CreateNewProject(link : str, ProjectFolderLink : str):
    title,  jsonRet = get_video_info(link)
    if title is not None:
        ydl_download(link, ProjectFolderLink + "\\" + title + "\\video.mp4")
        firstFrame = decord.VideoReader(ProjectFolderLink + "\\" + title + "\\video.mp4", ctx=decord.cpu(0), num_threads=1)[0]
        setting = {}
        setting["title"] = jsonRet["title"]
        setting["link"] = link

        setting["movie_width"] = firstFrame.shape[1]
        setting["movie_height"] = firstFrame.shape[0]
        setting["movie_frame_rate"] = jsonRet["fps"]
        setting["movie_start_time"] = 0
        setting["movie_end_time"] = float(jsonRet["duration"])
        setting["movie_preview_time"] = 0

        setting['timeBoxx'] = 10
        setting['timeBoxy'] = 10
        setting['timeBoxw'] = 50
        setting['timeBoxh'] = 50

        setting['skillBoxx'] = 10
        setting['skillBoxy'] = 10
        setting['skillBoxw'] = 50
        setting['skillBoxh'] = 50

        setting['costBoxx'] = 10
        setting['costBoxy'] = 10
        setting['costBoxw'] = 50
        setting['costBoxh'] = 50
        setting['skillOffset'] = 500

        response = requests.get(jsonRet["thumbnail"])
        with open(ProjectFolderLink + "\\" + title + "\\thumbnail.jpg", "wb") as file:
            file.write(response.content)
            
        with open(ProjectFolderLink + "\\" + title + "\\setting.json", "w",encoding="utf-8") as file:
            json.dump(setting,file, ensure_ascii=False, indent=4)
            
        print(jsonRet)
def GetAllProjects(savePath: str) -> list:
    paths = []
    for name in os.walk(savePath).__next__()[1]:
        videoFile = False
        settingFile = False

        for file in os.walk(savePath + "\\" + name).__next__()[2]:
            if not videoFile:
                if file == "video.mp4":
                    videoFile = True
            if not settingFile:
                if file == "setting.json":
                    settingFile = True
        if videoFile and settingFile:
            paths.append(savePath + "\\" + name)
            continue
    return paths

def gui():
    ret = -1
    savePath = os.path.normpath(os.path.dirname(__file__) + "\\..\\Projects")
    imgui.text("ワークスペース: " + savePath)
    if not os.path.exists(savePath):
        os.mkdir(savePath)
    
    if not hasattr(static, 'projectID'):
        static.projectID = 0
        selectedNewProject = True
    paths = GetAllProjects(savePath)
    selectedNewProject = False
    imgui.begin_horizontal("プロジェクト")
    if imgui.begin_list_box("##プロジェクトリスト"):
        for n, item in enumerate(paths):
            isSelected = static.projectID == n
            if imgui.selectable(item, isSelected)[1]:
                static.projectID = n
                selectedNewProject = True
        imgui.end_list_box()
        
    if selectedNewProject:
        with open(paths[static.projectID] + "\\thumbnail.jpg", "rb") as file:
            static.previewImg = cv2.cvtColor(cv2.imdecode(np.fromstring(file.read(), np.uint8),1),cv2.COLOR_BGR2RGB)
    if hasattr(static, 'previewImg'):
        immvision.image_display("##preview", static.previewImg,(320,180),selectedNewProject)
    imgui.end_horizontal()
    if imgui.button("このプロジェクトで続く"):
        global selectedProject 
        selectedProject = paths[static.projectID]
        ret = 2

    if not hasattr(static, 'videoLinkToDownload'):
        static.videoLinkToDownload = "https://www.youtube.com/watch?v=cQV0FF0zPH4"#"Set Link Here"
    _, static.videoLinkToDownload = imgui.input_text("##YouTubeリンクをここに", static.videoLinkToDownload)

    if imgui.button("ダウンロード"):

        CreateNewProject(static.videoLinkToDownload, savePath)

    return ret
    

#https://www.youtube.com/watch?v=idZov-CjcHA