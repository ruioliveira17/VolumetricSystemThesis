from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2
from FrameState import frameState

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

    if (abs(xmin2 - xmin1) <= 3 and abs(ymin2 - ymin1) <= 3) or (abs(xmax2 - xmax1) <= 3 and abs(ymax2 - ymax1) <= 3):
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

    cv2.drawContours(colorToDepth_copy, [hull], 0, (255, 0, 0), 2)

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

def bundle(colorToDepthFrame, depthFrame, objects_info, colorSlope, volumeMode):
    contours = []
    box_ws = []
    box_limits = []
    shifted_contours = []
    correct_shifted_contours = []
    depths = []
    object_outOfLine = []
    belongs_to_previous = False

    colorToDepth_copy = colorToDepthFrame.copy()

    if len(objects_info) != 0:
        for obj in objects_info:

            x1, y1, x2, y2 = obj["workspace_limits"]
            workspace_area2 = depthFrame[y1:y2, x1:x2]

            mask = (workspace_area2 >= (obj["depth"] - 25)) & (workspace_area2 <= (obj["depth"] + 25))

            depth_filtered = numpy.where(mask, workspace_area2, 0).astype(numpy.uint16)

            depth_img = depthImg(depth_filtered, colorSlope)

            gray = cv2.cvtColor(depth_img, cv2.COLOR_BGR2GRAY)
        
            blur = cv2.GaussianBlur(gray, (15,15), 0)
            
            _, binary = cv2.threshold(blur, 140, 255, cv2.THRESH_BINARY)

            invBinary = cv2.bitwise_not(binary)

            element = numpy.ones((3, 3), numpy.uint8)
            morf = cv2.morphologyEx(invBinary, cv2.MORPH_GRADIENT, element)

            contour, _ = cv2.findContours(morf, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            shifted_contours = [c + numpy.array([[[x1, y1]]], dtype=numpy.int32) for c in contour]
            
            shifted_contours_sorted = sorted(shifted_contours, key=lambda x: len(x), reverse=True)

            print("Depth:", obj["depth"])
            print("-------------------------------------------------------------------")

            for c in shifted_contours_sorted:
                if not is_valid_area(c):
                    print("Contornos Inválidos")
                    continue

                bbox_c = get_bbox(c)

                for prev_list in contours:
                    for prev_c in prev_list:
                        bbox_prev = get_bbox(prev_c)

                        if boxes_overlap(bbox_c, bbox_prev):
                            print("Wotefoque")
                            boxesOverlap, colorToDepth_copy = contours_overlap_by_points(c, prev_c, colorToDepth_copy)
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

                    if ((bbox_c[0] < workspace_warning[0]) or (bbox_c[1] > workspace_warning[2]) or (bbox_c[2] < workspace_warning[1]) or (bbox_c[3] > workspace_warning[3])):
                        value = True
                    else:
                        value = False

                    object_outOfLine.append(value)

                    correct_shifted_contours = []
                    correct_shifted_contours.append(c)
                    print("Adicionar ao Conjunto")
                    belongs_to_previous = False
                    all_shifted_contours = numpy.vstack(correct_shifted_contours)
                    contours.append([all_shifted_contours])
                    box_ws.append(obj["workspace_limits"])
                    depths.append(obj["depth"])
                    print("Número de Objetos no contours", len(contours))

            print("-------------------------------------------------------------------")

    colorToDepth_copy = cv2.resize(colorToDepth_copy, (640, 480))

    for obj_id, contour_list in enumerate(contours, start=1):
        for c in contour_list:
            rect = cv2.minAreaRect(c)
            box = cv2.boxPoints(rect)
            box = numpy.round(box).astype(numpy.int32)
            cv2.drawContours(colorToDepth_copy, [box], 0, (0, 255, 0), 2)
            idx_y = numpy.argmin(box[:,1])
            idx_x = numpy.argmin(box[:,0])
            x, y = box[idx_x]
            x2, y2 = box[idx_y]
            if abs(x - x2) <= 20 and abs(y - y2) <= 20:
                print("Próx")
                cv2.putText(colorToDepth_copy, str(obj_id), (x + 8, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4, cv2.LINE_AA)
                cv2.putText(colorToDepth_copy, str(obj_id), (x + 8, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
            else:
                print("Afast")
                cv2.putText(colorToDepth_copy, str(obj_id), (x + 10, y + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4, cv2.LINE_AA)
                cv2.putText(colorToDepth_copy, str(obj_id), (x + 10, y + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
            frameState.colorToDepthFrameObject = colorToDepth_copy

    box_limits = [c for contour_list in contours for c in contour_list if c.size > 0]
    print("Número Objetos:", len(box_limits))

    colorToDepth_copy = colorToDepthFrame.copy()
    colorToDepth_copy = cv2.resize(colorToDepth_copy, (640, 480))

    if len(box_limits) > 0 and volumeMode == "Bundle":
        all_points = numpy.vstack(box_limits)

        rect = cv2.minAreaRect(all_points)
        box = cv2.boxPoints(rect)
        box = numpy.round(box).astype(numpy.int32)

        cv2.drawContours(colorToDepth_copy, [box], 0,  (0, 255, 0), 2)
        frameState.colorToDepthFrameObjects = colorToDepth_copy

    not_set = 1
    minimum_value = 6000
                    
    return minimum_value, not_set, box_ws, box_limits, depths, object_outOfLine