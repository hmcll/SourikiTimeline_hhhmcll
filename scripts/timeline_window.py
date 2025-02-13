from imgui_bundle import imgui
from imgui_bundle.immapp import static
from imgui_bundle import immvision
import os
from imgui_bundle import implot
import cv2
import numpy as np
import download_window

import threading
import ocr_utils
import csv
import json
from chara_skill import CharaSkill
from paddleocr import PaddleOCR

skillOCR = PaddleOCR(use_angle_cls=False, lang='japan', show_log=False)
timeOCR = PaddleOCR(use_angle_cls=False, lang='en', show_log=False)

videoFile : cv2.VideoCapture | None = None

skills = CharaSkill.from_tsv()

class SkillUse:
    FrameID : int = 0
    FromCost : float = 0
    ToCost : float = 0
    SkillOffset : int = 0
    TimeString : str = ""
    SkillStringRaw : str = ""
    DetectedSkill : str = ""
    Disabled : bool = False
    Meta : str = ""
    
    def ToList(self) ->list:
        return [self.ToCost,self.FromCost,self.FrameID,self.SkillOffset,self.TimeString,self.SkillStringRaw,self.DetectedSkill,self.Disabled,self.Meta]
    
    def ToString(self) ->str:
        return f"スキル：{self.DetectedSkill} \n時間：{self.TimeString} \nスキル判定オフセット:{self.SkillOffset} ms\n{"無効"if self.Disabled else "有効"}\n{self.Meta}"

    def FromList(data : list) -> 'SkillUse':
        ret : 'SkillUse' = SkillUse()
        if len(data) > 0:
            ret.ToCost = int(data[0])
        if len(data) > 1:
            ret.FromCost = float(data[1])
        if len(data) > 2:
            ret.FrameID = float(data[2])
        if len(data) > 3:
            ret.SkillOffset = int(data[3])
        if len(data) > 4:
            ret.TimeString = str(data[4])
        if len(data) > 5:
            ret.SkillStringRaw = str(data[5])
        if len(data) > 6:
            ret.DetectedSkill = str(data[6])
        if len(data) > 7:
            ret.Disabled = data[7] == "True"
        if len(data) > 8:
            ret.Meta = str(data[8])
        return ret

def SaveCostFrame(CostFrame : list['SkillUse']):

    with open(download_window.selectedProject + '\\FullTimeline.csv', 'w', newline='', encoding='utf-8') as csvfile:
        spamwriter = csv.writer(csvfile)
        for row  in CostFrame:
            spamwriter.writerow(row.ToList())

def DetectSkills():
    
    global skills
    x,y,w,h = [static.config['skillBoxx'], static.config['skillBoxy'], static.config['skillBoxw'], static.config['skillBoxh']]
    
    for row in static.Cost_Frame:
        
        time = 1000 / static.config["FramePerSecond"] * row.FrameID
        success = videoFile.set(cv2.CAP_PROP_POS_MSEC, time + row.SkillOffset + static.config['skillOffset'])

        static.frameID = row.FrameID

        success, static.rawFrameImg = videoFile.read()
        
        drawRectangles()
        image = static.rawFrameImg[y:y+h, x:x+w]
        
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        result = skillOCR.ocr(image,cls= False)


        if not result or not result[0]:
            row.Disabled = True
            continue

        row.SkillStringRaw = ""
        for line in result[0]:
            row.SkillStringRaw += str(line[1][0])
            
        row.DetectedSkill, similarity = CharaSkill.find_best_match(skills,row.SkillStringRaw,50)
        if row.DetectedSkill is None:
            row.DetectedSkill = ""
        row.Disabled = row.DetectedSkill == ''

def DetectSkillOnly():
    DetectSkills()
    SaveCostFrame(static.Cost_Frame)

def LoadVideo():
    
    global videoFile
    
    videoFile.set(cv2.CAP_PROP_POS_MSEC, 0)

    static.Cost_Frame = list['SkillUse']()
    last_cost = 0.0
    
    x,y,w,h = [static.config['costBoxx'], static.config['costBoxy'], static.config['costBoxw'], static.config['costBoxh']]
    tx,ty,tw,th = [static.config['timeBoxx'], static.config['timeBoxy'], static.config['timeBoxw'], static.config['timeBoxh']]
    
    while True:
            
        success, static.rawFrameImg = videoFile.read()
        if not success:
            break
        static.frameID = int(videoFile.get(cv2.CAP_PROP_POS_FRAMES))
        
        drawRectangles()
        choppedImage = static.rawFrameImg[y : y + h, x : x + w, :]
        
        cost = ocr_utils.calculateCost(choppedImage)
        
        if last_cost > cost + .7 :
            image = cv2.cvtColor(static.rawFrameImg[ty : ty + th, tx : tx + tw, :], cv2.COLOR_BGR2GRAY)
            result = timeOCR.ocr(image,cls=False)
            
            if result[0] is None:
                continue

            time = ""
            for line in result[0]:
                time+=line[1][0]

            if time == "":
                continue

            static.Cost_Frame.append(SkillUse.FromList([cost, last_cost,static.frameID,0,time]))
            last_cost = cost
            continue
        last_cost = cost
        continue
        
    DetectSkills()
    SaveCostFrame(static.Cost_Frame)
            

