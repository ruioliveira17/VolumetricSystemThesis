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

def contours_overlap_by_points(c, prev_c, colorToDepth_copy):
    min_ratio = 0.20

    inside = 0
    inside_prev = 0
    total = len(c)
    total_prev = len(prev_c)
    #print("Total", total)

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
            
    print("Inside", inside)
    print("Quanto?", inside / total)

    print("Inside Prev", inside_prev)
    print("Quanto?", inside_prev / total_prev)
    
    return ((inside / total) >= min_ratio or (inside_prev / total_prev) >= min_ratio), colorToDepth_copy

def is_valid_area(c, min_area = 320):
    a = cv2.contourArea(c)
    print("Area", a)

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

    # ---------------- COLOR ----------------
    current = cv2.bitwise_and(colorFrame, colorFrame, mask=mask)
    cali = cv2.bitwise_and(calibrationColorFrame, calibrationColorFrame, mask=mask)

    currentGray = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)
    caliGray = cv2.cvtColor(cali, cv2.COLOR_BGR2GRAY)

    diff = cv2.absdiff(currentGray, caliGray)

    colorScore = numpy.sum(diff>10) / total_pixels

    # ---------------- DEPTH ----------------
    depthDiff = cv2.absdiff(
        depthFrame.astype(numpy.float32),
        calibrationDepthFrame.astype(numpy.float32)
    )

    validMask = depth_mask > 0

    depthScore = numpy.sum((depthDiff > 30) & validMask) / total_pixels_depth

    # ---------------- DECISION ----------------
    w_color = 0.25
    w_depth = 0.75

    #finalScore = (w_color * colorScore) + (w_depth * depthScore)

    #print("Color Score:", colorScore)
    print("Depth Score:", depthScore)
    #print("Final Score:", finalScore)

    #return finalScore >= 0.80
    return depthScore >= 0.80

