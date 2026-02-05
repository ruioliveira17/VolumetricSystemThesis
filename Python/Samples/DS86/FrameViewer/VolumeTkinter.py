from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2

def volumeAPI(workspace_depth, minimum_depth, box_limits, depths, fx, fy, cx, cy):
    #w_pixels = 0
    #h_pixels = 0
    
    volume = 0
    width_meters = 0
    height_meters = 0
    i = 0

    #vol = 0
    #height = 0
    #width = 0

    pts_m = []
    obj_pts_m = []
    allObj_pts_m = []
    bolume = []
    realVolume = 0

    for i in range((len(depths))):
        pts_flat = box_limits[i].reshape(-1,2)

        for (u,v) in pts_flat:
            X = (u - cx) * (depths[i] / 1000) / fx
            Y = (v - cy) * (depths[i] / 1000) / fy

            pts_m.append([X, Y])
            obj_pts_m.append([X, Y])
        allObj_pts_m.append(obj_pts_m)
        obj_pts_m = []

    pts_m = numpy.array(pts_m, dtype=numpy.float32)
    #allObj_pts_m = [numpy.array(obj, dtype=numpy.float32) for obj in allObj_pts_m]

    for idx, obj in enumerate(allObj_pts_m):
        allObj_pts_m[idx] = numpy.array(obj, dtype=numpy.float32)
        rect_m = cv2.minAreaRect(allObj_pts_m[idx])
        width_meters, height_meters = rect_m[1]

        if width_meters < height_meters:
            width_meters, height_meters = height_meters, width_meters

        xmin = allObj_pts_m[idx][:,0].min()
        xmax = allObj_pts_m[idx][:,0].max()
        ymin = allObj_pts_m[idx][:,1].min()
        ymax = allObj_pts_m[idx][:,1].max()

        wid = xmax + abs(xmin)
        hei = ymax + abs(ymin)

        if hei > wid:
            height_meters, width_meters = width_meters, height_meters

        volume = width_meters * height_meters * ((workspace_depth - depths[idx]) / 1000)
        bolume.append(volume)
        realVolume += volume

    print(bolume)
    print(realVolume)

    rect_m = cv2.minAreaRect(pts_m)
    width_meters, height_meters = rect_m[1]

    if width_meters < height_meters:
        width_meters, height_meters = height_meters, width_meters

    xmin = pts_m[:,0].min()
    xmax = pts_m[:,0].max()
    ymin = pts_m[:,1].min()
    ymax = pts_m[:,1].max()

    wid = xmax + abs(xmin)
    hei = ymax + abs(ymin)

    if hei > wid:
        height_meters, width_meters = width_meters, height_meters

    volume = width_meters * height_meters * ((workspace_depth - minimum_depth) / 1000)

    #for i in range((len(depths))):

        #all_points = numpy.vstack(box_limits[i])

        #rect = cv2.minAreaRect(all_points)
        #box = cv2.boxPoints(rect)
        #box = numpy.round(box).astype(numpy.int32)

        #w_pixels, h_pixels = rect[1]
        #if w_pixels < h_pixels:
        #    w_pixels, h_pixels = h_pixels, w_pixels

        #print("Width:", w_pixels)
        #print("Heigth:", h_pixels)

        #pts_flat = box_limits[i].reshape(-1,2)

        #xmin = pts_flat[:,0].min()
        #xmax = pts_flat[:,0].max()
        #ymin = pts_flat[:,1].min()
        #ymax = pts_flat[:,1].max()

        #wid = xmax - xmin
        #hei = ymax - ymin

        #if wid > hei:
        #    width_meters = w_pixels * (depths[i] / 1000.0) / fx
        #    print("Width:", width_meters, "Width Pixels:", w_pixels)
        #    height_meters = h_pixels * (depths[i]  / 1000.0) / fy
        #    print("Height:", height_meters, "Height Pixels:", h_pixels)
        #if hei > wid:
        #    width_meters = h_pixels * (depths[i]  / 1000.0) / fx
        #    print("Width:", width_meters, "Width Pixels:", h_pixels)
        #    height_meters = w_pixels * (depths[i]  / 1000.0) / fy
        #    print("Height:", height_meters, "Height Pixels:", w_pixels)

        #if width_meters < 0:
        #    width_meters = 0

        #if height_meters < 0:
        #    height_meters = 0

        #volume = width_meters * height_meters * ((workspace_depth - minimum_depth) / 1000)
        #vol += volume
        #width += width_meters
        #height += height_meters

    return volume, width_meters, height_meters