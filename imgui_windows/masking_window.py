from imgui_bundle import imgui
from imgui_bundle.immapp import static
from imgui_bundle import immvision
import os
import json
import cv2
import numpy as np
import imgui_windows.download_window as download_window
import launch 
import threading
import time

from scripts.debug_timer import DebugTimer

class videoStatus:
    videoFile : cv2.VideoCapture 
    frameCount : int
    frameWidth : int
    frameHeight : int

videoFile : cv2.VideoCapture | None = None

def renderThread(fps : int):
    waitTime = 1.0/fps
    while launch.currentWindowID == 1:
        pass

def gui():
    
    global videoFile
     
    if not hasattr(static, 'currentFrameID') or static.currentFrameID == -1:
        static.currentFrameID = -1
        static.sliderID = 0
    
    if videoFile is None:
        videoFile = cv2.VideoCapture(download_window.selectedProject + "\\video.mp4")
        static.frameCount = int(videoFile.get(cv2.CAP_PROP_FRAME_COUNT))
        
        #frameWidth = int(videoFile.get(cv2.CAP_PROP_FRAME_WIDTH))
        #frameHeight = int(videoFile.get(cv2.CAP_PROP_FRAME_HEIGHT))
        static.frameWidth = 1280
        static.frameHeight = 720
        
        
    static.sliderChanged, static.sliderID = imgui.slider_int("Time",static.sliderID, 0 , static.frameCount)
    if not static.sliderChanged and static.currentFrameID != static.sliderID:
        timer = DebugTimer()
        timer.start()
        static.currentFrameID = static.sliderID
        videoFile.set(cv2.CAP_PROP_POS_FRAMES, static.currentFrameID)
        success, static.frameImg = videoFile.read()
        timer.print("loaded")
        if success:
            immvision.image_display("frame", static.frameImg,(static.frameWidth , static.frameHeight),refresh_image = True)
            timer.print("end")
    else:
        immvision.image_display("frame", static.frameImg,(static.frameWidth , static.frameHeight),refresh_image = True)

            
    
    return -1