def overlap_ratio(b1, b2):
    inter, _ = cv2.intersectConvexConvex(
        b1.astype(numpy.int32),
        b2.astype(numpy.int32)
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

def objIdentifier(colorFrame, colorToDepthFrame, depthFrame, calibrationColorFrame, calibrationDepthFrame, volumeMode, objects_info, workspace_depth, threshold, colorSlope, cx_d, cy_d, cx_rgb, cy_rgb, fx_d, fy_d, fx_rgb, fy_rgb):
    contours = []
    box_ws = []
    box_limits = []
    depths = []
    object_outOfLine = []
    belongs_to_previous = False
    pending_merges = []
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
            # Using RGB
            # maskRGB = numpy.zeros(color_copy.shape[:2], dtype = numpy.uint8)

            # box_scaled = numpy.copy(box)
            # box_scaled[:,0] = (box[:,0] - cx_d) * Sx + cx_rgb + (offset_x_959mm_depth * or_depth_offset)/workspace_depth
            # box_scaled[:,1] = (box[:,1] - cy_d) * Sy + cy_rgb
            # box_scaled = numpy.round(box_scaled).astype(numpy.int32)

            # cv2.fillPoly(maskRGB, [box_scaled], 255)

            # workspaceArea = cv2.bitwise_and(color_copy, color_copy, mask=maskRGB)
            # ROI = cv2.cvtColor(workspaceArea, cv2.COLOR_BGR2GRAY)
            # BLUR = cv2.GaussianBlur(ROI, (5,5), 0)
            # Edges = cv2.Canny(BLUR, 50, 150)

            # cv2.imwrite("Edges.png", Edges)

            # CONTOUR, _ = cv2.findContours(Edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # colorToDepth_copy5 = colorToDepthFrame.copy()
            
            # CONTOUR_DEPTH = []

            # for c in CONTOUR:
            #     cnt = c.astype(numpy.float32)

            #     cnt[:, :, 0] = (cnt[:, :, 0] - cx_rgb - ((offset_x_959mm_depth * or_depth_offset)/workspace_depth)) / Sx + cx_d
            #     cnt[:, :, 1] = (cnt[:, :, 1] - cy_rgb) / Sy + cy_d

            #     CONTOUR_DEPTH.append(cnt.astype(numpy.int32))

            # cv2.drawContours(colorToDepth_copy5, CONTOUR_DEPTH, -1, (0, 255, 0), 2)
            # cv2.imwrite("DEPTHSRGB_contour.png", colorToDepth_copy5)

            mask = numpy.zeros(depth_copy.shape, dtype = numpy.uint8)
            print("Obj Workspace Limits:", obj["workspace_limits"])

            box = numpy.array(obj["workspace_limits"], dtype=numpy.int32)

            cv2.fillPoly(mask, [box], 255)

            workspace_area2 = cv2.bitwise_and(depth_copy, depth_copy, mask=mask)

            if i == 0:
                mask2 = (workspace_area2 >= (obj["depth"] - threshold)) & (workspace_area2 <= (obj["depth"] + threshold))
            else:
                if (obj["depth"] - threshold) < (objects_info[i-1]["depth"] + threshold):
                    print("Limite Inferior")
                    mask2 = (workspace_area2 >= (objects_info[i-1]["depth"] + threshold)) & (workspace_area2 <= (obj["depth"] + threshold))
                else:
                    print("É igual")
                    mask2 = (workspace_area2 >= (obj["depth"] - threshold)) & (workspace_area2 <= (obj["depth"] + threshold))
            
            binary = mask2.astype(numpy.uint8) * 255

            # Remove ruído pequeno
            element_open = numpy.ones((3, 3), numpy.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, element_open)

            # Fecha buracos e regulariza a forma
            element_close = numpy.ones((7, 7), numpy.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, element_close)

            contour, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for j, c in enumerate(contour):
                colorToDepth_copy4 = colorToDepthFrame.copy()
                
                cv2.drawContours(colorToDepth_copy4, [c], -1, (0, 255, 0), 2)
                
                texto = f"{float(obj['depth']):.1f}"
                cv2.putText(colorToDepth_copy4, texto, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 6, cv2.LINE_AA)
                cv2.putText(colorToDepth_copy4, texto, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2, cv2.LINE_AA)
                
                cv2.imwrite(f"DEPTHS{i}_contour{j}.png", colorToDepth_copy4)

            print("Depth:", obj["depth"])

            print("-------------------------------------------------------------------")
            
            shifted_contours_sorted = sorted(contour, key=lambda x: len(x), reverse=True)

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
                if not comparisonCaliImageCurrImage(colorFrame, calibrationColorFrame, depthFrame, calibrationDepthFrame, box_scaled, c):
                    print("Não passou no teste")
                    continue

                if not is_valid_area(c):
                    print("Contornos Inválidos")
                    continue

                bbox_c = get_bbox(c)

                for i_prev_obj, prev_list in enumerate(contours):
                    print("Watching Previous...")
                    for prev_c in prev_list:
                        bbox_prev = get_bbox(prev_c)
                        print("Wotefoque")
                        boxesOverlap, colorToDepth_copy2 = contours_overlap_by_points(c, prev_c, colorToDepth_copy2)
                        print("Previous Depth:", depths[i_prev_obj])
                        if boxesOverlap: #or contourDifference < 0.02:
                            #shouldMerge?
                            if obj['depth'] - 5 <= depths[i_prev_obj] + threshold:
                                print("Merge is emminent. Prepare for merging...")
                                
                                pending_merges.append({
                                    "current_index": curr_index,
                                    "prev_index": i_prev_obj
                                })
                            else:
                                belongs_to_previous = True
                                print("Pertence ao anterior o macaco")
                            break
                        # if abs(obj['depth'] - depths[i_prev_obj]) <= 5:
                        #     depth_between_contours = isThere_A_Object(c, prev_c, depthFrame)
                        #     if depth_between_contours < obj['depth']:
                        #         print("Merge is emminent. Prepare for merging...")
                            
                        #         pending_merges.append({
                        #             "current_index": curr_index,
                        #             "prev_index": i_prev_obj
                        #         })
                        if too_close(bbox_c, bbox_prev):
                            belongs_to_previous = True
                            print("Too Close")
                            break
                        print("Não pertence")
                        
                    if belongs_to_previous:
                        break
                if not belongs_to_previous:
                    print("New")
                    workspace_warning = obj["workspace_limits"]
                    ws_poly = numpy.array(workspace_warning, dtype = numpy.int32)
                    value = False

                    for pt in box:
                        x, y = int(pt[0]), int(pt[1])

                        if cv2.pointPolygonTest(ws_poly, (x, y), False) < 0:
                            value = True
                            print("Out of Line")
                            break

                    if not value:
                        print("Adicionar ao Conjunto")
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
                        print("Mean Depth:", mean_depth)

                        depths.append(mean_depth)
                        #depths.append(obj["depth"])
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
                img = numpy.zeros((480, 640, 3), dtype=numpy.uint8)
                merged_contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

                merged_contour = max(merged_contours, key=cv2.contourArea)          
                cv2.drawContours(img, [merged_contour], -1, (0, 0, 255), 2)

                cv2.imwrite(f"merged.png", img)

                A = cv2.contourArea(c)
                B = cv2.contourArea(prev_c)

                if A > B:
                    contours[current_index] = [merged_contour]

                    depths[current_index] = min(depths[current_index], depths[prev_index])

                    to_delete.add(prev_index)

                    print(f"Merged previous {prev_index} into current {current_index}")

                else:
                    contours[prev_index] = [merged_contour]

                    depths[prev_index] = min(depths[current_index], depths[prev_index])

                    to_delete.add(current_index)

                    print(f"Merged current {current_index} into previous {prev_index}")

            for idx in sorted(to_delete, reverse=True):
                del contours[idx]
                del depths[idx]
                del box_ws[idx]
                del object_outOfLine[idx]
                del binaryImgs[idx]

            print("-------------------------------------------------------------------")    

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
            #box = numpy.round(box).astype(numpy.int32)

            cv2.drawContours(colorToDepth_copy2, [box_scaled], 0, (0, 0, 0), 16)
            cv2.drawContours(colorToDepth_copy2, [box_scaled], 0, (255, 255, 0), 8)
            #cv2.drawContours(colorToDepth_copy, [box], 0,  (0, 255, 0), 2)

    elif volumeMode == "Real" or volumeMode == "Multi Bundle":
        # Separar objetos com a mesma profundidade :D
        # if volumeMode == "Real":
        #     contours_to_process = []
            # for i, cont in enumerate(contours):
            #     depth_img = depthFrame.copy()
            #     mask = numpy.zeros(depth_img.shape, dtype=numpy.uint8)

            #     cv2.drawContours(mask, cont, -1, 255, -1)

            #     depth_blur = cv2.bilateralFilter(depth_img.astype(numpy.float32), 9, 75, 75)

            #     sobelx = cv2.Sobel(depth_blur, cv2.CV_64F, 1, 0, ksize=3)
            #     sobely = cv2.Sobel(depth_blur, cv2.CV_64F, 0, 1, ksize=3)
            #     gradient_magnitude = numpy.sqrt(sobelx**2 + sobely**2)

            #     gradient_scaled = numpy.uint8(255 * (gradient_magnitude / gradient_magnitude.max()))

            #     _, edges = cv2.threshold(gradient_scaled, 50, 255, cv2.THRESH_BINARY)

            #     edges_inv = cv2.bitwise_not(edges)

            #     mask_separada = cv2.bitwise_and(mask, edges_inv)

            #     kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            #     mask_separada = cv2.morphologyEx(mask_separada, cv2.MORPH_OPEN, kernel)

            #     novos_contornos, _ = cv2.findContours(mask_separada, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            #     colorTD = colorToDepthFrame.copy()
            #     cv2.drawContours(colorTD, novos_contornos, -1, (0, 255, 0), 2)
            #     cv2.imwrite(f"ContoursDepth{i}.png", colorTD)

                # binary = binaryImgs[i]
                # dist = cv2.distanceTransform(binary, cv2.DIST_L2, 5)

                # dist_norm = cv2.normalize(
                #     dist,
                #     None,
                #     0,
                #     255,
                #     cv2.NORM_MINMAX
                # ).astype(numpy.uint8)

                # cv2.imwrite(f"distance{i}.png", dist_norm)

                # _, sure_fg = cv2.threshold(
                #     dist,
                #     0.5 * dist.max(),
                #     255,
                #     0
                # )

                # sure_fg = sure_fg.astype(numpy.uint8)

                # cv2.imwrite(f"sure_fg{i}.png", sure_fg)

                # num_labels, labels = cv2.connectedComponents(
                #     sure_fg.astype(numpy.uint8)
                # )

                # print(num_labels)

        #         if is_suspect_blob(cont[0], colorToDepthFrame):
        #             print("Inside")
        #             split_masks = split_contours(cont[0])

        #             if split_masks is not None:
        #                 for c in split_masks:
        #                     c = numpy.array(c, dtype=numpy.int32).reshape((-1, 1, 2))
        #                     contours_to_process.append([c])
        #                     depths.append(depths[-1])
        #             else:
        #                 contours_to_process.append(cont)
        #         else:
        #             print("Outside")
        #             contours_to_process.append(cont)

        #     contours = contours_to_process

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

                    box_i = cv2.boxPoints(cv2.minAreaRect(all_contours[idx]))
                    box_j = cv2.boxPoints(cv2.minAreaRect(all_contours[j]))

                    if overlap_ratio(box_i, box_j) > OVERLAP_RATIO or intersection_edge(box_i, box_j, depthFrame):
                        stack.append(j)

            groups.append(group)

        for obj_id, group in enumerate(groups, start=1):
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

    elif volumeMode == "Individual":
        # contours_to_process = []

        # for cont in contours:
        #     if is_suspect_blob(cont[0], colorToDepthFrame):
        #         split_masks = split_contours(cont[0])

        #         for c in split_masks:
        #             c = numpy.array(c, dtype=numpy.int32).reshape((-1, 1, 2))
        #             contours_to_process.append([c])
        #             depths.append(depths[-1])
        #     else:
        #         contours_to_process.append(cont)

        # if contours_to_process is not None:
        #     contours = contours_to_process

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

######################
def is_suspect_blob(c, ctd):
    image = ctd.copy()

    perimeter = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.02 * perimeter, True)

    pts = approx.reshape(-1, 2)

    for x, y in pts:
        cv2.circle(image, (x, y), 5, (0, 0, 255), -1)

    cv2.drawContours(image, [approx], -1, (0,255,0), 2)
    cv2.imwrite("Approx.png", image)

    return len(approx) > 4

