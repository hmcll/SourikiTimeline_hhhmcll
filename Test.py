

import matplotlib.pyplot as plt
from scripts.debug_timer import DebugTimer
from moviepy import VideoFileClip
import cv2
from scripts.ocr_utils import crop_image, draw_image_line, draw_image_rect, draw_image_string, get_color_fill_percentage, get_image_bar_percentage,get_image_bar_percentage_hmcll, get_mask_image_rect, ocr_image
from scripts.common_utils import convert_safe_filename, load_memo, load_timeline, save_image, save_memo, save_timeline, str_to_time, time_to_str
import csv
import numpy as np

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
                
                movie_time = start_time + (frame_id / frame_rate)
                movie_time_text = time_to_str(movie_time)

#                print(f"progress movie... {movie_time_text} / {end_time_text}")

                frame = subclip.get_frame(frame_id/frame_rate)
                input_image = crop_image(frame, (movie_x, movie_y, movie_width, movie_height))
                
#                 cv2.imshow('image',input_image)
#                 cv2.waitKey(0)

                
#                if remain_time_text == "":
#                    frame_id += 15
#                    continue
#                percentTimer = DebugTimer()
#                percentTimer.start()
                
                x,y,w,h = get_cost_mask_rect()
                choppedImage = input_image[y:y+h, x:x+w]
                #choppedImage = cv2.resize(cv2.resize(choppedImage,(100,1)),(200,21))
                
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
    with open('out.csv', 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        
        for row in reader:
            x.append(float(row[2]))
            y.append(float(row[0]))
    plot, axis = plt.subplots()
    axis.plot(x,y)
    axis.set(ylim=(0,10))

    # プロット表示(設定の反映)
    plt.show()

#LoadVideo()
plot()