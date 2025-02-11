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
from decord import cpu
import scripts.ocr_utils as ocr

from scripts.debug_timer import DebugTimer

class videoStatus:
    videoFile : cv2.VideoCapture 
    frameCount : int
    frameWidth : int
    frameHeight : int

videoFile : decord.VideoReader | None = None

def drawRectangles(staticVariables):
    staticVariables.frameImg = np.copy(staticVariables.rawFrameImg)
    cv2.rectangle(staticVariables.frameImg, (static.config['timeBoxx'], static.config['timeBoxy']),(static.config['timeBoxx'] + static.config['timeBoxw'], static.config['timeBoxy'] + static.config['timeBoxh']),(255,0,0),2)
    cv2.rectangle(staticVariables.frameImg, (static.config['skillBoxx'], static.config['skillBoxy']),(static.config['skillBoxx'] + static.config['skillBoxw'], static.config['skillBoxy'] + static.config['skillBoxh']),(0,255,0),2)
    cv2.rectangle(staticVariables.frameImg, (static.config['costBoxx'], static.config['costBoxy']),(static.config['costBoxx'] + static.config['costBoxw'], static.config['costBoxy'] + static.config['costBoxh']),(0,255,0),2)

def sliderInt4(tag, itemWidth, itemValues, frameValues):
    imgui.push_item_width(100)
    imgui.text(tag)
    imgui.same_line()
    imgui.push_item_width(itemWidth)
    changeda, itemValues[0] = imgui.slider_int("x##" + tag, itemValues[0], 0, frameValues[0] - itemValues[1]  , flags = imgui.SliderFlags_.always_clamp)
    imgui.same_line()
    imgui.push_item_width(itemWidth)
    changedb, itemValues[1] = imgui.slider_int("w##" + tag, itemValues[1], 0, frameValues[0] - itemValues[0]  , flags = imgui.SliderFlags_.always_clamp)
    imgui.same_line()
    imgui.push_item_width(itemWidth)
    changedc, itemValues[2] = imgui.slider_int("y##" + tag, itemValues[2], 0, frameValues[1] - itemValues[3] , flags = imgui.SliderFlags_.always_clamp)
    imgui.same_line()
    imgui.push_item_width(itemWidth)
    changedd, itemValues[3] = imgui.slider_int("h##" + tag, itemValues[3], 0, frameValues[1] - itemValues[2] , flags = imgui.SliderFlags_.always_clamp)
    
    return changeda or changedb or changedc or changedd, itemValues

def getCost(choppedImage, totalCost):
    vertSize = 20
    epsilon = 2
    choppedImage = cv2.resize(choppedImage,(totalCost * 10,vertSize))
    processedImg = np.floor(choppedImage /(totalCost * 2)).astype('uint8')*(totalCost*2)
    
    sum = np.average(np.unique(processedImg[:,:]))

    colsum = np.sum((choppedImage > sum),axis = 0)
    
    processedImg = ((choppedImage > sum)*255).astype('uint8')
    endID = (totalCost * 2)
    for blockID in range((totalCost * 2)):
        BlockSum = 0
        for lineID in range(totalCost):
            if colsum[lineID + blockID * totalCost] > vertSize - epsilon:
                BlockSum += 1
        if BlockSum == 0:
            endID = (blockID + 1)*totalCost
            break
    cost = 0
    for lineID in range(endID-1,0,-1):
        if colsum[lineID] > vertSize - epsilon:
            cost = lineID / (totalCost * 10)
            break
    cost = np.round(cost * totalCost, 1)
    return cost

def runOCR(config, frame):

    choppedImage = frame[config['costBoxy']:config['costBoxy']+config['costBoxh'], config['costBoxx']:config['costBoxx']+config['costBoxw'],2]
    return getCost(choppedImage, 10)

def gui():
    
    global videoFile
     
    if not hasattr(static, 'currentFrameID') or static.currentFrameID == -1:
        static.currentFrameID = -1
        static.sliderID = 0
        static.sliderChanged = False
    
    if videoFile is None:
        videoFile = decord.VideoReader(download_window.selectedProject + "\\video.mp4", ctx=cpu(0), num_threads=1)
        
        static.frameCount = len(videoFile)
        
        with open(download_window.selectedProject + "\\setting.json", "r",encoding="utf-8") as file:
            static.config = json.load(file)
        
        
        
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

    changeda, [static.config['timeBoxx'],static.config['timeBoxw'],static.config['timeBoxy'],static.config['timeBoxh']] = sliderInt4("時間", itemWidth, 
             [static.config['timeBoxx'],static.config['timeBoxw'],static.config['timeBoxy'],static.config['timeBoxh']],
            [static.config['movie_width'], static.config['movie_height']])
    
    changedb, [static.config['skillBoxx'],static.config['skillBoxw'],static.config['skillBoxy'],static.config['skillBoxh']] = sliderInt4("スキル", itemWidth, 
            [static.config['skillBoxx'],static.config['skillBoxw'],static.config['skillBoxy'],static.config['skillBoxh']],
            [static.config['movie_width'], static.config['movie_height']])
    
    changedc, [static.config['costBoxx'],static.config['costBoxw'],static.config['costBoxy'],static.config['costBoxh']] = sliderInt4("コスト", itemWidth, 
             [static.config['costBoxx'],static.config['costBoxw'],static.config['costBoxy'],static.config['costBoxh']],
            [static.config['movie_width'], static.config['movie_height']])
    
    if changeda or changedb or changedc:
        drawRectangles(static)
    if imgui.button("セーブ"):
        
        with open(download_window.selectedProject + "\\setting.json", "w",encoding="utf-8") as file:
            json.dump(static.config,file, ensure_ascii=False, indent=4)
            
            
    if imgui.button("識別"):
        static.cost = runOCR(static.config, static.rawFrameImg)
            
    

    return -1