from pickle import FALSE, TRUE
import sys
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "Python"))

from API.VzenseDS_api import *
import cv2
import numpy
from FrameState import frameState

def volumeBundleAPI(depthFrame, workspace_depth, minimum_depth, box_limits, depths, fx_d, fy_d, cx_d, cy_d): 
    volume = 0
    width_meters = 0
    height_meters = 0
    i = 0

    pts_m = []

    for i in range((len(depths))):
        pts_flat = box_limits[i].reshape(-1,2)
        rect_px = cv2.minAreaRect(pts_flat.astype(numpy.float32))
        box_px = cv2.boxPoints(rect_px)
        #Z = (depths[i] / 1000)
        cv2.drawContours(frameState.colorToDepthFrame, [numpy.int32(box_px)], 0, (0, 255, 0), 2)
        cv2.imwrite(f"colorToDepthFrame{i}.png", frameState.colorToDepthFrame)

        for (u,v) in pts_flat:
            #Z_radial = depthFrame[int(v), int(u)] / 1000
            Z = depthFrame[int(v), int(u)] / 1000
            #if Z_radial <= 0 or Z_radial >= workspace_depth:  # ignora píxeis sem profundidade válida
            if Z <= 0 or Z >= workspace_depth:
                X = 0
                Y = 0
            else:
                #Z = Z_radial / numpy.sqrt(1 + ((u - cx_d) / fx_d)**2 + ((v - cy_d) / fy_d)**2)
                X = (u - cx_d) * Z / fx_d
                Y = (v - cy_d) * Z / fy_d

            pts_m.append([X, Y])

    pts_m = numpy.array(pts_m, dtype=numpy.float32)

    rect_m = cv2.minAreaRect(pts_m)
    width_meters, height_meters = rect_m[1]

    #if width_meters < height_meters:
    #    width_meters, height_meters = height_meters, width_meters

    #xmin = pts_m[:,0].min()
    #xmax = pts_m[:,0].max()
    #ymin = pts_m[:,1].min()
    #ymax = pts_m[:,1].max()

    #if xmin < 0:
    #    wid = xmax + abs(xmin)
    #else:
    #    wid = xmax - abs(xmin)
    #if ymin < 0:
    #    hei = ymax + abs(ymin)
    #else:
    #    hei = ymax - abs(ymin)

    #if hei > wid:
    #    height_meters, width_meters = width_meters, height_meters

    volume = width_meters * height_meters * ((workspace_depth - minimum_depth) / 1000)

    return volume, width_meters, height_meters

def volumeRealAPI(depthFrame, workspace_depth, box_limits, depths, fx_d, fy_d, cx_d, cy_d): 
    volume = 0
    width_meters = 0
    height_meters = 0
    i = 0

    obj_pts_m = []
    allObj_pts_m = []
    bolume = []
    uidth = []
    eight = []
    totalVolume = 0

    for i in range((len(depths))):
        pts_flat = box_limits[i].reshape(-1,2)
        rect_px = cv2.minAreaRect(pts_flat.astype(numpy.float32))
        box_px = cv2.boxPoints(rect_px)
        cv2.drawContours(frameState.colorToDepthFrame, [numpy.int32(box_px)], 0, (0, 255, 0), 2)
        cv2.imwrite(f"colorToDepthFrame{i}.png", frameState.colorToDepthFrame)

        #Z_mean = depths[i] / 1000

        for (u,v) in pts_flat:
            Z_radial = depthFrame[int(v), int(u)] / 1000
            if Z_radial <= 0 or Z_radial >= workspace_depth:
                X = 0
                Y = 0
            else:
                Z = Z_radial / numpy.sqrt(1 + ((u - cx_d) / fx_d)**2 + ((v - cy_d) / fy_d)**2)

                X = (u - cx_d) * Z / fx_d
                Y = (v - cy_d) * Z / fy_d
                obj_pts_m.append([X, Y])

        allObj_pts_m.append(obj_pts_m)
        obj_pts_m = []

    for idx, obj in enumerate(allObj_pts_m):
        allObj_pts_m[idx] = numpy.array(obj, dtype=numpy.float32)
        #print(f"Objeto {idx} — pontos em metros: {allObj_pts_m[idx]}")
        rect_m = cv2.minAreaRect(allObj_pts_m[idx])
        width_meters, height_meters = rect_m[1]
        #print(f"Width: {width_meters:.4f}m ({width_meters*100:.2f}cm)")
        #print(f"Height: {height_meters:.4f}m ({height_meters*100:.2f}cm)")
        #print(f"Z usado (depths[{idx}]): {depths[idx]}mm")

        #if width_meters < height_meters:
        #    width_meters, height_meters = height_meters, width_meters

        #xmin = allObj_pts_m[idx][:,0].min()
        #xmax = allObj_pts_m[idx][:,0].max()
        #ymin = allObj_pts_m[idx][:,1].min()
        #ymax = allObj_pts_m[idx][:,1].max()

        #if xmin < 0:
        #    wid = xmax + abs(xmin)
        #else:
        #    wid = xmax - abs(xmin)
        #if ymin < 0:
        #    hei = ymax + abs(ymin)
        #else:
        #    hei = ymax - abs(ymin)

        #if hei > wid:
        #    height_meters, width_meters = width_meters, height_meters

        volume = width_meters * height_meters * ((workspace_depth - depths[idx]) / 1000)
        uidth.append(width_meters)
        eight.append(height_meters)
        bolume.append(volume)
        #if realVolumeMode == "On":
        totalVolume += volume

    bolume.append(totalVolume)
    volume = bolume
    width_meters = uidth
    height_meters = eight

    return volume, width_meters, height_meters