def split_contours(c):
    points_to_analize = []
    contour = []
    possibleContour = []
    perimeter = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.02 * perimeter, True)

    pts = approx.reshape(-1, 2).tolist()

    points_to_analize = pts.copy()
    remaining = points_to_analize.copy()

    if len(points_to_analize) > 4:
        while len(points_to_analize) >= 4:
            if len(possibleContour) == 0:
                possibleContour.append(remaining[0])
                remaining.pop(0)
            else:
                if len(possibleContour) == 1 or len(possibleContour) == 3:
                    print("X")
                    print("0/2 PossibleContour-1", possibleContour[-1])
                    point = same_x(possibleContour[-1], remaining)
                    if point is not None:
                        possibleContour.append(point)
                        if point in remaining:
                            remaining.remove(point)
                if len(possibleContour) == 2:
                    print("Y")
                    print("1 PossibleContour-1", possibleContour[-1])
                    point = same_y(possibleContour[-1], remaining)
                    if point is not None:
                        possibleContour.append(point)
                        if point in remaining:
                            remaining.remove(point)

            if len(possibleContour) == 4:
                print("3 PossibleContour-1", possibleContour[-1])
                #print("Trying")
                if abs(possibleContour[-1][1] - possibleContour[0][1]) <= 10:
                    contour.append(possibleContour.copy())
                    points_to_analize.remove(possibleContour[0])
                    points_to_analize.remove(possibleContour[1])
                    points_to_analize.remove(possibleContour[2])
                    points_to_analize.remove(possibleContour[3])
                    possibleContour.clear()
                else:
                    if possibleContour[2][1] > possibleContour[-1][1]:
                        tempContour = []
                        if possibleContour[0][1] > possibleContour[-1][1]:
                            x = possibleContour[2][0]
                            y = possibleContour[0][1]
                            VP = [x, y]
                            tempContour.append(possibleContour[0])
                            tempContour.append(possibleContour[1])
                            tempContour.append(possibleContour[2])
                            tempContour.append(VP)
                            contour.append(tempContour.copy())
                        
                            points_to_analize.remove(possibleContour[0])
                            points_to_analize.remove(possibleContour[1])
                            points_to_analize.remove(possibleContour[2])
                            points_to_analize.append(VP)

                        else:
                            x = possibleContour[1][0]
                            y = possibleContour[-1][1]
                            VP = [x, y]
                            tempContour.append(possibleContour[1])
                            tempContour.append(possibleContour[2])
                            tempContour.append(possibleContour[3])
                            tempContour.append(VP)
                            contour.append(tempContour.copy())

                            points_to_analize.remove(possibleContour[1])
                            points_to_analize.remove(possibleContour[2])
                            points_to_analize.remove(possibleContour[3])
                            points_to_analize.append(VP)

                        possibleContour.clear()
                        print("Contorno Adicionado")
                    else:
                        tempFirst = possibleContour[2]
                        possibleContour.clear()
                        possibleContour.append(tempFirst)
                        print("Temporary PossibleContour-1", possibleContour[-1])
                        
                remaining = points_to_analize.copy()

    return contour

