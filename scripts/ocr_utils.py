import cv2
import numpy as np
def calculateCost(choppedImage,threshold:int, totalCost: int, DiffColor :np.matrix):
    
    choppedImage = cv2.resize(choppedImage, (400,15))
    
    framediff = np.linalg.norm(choppedImage - DiffColor,axis=2) / 1.8

    bluediff = np.abs(choppedImage[:,:,0] - DiffColor[0])

    min = np.min([framediff, bluediff],axis= 0)

    min = np.max(abs(choppedImage.astype(int) - np.asarray(DiffColor).astype(int)).astype(np.uint8),axis=2)

    ddiff = abs(choppedImage.astype(int) - np.asarray(DiffColor).astype(int)).astype(np.uint8)
    ddiffc = abs(choppedImage.astype(int) - np.asarray((np.asarray([255,255,255]) - DiffColor) * 0.7 +DiffColor).astype(int)).astype(np.uint8)
    min = np.min([ddiff,ddiffc],axis=0)
    max = np.max(min,axis=2)
    
    
    min = max

    
    # optimizable
    colsum = np.sum((min > threshold),axis = 0)
    
    
    id = 400 - 1
    while id >= 1:
        
        if colsum[id] < 10 and colsum[id-1] < 10 and colsum[id-2] < 10 and colsum[id-3] < 10:
            break
        id -= 1
                
                

    return np.round((id + 1) / (800 / totalCost), 1)