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

def drawRectangles(staticVariables):
    staticVariables.frameImg = np.copy(staticVariables.rawFrameImg)
    cv2.rectangle(staticVariables.frameImg, (static.timeBoxx, static.timeBoxy),(static.timeBoxx + static.timeBoxw, static.timeBoxy + static.timeBoxh),(255,0,0),2)


def gui():
    
    global videoFile
     
    if not hasattr(static, 'currentFrameID') or static.currentFrameID == -1:
        static.currentFrameID = -1
        static.sliderID = 0
        static.sliderChanged = False
    
    if videoFile is None:
        videoFile = decord.VideoReader(download_window.selectedProject + "\\video.mp4")

        static.frameCount = len(videoFile)
        frame = videoFile[static.currentFrameID]
        static.frameWidth = frame.shape[1]
        static.frameHeight = frame.shape[0]
        static.timeBoxx = 10
        static.timeBoxy = 10
        static.timeBoxw = 50
        static.timeBoxh = 50
    windowWidth = imgui.get_content_region_avail().x
    videoViewWidth = int(windowWidth / 5 * 3)
    videoHeight = int(videoViewWidth / 16 * 9)
    if not static.sliderChanged and static.currentFrameID != static.sliderID:
        timer = DebugTimer()
        timer.start()
        static.currentFrameID = static.sliderID
        
        static.rawFrameImg = videoFile[static.currentFrameID].asnumpy()
        timer.print("loaded")
        drawRectangles(static)
        immvision.image_display("frame", static.frameImg,(videoViewWidth, videoHeight), refresh_image = True)
        timer.print("end")
    else:
        immvision.image_display("frame", static.frameImg,(videoViewWidth, videoHeight), refresh_image = True)

    imgui.push_item_width(windowWidth)
    static.sliderChanged, static.sliderID = imgui.slider_int("Time",static.sliderID, 0 , static.frameCount)
    
    itemWidth = (windowWidth - 100 ) / 4
    imgui.push_item_width(100)
    imgui.text("時間")
    imgui.same_line()
    imgui.push_item_width(itemWidth)
    changeda, static.timeBoxx = imgui.slider_int("x##time", static.timeBoxx, 0, static.frameWidth - static.timeBoxw  , flags = imgui.SliderFlags_.always_clamp)
    imgui.same_line()
    imgui.push_item_width(itemWidth)
    changedb, static.timeBoxw = imgui.slider_int("w##time", static.timeBoxw, 0, static.frameWidth - static.timeBoxx  , flags = imgui.SliderFlags_.always_clamp)
    imgui.same_line()
    imgui.push_item_width(itemWidth)
    changedc, static.timeBoxy = imgui.slider_int("y##time", static.timeBoxy, 0, static.frameHeight - static.timeBoxh , flags = imgui.SliderFlags_.always_clamp)
    imgui.same_line()
    imgui.push_item_width(itemWidth)
    changedd, static.timeBoxh = imgui.slider_int("h##time", static.timeBoxh, 0, static.frameHeight - static.timeBoxy , flags = imgui.SliderFlags_.always_clamp)
    
    

    if changeda or changedb or changedc or changedd:
        drawRectangles(static)


    return -1