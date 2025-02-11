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
import json
from scripts.chara_skill import CharaSkill
from paddleocr import PaddleOCR

skillOCR = PaddleOCR(use_angle_cls=False, lang='japan', show_log=False)
timeOCR = PaddleOCR(use_angle_cls=False, lang='en', show_log=False)

videoFile : cv2.VideoCapture | None = None

skills = CharaSkill.from_tsv()
videoProgress = 0

class SkillUse:
    FrameID : int = 0
    FromCost : float = 0
    ToCost : float = 0
    SkillOffset : int = 0
    TimeString : str = ""
    SkillStringRaw : str = ""
    DetectedSkill : str = ""
    
    def ToList(self) ->list:
        return [self.ToCost,self.FromCost,self.FrameID,self.SkillOffset,self.TimeString,self.SkillStringRaw,self.DetectedSkill]
    
    def ToString(self) ->str:
        return f"スキル：{self.DetectedSkill} \n時間：{self.TimeString} \nスキル判定オフセット:{self.SkillOffset} ms "

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
        if len(data) > 5:
            ret.DetectedSkill = str(data[6])
        return ret

def SaveCostFrame(CostFrame : list['SkillUse']):

    with open(download_window.selectedProject + '\\out.csv', 'w', newline='', encoding='utf-8') as csvfile:
        spamwriter = csv.writer(csvfile)
        for row  in CostFrame:
            spamwriter.writerow(row.ToList())

def DetectSkills(ref):
    
    global skills
    x,y,w,h = [ref.config['skillBoxx'], ref.config['skillBoxy'], ref.config['skillBoxw'], ref.config['skillBoxh']]
    
    for row in ref.Cost_Frame:
        
        time = 1000 / ref.config["movie_frame_rate"] * row.FrameID
        success = videoFile.set(cv2.CAP_PROP_POS_MSEC, time + row.SkillOffset + ref.config['skillOffset'])

        success, image = videoFile.read()
        
        image = image[y:y+h, x:x+w]
        
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        result = skillOCR.ocr(image,cls= False)


        if not result or not result[0]:
            continue

        row.SkillStringRaw = ""
        for line in result[0]:
            row.SkillStringRaw += str(line[1][0])
            
        row.DetectedSkill, similarity = CharaSkill.find_best_match(skills,row.SkillStringRaw,50)

def LoadVideo(ref):
    global videoProgress
    videoProgress = 0
    
    global videoFile
    
    videoFile.set(cv2.CAP_PROP_POS_MSEC, 0)

    ref.Cost_Frame = list['SkillUse']()
    frameCount = ref.frameCount
    last_cost = 0.0
    frame_id = 0
    x,y,w,h = [ref.config['costBoxx'], ref.config['costBoxy'], ref.config['costBoxw'], ref.config['costBoxh']]
    tx,ty,tw,th = [ref.config['timeBoxx'], ref.config['timeBoxy'], ref.config['timeBoxw'], ref.config['timeBoxh']]
    
    while frame_id < frameCount:
            
        videoProgress = (frame_id / frameCount) * 100
        success, frame = videoFile.read()
        if not success:
            frame_id+=10
            continue
        
        choppedImage = frame[y : y + h, x : x + w, :]
        
        cost = ocr_utils.calculateCost(choppedImage)
        
        if last_cost > cost + .7 :
            image = cv2.cvtColor(frame[ty : ty + th, tx : tx + tw, :], cv2.COLOR_BGR2GRAY)
            result = timeOCR.ocr(image,cls=False)
            
            if result[0] is None:
                frame_id += 1
                continue

            time = ""
            for line in result[0]:
                time+=line[1][0]

            if time == "":
                frame_id += 1
                continue

            ref.Cost_Frame.append(SkillUse.FromList([cost, last_cost,frame_id,0,time]))
            last_cost = cost
            frame_id += 1
            continue
        last_cost = cost
        frame_id += 1
        continue
        
    DetectSkills(ref)
    SaveCostFrame(ref.Cost_Frame)
            

