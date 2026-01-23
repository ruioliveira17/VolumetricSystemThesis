from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2

def volumeAPI(workspace_depth, minimum_depth, box_limits, objects_info, fx, fy):
    w_pixels = 0
    h_pixels = 0
    
    volume = 0
    width_meters = 0
    height_meters = 0
    i = 0

    for i in range((len(objects_info))):
        all_points = numpy.vstack(box_limits[i])

        rect = cv2.minAreaRect(all_points)
        box = cv2.boxPoints(rect)
        box = numpy.round(box).astype(numpy.int32)

        w_pixels, h_pixels = rect[1]
        if w_pixels < h_pixels:
            w_pixels, h_pixels = h_pixels, w_pixels

        print("Width:", w_pixels)
        print("Heigth:", h_pixels)

        pts_flat = box_limits[i].reshape(-1,2)

        xmin = pts_flat[:,0].min()
        xmax = pts_flat[:,0].max()
        ymin = pts_flat[:,1].min()
        ymax = pts_flat[:,1].max()

    #xs = box_limits[:, 0, 0]
    #ys = box_limits[:, 0, 1]

    #xmin = xs.min()
    #xmax = xs.max()
    #ymin = ys.min()
    #ymax = ys.max()

        wid = xmax - xmin
        hei = ymax - ymin

    #if box_ws is not None and len(box_ws) > 0:
        #print(len(box_ws))
        #while i < len(box_ws):
            #ws_lim = box_ws[i]
        if wid > hei:
            width_meters = w_pixels * (objects_info[i]["depth"] / 1000.0) / fx
            print("Width:", width_meters, "Width Pixels:", w_pixels)
            height_meters = h_pixels * (objects_info[i]["depth"]  / 1000.0) / fy
            print("Height:", height_meters, "Height Pixels:", h_pixels)
        if hei > wid:
            width_meters = h_pixels * (objects_info[i]["depth"]  / 1000.0) / fx
            print("Width:", width_meters, "Width Pixels:", h_pixels)
            height_meters = w_pixels * (objects_info[i]["depth"]  / 1000.0) / fy
            print("Height:", height_meters, "Height Pixels:", w_pixels)
            #i += 1
        #i = 0

        if width_meters < 0:
            width_meters = 0

        if height_meters < 0:
            height_meters = 0

        volume = width_meters * height_meters * ((workspace_depth - minimum_depth) / 1000)

    return volume, width_meters, height_meters, minimum_depth