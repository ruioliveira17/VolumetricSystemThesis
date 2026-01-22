from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2
from FrameState import frameState

def depthImg(hdrDepth, colorSlope):
    img = numpy.int32(hdrDepth)
    img = img*255/colorSlope
    img = numpy.clip(img, 0, 255)
    img = numpy.uint8(img)
    depth_img = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)

    return depth_img

def bundle(hdrColor, hdrDepth_img, objects_info, threshold, hdrDepth):

    w_pixels = 0
    h_pixels = 0

    contours = []
    ws_limits = []
    all_points_list = []
    shifted_contours = 0

    if len(objects_info) != 0:
        for obj in objects_info:

            x1, y1, x2, y2 = obj["workspace_limits"]
            workspace_area2 = hdrDepth[y1:y2, x1:x2]

            mask = (workspace_area2 >= (obj["depth"] - threshold)) & (workspace_area2 <= (obj["depth"] + threshold))

            depth_filtered = numpy.where(mask, workspace_area2, 0).astype(numpy.uint16)

            img = numpy.int32(depth_filtered)
            img = img*255/1500
            img = numpy.clip(img, 0, 255)
            img = numpy.uint8(img)
            hdrDepth_img = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)

            gray = cv2.cvtColor(hdrDepth_img, cv2.COLOR_BGR2GRAY)
        
            blur = cv2.GaussianBlur(gray, (15,15), 0)
            
            _, binary = cv2.threshold(blur, 140, 255, cv2.THRESH_BINARY)

            invBinary = cv2.bitwise_not(binary)

            element = numpy.ones((3, 3), numpy.uint8)
            morf = cv2.morphologyEx(invBinary, cv2.MORPH_GRADIENT, element)

            contour, _ = cv2.findContours(morf, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            shifted_contours = [c + numpy.array([[[x1, y1]]], dtype=numpy.int32) for c in contour]

            contours.append(shifted_contours)
            ws_limits.append(obj["workspace_limits"])

    hdrColor_copy = hdrColor.copy()
    hdrColor_copy = cv2.resize(hdrColor_copy, (640, 480))

    for contour_list in contours:
        for c in contour_list:
            rect = cv2.minAreaRect(c)
            box = cv2.boxPoints(rect)
            box = numpy.round(box).astype(numpy.int32)
            cv2.drawContours(hdrColor_copy, [box], 0, (0, 255, 0), 2)
            frameState.colorToDepthFrameObject = hdrColor_copy

    all_points_list = [c for contour_list in contours for c in contour_list if c.size > 0]

    hdrColor_copy = hdrColor.copy()
    hdrColor_copy = cv2.resize(hdrColor_copy, (640, 480))

    if len(all_points_list) > 0:
        all_points = numpy.vstack(all_points_list)

        rect = cv2.minAreaRect(all_points)
        box = cv2.boxPoints(rect)
        box = numpy.round(box).astype(numpy.int32)

        w_pixels, h_pixels = rect[1]
        if w_pixels < h_pixels:
            w_pixels, h_pixels = h_pixels, w_pixels

        cv2.drawContours(hdrColor_copy, [box], 0,  (0, 255, 0), 2)
        frameState.colorToDepthFrameObjects = hdrColor_copy
        print("Width:", w_pixels)
        print("Heigth:", h_pixels)
        print("FESTAAAAAAA")

    not_set = 1
    minimum_value = 6000
                    
    return w_pixels, h_pixels, minimum_value, not_set, all_points, ws_limits