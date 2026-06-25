from pickle import FALSE, TRUE
import sys
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "Python"))

from API.VzenseDS_api import *
import cv2
import numpy
from FrameState import frameState

OVERLAP_RATIO = 0.05

i = None

def volumeSingleBundleAPI(depthFrame, workspace_depth, minimum_depth, box_limits, depths, fx_d, fy_d, cx_d, cy_d): 
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
        cv2.drawContours(frameState.colorToDepthFrame, [numpy.int32(box_px)], 0, (0, 255, 0), 2)
        cv2.imwrite(f"colorToDepthFrame{i}.png", frameState.colorToDepthFrame)

        DEPTH_TOL_MM = 40
        for (u,v) in pts_flat:
            Z_mm = depthFrame[int(v), int(u)]
            if Z_mm <= 0 or Z_mm >= workspace_depth:
                continue
            if abs(Z_mm - depths[i]) > DEPTH_TOL_MM:
                continue
            Z = Z_mm / 1000
            X = (u - cx_d) * Z / fx_d
            Y = (v - cy_d) * Z / fy_d

            pts_m.append([X, Y])

    pts_m = numpy.array(pts_m, dtype=numpy.float32)

    rect_m = cv2.minAreaRect(pts_m)
    width_meters, length_meters = rect_m[1]
    height_meters = (workspace_depth - minimum_depth) / 1000

    volume = width_meters * length_meters * height_meters

    return volume, width_meters, length_meters, height_meters

def volumeMultiBundleAPI(depthFrame, calibrationDepthFrame, workspace_depth, box_limits, depths, fx_d, fy_d, cx_d, cy_d): 
    volume = 0
    width_meters = 0
    length_meters = 0
    i = 0

    allObj_pts_m = []
    bolume = []
    uidth = []
    ength = []
    eight = []
    totalVolume = 0

    pts_m = []
    groups = []
    used = set()
    depthsObj = []

    MIN_OBJ_HEIGHT_MM = 30

    calibrationDepthFrame_copy = calibrationDepthFrame.copy()

    print("Box Limits Len:", len(box_limits))

    for i in range(len(box_limits)):
        if i in used:
            continue

        stack = [i]
        group = []

        while stack:
            idx = stack.pop()

            if idx in used:
                continue

            used.add(idx)
            group.append((box_limits[idx], depths[idx]))

            for j in range(len(box_limits)):
                if j in used:
                    continue

                box_i = cv2.boxPoints(cv2.minAreaRect(box_limits[idx]))
                box_j = cv2.boxPoints(cv2.minAreaRect(box_limits[j]))

                if overlap_ratio(box_i, box_j) > OVERLAP_RATIO or intersection_edge(box_i, box_j, depthFrame):
                    stack.append(j)

        groups.append(group)

    print("Number of groups:", len(groups))

    for i in range((len(groups))):
        objPoints = []
        group = groups[i]
        min_depth = min(depth for _, depth in group)
        obj_height_mm = workspace_depth - min_depth
        if obj_height_mm < MIN_OBJ_HEIGHT_MM:
            print("Skipping ghost object", i, ": height", obj_height_mm, "mm")
            continue
         
        for contour, depth in group:
            fill_img = numpy.zeros((480, 640), dtype=numpy.uint8)
            cv2.fillPoly(fill_img, [contour.astype(numpy.int32)], 255)

            ys_all, xs_all = numpy.where(fill_img > 0)
            if len(xs_all) == 0 or len(ys_all) == 0:
                continue

            DEPTH_TOL_MM = 40
            zs_all = depthFrame[ys_all, xs_all].astype(numpy.float32)
            valid = (zs_all > 0) & (zs_all < workspace_depth) & (numpy.abs(zs_all - depth) <= DEPTH_TOL_MM)
            xs_v, ys_v, zs_v = xs_all[valid], ys_all[valid], zs_all[valid]

            Z = zs_v / 1000.0
            X = (xs_v - cx_d) * Z / fx_d
            Y = (ys_v - cy_d) * Z / fy_d

            objPoints.extend(numpy.column_stack([X,Y]))

        all_points = numpy.vstack([contour for contour, _ in group])
        pts_flat = all_points.reshape(-1,2)

        rect_px = cv2.minAreaRect(pts_flat.astype(numpy.float32))
        box_px = cv2.boxPoints(rect_px)
        cv2.drawContours(frameState.colorToDepthFrame, [numpy.int32(box_px)], 0, (0, 255, 0), 2)
        cv2.imwrite(f"colorToDepthFrame{i}.png", frameState.colorToDepthFrame)

        allObj_pts_m.append(objPoints)
        depthsObj.append(min_depth)
      
    for idx, obj in enumerate(allObj_pts_m):
        allObj_pts_m = [numpy.array(obj, dtype=numpy.float32) for obj in allObj_pts_m]
        rect_m = cv2.minAreaRect(allObj_pts_m[idx])
        width_meters, length_meters = rect_m[1]

        pts_flat_h = allObj_pts_m[idx].reshape(-1, 2)
        mask_h = numpy.zeros(calibrationDepthFrame_copy.shape, dtype=numpy.uint8)
        cv2.fillPoly(mask_h, [pts_flat_h.astype(numpy.int32)], 255)
        ws_vals_h = calibrationDepthFrame_copy[mask_h == 255].astype(numpy.float32)
        ws_vals_h = ws_vals_h[(ws_vals_h >= 150) & (ws_vals_h <= workspace_depth + 15)]
        ws_d_h = float(numpy.median(ws_vals_h)) if ws_vals_h.size > 0 else float(workspace_depth)
        height_meters = (ws_d_h - depthsObj[idx]) / 1000

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

    print("Volume:", volume)

    return volume, width_meters, length_meters, height_meters

