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

def depthImg(depthFrame, colorSlope):
    img = numpy.int32(depthFrame)
    img = img*255/colorSlope
    img = numpy.clip(img, 0, 255)
    img = numpy.uint8(img)
    depth_img = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)

    return depth_img

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

def boxes_overlap(box1, box2):
    xmin1, xmax1, ymin1, ymax1 = box1 #Current
    xmin2, xmax2, ymin2, ymax2 = box2 #Previous

    print("Atual:", xmin1, xmax1, ymin1, ymax1)
    print("Anterior:", xmin2, xmax2, ymin2, ymax2)
    
    if ((xmin2 <= xmin1 <= xmax2) or (ymin2 <= ymin1 <= ymax2) or (ymin2 <= ymax1 <= ymax2) or (xmin2 <= xmax1 <= xmax2)):
        return True
    return False

def contours_overlap_by_points(c, prev_c, colorToDepth_copy, min_ratio = 0.4):
    inside = 0
    total = len(c)
    print("Total", total)

    hull = cv2.convexHull(prev_c)

    #cv2.drawContours(colorToDepth_copy, [hull], 0, (255, 0, 0), 2)

    for p in c:
        x = int(p[0][0])
        y = int(p[0][1])

        if cv2.pointPolygonTest(hull, (x, y), False) >= 0:
            inside += 1
            
    print("Inside", inside)
    print("Quanto?", inside / total)
    
    return (inside / total) >= min_ratio, colorToDepth_copy

def is_valid_area(c, min_area = 150):
    a = cv2.contourArea(c)
    print("Area", a)

    if a < min_area:
        return False

    return True

def comparisonCaliImageCurrImage(colorFrame, calibrationColorFrame, box_scaled):
    mask = numpy.zeros(colorFrame.shape[:2], dtype=numpy.uint8)

    cv2.fillPoly(mask, [box_scaled], 255)
    total_pixels = numpy.count_nonzero(mask)

    current = cv2.bitwise_and(colorFrame, colorFrame, mask=mask)
    cali = cv2.bitwise_and(calibrationColorFrame, calibrationColorFrame, mask=mask)

    currentGray = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)
    caliGray = cv2.cvtColor(cali, cv2.COLOR_BGR2GRAY)

    diff = cv2.absdiff(currentGray, caliGray)

    diffPercentage = numpy.sum(diff>20) / total_pixels
    print("Diff Percentage:", diffPercentage)

    if diffPercentage > 0.6:
        return True
    
    return False

