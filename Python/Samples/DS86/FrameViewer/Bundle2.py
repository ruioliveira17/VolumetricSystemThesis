from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2

def bundle(hdrColor, hdrDepth_img, objects_info):

    w_pixels = 0
    h_pixels = 0

    x1, y1, x2, y2 = objects_info[0]["workspace_limits"]
    workspace_area = hdrDepth_img[y1:y2, x1:x2]

    grey = cv2.cvtColor(workspace_area, cv2.COLOR_BGR2GRAY)
    
    blur = cv2.GaussianBlur(grey, (27,27), 0)
    cv2.imshow("Blur", blur)
    
    _, binary = cv2.threshold(blur, 140, 255, cv2.THRESH_BINARY)

    #if numpy.mean(binary) > 127:
    #    binary = cv2.bitwise_not(binary)

    cv2.imshow("binary", binary)

    element = numpy.ones((5, 5), numpy.uint8)
    morf = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, element)

    contour, _ = cv2.findContours(morf, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contour) > 0:
        all_points = numpy.vstack(contour)
        if len(contour) == 1:
            rect = cv2.minAreaRect(all_points)
            box = cv2.boxPoints(rect)
            box = numpy.round(box).astype(numpy.int32)

            w_pixels, h_pixels = rect[1]
            cv2.drawContours(hdrColor, [box + [x1, y1]], 0,  (0, 0, 255), 2)

        else:
            x, y, w_pixels, h_pixels = cv2.boundingRect(all_points)
            cv2.rectangle(hdrColor, (x1 + x,  y1 + y), (x1 + x + w_pixels, y1 + y + h_pixels), (0, 0, 255), 2)

    not_set = 1
    minimum_value = 6000
                    
    return w_pixels, h_pixels, minimum_value, not_set