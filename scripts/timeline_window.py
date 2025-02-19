from imgui_bundle import imgui, immvision, implot
from imgui_bundle.immapp import static

import os
import cv2
import numpy as np
import threading
import ocr_utils
import csv
import json
from paddleocr import PaddleOCR
from chara_skill import CharaSkill
import download_window
import subprocess

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
        if self.Disabled:
            disabledString = "無効"
        else: 
            disabledString = "有効"
        return f"スキル：{self.DetectedSkill} \n時間：{self.TimeString} \nスキル判定オフセット:{self.SkillOffset} ms\n{disabledString}\n{self.Meta}"

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
    x,y,w,h = [static.config['SkillBoxx'], static.config['SkillBoxy'], static.config['SkillBoxw'], static.config['SkillBoxh']]
    
    for id, row in enumerate(static.Cost_Frame):
        
        time = 1000 / static.config["FramePerSecond"] * row.FrameID
        success = videoFile.set(cv2.CAP_PROP_POS_MSEC, time + row.SkillOffset + static.config['SkillOffset'])

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
        row.Disabled = row.DetectedSkill == ""
        backtrace = id-1
        while backtrace >=0:
            if not static.Cost_Frame[id].Disabled:
                if abs(static.Cost_Frame[id].ToCost - row.FromCost) < 0.2:
                    row.FromCost = -row.FromCost
                break
            backtrace -= 1 

def DetectSkillOnly():
    DetectSkills()
    SaveCostFrame(static.Cost_Frame)

def LoadVideo():
    
    global videoFile
    
    videoFile.set(cv2.CAP_PROP_POS_MSEC, 1000 * static.config["FrameStart"]/ static.config["FramePerSecond"])

    static.Cost_Frame = list['SkillUse']()
    last_cost = 0.0
    
    x,y,w,h = [static.config['CostBoxx'], static.config['CostBoxy'], static.config['CostBoxw'], static.config['CostBoxh']]
    tx,ty,tw,th = [static.config['TimeBoxx'], static.config['TimeBoxy'], static.config['TimeBoxw'], static.config['TimeBoxh']]
    diffColor = [np.uint8(static.config['DiffColorb']),np.uint8(static.config['DiffColorg']), np.uint8(static.config['DiffColorr'])]
    TotalCost = static.config['TotalCost']
    while True:
            
        success, image = videoFile.read()
        if not success:
            break
        static.frameID = int(videoFile.get(cv2.CAP_PROP_POS_FRAMES))
        
        static.rawFrameImg = image
        drawRectangles()
        if static.frameID >= static.config["FrameEnd"]:
            break
        choppedImage = static.rawFrameImg[y : y + h, x : x + w, :]
        
        cost = ocr_utils.CalculateCost(choppedImage,int(static.config["Threshold"]),TotalCost , diffColor,5)
        
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
    static.frameImage = np.copy(static.rawFrameImg)
    cv2.rectangle(static.frameImage, (static.config['TimeBoxx'], static.config['TimeBoxy']),(static.config['TimeBoxx'] + static.config['TimeBoxw'], static.config['TimeBoxy'] + static.config['TimeBoxh']),(0,0,255),2)
    cv2.rectangle(static.frameImage, (static.config['SkillBoxx'], static.config['SkillBoxy']),(static.config['SkillBoxx'] + static.config['SkillBoxw'], static.config['SkillBoxy'] + static.config['SkillBoxh']),(0,255,0),2)
    cv2.rectangle(static.frameImage, (static.config['CostBoxx'], static.config['CostBoxy']),(static.config['CostBoxx'] + static.config['CostBoxw'], static.config['CostBoxy'] + static.config['CostBoxh']),(0,255,255),2)