def drawRectangles():
    static.rawFrame = np.copy(static.rawFrameImg)
    cv2.rectangle(static.rawFrame, (static.config['timeBoxx'], static.config['timeBoxy']),(static.config['timeBoxx'] + static.config['timeBoxw'], static.config['timeBoxy'] + static.config['timeBoxh']),(0,0,255),2)
    cv2.rectangle(static.rawFrame, (static.config['skillBoxx'], static.config['skillBoxy']),(static.config['skillBoxx'] + static.config['skillBoxw'], static.config['skillBoxy'] + static.config['skillBoxh']),(0,255,0),2)
    cv2.rectangle(static.rawFrame, (static.config['costBoxx'], static.config['costBoxy']),(static.config['costBoxx'] + static.config['costBoxw'], static.config['costBoxy'] + static.config['costBoxh']),(0,255,255),2)

def sliderInt4(tag, itemWidth, itemValues, frameValues):
    imgui.separator_text(tag)
    
    imgui.push_item_width(itemWidth - 30)

    imgui.text("x:")
    imgui.same_line()
    changeda, itemValues[0] = imgui.slider_int("##x" + tag, itemValues[0], 0, frameValues[0] - itemValues[1]  , flags = imgui.SliderFlags_.always_clamp)
    imgui.text("w:")
    imgui.same_line()
    changedb, itemValues[1] = imgui.slider_int("##w" + tag, itemValues[1], 0, frameValues[0] - itemValues[0]  , flags = imgui.SliderFlags_.always_clamp)
    imgui.text("y:")
    imgui.same_line()
    changedc, itemValues[2] = imgui.slider_int("##y" + tag, itemValues[2], 0, frameValues[1] - itemValues[3] , flags = imgui.SliderFlags_.always_clamp)
    
    imgui.text("h:")
    imgui.same_line()
    changedd, itemValues[3] = imgui.slider_int("##h" + tag, itemValues[3], 0, frameValues[1] - itemValues[2] , flags = imgui.SliderFlags_.always_clamp)
    imgui.pop_item_width()


    return changeda or changedb or changedc or changedd, itemValues

