import cv2
import numpy as np
def calculateCost(choppedImage):
    
    choppedImage = cv2.resize(choppedImage,(200,20))
    
    framediff = np.linalg.norm(choppedImage - [243,222,68],axis=2) / 1.8

    bluediff = np.abs(choppedImage[:,:,0] - 243)

    min = np.min([framediff, bluediff],axis= 0)
    
    threshold = 25
    
    # optimizable
    colsum = np.sum((min > threshold),axis = 0)
    
    
    id = 199
    while id >= 1:
        
        if colsum[id] < 10 and colsum[id-1] < 10:# and colsum[id-2] < 10:
            break
        id -= 1
                
                

    return np.round((id + 1) / 20, 1)