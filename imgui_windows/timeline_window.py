from imgui_bundle import imgui
from imgui_bundle.immapp import static
from imgui_bundle import immvision
import os
from imgui_bundle import implot
import cv2
import numpy as np
import imgui_windows.download_window as download_window

import threading
import imgui_windows.ocr_utils as ocr_utils
import csv
import importlib

costBox = [1254,941,int(468),int(25)]

totalTime = 198

videoFile : cv2.VideoCapture | None = None

videoProgress = 0

def LoadVideo():
    global videoProgress
    videoProgress = 0
    Cost_Frame = []
    global videoFile
    global totalTime
    videoFile.set(cv2.CAP_PROP_POS_MSEC, 0)

    Cost_Frame = []
    frame_count = int(60 * totalTime)
    last_cost = 0.0
    frame_id = 0
    
    while frame_id < frame_count:
            
        videoProgress = (frame_id / frame_count) * 100
        success, frame = videoFile.read()
        if not success:
            frame_id+=10
            continue
        
        x,y,w,h = costBox
        choppedImage = frame[y:y+h, x:x+w]

        
        framediff = np.linalg.norm(choppedImage - [243,222,68],axis=2) / 1.8
    
        bluediff = np.abs(choppedImage[:,:,0] - 243)

        min = np.min([framediff, bluediff],axis= 0)
        cost = ocr_utils.calculateCost(min)
        
        if last_cost > cost + .7 :
            last_cost = cost
            Cost_Frame.append([last_cost,frame_id])
            frame_id += 1
            continue
            
        frame_id += 1

        continue
        
        
    with open('out.csv', 'w', newline='') as csvfile:
        spamwriter = csv.writer(csvfile)
        for row in Cost_Frame:
            spamwriter.writerow(row)
    return Cost_Frame

def gui():
    global costBox
    global totalTime
    global videoProgress
    global videoFile

    if not hasattr(static, 'currentFrameID') or static.currentFrameID == -1:
        static.currentFrameID = -1
        static.sliderID = 0
        static.sliderChanged = False
        with open('out.csv', 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            static.x = []
            static.y = []
            for row in reader:
                
                static.x.append(float(row[0]))
                static.y.append(float(row[1]))
    windowWidth = imgui.get_content_region_avail().x

    if videoFile is None:
            
        videoFile = cv2.VideoCapture(download_window.selectedProject + "\\video.mp4")
        

        static.frameCount = totalTime * 60
        success, frame = videoFile.read()
        static.frameWidth = frame.shape[1]
        static.frameHeight = frame.shape[0]

    if not static.sliderChanged and static.currentFrameID != static.sliderID:
        
        static.currentFrameID = static.sliderID
        time = 1000 / 60 * static.currentFrameID
        success = videoFile.set(cv2.CAP_PROP_POS_MSEC, time)

        success, static.rawFrameImg = videoFile.read()

        static.frameImg = np.copy(static.rawFrameImg[costBox[1] :costBox[1] + costBox[3], costBox[0] :costBox[0] + costBox[2],  :])

        #243 222 68
    
    #np.maximum(static.frameImg[:,:,2], static.frameImg[:,:,1])
    immvision.image_display("framer", static.frameImg,(costBox[2], costBox[3]), refresh_image = True)
    imgui.same_line()
    framediff = np.linalg.norm(static.frameImg - [243,222,68],axis=2) / 1.8
    
    immvision.image_display("frameg", np.asarray(framediff).astype('uint8'), refresh_image = True)
    imgui.same_line()
    
    immvision.image_display("frameb", np.ascontiguousarray (static.frameImg[:,:,0]),(costBox[2], costBox[3]), refresh_image = True)
    imgui.same_line()
    imgui.push_item_width(200)
    imgui.spacing()

    bluediff = np.abs(static.frameImg[:,:,0] - 243)
    small = cv2.resize(static.frameImg[:,:,0], (10,1))

    #np.maximum(static.frameImg[:,:,2], static.frameImg[:,:,1]))
    immvision.image_display("framer1",np.min([framediff, bluediff],axis= 0),(costBox[2], costBox[3]), refresh_image = True)
    imgui.same_line()
    
    immvision.image_display("frameg1", np.ascontiguousarray (bluediff),(costBox[2], costBox[3]), refresh_image = True)
    imgui.same_line()
    
    immvision.image_display("frameb1", np.ascontiguousarray ((np.floor(static.frameImg[:,:,0] / 20) * 20 > (256 /2)).astype('uint8') * 255),(costBox[2], costBox[3]), refresh_image = True)
    imgui.same_line()
    imgui.push_item_width(200)
    imgui.spacing()

    min = np.min([framediff, bluediff],axis= 0)
    #np.maximum(static.frameImg[:,:,2], static.frameImg[:,:,1]))
    immvision.image_display("framer2",min,(costBox[2], costBox[3]), refresh_image = True)
    imgui.same_line()
    
    immvision.image_display("frameg2", cv2.resize(min,(200,20)),(costBox[2], costBox[3]), refresh_image = True)
    imgui.same_line()
    
    immvision.image_display("frameb2", np.ascontiguousarray ((np.floor(static.frameImg[:,:,0] / 20) * 20 > (256 /2)).astype('uint8') * 255),(costBox[2], costBox[3]), refresh_image = True)
    imgui.same_line()
    imgui.push_item_width(200)
    imgui.spacing()


    imgui.begin_horizontal("TimeControl")
    static.sliderChanged = False

    imgui.push_item_width(100)
    if imgui.button("<##Time"):
        static.sliderChanged = True
        static.sliderID -= 1

    imgui.push_item_width(windowWidth - 200)

    changed, static.sliderID = imgui.slider_int("Time",static.sliderID, 0 , static.frameCount)
    static.sliderChanged |= changed 

    imgui.push_item_width(100)

    if imgui.button(">##Time"):
        static.sliderChanged = True
        static.sliderID += 1

    imgui.end_horizontal()

    if imgui.button("キャプチャー"):
        if not hasattr(static, 'loadVideoThread'):
            static.loadVideoThread = threading.Thread(target=LoadVideo, args= ())
            static.loadVideoThread.start()
        elif not static.loadVideoThread.is_alive() and videoProgress <= 0:
                
            static.loadVideoThread.start()

    if videoProgress > 0 and not static.loadVideoThread.is_alive():
        with open('out.csv', 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            static.x = []
            static.y = []
            for row in reader:
                static.x.append(float(row[0]))
                static.y.append(float(row[1]))
        videoProgress = 0

    imgui.same_line()
    imgui.text(str(videoProgress))
        
    if hasattr(static, 'x'):
        if implot.begin_plot("##cost plot"):
            implot.setup_axes("frame", "cost", implot.AxisFlags_.range_fit,implot.AxisFlags_.lock_min | implot.AxisFlags_.lock_max)
            implot.setup_axis_limits(implot.ImAxis_.y1, 0,10)
            implot.plot_inf_lines("frame",np.asarray([static.currentFrameID]))
            implot.plot_line("cost",np.asarray(static.y),np.asarray(static.x))
            implot.end_plot()
    imgui.text("Cost :" + str( ocr_utils.calculateCost(min)))
    if imgui.button("reload lib"):
        importlib.reload(ocr_utils)
    return 2