def sliderInt4(tag, itemWidth,itemHeight, itemValues, frameValues, color):
    imgui.begin_group()#("##Child"+tag,(itemWidth,itemHeight-10))
    imgui.push_id(tag)
    imgui.text_colored(imgui.color_convert_u32_to_float4(color),tag)

    maxValues = [frameValues[0] - itemValues[1], frameValues[0] - itemValues[0], frameValues[1] - itemValues[3], frameValues[1] - itemValues[2]]
    changed = False
    for i, name in enumerate(["x","w","y","z"]):
        
        imgui.begin_group()
        imgui.push_id(name)
        if imgui.button("-",((itemWidth)/4,20)):
            itemValues[i] = itemValues[i] -1
            changed = True
        ret, itemValues[i] = imgui.v_slider_int("",((itemWidth)/4,itemHeight - 80), itemValues[i],  maxValues[i],1 ,name+"\n%d")
        changed = changed or ret
        
        if imgui.button("+",((itemWidth)/4,20)):
            itemValues[i] = itemValues[i] + 1
            changed = True
        itemValues[i] = max(1, min(itemValues[i], maxValues[i]-1))
        imgui.pop_id()
        imgui.end_group()
        
        imgui.same_line()


    imgui.pop_id()
    imgui.end_group()
    return changed, itemValues

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
        
        static.frameID = FrameID
        drawRectangles()

def PlotSeekbar(size):
    
    if implot.begin_plot("##seekbar", size,implot.Flags_.no_frame):
        
        implot.setup_axes("", "", implot.AxisFlags_.range_fit | implot.AxisFlags_.no_label | implot.AxisFlags_.none ,implot.AxisFlags_.lock | implot.AxisFlags_.no_decorations )
        
        implot.setup_axis_limits(implot.ImAxis_.y1, 0, static.config['TotalCost'])
        implot.setup_axis_limits(implot.ImAxis_.x1, 0, static.config['FrameCount'])
        implot.setup_axis_links(implot.ImAxis_.y1, implot.BoxedValue(0), implot.BoxedValue(static.config['TotalCost']))
        
        
        implot.setup_axis_limits_constraints(implot.ImAxis_.x1, 0, static.config['FrameCount'])
        implot.setup_axis_limits_constraints(implot.ImAxis_.y1, 0, static.config['TotalCost'])

        draw_list = implot.get_plot_draw_list()


        limit = implot.get_plot_limits()
        
        ret = implot.drag_line_x(0,static.config["FrameStart"],imgui.color_convert_u32_to_float4(0XFF00FF00),out_clicked=True,held=True)
        if ret[2] and not ret[4]:
            static.config["FrameStart"] = np.floor(ret[1])
            pass

        lb = implot.plot_to_pixels(limit.x.min,limit.y.min)
        ru = implot.plot_to_pixels(limit.x.max,limit.y.max)
        draw_list.push_clip_rect(imgui.ImVec2(lb.x,ru.y),imgui.ImVec2(ru.x,lb.y))

        mousepos = implot.get_plot_mouse_pos()
        mousex = min(static.config['FrameCount'], np.round(mousepos.x))
        rangeBoxLU = implot.plot_to_pixels(static.config["FrameStart"], limit.y.max)
        rangeBoxRD = implot.plot_to_pixels(static.config["FrameEnd"], limit.y.min)

        draw_list.add_rect_filled(rangeBoxLU, rangeBoxRD, 0X11FFFFFF)
        if False:#implot.is_plot_hovered():

            top  = implot.plot_to_pixels(mousex - halfWidth, limit.y.max)
            bot = implot.plot_to_pixels(mousex + halfWidth, limit.y.min)
            
            draw_list.add_rect_filled(top, bot, 0X66FFFFFF)
            if imgui.is_mouse_released(imgui.MouseButton_.left) and imgui.get_mouse_drag_delta(imgui.MouseButton_.left).x == 0:
                global videoFile
                if not hasattr(static, 'loadVideoThread') or not static.loadVideoThread.is_alive():
                    LoadFrame(mousex,videoFile)

        draw_list.add_line(implot.plot_to_pixels(static.frameID, limit.y.max), implot.plot_to_pixels(static.frameID, limit.y.min), 0XFFFFFFFF)
        draw_list.add_line([rangeBoxLU.x,rangeBoxLU.y],[rangeBoxLU.x,rangeBoxRD.y], 0XFF00FF00)
        draw_list.add_line([rangeBoxRD.x,rangeBoxLU.y],[rangeBoxRD.x,rangeBoxRD.y], 0XFF0000FF)
        
        
        draw_list.pop_clip_rect()
        implot.end_plot()