def same_x(ref, remaining, tolerance = 10):
    best = None
    best_dist = float("inf")

    if ref is not None:
        rx, ry = ref

        for p in remaining:
            if numpy.array_equal(p, ref):
                continue

            x, y = p

            if abs(x - rx) <= tolerance:
                d = abs(x - rx)
                if d < best_dist:
                    best = p
                    best_dist = d
                
    return best

def same_y(ref, remaining, tolerance = 10):

    best = None
    best_dist = float("inf")

    if ref is not None:
        rx, ry = ref

        for p in remaining:
            if numpy.array_equal(p, ref):
                continue

            x, y = p

            if abs(y - ry) <= tolerance:
                d = abs(y - ry)
                if d < best_dist:
                    best = p
                    best_dist = d
                
    return best

def isThere_A_Object(c, prev_c, depthFrame):
    depth_img = depthFrame.copy()
    mask1 = numpy.zeros(depth_img.shape, dtype=numpy.uint8)
    mask2 = numpy.zeros(depth_img.shape, dtype=numpy.uint8)

    cv2.drawContours(mask1, [c], -1, 1, -1)
    cv2.drawContours(mask2, [prev_c], -1, 1, -1)

    union = cv2.bitwise_or(mask1, mask2)
    between = (union == 0)

    x, y, w, h = cv2.boundingRect(numpy.vstack((c, prev_c)))
    roi_between = between[y: y+h, x: x+w]
    roi_depth = depth_img[y: y+h, x: x+w]

    between_depths = roi_depth[roi_between]

    depth_between_contours = numpy.mean(between_depths)
    print("Depth_Between:", depth_between_contours)

    return depth_between_contours