import cv2
import numpy as np
def CalculateCost(choppedImage,threshold:int, totalCost: int, DiffColor :np.matrix,threshold2: int):
    
    choppedImage = cv2.resize(choppedImage, (400,15))
    
    #framediff = np.linalg.norm(choppedImage - DiffColor,axis=2) / 1.8

    #bluediff = np.abs(choppedImage[:,:,0] - DiffColor[0])

    #min = np.min([framediff, bluediff],axis= 0)

    #min = np.max(abs(choppedImage.astype(int) - np.asarray(DiffColor).astype(int)).astype(np.uint8),axis=2)

    ddiff = abs(choppedImage.astype(int) - np.asarray(DiffColor).astype(int)).astype(np.uint8)
    ddiffc = abs(choppedImage.astype(int) - np.asarray((np.asarray([255,255,255]) - DiffColor) * 0.5 +DiffColor).astype(int)).astype(np.uint8)
    min = np.min([ddiff,ddiffc],axis=0)
    max = np.max(min,axis=2)
    
    
    min = max

    
    # optimizable
    colsum = np.sum((min > threshold),axis = 0)
    
    id = 0
    
    while id <  400 - 3:
        
        if colsum[id] > threshold2 and colsum[id+1] > threshold2 and colsum[id+2] > threshold2 and colsum[id+3] > threshold2:
            break
        id += 1
                
                

    return np.round((id + 1) / (400 / totalCost), 1)