from imgui_bundle import imgui
from imgui_bundle.immapp import static
from imgui_bundle import immvision
import os
import json
import cv2
import numpy as np
import requests

from io import StringIO
import sys
import threading


from media_utils import ydl_download, get_video_info

selectedProject = ""

def CreateNewProject(link : str, ProjectFolderLink : str):
    try:
        title,  jsonRet = get_video_info(link)
        title = title.replace('\\','-')
        title = title.replace('/','-')
    except:
        print("リンク無効")
        return
    if title is not None:
        
        ydl_download(link, ProjectFolderLink + "\\" + title + "\\video.mp4")
        setting = {}
        setting["title"] = jsonRet["title"]
        setting["link"] = link
        
        videoFile = cv2.VideoCapture(ProjectFolderLink + "\\" + title + "\\video.mp4")
        
        success, Image = videoFile.read()
        setting["FrameWidth"] = Image.shape[1]
        setting["FrameHeight"] = Image.shape[0]
        setting["FramePerSecond"] = videoFile.get(cv2.CAP_PROP_FPS)
        setting["FrameCount"] =  int(videoFile.get(cv2.CAP_PROP_FRAME_COUNT))
        
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
        
    print("ダウンロード完了")
            
            
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


class QueueIO(StringIO):
    def __init__(self, q):
        super().__init__()
        self.q = q

    def write(self, data):
        super().write(data)
        self.q.put(data)

def gui():
    ret = -1
    savePath = os.path.normpath(os.path.dirname(__file__) + "\\..\\Projects")
    imgui.text("ワークスペース: " + savePath)
    if not os.path.exists(savePath):
        os.mkdir(savePath)
    
    if not hasattr(static, 'projectID'):
        static.projectID = 0
        selectedNewProject = True
        static.newStdout = StringIO()
        
        

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
            static.previewImg = cv2.imdecode(np.fromstring(file.read(), np.uint8),1)
    if hasattr(static, 'previewImg'):
        immvision.image_display("##preview", static.previewImg,(320,180),selectedNewProject)
    imgui.end_horizontal()
    
    if not hasattr(static, 'downloadVideoThread') or not static.downloadVideoThread.is_alive():
        if imgui.button("このプロジェクトで続く"):
            global selectedProject 
            selectedProject = paths[static.projectID]
            ret = 1

    imgui.separator_text("ダウンロード")
    if not hasattr(static, 'videoLinkToDownload'):
        static.videoLinkToDownload = ""
    
    _, static.videoLinkToDownload = imgui.input_text_with_hint("リンク","YouTubeリンクをここに", static.videoLinkToDownload)


    if not hasattr(static, 'downloadVideoThread') or not static.downloadVideoThread.is_alive():
        if sys.stdout != sys.__stdout__:
            sys.stdout = sys.__stdout__
            
        if imgui.button("ダウンロード##Button"):
            
            static.newStdout = sys.stdout = StringIO()
            static.downloadVideoThread = threading.Thread(target=CreateNewProject, args= [static.videoLinkToDownload,savePath])
            static.downloadVideoThread.start()
            
    imgui.input_text_multiline("##stdout",static.newStdout.getvalue(),flags=imgui.InputTextFlags_.read_only,size=[-1,-1])

    return ret
    

