import cv2
import numpy as np
def CalculateCost(choppedImage,threshold:int, totalCost: int, DiffColor :np.matrix,threshold2: int):
    
    
    ddiff = abs(choppedImage.astype(int) - np.asarray(DiffColor).astype(int)).astype(np.uint8)
    ddiffc = abs(choppedImage.astype(int) - np.asarray((np.asarray([255,255,255]) - DiffColor) * 0.7 +DiffColor).astype(int)).astype(np.uint8)


    colsum = np.sum((np.max(np.min([ddiff,ddiffc],axis=0),axis=2) > threshold),axis = 0) < (20- threshold2)
    
    
    n = len(colsum)
    grace = int(np.ceil(n/100))
    id = n
    for i in range(n):
        
        start = max(0, i - grace)
        end = min(n, i + grace + 1)  # +1 to include i+units
        
        # Count the number of True values in the window
        count_true = sum(colsum[start:end])
        if count_true == 0:
            id = i
            break
                

    return np.round((id + 1) / (n / totalCost), 1)