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
import decord

from scripts.debug_timer import DebugTimer

class videoStatus:
    videoFile : cv2.VideoCapture 
    frameCount : int
    frameWidth : int
    frameHeight : int

videoFile : decord.VideoReader | None = None


def gui():
    
    global videoFile
     
    if not hasattr(static, 'currentFrameID') or static.currentFrameID == -1:
        static.currentFrameID = -1
        static.sliderID = 0
        static.sliderChanged = False
    
    if videoFile is None:
        videoFile = decord.VideoReader(download_window.selectedProject + "\\video.mp4")

        static.frameCount = len(videoFile)
        
        static.frameWidth = 1280
        static.frameHeight = 720
        
        
    if not static.sliderChanged and static.currentFrameID != static.sliderID:
        timer = DebugTimer()
        timer.start()
        static.currentFrameID = static.sliderID
        
        static.frameImg = videoFile[static.currentFrameID].asnumpy()
        timer.print("loaded")
        
        immvision.image_display("frame", static.frameImg,(static.frameWidth , static.frameHeight),refresh_image = True)
        timer.print("end")
    else:
        immvision.image_display("frame", static.frameImg,(static.frameWidth , static.frameHeight),refresh_image = True)

    static.sliderChanged, static.sliderID = imgui.slider_int("Time",static.sliderID, 0 , static.frameCount)
    
            
    
    return -1