def LoadData(projectPath)-> list['SkillUse']:
    ret = []
    if os.path.exists(projectPath + "\\FullTimeline.csv"):
        with open(projectPath + "\\FullTimeline.csv", 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                ret.append(SkillUse.FromList(row))
    return ret

def LoadFrame(FrameID, video):

        time = 1000 / static.config["FramePerSecond"] * FrameID
        success = videoFile.set(cv2.CAP_PROP_POS_MSEC, time)

        success, static.rawFrameImg = video.read()

        static.rawFrame = np.copy(static.rawFrameImg)
        static.frameID = FrameID
        drawRectangles()

def PlotSkill(data : list['SkillUse'], halfWidth = 10):

    draw_list = implot.get_plot_draw_list()


    limit = implot.get_plot_limits()
    

    lb = implot.plot_to_pixels(limit.x.min,limit.y.min)
    ru = implot.plot_to_pixels(limit.x.max,limit.y.max)
    draw_list.push_clip_rect(imgui.ImVec2(lb.x,ru.y),imgui.ImVec2(ru.x,lb.y))

    mousepos = implot.get_plot_mouse_pos()
    mousex = min(static.config['FrameCount'], np.round(mousepos.x))
    if implot.is_plot_hovered():

        top  = implot.plot_to_pixels(mousex - halfWidth, limit.y.max)
        bot = implot.plot_to_pixels(mousex + halfWidth, limit.y.min)
        
        draw_list.add_rect_filled(top, bot, 0X66666666)
        if imgui.is_mouse_released(imgui.MouseButton_.left) and imgui.get_mouse_drag_delta(imgui.MouseButton_.left).x == 0:
            global videoFile
            if not hasattr(static, 'loadVideoThread') or not static.loadVideoThread.is_alive():
                LoadFrame(mousex,videoFile)
    draw_list.add_line(implot.plot_to_pixels(static.frameID, limit.y.max), implot.plot_to_pixels(static.frameID, limit.y.min), 0XFFFFFFFF)
    tooltipShown = False
    
    for row in data:

        SkillUseBoxLB = implot.plot_to_pixels(row.FrameID - halfWidth, row.ToCost)
        SkillUseBoxRH = implot.plot_to_pixels(row.FrameID + halfWidth, row.FromCost)
        offsetToFrame = (row.SkillOffset+static.config['skillOffset'])/ 1000 * static.config['FramePerSecond']
        SkillDiffChecker = implot.plot_to_pixels(int(row.FrameID  +  offsetToFrame), (row.ToCost + row.FromCost) / 2)
        Brightness = 0XAAAAAAAA
        if not tooltipShown:
            if mousex > row.FrameID - halfWidth and mousex < row.FrameID + halfWidth:
                if mousepos.y > row.ToCost and mousepos.y < row.FromCost:
                    imgui.set_tooltip(row.ToString())
                    Brightness  = 0XFFDDDDDD
                    tooltipShown = True
                    if imgui.is_mouse_released(imgui.MouseButton_.middle) and imgui.get_mouse_drag_delta(imgui.MouseButton_.middle).x == 0:
                        row.Disabled = not row.Disabled 
                        SaveCostFrame(static.Cost_Frame)
        if row.Disabled:
            draw_list.add_rect(SkillUseBoxLB, SkillUseBoxRH, Brightness & (0XFF00FF00 if row.DetectedSkill != "" else 0XFF00FFFF))
        else:
            draw_list.add_rect_filled(SkillUseBoxLB, SkillUseBoxRH, Brightness & (0XFF00FF00 if row.DetectedSkill != "" else 0XFF00FFFF))
                
            if SkillUseBoxRH.x > SkillDiffChecker.x:

                draw_list.add_line([SkillDiffChecker.x,SkillDiffChecker.y], [SkillUseBoxRH.x,SkillDiffChecker.y], Brightness & 0XFF00FF00)
            else:
                draw_list.add_line([SkillUseBoxRH.x,SkillDiffChecker.y], [SkillDiffChecker.x,SkillDiffChecker.y], Brightness & 0XFF00FF00)

            draw_list.add_circle_filled(SkillDiffChecker,3.0, Brightness & 0XFF00FF00)

    draw_list.pop_clip_rect()

def gui():
    
    global videoFile
    
    windowWidth = imgui.get_content_region_avail().x

    if videoFile is None:
            
        with open(download_window.selectedProject + "\\setting.json", "r",encoding="utf-8") as file:
            static.config = json.load(file)
        static.Cost_Frame = LoadData(download_window.selectedProject)
        videoFile = cv2.VideoCapture(download_window.selectedProject + "\\video.mp4")
        
        success, static.rawFrameImg = videoFile.read()
        
        static.rawFrame = np.copy(static.rawFrameImg)
        static.costImg = np.copy(static.rawFrameImg[static.config['costBoxy'] : static.config['costBoxy'] + static.config['costBoxh'], static.config['costBoxx']: static.config['costBoxx'] + static.config['costBoxw'],  :])

        static.currentCost = str( ocr_utils.calculateCost(static.costImg))
        static.frameID = 0
        static.dataFrameID = -1
        drawRectangles()



    windowWidth = imgui.get_content_region_avail().x
    videoViewWidth = int(windowWidth / 5 * 3)
    videoHeight = int(videoViewWidth / 16 * 9)
    sideBuffer = (windowWidth-videoViewWidth)/2
    
    imgui.begin_child("##LeftWindow",[sideBuffer-10,videoHeight])
    imgui.separator_text("ボックス調整")
    imgui.begin_child("##DetectionBoxAdjustments",[-1,videoHeight/2 - 50])


    changeda, [static.config['timeBoxx'],static.config['timeBoxw'],static.config['timeBoxy'],static.config['timeBoxh']] = sliderInt4("時間", sideBuffer, 
            [static.config['timeBoxx'],static.config['timeBoxw'],static.config['timeBoxy'],static.config['timeBoxh']],
            [static.config['FrameWidth'], static.config['FrameHeight']])
    
    changedb, [static.config['skillBoxx'],static.config['skillBoxw'],static.config['skillBoxy'],static.config['skillBoxh']] = sliderInt4("スキル", sideBuffer, 
            [static.config['skillBoxx'],static.config['skillBoxw'],static.config['skillBoxy'],static.config['skillBoxh']],
            [static.config['FrameWidth'], static.config['FrameHeight']])
    
    changedc, [static.config['costBoxx'],static.config['costBoxw'],static.config['costBoxy'],static.config['costBoxh']] = sliderInt4("コスト", sideBuffer, 
            [static.config['costBoxx'],static.config['costBoxw'],static.config['costBoxy'],static.config['costBoxh']],
            [static.config['FrameWidth'], static.config['FrameHeight']])
        
    if changeda or changedb or changedc:
        static.dataFrameID = -1
        drawRectangles()


    if imgui.button("ボックス範囲を保存"):
        
        with open(download_window.selectedProject + "\\setting.json", "w",encoding="utf-8") as file:
            json.dump(static.config,file, ensure_ascii=False, indent=4)
    
    imgui.end_child()

    imgui.separator_text("動画識別コントロールパネル")

    imgui.begin_child("##VideoControlPanel",[-1,videoHeight/2 - 50],window_flags= imgui.WindowFlags_.no_scrollbar)
    imgui.text("スキル判定オフセット")
    changed, static.config['skillOffset']  = imgui.input_int("##SkillOffsetInput",static.config['skillOffset']) 
        
    if not hasattr(static, 'loadVideoThread') or not static.loadVideoThread.is_alive():
        imgui.begin_vertical("LoadVideoButtons")
        if imgui.button("識別"):
            static.loadVideoThread = threading.Thread(target=LoadVideo, args= [])
            static.loadVideoThread.start()
            
        if hasattr(static, 'Cost_Frame') and static.Cost_Frame is not None and len(static.Cost_Frame) > 0:
            if imgui.button("スキルだけ再識別"):
                
                static.loadVideoThread = threading.Thread(target=DetectSkillOnly, args= [])
                static.loadVideoThread.start()
        imgui.end_vertical()
        indicatorY = imgui.get_item_rect_size().y

        imgui.same_line()
        imgui.color_button("LoadVideoRunningIndicator", [0,255,0,255] ,imgui.ColorEditFlags_.no_tooltip | imgui.ColorEditFlags_.no_inputs,[indicatorY,indicatorY])
                
    else:
        imgui.text("識別中")
        imgui.same_line()
        imgui.color_button("LoadVideoRunningIndicator", [255,255,0,255] ,imgui.ColorEditFlags_.no_tooltip | imgui.ColorEditFlags_.no_inputs)
    

    imgui.end_child()

    imgui.end_child()

    imgui.same_line()
    
    immvision.image_display("##frame", static.rawFrame,(videoViewWidth, videoHeight), refresh_image = True)

    imgui.same_line()
    

    imgui.begin_child("##RightWindow",[sideBuffer -20,videoHeight],window_flags= imgui.WindowFlags_.no_scrollbar)

    imgui.separator_text("コスト識別データ")
    imgui.begin_child("##コスト識別データ",[ -1,videoHeight/2 - 50])
    
    
    if static.dataFrameID != static.frameID:
        static.costImg = np.copy(static.rawFrameImg[static.config['costBoxy'] : static.config['costBoxy'] + static.config['costBoxh'], static.config['costBoxx']: static.config['costBoxx'] + static.config['costBoxw'],  :])
        framediff = np.linalg.norm(static.costImg - [243,222,68],axis=2) / 1.8
        bluediff = np.abs(static.costImg[:,:,0] - 243)
        min = np.min([framediff, bluediff],axis= 0)

        static.costVis1min = min
        static.cosVis2min = cv2.resize(min,(200,20))
        static.dataFrameID = static.frameID
        static.currentCost = str( ocr_utils.calculateCost(static.costImg))
        
    displaySize = (int(sideBuffer -20), int(sideBuffer/20 - 1))
    imgui.text("コスト")
    immvision.image_display("##costImage", static.costImg, displaySize, refresh_image = True)
    imgui.text("識別用")
    immvision.image_display("##minImage",static.costVis1min, displaySize, refresh_image = True)
    imgui.text("計算用")        
    immvision.image_display("##calImage", static.cosVis2min, displaySize, refresh_image = True)
    
    imgui.text("Cost :" + static.currentCost)

    imgui.end_child()
        
    imgui.begin_child("##OutputWindow",[-1,videoHeight/2 - 50])
    
    if hasattr(static, 'Cost_Frame') and static.Cost_Frame is not None and len(static.Cost_Frame) > 0:
        if imgui.button("出力"):
            
            with open(download_window.selectedProject + '\\PartialTimeline.txt', 'w', newline='', encoding='utf-8') as file:
                
                for row  in static.Cost_Frame:
                    if not row.Disabled:
                        
                        file.write(str(row.FromCost) + " " + row.DetectedSkill + " " + row.TimeString + "\n")
    imgui.end_child()
    imgui.end_child()


    if implot.begin_plot("##cost plot",size=[-1,-1]):
        
        implot.setup_axes("frame", "cost", implot.AxisFlags_.range_fit,implot.AxisFlags_.lock)

        implot.setup_axis_limits(implot.ImAxis_.y1, 0, 10)
        implot.setup_axis_limits(implot.ImAxis_.x1, 0, static.config['FrameCount'])
        implot.setup_axis_limits_constraints(implot.ImAxis_.x1, 0, static.config['FrameCount'])
        PlotSkill( static.Cost_Frame)
        implot.end_plot()
    if hasattr(static, 'SelectedCostFrame') and static.SelectedCostFrame >= 0:
        pass
    
    return 1
