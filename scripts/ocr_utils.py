import cv2
import numpy as np
def CalculateCost(choppedImage,threshold:int, totalCost: int, DiffColor :np.matrix,threshold2: int):
    
    choppedImage = cv2.resize(choppedImage, (400,15))
    
    ddiff = abs(choppedImage.astype(int) - np.asarray(DiffColor).astype(int)).astype(np.uint8)
    ddiffc = abs(choppedImage.astype(int) - np.asarray((np.asarray([255,255,255]) - DiffColor) * 0.5 +DiffColor).astype(int)).astype(np.uint8)


    # optimizable
    colsum = np.sum((np.max(np.min([ddiff,ddiffc],axis=0),axis=2) > threshold),axis = 0) < threshold2
    
    id = 0
    n = len(colsum)
    for i in range(n):
        
        start = max(0, i - 3)
        end = min(n, i + 3 + 1)  # +1 to include i+units
        
        # Count the number of True values in the window
        count_true = sum(colsum[start:end])
        if count_true < 2:
            id = i
            break
                

    return np.round((id + 1) / (400 / totalCost), 1)