from pickle import FALSE, TRUE
import sys
import os
import numpy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "Python"))

from API.VzenseDS_api import *
import cv2
from FrameState import frameState

offset_x_959mm_depth = 40
offset_y_959mm_depth = -15
or_depth_offset = 959.548329678014

OVERLAP_RATIO = 0.05

def get_bbox(pts):
    pts_flat = pts.reshape(-1, 2)
    xmin = pts_flat[:,0].min()
    xmax = pts_flat[:,0].max()
    ymin = pts_flat[:,1].min()
    ymax = pts_flat[:,1].max()
    return xmin, xmax, ymin, ymax

def too_close(box1, box2):
    xmin1, xmax1, ymin1, ymax1 = box1 #Current
    xmin2, xmax2, ymin2, ymax2 = box2 #Previous

    if (abs(xmin2 - xmin1) < 1 and abs(ymin2 - ymin1) < 1) or (abs(xmax2 - xmax1) < 1 and abs(ymax2 - ymax1) < 1):
        return True
    return False

def contours_overlap_by_points(c, prev_c):
    min_ratio = 0.20

    inside = 0
    inside_prev = 0
    total = len(c)
    total_prev = len(prev_c)

    for p in c:
        x = int(p[0][0])
        y = int(p[0][1])

        if cv2.pointPolygonTest(prev_c, (x, y), False) >= 0:
            inside += 1

    for p in prev_c:
        x = int(p[0][0])
        y = int(p[0][1])

        if cv2.pointPolygonTest(c, (x, y), False) >= 0:
            inside_prev += 1
            
    # print("Inside", inside)
    # print("Quanto?", inside / total)

    # print("Inside Prev", inside_prev)
    # print("Quanto?", inside_prev / total_prev)
    
    return ((inside / total) >= min_ratio or (inside_prev / total_prev) >= min_ratio)

def intersection_edge(b1, b2, depthFrame, kernel_size=3):
    mask1 = numpy.zeros(depthFrame.shape[:2], dtype=numpy.uint8)
    mask2 = numpy.zeros(depthFrame.shape[:2], dtype=numpy.uint8)

    b1 = b1.astype(numpy.int32)
    b2 = b2.astype(numpy.int32)

    cv2.fillPoly(mask1, [b1], 255)
    cv2.fillPoly(mask2, [b2], 255)
    
    kernel = numpy.ones((kernel_size, kernel_size), numpy.uint8)
    mask1 = cv2.dilate(mask1, kernel)
    mask2 = cv2.dilate(mask2, kernel)

    cv2.imwrite("mask1.png", mask1)
    cv2.imwrite("mask2.png", mask2)

    #if numpy.any(cv2.bitwise_and(mask1, mask2)):
        #print("Intersection")

    return numpy.any(cv2.bitwise_and(mask1, mask2))

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

def is_valid_area(c, min_area = 320):
    a = cv2.contourArea(c)
    #print("Area", a)

    if a < min_area:
        return False

    return True

def comparisonCaliImageCurrImage(colorFrame, calibrationColorFrame, depthFrame, calibrationDepthFrame, box_scaled, contour):
    mask = numpy.zeros(colorFrame.shape[:2], dtype=numpy.uint8)
    depth_mask = numpy.zeros(depthFrame.shape[:2], dtype=numpy.uint8)

    cv2.fillPoly(mask, [box_scaled], 255)
    total_pixels = numpy.count_nonzero(mask)

    hull = cv2.convexHull(contour.astype(numpy.int32))

    cv2.fillPoly(depth_mask, contour, 255)
    total_pixels_depth = numpy.count_nonzero(depth_mask)

    # ---------------- DEPTH ----------------
    depthDiff = cv2.absdiff(
        depthFrame.astype(numpy.float32),
        calibrationDepthFrame.astype(numpy.float32)
    )

    validMask = depth_mask > 0

    depthScore = numpy.sum((depthDiff > 30) & validMask) / total_pixels_depth

    return depthScore >= 0.80

