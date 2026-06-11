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
    length_meters = 0
    i = 0

    pts_m = []

    print("Depths Len:", len(depths))
    print("Box Limits Len:", len(box_limits))

    MIN_OBJ_HEIGHT_MM = 30
    for i in range((len(depths))):
        obj_height_mm = workspace_depth - depths[i]
        if obj_height_mm < MIN_OBJ_HEIGHT_MM:
            print("Skipping ghost object", i, ": height", obj_height_mm, "mm")
            continue
        pts_flat = box_limits[i].reshape(-1,2)
        rect_px = cv2.minAreaRect(pts_flat.astype(numpy.float32))
        box_px = cv2.boxPoints(rect_px)
        #Z = (depths[i] / 1000)
        cv2.drawContours(frameState.colorToDepthFrame, [numpy.int32(box_px)], 0, (0, 255, 0), 2)
        cv2.imwrite(f"colorToDepthFrame{i}.png", frameState.colorToDepthFrame)

        DEPTH_TOL_MM = 40
        for (u,v) in pts_flat:
            #Z_radial = depthFrame[int(v), int(u)] / 1000
            Z_mm = depthFrame[int(v), int(u)]
            #if Z_radial <= 0 or Z_radial >= workspace_depth:  # ignora píxeis sem profundidade válida
            if Z_mm <= 0 or Z_mm >= workspace_depth:
                continue
            if abs(Z_mm - depths[i]) > DEPTH_TOL_MM:
                continue
            #Z = Z_radial / numpy.sqrt(1 + ((u - cx_d) / fx_d)**2 + ((v - cy_d) / fy_d)**2)
            Z = Z_mm / 1000
            X = (u - cx_d) * Z / fx_d
            Y = (v - cy_d) * Z / fy_d

            pts_m.append([X, Y])

    pts_m = numpy.array(pts_m, dtype=numpy.float32)

    rect_m = cv2.minAreaRect(pts_m)
    width_meters, length_meters = rect_m[1]
    height_meters = (workspace_depth - minimum_depth) / 1000

    #if width_meters < length_meters:
    #    width_meters, length_meters = length_meters, width_meters

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
    #    length_meters, width_meters = width_meters, length_meters

    volume = width_meters * length_meters * height_meters

    return volume, width_meters, length_meters, height_meters

def volumeRealAPI(depthFrame, calibrationDepthFrame, workspace_depth, box_limits, depths, fx_d, fy_d, cx_d, cy_d): 
    MIN_OBJ_HEIGHT_MM = 30

    volume = 0
    width_meters = 0
    length_meters = 0
    height_meters = 0
    i = 0

    allObj_pts_m = []
    bolume = []
    uidth = []
    ength = []
    eight = []
    totalVolume = 0

    calibrationDepthFrame_copy = calibrationDepthFrame.copy()
    
    print("Depths Len:", len(depths))
    print("Box Limits Len:", len(box_limits))

    for i in range((len(depths))):
        pts_flat = box_limits[i].reshape(-1,2)

        mask = numpy.zeros(calibrationDepthFrame_copy.shape, dtype=numpy.uint8)
        cv2.fillPoly(mask, [pts_flat.astype(numpy.int32)], 255)
        ws_values = calibrationDepthFrame_copy[mask == 255].astype(numpy.float32)
        ws_values = ws_values[(ws_values >= 150) & (ws_values < workspace_depth + 15)]
        ws_depth = numpy.median(ws_values)
        print("Workspace Depth:", ws_depth)

        obj_height_mm = workspace_depth - depths[i]
        if obj_height_mm < MIN_OBJ_HEIGHT_MM:
            print("Skipping ghost object", i, ": height", obj_height_mm, "mm")
            continue

        fill_img = numpy.zeros((480, 640), dtype=numpy.uint8)
        cv2.fillPoly(fill_img, [pts_flat.astype(numpy.int32)], 255)

        rect_px = cv2.minAreaRect(pts_flat.astype(numpy.float32))
        box_px = cv2.boxPoints(rect_px)
        cv2.drawContours(frameState.colorToDepthFrame, [numpy.int32(box_px)], 0, (0, 255, 0), 2)
        cv2.imwrite(f"colorToDepthFrame{i}.png", frameState.colorToDepthFrame)

        #ws_values = calibrationDepthFrame[mask == 255].astype(numpy.float32)
        #ws_values = ws_values[(ws_values >= 150) & (ws_values < workspace_depth + 15)]
        #ws_depth = numpy.mean(ws_values)

        ys_all, xs_all = numpy.where(fill_img > 0)
        if len(xs_all) == 0 or len(ys_all) == 0:
            continue

        DEPTH_TOL_MM = 40
        zs_all = depthFrame[ys_all, xs_all].astype(numpy.float32)
        valid = (zs_all > 0) & (zs_all < workspace_depth) & (numpy.abs(zs_all - depths[i]) <= DEPTH_TOL_MM)
        xs_v, ys_v, zs_v = xs_all[valid], ys_all[valid], zs_all[valid]

        Z = zs_v / 1000.0
        X = (xs_v - cx_d) * Z / fx_d
        Y = (ys_v - cy_d) * Z / fy_d
        allObj_pts_m.append(numpy.column_stack([X, Y]).tolist())

    for idx, obj in enumerate(allObj_pts_m):
        allObj_pts_m[idx] = numpy.array(obj, dtype=numpy.float32)
        rect_m = cv2.minAreaRect(allObj_pts_m[idx])
        width_meters, length_meters = rect_m[1]
        if width_meters > length_meters:
            width_meters, length_meters = length_meters, width_meters

        pts_flat_h = box_limits[idx].reshape(-1, 2)
        mask_h = numpy.zeros(calibrationDepthFrame_copy.shape, dtype=numpy.uint8)
        cv2.fillPoly(mask_h, [pts_flat_h.astype(numpy.int32)], 255)
        ws_vals_h = calibrationDepthFrame_copy[mask_h == 255].astype(numpy.float32)
        ws_vals_h = ws_vals_h[(ws_vals_h >= 150) & (ws_vals_h <= workspace_depth + 15)]
        ws_d_h = float(numpy.median(ws_vals_h)) if ws_vals_h.size > 0 else float(workspace_depth)
        height_meters = (ws_d_h - depths[idx]) / 1000

        print("Verifying object ")
        for j in range(idx + 1, len(allObj_pts_m)):
            if isInside(box_limits[idx], box_limits[j]):
                print("Inside")
                height_meters = (depths[j] - depths[idx]) / 1000
                break

        volume = width_meters * length_meters * height_meters
        uidth.append(width_meters)
        ength.append(length_meters)
        eight.append(height_meters)
        bolume.append(volume)
        totalVolume += volume

    bolume.append(totalVolume)
    volume = bolume
    width_meters = uidth
    length_meters = ength
    height_meters = eight

    return volume, width_meters, length_meters, height_meters

def isInside(box1, box2):
    box1 = box1.reshape(-1, 2).astype(numpy.float32)
    box2 = to_hull(box2)
    inside = 0

    for (u, v) in box1:
        if cv2.pointPolygonTest(box2, (u, v), False) >= 0:
            inside += 1

    result = inside / len(box1)
    
    if result > 0.15:
        return True
    else:
        return False
    
def to_hull(points):
    points = numpy.array(points, dtype=numpy.float32)
    hull = cv2.convexHull(points)
    return hull