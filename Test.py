

import matplotlib.pyplot as plt
from scripts.debug_timer import DebugTimer
from moviepy import VideoFileClip
import cv2
from scripts.ocr_utils import crop_image, draw_image_line, draw_image_rect, draw_image_string, get_color_fill_percentage, get_image_bar_percentage,get_image_bar_percentage_hmcll, get_mask_image_rect, ocr_image
from scripts.common_utils import convert_safe_filename, load_memo, load_timeline, save_image, save_memo, save_timeline, str_to_time, time_to_str
import csv
import numpy as np
import scipy.stats as stats

input_path = "D:/movie.mp4"
start_time = 15
frame_rate = 60

movie_x= 0
movie_y=0
movie_width= 1728
movie_height= 1080

mask_image_w = 1920
mask_image_h = 1080

mask_cost_x= 1241
mask_cost_y= 1024
mask_cost_w= 476
mask_cost_h= 24

mask_time_x = 1629
mask_time_y = 29
mask_time_w = 183
mask_time_h = 56

def get_movie_size():
    return (movie_width, movie_height)

def get_mask_size():
    return (mask_image_w, mask_image_h)

def adjust_mask_rect(mask_rect, mask_image_size, image_size, anchor=(0, 0)):
    x, y, w, h = mask_rect
    image_rate = image_size[0] / mask_image_size[0]
    x *= image_rate
    y *= image_rate
    w *= image_rate
    h *= image_rate
    #x += (image_size[0] - mask_image_size[0]) * anchor[0]
    y += (image_size[1] - mask_image_size[1] * image_rate) * anchor[1]
    return (int(x), int(y), int(w), int(h))


def get_cost_mask_rect():
    mask_rect = (
        int(mask_cost_x),
        int(mask_cost_y),
        int(mask_cost_w),
        int(mask_cost_h)
    )
    anchor = (1, 1)
    return adjust_mask_rect(mask_rect, get_mask_size(), get_movie_size(), anchor)

mask_time_rect = adjust_mask_rect([mask_time_x,mask_time_y,mask_time_w,mask_time_h], get_mask_size(), get_movie_size(),(1, 0))

def format_time_string(time_str: str):
    time_str = ''.join(filter(str.isdigit, time_str))
    if len(time_str) == 4:
        return f"{time_str[:2]}:{time_str[2:]}"
    elif len(time_str) == 7:
        return f"{time_str[:2]}:{time_str[2:4]}.{time_str[4:]}"
    else:
        return ""
    
def LoadVideo():
    Cost_Frame = []
    timer = DebugTimer()
    timer.start()
    
    with VideoFileClip(input_path) as clip:
        
        with clip.subclipped(start_time, clip.duration).with_fps(frame_rate) as subclip:

            frame_Markers = []
            Cost_Frame = []
            frame_count = int(frame_rate * subclip.duration)
            last_cost = 0.0
            frame_id = 0
            last_time = 9999999999999
            while frame_id < frame_count:
                
                frame = subclip.get_frame(frame_id/frame_rate)
                input_image = crop_image(frame, (movie_x, movie_y, movie_width, movie_height))
                
                
                