def areContoursClose(c1, c2, threshold):
    pts1 = c1.reshape(-1, 2)
    pts2 = c2.reshape(-1, 2)

    for p1 in pts1:
        dists = numpy.linalg.norm(pts2 - p1, axis=1)
        if numpy.min(dists) <= threshold:
            return True

    return False

def objIdentifier(colorFrame, colorToDepthFrame, depthFrame, calibrationColorFrame, calibrationDepthFrame, volumeMode, objects_info, workspace_depth, threshold, colorSlope, cx_d, cy_d, cx_rgb, cy_rgb, fx_d, fy_d, fx_rgb, fy_rgb):
    contours = []
    box_ws = []
    box_limits = []
    depths = []
    object_outOfLine = []
    belongs_to_previous = False
    pending_merges = []
    contours_united = set()
    binaryImgs = []
    curr_index = 0

    colorToDepth_copy2 = colorFrame.copy()
    colorToDepth_copy3 = colorToDepthFrame.copy()
    depth_copy = depthFrame.copy()
    color_copy = colorFrame.copy()

    Sx = fx_rgb / fx_d
    Sy = fy_rgb / fy_d

    if len(objects_info) != 0:
        for i, obj in enumerate(objects_info):
            mask = numpy.ones(depth_copy.shape, dtype = numpy.uint8)
            #print("Obj Workspace Limits:", obj["workspace_limits"])

            #box = numpy.array(obj["workspace_limits"], dtype=numpy.int32)

            #cv2.fillPoly(mask, [box], 255)

            workspace_area2 = cv2.bitwise_and(depth_copy, depth_copy, mask=mask)

            if i == 0:
                mask2 = (workspace_area2 >= (obj["depth"] - threshold)) & (workspace_area2 <= (obj["depth"] + threshold))
            else:
                if (obj["depth"] - threshold) < (objects_info[i-1]["depth"] + threshold):
                    #print("Limite Inferior")
                    mask2 = (workspace_area2 >= (objects_info[i-1]["depth"] + threshold)) & (workspace_area2 <= (obj["depth"] + threshold))
                else:
                    #print("É igual")
                    mask2 = (workspace_area2 >= (obj["depth"] - threshold)) & (workspace_area2 <= (obj["depth"] + threshold))
            
            binary = mask2.astype(numpy.uint8) * 255
            #cv2.imwrite(f"binary_{i}_0_mask.png", binary)

            # Remove ruído pequeno
            element_open = numpy.ones((3, 3), numpy.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, element_open)
            #cv2.imwrite(f"binary_{i}_1_mask.png", binary)

            # Fecha buracos e regulariza a forma
            element_close = numpy.ones((7, 7), numpy.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, element_close)
            #cv2.imwrite(f"binary_{i}_2_mask.png", binary)

            contour, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for j, c in enumerate(contour):
                colorToDepth_copy4 = colorToDepthFrame.copy()
                
                cv2.drawContours(colorToDepth_copy4, [c], -1, (0, 255, 0), 2)
                box = numpy.array(obj["workspace_limits"], dtype=numpy.int32)
                cv2.drawContours(colorToDepth_copy4, [box], 0, (0, 0, 255), 2)
                
                texto = f"{float(obj['depth']):.1f}"
                cv2.putText(colorToDepth_copy4, texto, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 6, cv2.LINE_AA)
                cv2.putText(colorToDepth_copy4, texto, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2, cv2.LINE_AA)
                
                cv2.imwrite(f"DEPTHS{i}_contour{j}.png", colorToDepth_copy4)

            # print("Depth:", obj["depth"])

            # print("-------------------------------------------------------------------")

            for c in contour:
                belongs_to_previous = False
                rect = cv2.minAreaRect(c)
                box = cv2.boxPoints(rect)
                #print("Box :", box)
                box_scaled = numpy.copy(box)
                box_scaled[:,0] = (box[:,0] - cx_d) * Sx + cx_rgb + (offset_x_959mm_depth * or_depth_offset)/workspace_depth
                box_scaled[:,1] = (box[:,1] - cy_d) * Sy + cy_rgb #+ (offset_y_959mm_depth * or_depth_offset)/workspace_depth
                box_scaled = numpy.round(box_scaled).astype(numpy.int32)
                #print("Box_Scaled:", box_scaled)
                if not comparisonCaliImageCurrImage(colorFrame, calibrationColorFrame, depthFrame, calibrationDepthFrame, box_scaled, c):
                    #print("Não passou no teste")
                    continue

                if not is_valid_area(c):
                    #print("Contornos Inválidos")
                    continue

                bbox_c = get_bbox(c)

                for i_prev_obj, prev_list in enumerate(contours):
                    #print("Watching Previous...")
                    for prev_c in prev_list:
                        bbox_prev = get_bbox(prev_c)
                        #print("Wotefoque")
                        #print("Previous Depth:", depths[i_prev_obj])
                        if contours_overlap_by_points(c, prev_c):
                            if obj['depth'] - 5 <= depths[i_prev_obj] + threshold:
                                #print("Merge is emminent. Prepare for merging...")
                                
                                pending_merges.append({
                                    "current_index": curr_index,
                                    "prev_index": i_prev_obj
                                })
                            # else:
                            #     print("Objetos diferentes")
                            break

                        if areContoursClose(c, prev_c, 10):
                            #print("Close gap")
                            imagIna = numpy.zeros(depthFrame.shape[:2], numpy.uint8)
                            mask_prev = numpy.zeros(depthFrame.shape[:2], numpy.uint8)
                            mask_curr = numpy.zeros(depthFrame.shape[:2], numpy.uint8)

                            cv2.drawContours(mask_prev, [prev_c], -1, 255, -1)
                            cv2.drawContours(mask_curr, [c], -1, 255, -1)

                            union = cv2.bitwise_or(mask_prev, mask_curr)

                            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7,7))
                            closed = cv2.morphologyEx(union, cv2.MORPH_CLOSE, kernel)

                            new_pixels = cv2.subtract(closed, union)

                            result = cv2.bitwise_or(mask_curr, new_pixels)

                            contorno, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
                            if len(contorno) > 0:
                                #print("Unite Contour")
                                new_c = max(contorno, key=cv2.contourArea)
                                if cv2.contourArea(new_c) > 0:
                                    contours_united.add((curr_index, i_prev_obj))
                                    c = new_c
                                cv2.drawContours(imagIna, [new_c], -1, 255, 2)
                            # else:
                            #     print("No contour was found")
                        # else:
                        #     print("No contours to unite")

                        if too_close(bbox_c, bbox_prev):
                            belongs_to_previous = True
                            #print("Too Close")
                            break
                        #print("Não pertence")
                        
                    if belongs_to_previous:
                        break
                if not belongs_to_previous:
                    #print("New")
                    workspace_warning = obj["workspace_limits"]
                    ws_poly = numpy.array(workspace_warning, dtype = numpy.int32)
                    #Giving a little margin to identify objects on the border
                    margin = 3
                    xmin = ws_poly[:, 0].min() - margin
                    xmax = ws_poly[:, 0].max() + margin
                    ymin = ws_poly[:, 1].min() - margin
                    ymax = ws_poly[:, 1].max() + margin
                    ws_poly = numpy.array([
                        [xmin, ymin],
                        [xmax, ymin],
                        [xmax, ymax],
                        [xmin, ymax]
                    ], dtype=numpy.int32)
                    value = False

                    for pt in box:
                        x, y = int(pt[0]), int(pt[1])

                        if cv2.pointPolygonTest(ws_poly, (x, y), False) < 0:
                            value = True
                            #print("Out of Line")
                            break

                    if not value:
                        #print("Adicionar ao Conjunto")
                        belongs_to_previous = False
                        all_shifted_contours = numpy.vstack([c])
                        contours.append([all_shifted_contours])
                        box_ws.append(obj["workspace_limits"])
                        binaryImgs.append(binary)

                        previous_mask = numpy.zeros(depth_copy.shape, dtype=numpy.uint8)

                        valid_mask = (
                            (mask2 == 255) &
                            (previous_mask == 0) &
                            (depth_copy > 150) &
                            (depth_copy < workspace_depth - threshold)
                        )

                        depth_values = depth_copy[valid_mask]
                        mean_depth = float(numpy.median(depth_values)) if depth_values.size > 0 else float(obj["depth"])
                        #print("Mean Depth:", mean_depth)

                        depths.append(mean_depth)
                        curr_index += 1

                    object_outOfLine.append(value)

        if len(pending_merges) > 0:
            to_delete = set()

            for merge in pending_merges:
                current_index = merge["current_index"]
                prev_index = merge["prev_index"]

                if current_index in to_delete:
                    continue

                if prev_index in to_delete:
                    continue

                c = contours[current_index][0]
                prev_c = contours[prev_index][0]

                mask = numpy.zeros((480, 640), dtype=numpy.uint8)

                cv2.fillPoly(mask, [c.astype(numpy.int32)], 255)
                cv2.fillPoly(mask, [prev_c.astype(numpy.int32)], 255)

                kernel = numpy.ones((3,3), numpy.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)      
                
                merged_contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

                merged_contour = max(merged_contours, key=cv2.contourArea)          
                # cv2.drawContours(img, [merged_contour], -1, (0, 0, 255), 2)
                # img = numpy.zeros((480, 640, 3), dtype=numpy.uint8)
                # cv2.imwrite(f"merged.png", img)

                A = cv2.contourArea(c)
                B = cv2.contourArea(prev_c)

                if A > B:
                    contours[current_index] = [merged_contour]

                    depths[current_index] = min(depths[current_index], depths[prev_index])

                    to_delete.add(prev_index)

                    new_contours_united = set()
                    for k, (a, b) in enumerate(contours_united):
                        if a > prev_index:
                            a -= 1
                        if b > prev_index:
                            b -= 1
                        new_contours_united.add((a, b))

                    contours_united = new_contours_united

                    #print(f"Merged previous {prev_index} into current {current_index}")

                else:
                    contours[prev_index] = [merged_contour]

                    depths[prev_index] = min(depths[current_index], depths[prev_index])

                    to_delete.add(current_index)

                    new_contours_united = set()
                    for k, (a, b) in enumerate(contours_united):
                        if a > current_index:
                            a -= 1
                        if b > current_index:
                            b -= 1
                        new_contours_united.add((a, b))

                    contours_united = new_contours_united

                    #print(f"Merged current {current_index} into previous {prev_index}")

            for idx in sorted(to_delete, reverse=True):
                del contours[idx]
                del depths[idx]
                del box_ws[idx]
                del object_outOfLine[idx]
                del binaryImgs[idx]

            #print("-------------------------------------------------------------------")    

    if volumeMode == "Single Bundle":
        box_limits = [c for contour_list in contours for c in contour_list if c.size > 0]

        if len(box_limits) > 0:
            all_points = numpy.vstack(box_limits)

            rect = cv2.minAreaRect(all_points)
            box = cv2.boxPoints(rect)
            box_scaled = numpy.copy(box)
            box_scaled[:,0] = (box[:,0] - cx_d) * Sx + cx_rgb + (offset_x_959mm_depth * or_depth_offset)/workspace_depth
            box_scaled[:,1] = (box[:,1] - cy_d) * Sy + cy_rgb #+ (offset_y_959mm_depth * or_depth_offset)/workspace_depth
            box_scaled = numpy.round(box_scaled).astype(numpy.int32)

            cv2.drawContours(colorToDepth_copy2, [box_scaled], 0, (0, 0, 0), 16)
            cv2.drawContours(colorToDepth_copy2, [box_scaled], 0, (255, 255, 0), 8)

    elif volumeMode == "Real" or volumeMode == "Multi Bundle":
        all_contours = [c for contour_list in contours for c in contour_list if c.size > 0]
        groups = []
        used = set()

        for i in range(len(all_contours)):
            if i in used:
                continue

            stack = [i]
            group = []

            while stack:
                idx = stack.pop()
                

                if idx in used:
                    continue

                used.add(idx)
                group.append(all_contours[idx])

                for j in range(len(all_contours)):
                    if j in used:
                        continue

                    box_i = all_contours[idx]
                    box_j = all_contours[j]

                    if contours_overlap_by_points(box_i, box_j) or intersection_edge(box_i, box_j, depthFrame) or areContoursClose(box_i, box_j, 10):
                        stack.append(j)
                        #print(f"BUNDLE joined {i} with {j}")

            groups.append(group)

        #contours_img = numpy.zeros((depthFrame.shape[0], depthFrame.shape[1], 3), dtype=numpy.uint8)

        for obj_id, group in enumerate(groups, start=1):
            #for c in group:
            #    cv2.drawContours(contours_img, [c], -1, (255, 255, 255), 1)
            all_points = numpy.vstack(group)
            rect = cv2.minAreaRect(all_points)
            box = cv2.boxPoints(rect)
            box = numpy.round(box).astype(numpy.int32)
            box_scaled = numpy.copy(box)
            box_scaled[:,0] = (box[:,0] - cx_d) * Sx + cx_rgb + (offset_x_959mm_depth * or_depth_offset)/workspace_depth
            box_scaled[:,1] = (box[:,1] - cy_d) * Sy + cy_rgb
            box_scaled = numpy.round(box_scaled).astype(numpy.int32)
            
            cv2.drawContours(colorToDepth_copy2, [box_scaled], 0, (0, 0, 0), 16)
            cv2.drawContours(colorToDepth_copy2, [box_scaled], 0, (255, 255, 0), 8)

            box = numpy.round(box).astype(numpy.int32)
            cv2.drawContours(colorToDepth_copy3, [box], 0, (0, 0, 0), 2)
            cv2.drawContours(colorToDepth_copy3, [box], 0, (255, 255, 0), 1)

            idx_x = numpy.argmax(box_scaled[:,0])
            x, y = box_scaled[idx_x]

            cv2.putText(colorToDepth_copy2, str(obj_id), (x + 15, y + 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 14, cv2.LINE_AA)
            cv2.putText(colorToDepth_copy2, str(obj_id), (x + 15, y + 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 7, cv2.LINE_AA)    

       # cv2.imwrite("groups.png", contours_img)

    elif volumeMode == "Individual":
        for obj_id, contour_list in enumerate(contours, start=1):
            for c in contour_list:
                rect = cv2.minAreaRect(c)
                box = cv2.boxPoints(rect)
                box_scaled = numpy.copy(box)
                box_scaled[:,0] = (box[:,0] - cx_d) * Sx + cx_rgb + (offset_x_959mm_depth * or_depth_offset)/workspace_depth
                box_scaled[:,1] = (box[:,1] - cy_d) * Sy + cy_rgb #+ (offset_y_959mm_depth * or_depth_offset)/workspace_depth
                box_scaled = numpy.round(box_scaled).astype(numpy.int32)
                
                cv2.drawContours(colorToDepth_copy2, [box_scaled], 0, (0, 0, 0), 16)
                cv2.drawContours(colorToDepth_copy2, [box_scaled], 0, (255, 255, 0), 8)

                box = numpy.round(box).astype(numpy.int32)
                cv2.drawContours(colorToDepth_copy3, [box], 0, (0, 0, 0), 2)
                cv2.drawContours(colorToDepth_copy3, [box], 0, (255, 255, 0), 1)
                
                idx_x = numpy.argmax(box_scaled[:,0])
                x, y = box_scaled[idx_x]
                
                cv2.putText(colorToDepth_copy2, str(obj_id), (x + 15, y + 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 14, cv2.LINE_AA)
                cv2.putText(colorToDepth_copy2, str(obj_id), (x + 15, y + 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 7, cv2.LINE_AA)
    
    colorToDepth_copy2 = cv2.resize(colorToDepth_copy2, (640, 480))
    frameState.detectedObjectsFrame = colorToDepth_copy2
    #cv2.imwrite("Objects.png", colorToDepth_copy3)
    box_limits = [c for contour_list in contours for c in contour_list if c.size > 0]
    #print("Número Objetos:", len(box_limits))
    print("OutOfLine", object_outOfLine)

    not_set = 1
    minimum_value = 6000
                    
    return minimum_value, not_set, box_ws, box_limits, depths, object_outOfLine, contours_united