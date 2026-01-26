from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2

def volumeAPI(workspace_depth, minimum_depth, box_limits, depths, fx, fy):
    w_pixels = 0
    h_pixels = 0
    
    volume = 0
    width_meters = 0
    height_meters = 0
    i = 0

    vol = 0
    height = 0
    width = 0

    for i in range((len(depths))):
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

        wid = xmax - xmin
        hei = ymax - ymin

        if wid > hei:
            width_meters = w_pixels * (depths[i] / 1000.0) / fx
            print("Width:", width_meters, "Width Pixels:", w_pixels)
            height_meters = h_pixels * (depths[i]  / 1000.0) / fy
            print("Height:", height_meters, "Height Pixels:", h_pixels)
        if hei > wid:
            width_meters = h_pixels * (depths[i]  / 1000.0) / fx
            print("Width:", width_meters, "Width Pixels:", h_pixels)
            height_meters = w_pixels * (depths[i]  / 1000.0) / fy
            print("Height:", height_meters, "Height Pixels:", w_pixels)

        if width_meters < 0:
            width_meters = 0

        if height_meters < 0:
            height_meters = 0

        volume = width_meters * height_meters * ((workspace_depth - minimum_depth) / 1000)
        vol += volume
        width += width_meters
        height += height_meters

    return vol, width, height