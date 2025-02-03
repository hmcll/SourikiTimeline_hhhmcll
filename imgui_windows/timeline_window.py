from imgui_bundle import imgui
from imgui_bundle.immapp import static
from imgui_bundle import immvision
import os
from imgui_bundle import implot
import cv2
import numpy as np
import imgui_windows.download_window as download_window

import threading
import csv

costBox = [1254,941,int(468),int(25)]

totalTime = 198

videoFile : cv2.VideoCapture | None = None


def LoadVideo():
    Cost_Frame = []
    global videoFile
    global totalTime
    videoFile.set(cv2.CAP_PROP_POS_MSEC, 0)

    Cost_Frame = []
    frame_count = int(60 * totalTime)
    last_cost = 0.0
    frame_id = 0
    last_time = 9999999999999
    while frame_id < frame_count:
        if(frame_id %50) == 0:
            print(frame_id)
        success, frame = videoFile.read()
        if not success:
            frame_id+=10
            continue
        
        x,y,w,h = costBox
        choppedImage = frame[y:y+h, x:x+w,2]
        choppedImage = cv2.resize(choppedImage,(200,20))
        
        
        processedImg = np.floor(choppedImage /20).astype('uint8')*20
        

        sum = np.average(np.unique(processedImg[:,:]))

        colsum = np.sum((choppedImage > sum),axis = 0)
        
        processedImg = ((choppedImage > sum)*255).astype('uint8')
        endID = 20
        for blockID in range(20):
            BlockSum = 0
            for lineID in range(10):
                if colsum[lineID + blockID * 10] > 18:
                    BlockSum += 1
            if BlockSum == 0:
                endID = (blockID + 1)*10
                break
        cost = 0
        for lineID in range(endID-1,0,-1):
            if colsum[lineID] > 17:
                cost = lineID / 200
                break
        cost = np.round(cost * 10, 1)
        if cost != last_cost:
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
        
        
    #np.maximum(static.frameImg[:,:,2], static.frameImg[:,:,1])
    immvision.image_display("framer", np.ascontiguousarray (static.frameImg[:,:,2]),(costBox[2], costBox[3]), refresh_image = True)
    imgui.same_line()
    
    immvision.image_display("frameg", np.ascontiguousarray (static.frameImg[:,:,1]),(costBox[2], costBox[3]), refresh_image = True)
    imgui.same_line()
    
    immvision.image_display("frameb", np.ascontiguousarray (static.frameImg[:,:,0]),(costBox[2], costBox[3]), refresh_image = True)
    imgui.same_line()
    imgui.push_item_width(200)
    imgui.spacing()

    small = cv2.resize(static.frameImg[:,:,0], (10,1))

    #np.maximum(static.frameImg[:,:,2], static.frameImg[:,:,1]))
    immvision.image_display("framer1",small,(costBox[2], costBox[3]), refresh_image = True)
    imgui.same_line()
    
    immvision.image_display("frameg1", np.ascontiguousarray (static.frameImg[:,:,2] - static.frameImg[:,:,0]),(costBox[2], costBox[3]), refresh_image = True)
    imgui.same_line()
    
    immvision.image_display("frameb1", np.ascontiguousarray (static.frameImg[:,:,0]),(costBox[2], costBox[3]), refresh_image = True)
    imgui.same_line()
    imgui.push_item_width(200)
    imgui.spacing()

    imgui.push_item_width(windowWidth)
    static.sliderChanged, static.sliderID = imgui.slider_int("Time",static.sliderID, 0 , static.frameCount)
    
    if imgui.button("キャプチャー"):
        LoadVideo()
        
        
    if hasattr(static, 'x'):
        if implot.begin_plot("##cost plot"):
            implot.plot_inf_lines("frame",np.asarray([static.currentFrameID]))
            implot.plot_line("cost",np.asarray(static.y),np.asarray(static.x))
            implot.end_plot()
    return 2
