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
    
    videoFile.set(cv2.CAP_PROP_POS_MSEC, 1000 * static.config["FrameStart"]/ static.config["FramePerSecond"])

    static.Cost_Frame = list['SkillUse']()
    last_cost = 0.0
    
    x,y,w,h = [static.config['costBoxx'], static.config['costBoxy'], static.config['costBoxw'], static.config['costBoxh']]
    tx,ty,tw,th = [static.config['timeBoxx'], static.config['timeBoxy'], static.config['timeBoxw'], static.config['timeBoxh']]
    
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
    static.frameImage = np.copy(static.rawFrameImg)
    cv2.rectangle(static.frameImage, (static.config['timeBoxx'], static.config['timeBoxy']),(static.config['timeBoxx'] + static.config['timeBoxw'], static.config['timeBoxy'] + static.config['timeBoxh']),(0,0,255),2)
    cv2.rectangle(static.frameImage, (static.config['skillBoxx'], static.config['skillBoxy']),(static.config['skillBoxx'] + static.config['skillBoxw'], static.config['skillBoxy'] + static.config['skillBoxh']),(0,255,0),2)
    cv2.rectangle(static.frameImage, (static.config['costBoxx'], static.config['costBoxy']),(static.config['costBoxx'] + static.config['costBoxw'], static.config['costBoxy'] + static.config['costBoxh']),(0,255,255),2)

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

def BoxSizePanel(panelWidth, panelHeight):

    imgui.begin_child("##DetectionBoxAdjustments",[-1,panelHeight])

    imgui.separator_text("ボックス調整")

    changeda, [static.config['timeBoxx'],static.config['timeBoxw'],static.config['timeBoxy'],static.config['timeBoxh']] = sliderInt4("時間", panelWidth - 50, 
            [static.config['timeBoxx'],static.config['timeBoxw'],static.config['timeBoxy'],static.config['timeBoxh']],
            [static.config['FrameWidth'], static.config['FrameHeight']])
    
    changedb, [static.config['skillBoxx'],static.config['skillBoxw'],static.config['skillBoxy'],static.config['skillBoxh']] = sliderInt4("スキル", panelWidth - 50, 
            [static.config['skillBoxx'],static.config['skillBoxw'],static.config['skillBoxy'],static.config['skillBoxh']],
            [static.config['FrameWidth'], static.config['FrameHeight']])
    
    changedc, [static.config['costBoxx'],static.config['costBoxw'],static.config['costBoxy'],static.config['costBoxh']] = sliderInt4("コスト", panelWidth - 50, 
            [static.config['costBoxx'],static.config['costBoxw'],static.config['costBoxy'],static.config['costBoxh']],
            [static.config['FrameWidth'], static.config['FrameHeight']])
        
    if changeda or changedb or changedc:
        static.dataFrameID = -1
        drawRectangles()
        with open(download_window.selectedProject + "\\setting.json", "w",encoding="utf-8") as file:
            json.dump(static.config,file, ensure_ascii=False, indent=4)
    
    imgui.end_child()

def AnalyzationControlPanel(panelHeight):

    imgui.begin_child("##VideoControlPanel",[-1,panelHeight],window_flags= imgui.WindowFlags_.no_scrollbar)
    imgui.separator_text("動画識別コントロールパネル")
    if not hasattr(static, 'loadVideoThread') or not static.loadVideoThread.is_alive():
        imgui.push_style_color(imgui.Col_.button,0XFF007700)
        imgui.push_style_color(imgui.Col_.button_active,0XFF009900)
        imgui.push_style_color(imgui.Col_.button_hovered,0XFF003300)
        if imgui.button("スタートフレームセット"):
            static.config["FrameStart"] = static.frameID
        imgui.pop_style_color(3)
        imgui.same_line(spacing= 50)
        imgui.push_style_color(imgui.Col_.button,0XFF000077)
        imgui.push_style_color(imgui.Col_.button_active,0XFF000099)
        imgui.push_style_color(imgui.Col_.button_hovered,0XFF000033)
        if imgui.button("エンドフレームセット"):
            static.config["FrameEnd"] = static.frameID
        imgui.pop_style_color(3)
    imgui.text("全体スキル判定オフセット")
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
    
    if static.showGraph:
        if imgui.button("テーブル表示"):
            static.showGraph = False

    else:
        if imgui.button("グラフ表示"):
            static.showGraph = True


    imgui.end_child()

