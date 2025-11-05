from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2

def bundle(hdrColor, hdrDepth_img, workspace_limits):

    workspace_area = hdrDepth_img[workspace_limits[1]:workspace_limits[3], workspace_limits[0]:workspace_limits[2]]

    grey = cv2.cvtColor(workspace_area, cv2.COLOR_BGR2GRAY)
    
    blur = cv2.GaussianBlur(grey, (5,5), 0)
    
    _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    if numpy.mean(binary) > 127:
        binary = cv2.bitwise_not(binary)

    element = numpy.ones((5, 5), numpy.uint8)
    morf = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, element)

    contour, _ = cv2.findContours(morf, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contour) > 0:

        all_points = numpy.vstack(contour)

        x, y, largura, altura = cv2.boundingRect(all_points)

        cv2.rectangle(hdrColor, (workspace_limits[0] + x,  workspace_limits[1] + y), (workspace_limits[0] + x + largura, workspace_limits[1] + y + altura), (0, 0, 255), 2)