def PlotSkill(data : list['SkillUse'], halfWidth = 10):

    draw_list = implot.get_plot_draw_list()


    limit = implot.get_plot_limits()
    

    lb = implot.plot_to_pixels(limit.x.min,limit.y.min)
    ru = implot.plot_to_pixels(limit.x.max,limit.y.max)
    draw_list.push_clip_rect(imgui.ImVec2(lb.x,ru.y),imgui.ImVec2(ru.x,lb.y))

    mousepos = implot.get_plot_mouse_pos()
    mousex = min(static.config['FrameCount'], np.round(mousepos.x))
    rangeBoxLU = implot.plot_to_pixels(static.config["FrameStart"], limit.y.max)
    rangeBoxRD = implot.plot_to_pixels(static.config["FrameEnd"], limit.y.min)

    draw_list.add_rect_filled(rangeBoxLU, rangeBoxRD, 0X11FFFFFF)
    if implot.is_plot_hovered():

        top  = implot.plot_to_pixels(mousex - halfWidth, limit.y.max)
        bot = implot.plot_to_pixels(mousex + halfWidth, limit.y.min)
        
        draw_list.add_rect_filled(top, bot, 0X66FFFFFF)
        if imgui.is_mouse_released(imgui.MouseButton_.left) and imgui.get_mouse_drag_delta(imgui.MouseButton_.left).x == 0:
            global videoFile
            if not hasattr(static, 'loadVideoThread') or not static.loadVideoThread.is_alive():
                LoadFrame(mousex,videoFile)

    draw_list.add_line(implot.plot_to_pixels(static.frameID, limit.y.max), implot.plot_to_pixels(static.frameID, limit.y.min), 0XFFFFFFFF)
    draw_list.add_line([rangeBoxLU.x,rangeBoxLU.y],[rangeBoxLU.x,rangeBoxRD.y], 0XFF00FF00)
    draw_list.add_line([rangeBoxRD.x,rangeBoxLU.y],[rangeBoxRD.x,rangeBoxRD.y], 0XFF0000FF)
    
    tooltipShown = False
    
    for row in data:

        SkillUseBoxLB = implot.plot_to_pixels(row.FrameID - halfWidth, row.ToCost)
        SkillUseBoxRH = implot.plot_to_pixels(row.FrameID + halfWidth, abs(row.FromCost))
        offsetToFrame = (row.SkillOffset+static.config['SkillOffset'])/ 1000 * static.config['FramePerSecond']
        SkillDiffChecker = implot.plot_to_pixels(int(row.FrameID  +  offsetToFrame), (row.ToCost + abs(row.FromCost)) / 2)
        Brightness = 0XAAAAAAAA
        if not tooltipShown:
            if mousex > row.FrameID - halfWidth and mousex < row.FrameID + halfWidth:
                if mousepos.y > row.ToCost and mousepos.y < abs(row.FromCost):
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

def BoxSizePanel(panelWidth, panelHeight):

    imgui.begin_group()#("##DetectionBoxAdjustments",[panelWidth,panelHeight],imgui.WindowFlags_.no_scroll_with_mouse |imgui.WindowFlags_.no_scrollbar)

    imgui.text("ボックス調整")
    
    changeda, [static.config['TimeBoxx'],static.config['TimeBoxw'],static.config['TimeBoxy'],static.config['TimeBoxh']] = sliderInt4("時間", panelWidth/3, panelHeight,
            [static.config['TimeBoxx'],static.config['TimeBoxw'],static.config['TimeBoxy'],static.config['TimeBoxh']],
            [static.config['FrameWidth'], static.config['FrameHeight']],0XFF0000FF)
    imgui.same_line()
    changedb, [static.config['SkillBoxx'],static.config['SkillBoxw'],static.config['SkillBoxy'],static.config['SkillBoxh']] = sliderInt4("スキル", panelWidth/3, panelHeight,
            [static.config['SkillBoxx'],static.config['SkillBoxw'],static.config['SkillBoxy'],static.config['SkillBoxh']],
            [static.config['FrameWidth'], static.config['FrameHeight']],0XFF00FF00)
    imgui.same_line()
    changedc, [static.config['CostBoxx'],static.config['CostBoxw'],static.config['CostBoxy'],static.config['CostBoxh']] = sliderInt4("コスト", panelWidth/3, panelHeight,
            [static.config['CostBoxx'],static.config['CostBoxw'],static.config['CostBoxy'],static.config['CostBoxh']],
            [static.config['FrameWidth'], static.config['FrameHeight']],0XFF00FFFF)
        
        
    if changeda or changedb or changedc:
        static.dataFrameID = -1
        drawRectangles()
        static.Dirty = True
        
    
    imgui.end_group()

