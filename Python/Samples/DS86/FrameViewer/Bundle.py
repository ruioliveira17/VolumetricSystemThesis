from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2

def bundle(hdrColor, hdrDepth_img, workspace_limits):

    w_pixels = 0
    h_pixels = 0
    largura = 0
    altura = 0

    workspace_area = hdrDepth_img[workspace_limits[1]:workspace_limits[3], workspace_limits[0]:workspace_limits[2]]

    grey = cv2.cvtColor(workspace_area, cv2.COLOR_BGR2GRAY)
    
    blur = cv2.GaussianBlur(grey, (5,5), 0)
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
            cv2.drawContours(hdrColor, [box + [workspace_limits[0], workspace_limits[1]]], 0,  (0, 0, 255), 2)

        else:
            x, y, largura, altura = cv2.boundingRect(all_points)
            cv2.rectangle(hdrColor, (workspace_limits[0] + x,  workspace_limits[1] + y), (workspace_limits[0] + x + largura, workspace_limits[1] + y + altura), (0, 0, 255), 2)
                  

    return w_pixels, h_pixels