def volumeRealAPI(depthFrame, calibrationDepthFrame, workspace_depth, box_limits, depths, fx_d, fy_d, cx_d, cy_d): 
    volume = 0
    width_meters = 0
    length_meters = 0
    i = 0

    groupWidths= []
    groupLengths = []
    groupHeights = []
    groupHeightsOverlapped = []
    groupAngles = []
    groupRealVolume = []

    bolume = []
    uidth = []
    ength = []
    eight = []
    totalVolume = 0

    allDepths = []

    pts_m = []
    allGroupsObjPoints = []
    allObjCenter = []
    groups = []
    used = set()

    MIN_OBJ_HEIGHT_MM = 30

    calibrationDepthFrame_copy = calibrationDepthFrame.copy()
    colorToDepthFrameX = frameState.colorToDepthFrame.copy()

    print("Box Limits Len:", len(box_limits))

    for i in range(len(box_limits)):
        if i in used:
            continue

        stack = [i]
        group = []

        while stack:
            idx = stack.pop()

            if idx in used:
                continue

            used.add(idx)
            group.append((box_limits[idx], depths[idx]))

            for j in range(len(box_limits)):
                if j in used:
                    continue

                box_i = cv2.boxPoints(cv2.minAreaRect(box_limits[idx]))
                box_j = cv2.boxPoints(cv2.minAreaRect(box_limits[j]))

                if overlap_ratio(box_i, box_j) > OVERLAP_RATIO or intersection_edge(box_i, box_j, depthFrame):
                    stack.append(j)

        groups.append(group)

    print("Number of groups:", len(groups))
    
    print("Depths Len:", len(depths))
    print("Box Limits Len:", len(box_limits))

    for i in range((len(groups))):
        objPoints = []
        allObj_pts_m = []
        depthsObj = []
        objCenter = []
        irregularGroup = []
        group = groups[i]
        group.sort(key=lambda x: x[1], reverse=False)
        min_depth = min(depth for _, depth in group)
        obj_height_mm = workspace_depth - min_depth
        if obj_height_mm < MIN_OBJ_HEIGHT_MM:
            print("Skipping ghost object", i, ": height", obj_height_mm, "mm")
            continue

        for contour, depth in group:
            fill_img = numpy.zeros((480, 640), dtype=numpy.uint8)
            cv2.fillPoly(fill_img, [contour.astype(numpy.int32)], 255)

            ys_all, xs_all = numpy.where(fill_img > 0)
            if len(xs_all) == 0 or len(ys_all) == 0:
                continue

            DEPTH_TOL_MM = 40
            zs_all = depthFrame[ys_all, xs_all].astype(numpy.float32)
            valid = (zs_all > 0) & (zs_all < workspace_depth) & (numpy.abs(zs_all - depth) <= DEPTH_TOL_MM)
            xs_v, ys_v, zs_v = xs_all[valid], ys_all[valid], zs_all[valid]

            Z = zs_v / 1000.0
            X = (xs_v - cx_d) * Z / fx_d
            Y = (ys_v - cy_d) * Z / fy_d

            objPoints.extend(numpy.column_stack([X,Y]))

        allObj_pts_m.append(objPoints)
        depthsObj.append(min_depth)

        for j in range(len(group)):
            irregular = False
            contour, depth = group[j]
            obj_height_mm = workspace_depth - depth
            if obj_height_mm < MIN_OBJ_HEIGHT_MM:
                print("Skipping ghost object", i, ": height", obj_height_mm, "mm")
                continue
            
            pts_flat = contour.reshape(-1,2)

            mask = numpy.zeros(calibrationDepthFrame_copy.shape, dtype=numpy.uint8)
            cv2.fillPoly(mask, [pts_flat.astype(numpy.int32)], 255)

            fill_img = numpy.zeros((480, 640), dtype=numpy.uint8)
            cv2.fillPoly(fill_img, [pts_flat.astype(numpy.int32)], 255)

            ys_all, xs_all = numpy.where(fill_img > 0)
            if len(xs_all) == 0 or len(ys_all) == 0:
                continue

            DEPTH_TOL_MM = 40
            zs_all = depthFrame[ys_all, xs_all].astype(numpy.float32)
            valid = (zs_all > 0) & (zs_all < workspace_depth) & (numpy.abs(zs_all - depth) <= DEPTH_TOL_MM)
            xs_v, ys_v, zs_v = xs_all[valid], ys_all[valid], zs_all[valid]

            Z = zs_v / 1000.0
            X = (xs_v - cx_d) * Z / fx_d
            Y = (ys_v - cy_d) * Z / fy_d

            Xc = (max(X) + min(X)) / 2
            Yc = (max(Y) + min(Y)) / 2

            Xcp = float(numpy.mean(xs_v))
            Ycp = float(numpy.mean(ys_v))

            cv2.circle(colorToDepthFrameX,
                    (int(Xcp), int(Ycp)),
                    7,
                    (0, 0, 255),
                    2)

            objCenter.append((Xc * 100, Yc * 100))

            allObj_pts_m.append(numpy.column_stack([X, Y]).tolist())
            depthsObj.append(depth)

            #rect_px = cv2.minAreaRect(pts_flat.astype(numpy.float32))
            #box_px = cv2.boxPoints(rect_px)
            #cv2.drawContours(frameState.colorToDepthFrame, [numpy.int32(box_px)], 0, (0, 255, 0), 2)
            #cv2.imwrite(f"colorToDepthFrame{i}.png", frameState.colorToDepthFrame)
            if is_suspect_blob(contour):
                irregular = True

            print("Irregular:", irregular)

            irregularGroup.append(irregular)

        allGroupsObjPoints.append((allObj_pts_m, irregularGroup))
        allDepths.append(depthsObj)
        allObjCenter.append(objCenter)
        
        #print("Size of allGroupsObjPoints:", len(allGroupsObjPoints))
        #print("Size of allObj_pts_m:", len(allObj_pts_m))
        #print("Size of allDepths", len(allDepths))

    for idx, (allObjPtsM, irregular) in enumerate(allGroupsObjPoints):
        #print("Grupo:", idx)
        #print("------------------------")
        #print("Size of allObjPtsM:", len(allObjPtsM))
        depths = allDepths[idx]

        objWidth= []
        objLength = []
        objHeight = []
        objHeightOverlapped = []
        objAngle = []
        realVolume = 0

        print("Irregular")
        print(irregular)
        print("-------------")
        
        for i, obj in enumerate(allObjPtsM):
            height_meters_overlappedObject = 0
            #print(irregular)
            #print("-------------")
            allObjPtsM = [numpy.array(obj, dtype=numpy.float32) for obj in allObjPtsM]
            rect_m = cv2.minAreaRect(allObjPtsM[i])
            width_meters, length_meters = rect_m[1]
            angle = rect_m[2]

            pts_flat_h = allObjPtsM[i].reshape(-1, 2)
            mask_h = numpy.zeros(calibrationDepthFrame_copy.shape, dtype=numpy.uint8)
            cv2.fillPoly(mask_h, [pts_flat_h.astype(numpy.int32)], 255)
            ws_vals_h = calibrationDepthFrame_copy[mask_h == 255].astype(numpy.float32)
            ws_vals_h = ws_vals_h[(ws_vals_h >= 150) & (ws_vals_h <= workspace_depth + 15)]
            ws_d_h = float(numpy.median(ws_vals_h)) if ws_vals_h.size > 0 else float(workspace_depth)
            height_meters = (ws_d_h - depths[i]) / 1000

            print(i)
            if i!=0:
                print(irregular[i-1])

            if i!= 0:
                if irregular[i-1]:
                    hull = cv2.convexHull(allObjPtsM[i])
                    volume = cv2.contourArea(hull) * height_meters
                else:
                    if i!=0 and i < (len(allObjPtsM) - 1):
                        print("Verifying object")
                        for j in range(i + 1, len(allObjPtsM)):
                            if isInside(allObjPtsM[i], allObjPtsM[j]):
                                print("Inside")
                                height_meters = (depths[j] - depths[i]) / 1000
                                height_meters_overlappedObject = ((ws_d_h - depths[i]) / 1000) - height_meters
                                break

            if i != 0:
                if not irregular[i-1]:
                    volume = width_meters * length_meters * height_meters
                totalVolume += volume
                realVolume += volume
                print("Volume:", volume)
                print("Height:", height_meters)
                print("Width:", width_meters)
                print("Length:", length_meters)
                print("------------------------------")
            else:
                height_meters = (ws_d_h - depths[i]) / 1000
                volume = width_meters * length_meters * height_meters

            objWidth.append(width_meters)
            objLength.append(length_meters)
            objHeight.append(height_meters)
            objHeightOverlapped.append(height_meters_overlappedObject)
            objAngle.append(angle)
        
        groupWidths.append(objWidth)
        groupLengths.append(objLength)
        groupHeights.append(objHeight)
        groupHeightsOverlapped.append(objHeightOverlapped)
        groupAngles.append(objAngle)
        groupRealVolume.append(realVolume)
        
    cv2.imwrite("Centers.png", colorToDepthFrameX)
    #print(groupHeightsOverlapped)
    print(allObjCenter)
    print(groupAngles)
    print("------------------------------")
    uidth = groupWidths
    ength = groupLengths
    eight = groupHeights
    bolume = groupRealVolume
            
    bolume.append(totalVolume)
    volume = bolume
    width_meters = uidth
    length_meters = ength
    height_meters = eight

    return volume, width_meters, length_meters, height_meters, allObjCenter, groupAngles, groupHeightsOverlapped