def AnalyzationControlPanel(panelWidth, panelHeight):

    imgui.begin_child("##VideoControlPanel",[panelWidth,panelHeight],window_flags= imgui.WindowFlags_.no_scrollbar)
    imgui.separator_text("動画識別コントロールパネル")

            
    if static.config['TotalCost']  > 10:
        if imgui.button("20コスト"):
            static.config['TotalCost'] = 10
            static.Dirty = True

    else:
        if imgui.button("10コスト"):            
            static.config['TotalCost'] = 20
            static.Dirty = True


    if not hasattr(static, 'loadVideoThread') or not static.loadVideoThread.is_alive():
        imgui.push_style_color(imgui.Col_.button,0XFF007700)
        imgui.push_style_color(imgui.Col_.button_active,0XFF009900)
        imgui.push_style_color(imgui.Col_.button_hovered,0XFF003300)
        if imgui.button("スタートフレームセット"):
            static.config["FrameStart"] = static.frameID
            static.Dirty = True
        imgui.pop_style_color(3)
        imgui.same_line(spacing= 50)
        imgui.push_style_color(imgui.Col_.button,0XFF000077)
        imgui.push_style_color(imgui.Col_.button_active,0XFF000099)
        imgui.push_style_color(imgui.Col_.button_hovered,0XFF000033)
        if imgui.button("エンドフレームセット"):
            static.config["FrameEnd"] = static.frameID
            static.Dirty = True
        imgui.pop_style_color(3)
    imgui.text("全体スキル判定オフセット")

    changed, static.config['SkillOffset']  = imgui.input_int("##SkillOffsetInput",static.config['SkillOffset']) 
    static.Dirty = static.Dirty or changed
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

