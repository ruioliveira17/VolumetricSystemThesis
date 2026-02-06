from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2

def volumeAPI(workspace_depth, minimum_depth, box_limits, depths, fx, fy, cx, cy, volumeMode, realVolumeMode):
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
    uidth = []
    eight = []
    realVolume = 0

    if volumeMode == "Bundle":
        for i in range((len(depths))):
            pts_flat = box_limits[i].reshape(-1,2)

            for (u,v) in pts_flat:
                X = (u - cx) * (depths[i] / 1000) / fx
                Y = (v - cy) * (depths[i] / 1000) / fy

                pts_m.append([X, Y])
                if realVolumeMode == "On":
                    obj_pts_m.append([X, Y])
            if realVolumeMode == "On":
                allObj_pts_m.append(obj_pts_m)
                obj_pts_m = []

        pts_m = numpy.array(pts_m, dtype=numpy.float32)

        if realVolumeMode == "On":
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
                if realVolumeMode == "On":
                    realVolume += volume

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

        if realVolumeMode == "On":
            volume = realVolume
        else:
            volume = width_meters * height_meters * ((workspace_depth - minimum_depth) / 1000)

    if volumeMode == "Singular":

        for i in range((len(depths))):
            pts_flat = box_limits[i].reshape(-1,2)

            for (u,v) in pts_flat:
                X = (u - cx) * (depths[i] / 1000) / fx
                Y = (v - cy) * (depths[i] / 1000) / fy

                obj_pts_m.append([X, Y])
            allObj_pts_m.append(obj_pts_m)
            obj_pts_m = []

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
            uidth.append(width_meters)
            eight.append(height_meters)
            bolume.append(volume)
            if realVolumeMode == "On":
                realVolume += volume


        volume = bolume
        width_meters = uidth
        height_meters = eight

    return volume, width_meters, height_meters