def bundleIdentifier(colorFrame, colorToDepthFrame, depthFrame, calibrationColorFrame, objects_info, workspace_depth, threshold, colorSlope, cx_d, cy_d, cx_rgb, cy_rgb):
    contours = []
    box_ws = []
    box_limits = []
    shifted_contours = []
    correct_shifted_contours = []
    depths = []
    object_outOfLine = []
    belongs_to_previous = False

    colorToDepth_copy2 = colorFrame.copy()
    #colorToDepth_copy = colorToDepthFrame.copy()

    Sx = ((1600/2) / numpy.tan(numpy.radians(70/2))) / ((640/2) / numpy.tan(numpy.radians(60/2)))
    Sy = ((1200/2) / numpy.tan(numpy.radians(50/2))) / ((480/2) / numpy.tan(numpy.radians(45/2)))
    print("Sx:", Sx)
    print("Sy:", Sy)  

    if len(objects_info) != 0:
        for i, obj in enumerate(objects_info):

            #x1, y1, x2, y2 = obj["workspace_limits"]
            #workspace_area2 = depthFrame[y1:y2, x1:x2]

            mask = numpy.zeros(depthFrame.shape, dtype = numpy.uint8)

            box = numpy.array(obj["workspace_limits"], dtype=numpy.int32)

            cv2.fillPoly(mask, [box], 255)

            workspace_area2 = cv2.bitwise_and(depthFrame, depthFrame, mask=mask)

            if i == 0:
                mask = (workspace_area2 >= (obj["depth"] - threshold)) & (workspace_area2 <= (obj["depth"] + threshold))
            else:
                if (obj["depth"] - threshold) < (objects_info[i-1]["depth"] + threshold):
                    print("Limite Inferior")
                    mask = (workspace_area2 >= (objects_info[i-1]["depth"] + threshold)) & (workspace_area2 <= (obj["depth"] + threshold))
                else:
                    print("É igual")
                    mask = (workspace_area2 >= (obj["depth"] - threshold)) & (workspace_area2 <= (obj["depth"] + threshold))

            #depth_filtered = numpy.where(mask, workspace_area2, 0).astype(numpy.uint16)

            #depth_img = depthImg(depth_filtered, colorSlope)

            #gray = cv2.cvtColor(depth_img, cv2.COLOR_BGR2GRAY)
        
            #blur = cv2.GaussianBlur(gray, (5,5), 0)
            
            binary = mask.astype(numpy.uint8) * 255
            #_, binary = cv2.threshold(blur, 90, 255, cv2.THRESH_BINARY)
            #_, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Fecha buracos e regulariza a forma
            #element_close = numpy.ones((3, 3), numpy.uint8)
            #binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, element_close)

            # Remove ruído pequeno
            element_open = numpy.ones((3, 3), numpy.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, element_open)

            #invBinary = cv2.bitwise_not(binary)

            #element = numpy.ones((3, 3), numpy.uint8)
            #morf = cv2.morphologyEx(invBinary, cv2.MORPH_GRADIENT, element)

            #contour, _ = cv2.findContours(morf, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contour, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            #cv2.imwrite(f"debug_morf{i}.png", morf)
            #cv2.imwrite(f"debug_depth{i}.png", depth_filtered)
            #cv2.imwrite(f"debug_depthcolored{i}.png", depth_img)
            #cv2.imwrite(f"debug_binary{i}.png", binary)
            #cv2.imwrite(f"debug_inv{i}.png", invBinary)
            #debug_contours = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            #cv2.drawContours(debug_contours, contour, -1, (0,255,0), 2)
            #cv2.imwrite(f"debug_contours{i}.png", debug_contours)
            #cv2.drawContours(colorToDepthFrame, contour, -1, (0, 255, 0), 2)
            #cv2.imwrite(f"colorToDepthFrame{i}.png", colorToDepthFrame)

            #shifted_contours = [c + numpy.array([[[x1, y1]]], dtype=numpy.int32) for c in contour]
            
            #shifted_contours_sorted = sorted(shifted_contours, key=lambda x: len(x), reverse=True)
            shifted_contours_sorted = sorted(contour, key=lambda x: len(x), reverse=True)

            

            print("Depth:", obj["depth"])
            print("-------------------------------------------------------------------")

            for c in shifted_contours_sorted:
                rect = cv2.minAreaRect(c)
                box = cv2.boxPoints(rect)
                box_scaled = numpy.copy(box)
                box_scaled[:,0] = (box[:,0] - cx_d) * Sx + cx_rgb + (offset_x_959mm_depth * or_depth_offset)/workspace_depth
                box_scaled[:,1] = (box[:,1] - cy_d) * Sy + cy_rgb #+ (offset_y_959mm_depth * or_depth_offset)/workspace_depth
                box_scaled = numpy.round(box_scaled).astype(numpy.int32)
                if not comparisonCaliImageCurrImage(colorFrame, calibrationColorFrame, box_scaled):
                    continue

                if not is_valid_area(c):
                    print("Contornos Inválidos")
                    continue

                bbox_c = get_bbox(c)

                for prev_list in contours:
                    for prev_c in prev_list:
                        bbox_prev = get_bbox(prev_c)

                        if boxes_overlap(bbox_c, bbox_prev):
                            print("Wotefoque")
                            boxesOverlap, colorToDepth_copy2 = contours_overlap_by_points(c, prev_c, colorToDepth_copy2)
                            #contourDifference = cv2.matchShapes(c, prev_c, cv2.CONTOURS_MATCH_I1, 0)
                            #print("Contour Difference:", contourDifference)
                            if boxesOverlap: #or contourDifference < 0.02:
                                belongs_to_previous = True
                                print("Pertence ao anterior o macaco")
                                break
                        if too_close(bbox_c, bbox_prev):
                            belongs_to_previous = True
                            print("Too Close")
                            break
                        print("Não pertence")
                        belongs_to_previous = False
                    if belongs_to_previous:
                        break
                if not belongs_to_previous:
                    workspace_warning = obj["workspace_warning"]

                    ws_poly = numpy.array(workspace_warning, dtype = numpy.int32)
                    value = False

                    for pt in box:
                        x, y = int(pt[0]), int(pt[1])

                        if cv2.pointPolygonTest(ws_poly, (x, y), False) < 0:
                            value = True
                            break

                    #if ((bbox_c[0] < workspace_warning[0]) or (bbox_c[1] > workspace_warning[2]) or (bbox_c[2] < workspace_warning[1]) or (bbox_c[3] > workspace_warning[3])):
                    #    value = True
                    #else:
                    #    value = False
                    if value == False:
                        correct_shifted_contours = []
                        correct_shifted_contours.append(c)
                        print("Adicionar ao Conjunto")
                        belongs_to_previous = False
                        all_shifted_contours = numpy.vstack(correct_shifted_contours)
                        contours.append([all_shifted_contours])
                        box_ws.append(obj["workspace_limits"])

                        #mask = numpy.zeros(depthFrame.shape, dtype=numpy.uint8)
                        #kernel = numpy.ones((10, 10), dtype=numpy.uint8)
                        #mask = cv2.erode(mask, kernel, iterations=1)
                        #cv2.drawContours(mask, [c], contourIdx=-1, color=1, thickness=-1)
                        #valid_mask = (
                        #    (mask == 1) &
                        #    (depthFrame > 150) &
                        #    (depthFrame < workspace_depth - threshold)
                        #)

                        #depth_values = depthFrame[valid_mask]
                        #print("Depth Values:", depth_values)
                        #mean_depth = numpy.mean(depth_values)
                        #print("Mean Depth:", mean_depth)

                        #depths.append(mean_depth)
                        depths.append(obj["depth"])
                        print("Número de Objetos no contours", len(contours))

                    object_outOfLine.append(value)

            print("-------------------------------------------------------------------")      

    box_limits = [c for contour_list in contours for c in contour_list if c.size > 0]

    if len(box_limits) > 0:
        all_points = numpy.vstack(box_limits)

        rect = cv2.minAreaRect(all_points)
        box = cv2.boxPoints(rect)
        box_scaled = numpy.copy(box)
        box_scaled[:,0] = (box[:,0] - cx_d) * Sx + cx_rgb + (offset_x_959mm_depth * or_depth_offset)/workspace_depth
        box_scaled[:,1] = (box[:,1] - cy_d) * Sy + cy_rgb #+ (offset_y_959mm_depth * or_depth_offset)/workspace_depth
        box_scaled = numpy.round(box_scaled).astype(numpy.int32)
        #box = numpy.round(box).astype(numpy.int32)

        cv2.drawContours(colorToDepth_copy2, [box_scaled + [int(abs((cx_rgb) - cx_d*2.5)), int(abs((cy_rgb) - cy_d*2.5))]], 0, (0, 0, 0), 16)
        cv2.drawContours(colorToDepth_copy2, [box_scaled + [int(abs((cx_rgb) - cx_d*2.5)), int(abs((cy_rgb) - cy_d*2.5))]], 0, (255, 255, 0), 8)
        #cv2.drawContours(colorToDepth_copy, [box], 0,  (0, 255, 0), 2)
    
    colorToDepth_copy2 = cv2.resize(colorToDepth_copy2, (640, 480))
    frameState.detectedObjectsFrame = colorToDepth_copy2
    #cv2.imwrite("Bundle.png", colorToDepth_copy2)
    print("Número Objetos:", len(box_limits))
    print("OutOfLine", object_outOfLine)

    not_set = 1
    minimum_value = 6000
                    
    return minimum_value, not_set, box_ws, box_limits, depths, object_outOfLine

