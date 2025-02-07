import cv2
import numpy as np
def calculateCost(choppedImage):
    choppedImage = cv2.resize(choppedImage,(200,20))
    
    threshold = 25
    
    # optimizable
    colsum = np.sum((choppedImage > threshold),axis = 0)
    
    
    id = 199
    while id >= 1:
        
        if colsum[id] < 10 and colsum[id-1] < 10:# and colsum[id-2] < 10:
            break
        id -= 1
                
                

    return np.round((id + 1) / 20, 1)