def BoxVisualizationPanel(panelWidth, panelHeight):
    
    imgui.begin_group()

    BoxSizePanel(panelWidth/2, panelHeight/2)
    imgui.same_line()
    diffColor = [np.uint8(static.config['DiffColorb']),np.uint8(static.config['DiffColorg']), np.uint8(static.config['DiffColorr'])]

    if static.dataFrameID != static.frameID:
        static.costImg = np.copy(static.rawFrameImg[static.config['CostBoxy'] : static.config['CostBoxy'] + static.config['CostBoxh'], static.config['CostBoxx']: static.config['CostBoxx'] + static.config['CostBoxw'],  :])
        
        ddiff = abs(static.costImg.astype(int) - np.asarray(diffColor).astype(int)).astype(np.uint8)
        ddiffc = abs(static.costImg.astype(int) - np.asarray((np.asarray([255,255,255]) - diffColor) * 0.7 +diffColor).astype(int)).astype(np.uint8)
        min = np.min([ddiff,ddiffc],axis=0)
        max = np.max(min,axis=2)

        static.costVis1min = cv2.resize(max,(400,20))
        colsum = np.sum((max > static.config["Threshold"]),axis = 0)
        
        static.costVis2min = cv2.resize(((np.asarray([colsum])> 12)*255).astype(np.uint8),(400,20))

        static.dataFrameID = static.frameID
        static.currentCost = str( ocr_utils.CalculateCost(static.costImg,int(static.config["Threshold"]), static.config['TotalCost'], diffColor,5))
        static.TimeImg = np.copy(static.rawFrameImg[static.config['TimeBoxy'] : static.config['TimeBoxy'] + static.config['TimeBoxh'], static.config['TimeBoxx']: static.config['TimeBoxx'] + static.config['TimeBoxw'],  :])
        static.SkillImg = np.copy(static.rawFrameImg[static.config['SkillBoxy'] : static.config['SkillBoxy'] + static.config['SkillBoxh'], static.config['SkillBoxx']: static.config['SkillBoxx'] + static.config['SkillBoxw'],  :])
    
    imgui.begin_group()
    displayh = int(np.round(panelHeight/8))
    
    panelw = int(panelWidth/2 -40)
    Imgwhr = static.TimeImg.shape[1]/static.TimeImg.shape[0]
    displayw = Imgwhr*displayh
    if displayw > panelw:
        displayw = panelw
        displayh = np.round(panelw/Imgwhr)
    immvision.image_display("タイム##TimeImg", static.TimeImg, (int(np.round(displayw)),displayh), refresh_image = True)
    
    Imgwhr = static.SkillImg.shape[1]/static.SkillImg.shape[0]
    displayw = Imgwhr*displayh
    if displayw > panelw:
        displayw = panelw
        displayh = int(np.round(panelw/Imgwhr))
        
    immvision.image_display("スキル##SkillImg", static.SkillImg, (int(np.round(displayw)),displayh), refresh_image = True)
    
    imgui.end_group()

    imgui.text("コスト")
    imgui.color_button("識別色",[diffColor[2]/255,diffColor[1]/255,diffColor[0]/255,1])
    imgui.same_line()
    changed, static.config["Threshold"] = imgui.slider_int("##thresholdSlider", int(static.config["Threshold"]),0,255,flags=imgui.SliderFlags_.always_clamp)
    static.Dirty = changed or static.Dirty
    if changed:
        static.dataFrameID = -1

    displayh = int(np.round(panelHeight/4))

    panelw = int(panelWidth - 20)
    Imgwhr = static.costImg.shape[1]/static.costImg.shape[0]
    displayw = Imgwhr*displayh
    if displayw > panelw:
        displayw = panelw
        displayh = int(np.round(panelw/Imgwhr))

    if not hasattr(static, 'pts'):
        static.imageParams = immvision.ImageParams()
        static.imageParams.refresh_image= True
        static.imageParams.can_resize=False
        static.imageParams.image_display_size= (int(np.round(displayw)),displayh)
        static.imageParams.pan_with_mouse=False
        static.imageParams.zoom_with_mouse_wheel=False
        static.imageParams.show_zoom_buttons=False
        static.imageParams.show_alpha_channel_checkerboard=False
        static.imageParams.show_pixel_info=False
        static.imageParams.show_grid=False
        static.imageParams.show_school_paper_background = False
        static.imageParams.show_image_info = False
        static.imageParams.show_options_panel = False
        static.imageParams.show_options_button = False
        static.imageParams.watched_pixels = []
        static.imageParams.highlight_watched_pixels = False
        
    static.imageParams.show_options_panel = False

    immvision.image("##costImage", static.costImg, static.imageParams)
    if len(static.imageParams.watched_pixels) > 0:
        point = static.imageParams.watched_pixels[0]
        [static.config['DiffColorb'], static.config['DiffColorg'], static.config['DiffColorr']] = static.costImg[point[1],point[0],:].astype(float)
        static.imageParams.watched_pixels = []
        static.Dirty = True
        static.dataFrameID = -1
    
    imgui.text("識別色確認、黒い部分はコストとして識別されている")
    immvision.image_display("##minImage",static.costVis1min, (int(np.round(displayw)),displayh), refresh_image = True)
    imgui.text("計算確認、黒い部分はコストとして識別されている")        
    immvision.image_display("##calImage", static.costVis2min, (int(np.round(displayw)),displayh), refresh_image = True)
    
    imgui.text("Cost :" + static.currentCost)
    

    imgui.end_group()

def DrawGraph():

    if implot.begin_plot("##cost plot",size=[-1,-1]):
        
        implot.setup_axes("frame", "cost", implot.AxisFlags_.range_fit,implot.AxisFlags_.lock)

        implot.setup_axis_limits(implot.ImAxis_.y1, 0, static.config['TotalCost'])
        implot.setup_axis_limits(implot.ImAxis_.x1, 0, static.config['FrameCount'])
        implot.setup_axis_links(implot.ImAxis_.y1, implot.BoxedValue(0), implot.BoxedValue(static.config['TotalCost']))
        
        
        implot.setup_axis_limits_constraints(implot.ImAxis_.x1, 0, static.config['FrameCount'])
        implot.setup_axis_limits_constraints(implot.ImAxis_.y1, 0, static.config['TotalCost'])
        PlotSkill( static.Cost_Frame)
        implot.end_plot()
        
