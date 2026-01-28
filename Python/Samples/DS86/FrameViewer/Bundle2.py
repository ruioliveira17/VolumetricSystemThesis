from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2
from FrameState import frameState

def depthImg(hdrDepth, colorSlope):
    img = numpy.int32(hdrDepth)
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

def boxes_overlap(box1, box2):
    xmin1, xmax1, ymin1, ymax1 = box1 #Current
    xmin2, xmax2, ymin2, ymax2 = box2 #Previous

    print("Atual:", xmin1, xmax1, ymin1, ymax1)
    print("Anterior:", xmin2, xmax2, ymin2, ymax2)
    
    if ((xmin2 <= xmin1 <= xmax2) or (ymin2 <= ymin1 <= ymax2) or (ymin2 <= ymax1 <= ymax2) or (xmin2 <= xmax1 <= xmax2)):
        return True
    return False

def contours_overlap_by_points(c, prev_c, hdrColor_copy, min_ratio = 0.4):
    inside = 0
    total = len(c)
    print("Total", total)

    hull = cv2.convexHull(prev_c)

    cv2.drawContours(hdrColor_copy, [hull], 0, (255, 0, 0), 2)

    for p in c:
        x = int(p[0][0])
        y = int(p[0][1])

        #print("Dist:", cv2.pointPolygonTest(hull, (x,y), True))

        if cv2.pointPolygonTest(hull, (x, y), False) >= 0:
            inside += 1
            
    print("Inside", inside)
    print("Quanto?", inside / total)
    
    return (inside / total) >= min_ratio, hdrColor_copy

def is_valid_area(c, min_area = 150, min_points = 15):
    #n = len(c)
    #print("Pontos", n)

    a = cv2.contourArea(c)
    print("Area", a)

    #if n < min_points:
    #    return False
    if a < min_area:
        return False

    return True

def bundle(hdrColor, hdrDepth_img, objects_info, threshold, hdrDepth):
    contours = []
    ws_limits = []
    all_points_list = []
    shifted_contours = []
    correct_shifted_contours = []
    belongs_to_previous = False
    depths = []

    hdrColor_copy = hdrColor.copy()

    if len(objects_info) != 0:
        for obj in objects_info:

            x1, y1, x2, y2 = obj["workspace_limits"]
            workspace_area2 = hdrDepth[y1:y2, x1:x2]

            mask = (workspace_area2 >= (obj["depth"] - threshold)) & (workspace_area2 <= (obj["depth"] + threshold))

            depth_filtered = numpy.where(mask, workspace_area2, 0).astype(numpy.uint16)

            img = numpy.int32(depth_filtered)
            img = img*255/1500
            img = numpy.clip(img, 0, 255)
            img = numpy.uint8(img)
            hdrDepth_img = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)

            gray = cv2.cvtColor(hdrDepth_img, cv2.COLOR_BGR2GRAY)
        
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
                            a, hdrColor_copy = contours_overlap_by_points(c, prev_c, hdrColor_copy)
                            if a:
                                belongs_to_previous = True
                                print("Pertence ao anterior o macaco")
                                break
                        print("Não pertence")
                        belongs_to_previous = False
                    if belongs_to_previous:
                        break
                if not belongs_to_previous:
                    correct_shifted_contours = []
                    correct_shifted_contours.append(c)
                    print("Adicionar ao Conjunto")
                    belongs_to_previous = False
                    all_shifted_contours = numpy.vstack(correct_shifted_contours)
                    contours.append([all_shifted_contours])
                    ws_limits.append(obj["workspace_limits"])
                    depths.append(obj["depth"])
                    print("Número de Objetos no contours", len(contours))

            print("-------------------------------------------------------------------")

    #hdrColor_copy = hdrColor.copy()
    hdrColor_copy = cv2.resize(hdrColor_copy, (640, 480))

    for contour_list in contours:
        for c in contour_list:
            rect = cv2.minAreaRect(c)
            box = cv2.boxPoints(rect)
            box = numpy.round(box).astype(numpy.int32)
            cv2.drawContours(hdrColor_copy, [box], 0, (0, 255, 0), 2)
            frameState.colorToDepthFrameObject = hdrColor_copy

    all_points_list = [c for contour_list in contours for c in contour_list if c.size > 0]
    print("Número Objetos:", len(all_points_list))
    #print(all_points_list)

    hdrColor_copy = hdrColor.copy()
    hdrColor_copy = cv2.resize(hdrColor_copy, (640, 480))

    if len(all_points_list) > 0:
        all_points = numpy.vstack(all_points_list)

        rect = cv2.minAreaRect(all_points)
        box = cv2.boxPoints(rect)
        box = numpy.round(box).astype(numpy.int32)

        cv2.drawContours(hdrColor_copy, [box], 0,  (0, 255, 0), 2)
        frameState.colorToDepthFrameObjects = hdrColor_copy

    not_set = 1
    minimum_value = 6000
                    
    return minimum_value, not_set, all_points_list, ws_limits, depths