def objIdentifier(colorFrame, colorToDepthFrame, depthFrame, calibrationColorFrame, objects_info, workspace_depth, threshold, colorSlope, cx_d, cy_d, cx_rgb, cy_rgb):
    contours = []
    box_ws = []
    box_limits = []
    shifted_contours = []
    correct_shifted_contours = []
    depths = []
    object_outOfLine = []
    belongs_to_previous = False

    colorToDepth_copy2 = colorFrame.copy()
    colorToDepth_copy3 = colorToDepthFrame.copy()

    Sx = ((1600/2) / numpy.tan(numpy.radians(70/2))) / ((640/2) / numpy.tan(numpy.radians(60/2)))
    Sy = ((1200/2) / numpy.tan(numpy.radians(50/2))) / ((480/2) / numpy.tan(numpy.radians(45/2)))
    print("Sx:", Sx)
    print("Sy:", Sy)

    if len(objects_info) != 0:
        #for obj in objects_info:
        
        for i, obj in enumerate(objects_info):

            #x1, y1, x2, y2 = obj["workspace_limits"]
            #workspace_area2 = depthFrame[y1:y2, x1:x2]

            mask = numpy.zeros(depthFrame.shape, dtype = numpy.uint8)

            box = numpy.array(obj["workspace_limits"], dtype=numpy.int32)

            cv2.fillPoly(mask, [box], 255)

            workspace_area2 = cv2.bitwise_and(depthFrame, depthFrame, mask=mask)

            if i == 0:
                mask = (workspace_area2 >= (obj["depth"] - threshold)) & (workspace_area2 <= (obj["depth"] + threshold))
            else:
                if (obj["depth"] - threshold) < (objects_info[i-1]["depth"] + threshold):
                    print("Limite Inferior")
                    mask = (workspace_area2 >= (objects_info[i-1]["depth"] + threshold)) & (workspace_area2 <= (obj["depth"] + threshold))
                else:
                    print("É igual")
                    mask = (workspace_area2 >= (obj["depth"] - threshold)) & (workspace_area2 <= (obj["depth"] + threshold))
            
            binary = mask.astype(numpy.uint8) * 255

            # Remove ruído pequeno
            element_open = numpy.ones((3, 3), numpy.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, element_open)

            # Fecha buracos e regulariza a forma
            element_close = numpy.ones((7, 7), numpy.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, element_close)

            contour, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            shifted_contours_sorted = sorted(contour, key=lambda x: len(x), reverse=True)

            #cv2.imwrite(f"debug_morf{i}.png", morf)
            #cv2.imwrite(f"debug_depth{i}.png", depth_filtered)
            #cv2.imwrite(f"debug_depthcolored{i}.png", depth_img)
            cv2.imwrite(f"debug_binary{i}.png", binary)
            #cv2.imwrite(f"debug_inv{i}.png", invBinary)
            #debug_contours = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            #cv2.drawContours(debug_contours, contour, -1, (0,255,0), 2)
            #cv2.imwrite(f"debug_contours{i}.png", debug_contours)
            
            for j, c in enumerate(contour):
                colorToDepth_copy4 = colorToDepthFrame.copy()
                
                cv2.drawContours(colorToDepth_copy4, [c], -1, (0, 255, 0), 2)
                
                texto = f"{float(obj['depth']):.1f}"
                cv2.putText(colorToDepth_copy4, texto, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 6, cv2.LINE_AA)
                cv2.putText(colorToDepth_copy4, texto, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2, cv2.LINE_AA)
                
                cv2.imwrite(f"DEPTHS{i}_contour{j}.png", colorToDepth_copy4)

            print("Depth:", obj["depth"])
            print("-------------------------------------------------------------------")

            for c in shifted_contours_sorted:
                belongs_to_previous = False
                rect = cv2.minAreaRect(c)
                box = cv2.boxPoints(rect)
                print("Box :", box)
                box_scaled = numpy.copy(box)
                box_scaled[:,0] = (box[:,0] - cx_d) * Sx + cx_rgb + (offset_x_959mm_depth * or_depth_offset)/workspace_depth
                box_scaled[:,1] = (box[:,1] - cy_d) * Sy + cy_rgb #+ (offset_y_959mm_depth * or_depth_offset)/workspace_depth
                box_scaled = numpy.round(box_scaled).astype(numpy.int32)
                print("Box_Scaled:", box_scaled)
                if not comparisonCaliImageCurrImage(colorFrame, calibrationColorFrame, box_scaled):
                    continue

                if not is_valid_area(c):
                    #print("Contornos Inválidos")
                    continue

                bbox_c = get_bbox(c)

                for prev_list in contours:
                    print("Watching Previous...")
                    for prev_c in prev_list:
                        bbox_prev = get_bbox(prev_c)

                        if boxes_overlap(bbox_c, bbox_prev):
                            print("Wotefoque")
                            boxesOverlap, colorToDepth_copy2 = contours_overlap_by_points(c, prev_c, colorToDepth_copy2)
                            
                            if boxesOverlap: #or contourDifference < 0.02:
                                belongs_to_previous = True
                                print("Pertence ao anterior o macaco")
                                break
                        if too_close(bbox_c, bbox_prev):
                            belongs_to_previous = True
                            print("Too Close")
                            break
                        print("Não pertence")
                        
                    if belongs_to_previous:
                        break
                if not belongs_to_previous:
                    workspace_warning = obj["workspace_warning"]
                    ws_poly = numpy.array(workspace_warning, dtype = numpy.int32)
                    value = False

                    for pt in box:
                        x, y = int(pt[0]), int(pt[1])

                        if cv2.pointPolygonTest(ws_poly, (x, y), False) < 0:
                            value = True
                            break

                    if not value:
                        correct_shifted_contours = []
                        correct_shifted_contours.append(c)
                        print("Adicionar ao Conjunto")
                        belongs_to_previous = False
                        all_shifted_contours = numpy.vstack(correct_shifted_contours)
                        contours.append([all_shifted_contours])
                        box_ws.append(obj["workspace_limits"])

                        mask = numpy.zeros(depthFrame.shape, dtype=numpy.uint8)
                        kernel = numpy.ones((10, 10), dtype=numpy.uint8)
                        mask = cv2.erode(mask, kernel, iterations=1)
                        cv2.drawContours(mask, [c], contourIdx=-1, color=1, thickness=-1)

                        previous_mask = numpy.zeros(depthFrame.shape, dtype=numpy.uint8)

                        for prev_list in contours[:-1]:
                            for prev_c in prev_list:
                                cv2.drawContours(previous_mask, [prev_c], contourIdx=-1, color=1, thickness=-1)

                        valid_mask = (
                            (mask == 1) &
                            (previous_mask == 0) &
                            (depthFrame > 150) &
                            (depthFrame < workspace_depth - threshold)
                        )

                        depth_values = depthFrame[valid_mask]
                        print("Depth Values:", depth_values)
                        mean_depth = numpy.mean(depth_values)
                        print("Mean Depth:", mean_depth)

                        depths.append(mean_depth)
                        #depths.append(obj["depth"])

                    object_outOfLine.append(value)

            print("-------------------------------------------------------------------")

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
    cv2.imwrite("Objects.png", colorToDepth_copy3)
    box_limits = [c for contour_list in contours for c in contour_list if c.size > 0]
    print("Número Objetos:", len(box_limits))
    print("OutOfLine", object_outOfLine)

    not_set = 1
    minimum_value = 6000
                    
    return minimum_value, not_set, box_ws, box_limits, depths, object_outOfLine