def DrawTable():

    imgui.progress_bar(static.frameID/ static.config['FrameCount'],overlay="フレーム:" + str(int(static.frameID)))
    tableFlags =  imgui.TableFlags_.row_bg | imgui.TableFlags_.borders | imgui.TableFlags_.highlight_hovered_column | imgui.TableFlags_.scroll_y | imgui.TableFlags_.sizing_fixed_fit
    if imgui.begin_table("##cost table",columns = 10,flags=tableFlags):
        imgui.table_setup_scroll_freeze(0,1)
        imgui.table_setup_column("無効化")
        imgui.table_setup_column("フレーム", flags=imgui.TableColumnFlags_.width_fixed )
        imgui.table_setup_column("コスト", flags=imgui.TableColumnFlags_.width_stretch )
        imgui.table_setup_column("時間", flags=imgui.TableColumnFlags_.width_fixed)
        
        imgui.table_setup_column("生徒", flags=imgui.TableColumnFlags_.width_stretch )
        imgui.table_setup_column("スキル判定オフセット(ms)", flags=imgui.TableColumnFlags_.width_stretch )
        imgui.table_setup_column("識別したスキル名", flags=imgui.TableColumnFlags_.width_stretch )

        imgui.table_setup_column("メモ", flags=imgui.TableColumnFlags_.width_stretch )
        imgui.table_setup_column("コストフレーム")
        imgui.table_setup_column("スキルフレーム")
        imgui.table_headers_row()

        for rowID ,row in enumerate(static.Cost_Frame):
            
            imgui.table_next_row()
            imgui.table_next_column()
            changed1, static.Cost_Frame[rowID].Disabled = imgui.checkbox("##Disabled" + str(rowID),row.Disabled)
            imgui.table_next_column()
            imgui.text(str(int(row.FrameID)))
            imgui.table_next_column()
            realFromCost = static.Cost_Frame[rowID].FromCost 
            isInstant = realFromCost < 0
            realFromCost = abs(realFromCost)
            if isInstant :
                
                imgui.push_style_color(imgui.Col_.button,0XFF007700)
                imgui.push_style_color(imgui.Col_.button_active,0XFF000000)
                imgui.push_style_color(imgui.Col_.button_hovered,0XFF002200)
                if imgui.button("即##" + str(rowID)):
                    isInstant = False
                imgui.pop_style_color(3)
                
            else:
                imgui.push_style_color(imgui.Col_.button,0XFF000000)
                imgui.push_style_color(imgui.Col_.button_active,0XFF007700)
                imgui.push_style_color(imgui.Col_.button_hovered,0XFF005500)
                
                if imgui.small_button("@##" + str(rowID)):
                    isInstant = True
                imgui.pop_style_color(3)
            
            imgui.same_line()    
            changed3, realFromCost = imgui.input_float("##FromCost" + str(rowID),realFromCost,0.1,1.0,'%.1f',imgui.InputTextFlags_.auto_select_all)
        
            if isInstant:
                static.Cost_Frame[rowID].FromCost = realFromCost * -1
            else:
                static.Cost_Frame[rowID].FromCost = realFromCost
            imgui.table_next_column()
            imgui.text(row.TimeString)
                
            imgui.table_next_column()
            imgui.text(row.SkillStringRaw)

            imgui.table_next_column()
            changed4, static.Cost_Frame[rowID].SkillOffset = imgui.input_int("##SkillOffset" + str(rowID),row.SkillOffset,1,int(static.config['TotalCost']),imgui.InputTextFlags_.auto_select_all)
            
            
            imgui.table_next_column()
            changed2, static.Cost_Frame[rowID].DetectedSkill = imgui.input_text("##DetectedSkill" + str(rowID),row.DetectedSkill,imgui.InputTextFlags_.no_horizontal_scroll|imgui.InputTextFlags_.enter_returns_true|imgui.InputTextFlags_.auto_select_all)
                
            imgui.table_next_column()
            changed5, static.Cost_Frame[rowID].Meta = imgui.input_text("##Meta" + str(rowID),row.Meta)


            if changed1 or changed2 or changed3 or changed4 or changed5:
                SaveCostFrame(static.Cost_Frame)

            imgui.table_next_column()
            if imgui.button("コストフレーム##" + str(rowID)):
                LoadFrame(row.FrameID,videoFile)
            imgui.table_next_column()
            if imgui.button("スキルフレーム##" + str(rowID)):
                LoadFrame(row.FrameID + 0.001*(row.SkillOffset + static.config['SkillOffset']) *static.config["FramePerSecond"], videoFile )
            
                
        imgui.end_table()

