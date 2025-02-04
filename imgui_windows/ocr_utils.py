import cv2
import numpy as np
def calculateCost(choppedImage):
    choppedImage = cv2.resize(choppedImage,(200,20))
    
    
    processedImg = np.floor(choppedImage /20).astype('uint8')*20
    

    sum = 256/2

    colsum = np.sum((choppedImage > sum),axis = 0)
    
    endID = 20
    for blockID in range(20):
        BlockSum = 0
        for lineID in range(10):
            if colsum[lineID + blockID * 10] > 16:
                BlockSum += 1
        if BlockSum == 0:
            endID = (blockID + 1)*10
            break
    cost = 0
    for lineID in range(endID-1,0,-1):
        if colsum[lineID] > 16:
            cost = lineID / 200
            break
    return np.round(cost * 10, 1)