def BoxVisualizationPanel(panelWidth, panelHeight):
    
    imgui.begin_child("##コスト識別データ",[ -1,panelHeight])
    
    
    if static.dataFrameID != static.frameID:
        static.costImg = np.copy(static.rawFrameImg[static.config['costBoxy'] : static.config['costBoxy'] + static.config['costBoxh'], static.config['costBoxx']: static.config['costBoxx'] + static.config['costBoxw'],  :])
        framediff = np.linalg.norm(static.costImg - [243,222,68],axis=2) / 1.8
        bluediff = np.abs(static.costImg[:,:,0] - 243)
        min = np.min([framediff, bluediff],axis= 0)

        static.costVis1min = min
        static.cosVis2min = cv2.resize(min,(200,20))
        static.dataFrameID = static.frameID
        static.currentCost = str( ocr_utils.calculateCost(static.costImg))
        static.TimeImg = np.copy(static.rawFrameImg[static.config['timeBoxy'] : static.config['timeBoxy'] + static.config['timeBoxh'], static.config['timeBoxx']: static.config['timeBoxx'] + static.config['timeBoxw'],  :])
        static.SkillImg = np.copy(static.rawFrameImg[static.config['skillBoxy'] : static.config['skillBoxy'] + static.config['skillBoxh'], static.config['skillBoxx']: static.config['skillBoxx'] + static.config['skillBoxw'],  :])

        
    displaySize = (int(panelWidth -40), int(panelWidth/20 - 2))
    imgui.text("タイム")
    immvision.image_display("##TimeImg", static.TimeImg, displaySize, refresh_image = True)
    imgui.text("スキル")
    immvision.image_display("##SkillImg", static.SkillImg, displaySize, refresh_image = True)
    imgui.text("コスト")
    immvision.image_display("##costImage", static.costImg, displaySize, refresh_image = True)
    imgui.text("識別用")
    immvision.image_display("##minImage",static.costVis1min, displaySize, refresh_image = True)
    imgui.text("計算用")        
    immvision.image_display("##calImage", static.cosVis2min, displaySize, refresh_image = True)
    
    imgui.text("Cost :" + static.currentCost)

    imgui.end_child()