def Init():
    global videoFile
    with open(download_window.selectedProject + "\\setting.json", "r",encoding="utf-8") as file:
        static.config = json.load(file)
    static.Cost_Frame = LoadData(download_window.selectedProject)
    videoFile = cv2.VideoCapture(download_window.selectedProject + "\\video.mp4")
    
    static.Dirty = False
    LoadFrame(int(static.config["FrameStart"]),videoFile)
    
    static.dataFrameID = -1
    static.BottomWindowSwitch = 0

def WriteTimeLine(path, Cost_Frame):
    
    with open(path, 'w', newline='', encoding='utf-8') as file:
        
        for row  in Cost_Frame:
            if not row.Disabled:
                if row.FromCost > 0:
                    file.write(str(abs(row.FromCost)))
                else:
                    file.write("即") 
                file.write("\t" + row.DetectedSkill + "\t" + row.TimeString + "\t" + row.Meta + "\n" )
    subprocess.Popen("notepad.exe " + path)


def gui():
    
    ret = 1
    
    windowWidth = imgui.get_content_region_avail().x

    global videoFile
    if videoFile is None:
        Init()
        
    windowSize = imgui.get_content_region_avail()
    windowWidth = windowSize.x
    windowHeight = windowSize.y

    videoViewWidth = int(windowWidth / 2)
    videoHeight = int(videoViewWidth / 16 * 9)
    sideBuffer = (windowWidth-videoViewWidth)/2
    
    AnalyzationControlPanel(sideBuffer - 20, videoHeight/2)
    
    imgui.same_line()
    
    immvision.image_display("##frame", static.frameImage,(videoViewWidth, videoHeight), refresh_image = True)

    imgui.same_line()
    
    imgui.begin_child("##RightPanel",[sideBuffer - 20,videoHeight],window_flags= imgui.WindowFlags_.no_scrollbar)
    
    imgui.separator_text("ジェネラル")
    
    if not hasattr(static, 'loadVideoThread') or not static.loadVideoThread.is_alive():
        if hasattr(static, 'Cost_Frame') and static.Cost_Frame is not None and len(static.Cost_Frame) > 0:
            if imgui.button("タイムライン出力"):
                WriteTimeLine(download_window.selectedProject + '\\PartialTimeline.txt', static.Cost_Frame)
        if imgui.button("プロジェクト選択へ戻る"):
            videoFile = None
            ret = 0
            

    imgui.end_child()
    PlotSeekbar((windowWidth,500))
    height = windowHeight - videoHeight - 20
    imgui.begin_child("##DataWindow",(-1,-1),window_flags=imgui.WindowFlags_.no_scroll_with_mouse| imgui.WindowFlags_.no_scrollbar)
    imgui.begin_vertical("##DataWindowSelector",(50,height))
    
    if imgui.button("テ\nー\nブ\nル",size=(50,((static.BottomWindowSwitch == 1) + 1) *height/4)):
        static.BottomWindowSwitch = 1
        
    if imgui.button("グ\nラ\nフ",size=(50,((static.BottomWindowSwitch == 0) + 1) *height/4)):
        static.BottomWindowSwitch = 0

    if imgui.button("コ\nス\nト",size=(50,((static.BottomWindowSwitch == 2) + 1) * height/4)):
        static.BottomWindowSwitch = 2
        
        
    if hasattr(static, 'loadVideoThread') and static.loadVideoThread.is_alive():
        static.BottomWindowSwitch = 0
    imgui.end_vertical()
    
    imgui.same_line()
    imgui.begin_child("##DataDisplayWindow",size=[-1,-1])
    
    if static.BottomWindowSwitch == 0:
        DrawGraph()
    elif static.BottomWindowSwitch == 1:
        DrawTable()
    else:
        BoxVisualizationPanel(windowWidth - 50,height)
    imgui.end_child()
    
    imgui.end_child()
    if static.Dirty:
        with open(download_window.selectedProject + "\\setting.json", "w",encoding="utf-8") as file:
            json.dump(static.config,file, ensure_ascii=False, indent=4)
            static.Dirty = False
    return ret