def drawRectangles(staticVariables):
    staticVariables.rawFrame = np.copy(staticVariables.rawFrameImg)
    cv2.rectangle(staticVariables.rawFrame, (static.config['timeBoxx'], static.config['timeBoxy']),(static.config['timeBoxx'] + static.config['timeBoxw'], static.config['timeBoxy'] + static.config['timeBoxh']),(255,0,0),2)
    cv2.rectangle(staticVariables.rawFrame, (static.config['skillBoxx'], static.config['skillBoxy']),(static.config['skillBoxx'] + static.config['skillBoxw'], static.config['skillBoxy'] + static.config['skillBoxh']),(0,255,0),2)
    cv2.rectangle(staticVariables.rawFrame, (static.config['costBoxx'], static.config['costBoxy']),(static.config['costBoxx'] + static.config['costBoxw'], static.config['costBoxy'] + static.config['costBoxh']),(0,255,0),2)

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

def LoadData(projectPath)-> list['SkillUse']:
    ret = []
    if os.path.exists(projectPath + "\\out.csv"):
        with open(projectPath + "\\out.csv", 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                ret.append(SkillUse.FromList(row))
    return ret

def LoadFrame(context, FrameID, video):

        time = 1000 / context.config["movie_frame_rate"] * FrameID
        success = videoFile.set(cv2.CAP_PROP_POS_MSEC, time)

        success, context.rawFrameImg = video.read()

        context.rawFrame = np.copy(context.rawFrameImg)
        context.costImg = np.copy(context.rawFrameImg[context.config['costBoxy'] : context.config['costBoxy'] + context.config['costBoxh'], context.config['costBoxx']: context.config['costBoxx'] + context.config['costBoxw'],  :])

        context.currentCost = str( ocr_utils.calculateCost(context.costImg))
        context.frameID = FrameID
        drawRectangles(context)

def PlotSkill(context, data : list['SkillUse'], halfWidth = 10):

    draw_list = implot.get_plot_draw_list()


    limit = implot.get_plot_limits()
    

    lb = implot.plot_to_pixels(limit.x.min,limit.y.min)
    ru = implot.plot_to_pixels(limit.x.max,limit.y.max)
    draw_list.push_clip_rect(imgui.ImVec2(lb.x,ru.y),imgui.ImVec2(ru.x,lb.y))

    mousepos = implot.get_plot_mouse_pos()
    mousex = min(context.frameCount, np.round(mousepos.x))
    if implot.is_plot_hovered():

        top  = implot.plot_to_pixels(mousex - halfWidth, limit.y.max)
        bot = implot.plot_to_pixels(mousex + halfWidth, limit.y.min)

        draw_list.add_rect_filled(top, bot, 0X66666666)
        if imgui.is_mouse_released(imgui.MouseButton_.left) and imgui.get_mouse_drag_delta(imgui.MouseButton_.left).x == 0:
            global videoFile
            LoadFrame(context,mousex,videoFile)
    draw_list.add_line(implot.plot_to_pixels(context.frameID, limit.y.max), implot.plot_to_pixels(context.frameID, limit.y.min), 0XFFFFFFFF)
    tooltipShown = False
    
    for row in data:

        SkillUseBoxLB = implot.plot_to_pixels(row.FrameID - halfWidth, row.ToCost)
        SkillUseBoxRH = implot.plot_to_pixels(row.FrameID + halfWidth, row.FromCost)
        offsetToFrame = (row.SkillOffset+context.config['skillOffset'])/ 1000 * context.config['movie_frame_rate']
        SkillDiffChecker = implot.plot_to_pixels(int(row.FrameID  +  offsetToFrame), (row.ToCost + row.FromCost) / 2)
        Brightness = 0XAA888888
        if not tooltipShown:
            if mousex > row.FrameID - halfWidth and mousex < row.FrameID + halfWidth:
                if mousepos.y > row.ToCost and mousepos.y < row.FromCost:
                    imgui.set_tooltip(row.ToString())
                    Brightness  = 0XFFDDDDDD
                    tooltipShown = True
                    
        draw_list.add_rect_filled(SkillUseBoxLB, SkillUseBoxRH, Brightness & 0XFF00FFFF)
        if SkillUseBoxRH.x > SkillDiffChecker.x:

            draw_list.add_line([SkillDiffChecker.x,SkillDiffChecker.y], [SkillUseBoxRH.x,SkillDiffChecker.y], Brightness & 0XFF00FF00)
        else:
            draw_list.add_line([SkillUseBoxRH.x,SkillDiffChecker.y], [SkillDiffChecker.x,SkillDiffChecker.y], Brightness & 0XFF00FF00)

        draw_list.add_circle_filled(SkillDiffChecker,3.0, Brightness & 0XFF00FF00)

    draw_list.pop_clip_rect()

def gui():
    
    global videoProgress
    global videoFile
    
    windowWidth = imgui.get_content_region_avail().x

    if videoFile is None:
            
        with open(download_window.selectedProject + "\\setting.json", "r",encoding="utf-8") as file:
            static.config = json.load(file)
        static.Cost_Frame = LoadData(download_window.selectedProject)
        videoFile = cv2.VideoCapture(download_window.selectedProject + "\\video.mp4")
        
        static.frameCount =  int(videoFile.get(cv2.CAP_PROP_FRAME_COUNT))
        
        success, static.rawFrameImg = videoFile.read()
        static.frameWidth = static.rawFrameImg.shape[1]
        static.frameHeight = static.rawFrameImg.shape[0]
        
        static.rawFrame = np.copy(static.rawFrameImg)
        static.costImg = np.copy(static.rawFrameImg[static.config['costBoxy'] : static.config['costBoxy'] + static.config['costBoxh'], static.config['costBoxx']: static.config['costBoxx'] + static.config['costBoxw'],  :])

        static.currentCost = str( ocr_utils.calculateCost(static.costImg))
        static.frameID = 0
        drawRectangles(static)



    windowWidth = imgui.get_content_region_avail().x
    videoViewWidth = int(windowWidth / 5 * 3)
    videoHeight = int(videoViewWidth / 16 * 9)
    
    imgui.set_cursor_pos_x((windowWidth-videoViewWidth)/2)
    
    immvision.image_display("##frame", static.rawFrame,(videoViewWidth, videoHeight), refresh_image = True)


    
    itemWidth = (windowWidth - 100 ) / 4

    if imgui.collapsing_header("ボックス調整"):
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
    if imgui.collapsing_header("コスト識別データ"):
    
        
        immvision.image_display("コスト", static.costImg,(300, 30), refresh_image = True)
        imgui.same_line()
        framediff = np.linalg.norm(static.costImg - [243,222,68],axis=2) / 1.8
        
        bluediff = np.abs(static.costImg[:,:,0] - 243)
        imgui.same_line()
        
        min = np.min([framediff, bluediff],axis= 0)
        
        immvision.image_display("識別用",min,(400, 40), refresh_image = True)
        imgui.same_line()
        
        immvision.image_display("計算用", cv2.resize(min,(200,20)),(400, 40), refresh_image = True)
        imgui.same_line()
        
        imgui.push_item_width(200)
        imgui.spacing()


    if imgui.button("コスト識別"):
        if not hasattr(static, 'loadVideoThread') or not static.loadVideoThread.is_alive():
            static.loadVideoThread = threading.Thread(target=LoadVideo, args= [static])
            static.loadVideoThread.start()
           
    imgui.same_line()
    imgui.text(str(videoProgress))

    changed, static.config['skillOffset']  = imgui.input_int("スキル判定オフセット",static.config['skillOffset']) 
    if imgui.button("スキル再識別"):
        DetectSkills(static)
        SaveCostFrame(static.Cost_Frame)

        
    if hasattr(static, 'Cost_Frame') and static.Cost_Frame is not None:
            
            
        if implot.begin_plot("##cost plot"):
            
            implot.setup_axes("frame", "cost", implot.AxisFlags_.range_fit,implot.AxisFlags_.lock)

            implot.setup_axis_limits(implot.ImAxis_.y1, 0, 10)
            implot.setup_axis_limits(implot.ImAxis_.x1, 0, static.frameCount)
            implot.setup_axis_limits_constraints(implot.ImAxis_.x1, 0, static.frameCount)
            PlotSkill(static, static.Cost_Frame)
            implot.end_plot()
    if hasattr(static, 'SelectedCostFrame') and static.SelectedCostFrame >= 0:
        pass
    imgui.text("Cost :" + static.currentCost)
    
    return 2
