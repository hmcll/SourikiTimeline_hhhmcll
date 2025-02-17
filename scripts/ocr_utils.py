import cv2
import numpy as np
def calculateCost(choppedImage, totalCost: int, DiffColor :np.matrix):
    
    choppedImage = cv2.resize(choppedImage, 200,20)
    
    framediff = np.linalg.norm(choppedImage - DiffColor,axis=2) / 1.8

    bluediff = np.abs(choppedImage[:,:,0] - DiffColor[0])

    min = np.min([framediff, bluediff],axis= 0)
    
    threshold = 25
    
    # optimizable
    colsum = np.sum((min > threshold),axis = 0)
    
    
    id = 200 - 1
    while id >= 1:
        
        if colsum[id] < 10 and colsum[id-1] < 10:# and colsum[id-2] < 10:
            break
        id -= 1
                
                

    return np.round((id + 1) / (20), 1)