#                if remain_time_text == "":
#                    frame_id += 15
#                    continue
#                percentTimer = DebugTimer()
#                percentTimer.start()
                
                
                x,y,w,h = get_cost_mask_rect()
                choppedImage = input_image[y:y+h, x:x+w,2]
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
                    
                    if cost != Cost_Frame[len(Cost_Frame -2)][0]:

                    time_image = crop_image(input_image, mask_time_rect)
                    time_texts = ocr_image(time_image, None, 'en')
                    remain_time_text = format_time_string("".join(time_texts))
                    if(remain_time_text != ""):
                        s1 = remain_time_text.split(":")
                        if len(s1) == 2:
                            s2 = s1[1].split(".")
                            if len(s2) == 2:
                                time = float(s1[0]) * 60000 + float(s2[0])* 1000 + float(s2[1])
                                if time <= last_time:
                                    last_time = time
                                    Cost_Frame.append([last_cost,frame_id,time])
                                    last_cost = cost
                                    frame_id += 1
                                    continue
                    frame_id += 15
                    continue
                    
                frame_id += 1

                continue

                processedImg2 = np.zeros([20,200])
                processedImg3 = np.zeros([20,200])


                for lineID in range(0,endID):
                    processedImg2[:,lineID] = (colsum[lineID] > 17)*255
                    processedImg3[:,lineID] = (lineID < endID)*255



                processedImg2 = processedImg2.astype('uint8')
                processedImg3 = processedImg3.astype('uint8')

                    
                frameTimer.print("4")
                
                stackedImg = np.block([
                    [choppedImage],[processedImg],[processedImg2],[processedImg3]
                    ])
                
                frameTimer.print("frame")
                cv2.imshow('image',stackedImg,)
                cv2.waitKey(0)


                for lineID in range(0,200):
                    modeRes = stats.mode(processedImg[:,lineID])
                    if modeRes[1] > .95:
                        processedImg[:,lineID] = modeRes[0]
                    else:
                        processedImg[:,lineID] = 0
                for lineID in range(1,200):
                    if processedImg[0,lineID] > sum and processedImg[0,lineID -1] < sum:
                        sum = (processedImg[0,lineID] + processedImg[0,lineID -1])/2
                threshold =  np.copy(processedImg)
                threshold[:,:] = sum
                processedImg2 = np.copy(processedImg)
                
                for lineID in range(0,20):
                    modeRes = stats.mode(processedImg[0,lineID*10:lineID*10 + 10])
                    if modeRes[1] > .95:
                        processedImg2[:,lineID*10:lineID*10 + 10] = modeRes[0]
                    else:
                        processedImg2[:,lineID*10:lineID*10 + 10] = 0
                
                
                hsv = cv2.cvtColor(choppedImage,cv2.COLOR_RGB2HSV)
                hls = cv2.cvtColor(choppedImage,cv2.COLOR_RGB2HLS)
                luv = cv2.cvtColor(choppedImage,cv2.COLOR_RGB2LUV)
                lab = cv2.cvtColor(choppedImage,cv2.COLOR_RGB2LAB)
                stackedImg = np.block([
                    [choppedImage[:,:,0]],[choppedImage[:,:,1]],[choppedImage[:,:,2]],
                    [hsv[:,:,0]],[hsv[:,:,1]],[hsv[:,:,2]],
                    [hls[:,:,0]],[hls[:,:,1]],[hls[:,:,2]],
                    [luv[:,:,0]],[luv[:,:,1]],[luv[:,:,2]],
                    [lab[:,:,0]],[lab[:,:,1]],[lab[:,:,2]]
                    ])

                #cv2.imshow('image',stackedImg)
                #cv2.waitKey(0)

                shrinkedImage = cv2.resize(choppedImage[:,:,2],(100,1))[0]
                sum = 0 
                i = 0
                for i in range(100):
                    sum += shrinkedImage[i]
                    if shrinkedImage[i] < sum/(i+1):
                        sum = sum/(i+1)
                        break
                ret = i
                for j in range(i,100):
                    if shrinkedImage[j] > sum:
                        ret = j
                cost = ret /10
                
                if cost != last_cost:
                    
                    time_image = crop_image(input_image, mask_time_rect)
                    time_texts = ocr_image(time_image, None, 'en')
                    remain_time_text = format_time_string("".join(time_texts))
                    if(remain_time_text != ""):
                        s1 = remain_time_text.split(":")
                        if len(s1) == 2:
                            s2 = s1[1].split(".")
                            if len(s2) == 2:
                                time = float(s1[0]) * 60000 + float(s2[0])* 1000 + float(s2[1])
                                if time <= last_time:
                                    last_time = time
                                    Cost_Frame.append([last_cost,frame_id,time])
                                    last_cost = cost
                                    frame_id += 1
                                    continue
                    frame_id += 15
                    continue
                    
                frame_id += 1

    timer.print("End")
    
    with open('out.csv', 'w', newline='') as csvfile:
        spamwriter = csv.writer(csvfile)
        for row in Cost_Frame:
            spamwriter.writerow(row)
        
def plot():
    x = []
    y = []
    dydx = []
    smooth = []
    spike = []

    with open('out.csv', 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        
        for row in reader:
            
            x.append(float(row[2]))
            y.append(float(row[0]))
        dydx.append(0)
        for i in range(1,len(y)-1):
            dy = y[i-1]-y[i+1]
            dx = x[i-1]-x[i+1]
            if dx == 0:
                dx = 0.00001
            d = dy*1000/dx
            if(d < -1):
                spike.append(x[i])
            dydx.append(d)

        dydx.append(0)

        mode = stats.mode(dydx)
        #cdydx = np.clip(dydx,mode[0]-0.2,mode[0]+.2)

        #smooth = np.zeros(len(y))
        #for i in range (len(y)-2, 1, -1):
        #    smooth[i] = (y[i]+ y[i+1])/2
        #for j in range (0, 5):
        #    for i in range (len(y)-2, 1, -1):
        #        smooth[i] = (smooth[i]+ smooth[i+1])/2

    plot, axis = plt.subplots()
    #axis.plot(x,smooth,"g", linewidth=.5)
    axis.plot(x,dydx,"r", linewidth=.5)
    axis.plot(x,y,"b", linewidth=.5)
    axis.set(ylim=(-1,10))

    # プロット表示(設定の反映)
    plt.show()

#LoadVideo()
plot()