def volumeIndividualAPI(depthFrame, calibrationDepthFrame, workspace_depth, box_limits, depths, fx_d, fy_d, cx_d, cy_d): 
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
    box2 = box2.reshape(-1, 2).astype(numpy.float32)
    #box2 = to_hull(box2)
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

def overlap_ratio(b1, b2):
    inter, _ = cv2.intersectConvexConvex(
        b1.astype(numpy.float32),
        b2.astype(numpy.float32)
    )

    a1 = cv2.contourArea(b1)
    a2 = cv2.contourArea(b2)

    if a1 + a2 == 0:
        return 0

    return inter / min(a1, a2)

def intersection_edge(b1, b2, ctd, kernel_size=3):
    mask1 = numpy.zeros(ctd.shape, dtype=numpy.uint8)
    mask2 = numpy.zeros(ctd.shape, dtype=numpy.uint8)

    b1 = b1.astype(numpy.int32)
    b2 = b2.astype(numpy.int32)

    cv2.fillPoly(mask1, [b1], 255)
    cv2.fillPoly(mask2, [b2], 255)
    
    kernel = numpy.ones((kernel_size, kernel_size), numpy.uint8)
    mask1 = cv2.dilate(mask1, kernel)
    mask2 = cv2.dilate(mask2, kernel)

    return numpy.any(cv2.bitwise_and(mask1, mask2))

def is_suspect_blob(c):
    rect = cv2.minAreaRect(c)
    w, h = rect[1]

    rectArea = w * h
    contourArea = cv2.contourArea(c)

    print("Percentage", contourArea/rectArea)

    return contourArea/rectArea <= 0.85