def gui():
    
    ret = 1
    global videoFile
    
    windowWidth = imgui.get_content_region_avail().x

    if videoFile is None:
            
        with open(download_window.selectedProject + "\\setting.json", "r",encoding="utf-8") as file:
            static.config = json.load(file)
        static.Cost_Frame = LoadData(download_window.selectedProject)
        videoFile = cv2.VideoCapture(download_window.selectedProject + "\\video.mp4")
        
        
        LoadFrame(int(static.config["FrameStart"]),videoFile)
        
        static.dataFrameID = -1
        static.showGraph = True
        
        
    windowWidth = imgui.get_content_region_avail().x
    videoViewWidth = int(windowWidth / 2)
    videoHeight = int(videoViewWidth / 16 * 9)
    sideBuffer = (windowWidth-videoViewWidth)/2
    #left panel
    imgui.begin_child("##LeftPanel",[sideBuffer-10,videoHeight])

    BoxSizePanel(sideBuffer, videoHeight/2 - 25)
    AnalyzationControlPanel(videoHeight/2)

    imgui.end_child()

    imgui.same_line()
    
    immvision.image_display("##frame", static.frameImage,(videoViewWidth, videoHeight), refresh_image = True)

    imgui.same_line()
    
    imgui.begin_child("##RightPanel",[sideBuffer -20,videoHeight],window_flags= imgui.WindowFlags_.no_scrollbar)


    imgui.separator_text("コスト識別データ")
    BoxVisualizationPanel(sideBuffer, videoHeight/3 * 2 - 50)
    
    imgui.separator_text("ジェネラル")
    imgui.begin_child("##OutputWindow",[-1,videoHeight/3 - 50])
    
    if hasattr(static, 'Cost_Frame') and static.Cost_Frame is not None and len(static.Cost_Frame) > 0:
        if imgui.button("タイムライン出力"):
            
            with open(download_window.selectedProject + '\\PartialTimeline.txt', 'w', newline='', encoding='utf-8') as file:
                
                for row  in static.Cost_Frame:
                    if not row.Disabled:
                        file.write(str(row.FromCost) + "\t" + row.DetectedSkill + "\t" + row.TimeString + "\t" + row.Meta + "\n" )
            subprocess.Popen("notepad.exe " + download_window.selectedProject + '\\PartialTimeline.txt')

    if not hasattr(static, 'loadVideoThread') or not static.loadVideoThread.is_alive():
        if imgui.button("プロジェクト選択へ戻る"):
            videoFile = None
            ret = 0
    imgui.end_child()

    imgui.end_child()


    imgui.begin_child("##DataWindow",size=[-1,-1])
    if static.showGraph:
        if implot.begin_plot("##cost plot",size=[-1,-1]):
            
            implot.setup_axes("frame", "cost", implot.AxisFlags_.range_fit,implot.AxisFlags_.lock)

            implot.setup_axis_limits(implot.ImAxis_.y1, 0, 10)
            implot.setup_axis_limits(implot.ImAxis_.x1, 0, static.config['FrameCount'])
            implot.setup_axis_limits_constraints(implot.ImAxis_.x1, 0, static.config['FrameCount'])
            PlotSkill( static.Cost_Frame)
            implot.end_plot()
            
    else:
        imgui.progress_bar(static.frameID/ static.config['FrameCount'],overlay="フレーム:" + str(int(static.frameID)))
        tableFlags =  imgui.TableFlags_.row_bg | imgui.TableFlags_.borders | imgui.TableFlags_.highlight_hovered_column | imgui.TableFlags_.scroll_y | imgui.TableFlags_.sizing_fixed_fit
        if imgui.begin_table("##cost table",columns = 9,flags=tableFlags):
            imgui.table_setup_scroll_freeze(0,1)
            imgui.table_setup_column("無効化")
            imgui.table_setup_column("コスト", flags=imgui.TableColumnFlags_.width_stretch )
            imgui.table_setup_column("時間", flags=imgui.TableColumnFlags_.width_stretch )
            
            imgui.table_setup_column("生徒", flags=imgui.TableColumnFlags_.width_stretch )
            imgui.table_setup_column("スキル判定オフセット(ms)", flags=imgui.TableColumnFlags_.width_stretch )
            imgui.table_setup_column("識別したスキル名", flags=imgui.TableColumnFlags_.width_stretch )

            imgui.table_setup_column("メモ", flags=imgui.TableColumnFlags_.width_stretch )
            imgui.table_setup_column("コストフレーム")
            imgui.table_setup_column("スキルフレーム")
            imgui.table_headers_row()

            for rowID in range(len(static.Cost_Frame)):
                row = static.Cost_Frame[rowID]
                imgui.table_next_row()
                imgui.table_next_column()
                changed1, static.Cost_Frame[rowID].Disabled = imgui.checkbox("##Disabled" + str(rowID),row.Disabled)
                imgui.table_next_column()
                changed3, static.Cost_Frame[rowID].FromCost = imgui.input_float("##FromCost" + str(rowID),row.FromCost,0.1,1.0,'%.1f',imgui.InputTextFlags_.auto_select_all)
                 
                imgui.table_next_column()
                imgui.text(row.TimeString)
                 
                imgui.table_next_column()
                imgui.text(row.SkillStringRaw)

                imgui.table_next_column()
                changed4, static.Cost_Frame[rowID].SkillOffset = imgui.input_int("##SkillOffset" + str(rowID),row.SkillOffset,1,10,imgui.InputTextFlags_.auto_select_all)
                
                
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
                    LoadFrame(row.FrameID + 0.001*(row.SkillOffset + static.config['skillOffset']) *static.config["FramePerSecond"], videoFile )
                
                    
            imgui.end_table()
        
    imgui.end_child()
    return ret
