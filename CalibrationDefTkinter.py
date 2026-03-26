from pickle import FALSE, TRUE
import sys
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "Python", "Samples", "DS86", "FrameViewer"))
#from GetFrame import getFrame
#from FrameState import frameState

import cv2
import numpy
import requests

from color_presets import COLOR_PRESETS

x_area = 0
y_area = 0
x_area_plus_width = 0
y_area_plus_height = 0

detection_area = None
workspace_depth = None

color_shape = (1200, 1600, 3)
colorToDepth_shape   = (480, 640, 3)
depth_shape = (480, 640)

def maskAPI(colorToDepthFrame, lower, upper, color, cx_d, cy_d):
    detection_area = None
    #x_area = None
    #y_area = None
    #x_area_plus_width = None
    #y_area_plus_height = None

    try:
        colorToDepthFrame = cv2.resize(colorToDepthFrame, (640, 480))

        hsv_frame = cv2.cvtColor(colorToDepthFrame, cv2.COLOR_BGR2HSV)

        # ------------------ ÁREA EXTERIOR -------------------

        mask_hsv = cv2.inRange(hsv_frame, lower, upper)
        if color == "Red":
            preset = COLOR_PRESETS["Red2"]
            lower = numpy.array(preset["lower"])
            upper = numpy.array(preset["upper"])

            mask_hsv2 = cv2.inRange(hsv_frame, lower, upper)

            mask_hsv = mask_hsv | mask_hsv2

        result = cv2.bitwise_and(colorToDepthFrame, colorToDepthFrame, mask=mask_hsv)

        imgray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(imgray, 127, 255, 0)

        colorToDepthFrame_copy = colorToDepthFrame.copy()
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            """####
            x_area, y_area, wbound, hbound = cv2.boundingRect(largest_contour)
            x_area_plus_width = x_area + wbound
            y_area_plus_height = y_area + hbound

            if x_area is not None and y_area is not None and x_area_plus_width is not None and y_area_plus_height is not None:
                cv2.rectangle(colorToDepthFrame_copy, (x_area, y_area), (x_area_plus_width, y_area_plus_height), (255, 0, 0), 2)
                detection_area =  (x_area, y_area, x_area_plus_width, y_area_plus_height)       
            ####"""
            rect = cv2.minAreaRect(largest_contour)

            detection_area = cv2.boxPoints(rect)
            detection_area = numpy.int32(detection_area)

            cv2.drawContours(colorToDepthFrame_copy, [detection_area], 0, (255, 0, 0), 2)

        # PONTO CENTRAL
        
        cv2.circle(colorToDepthFrame_copy, (cx_d, cy_d), radius=3, color=(255, 255, 255), thickness=1)
        
        #return result, colorToDepthFrame_copy, depthFrame_copy, detection_area
        return result, colorToDepthFrame_copy, detection_area  
                
    except Exception as e :
        print(e)
    finally :
        print('end')

def manualWorkspaceDraw(colorToDepthFrame, detection_area, cx_d, cy_d):
    try:
        colorToDepthFrame = cv2.resize(colorToDepthFrame, (640, 480))

        colorToDepthFrame_copy = colorToDepthFrame.copy()
        
        cv2.drawContours(colorToDepthFrame_copy, [detection_area], 0, (255, 0, 0), 2)

        # PONTO CENTRAL
        
        cv2.circle(colorToDepthFrame_copy, (cx_d, cy_d), radius=3, color=(255, 255, 255), thickness=-1)
        
        return colorToDepthFrame_copy, detection_area
                
    except Exception as e :
        print(e)
    finally :
        print('end')

def calibrateAPI(colorToDepthFrame, depthFrame, colorFrame, detection_area, lower, upper, colorSlope, cx_d, cy_d, caliMode):
    center_aligned = False # Ponto central tem a cor da calibração

    workspace_interrupted = True # Fita não é interrompida
    workspace_free = False # Toda a área tem a mesma profundidade
    workspace_clear = False # Profundidade é igual em toda a workspace e borda amarela totalmente detetada
    
    calibrated = False

    workspace_depth = None

    #x_area, y_area, x_area_plus_width, y_area_plus_height = detection_area

    try:
        colorToDepthFrame = cv2.resize(colorToDepthFrame, (640, 480))

        hsv_frame = cv2.cvtColor(colorToDepthFrame, cv2.COLOR_BGR2HSV)

        h_min, s_min, v_min = lower
        h_max, s_max, v_max = upper

        # VERIFICAÇÃO ÁREA WORKSPACE DETETÁVEL NÃO INTERROMPIDA
        detection_area = numpy.array(detection_area, dtype=numpy.int32).reshape((-1, 1, 2))
        mask = numpy.zeros((480, 640), dtype = numpy.uint8)
        cv2.fillPoly(mask, [detection_area], 255)

        workspace_region = depthFrame[mask == 255]

        if caliMode == "Automatic":

            # ---------------- VERIFICAÇÃO COR ------------------

            """####
                # ------------ Lateral Esquerda ---------------
            LE = hsv_frame[y_area: y_area_plus_height, x_area + 3]
            mask_le = (((LE[:,0] >= h_min) & (LE[:,0] <= h_max)) & ((LE[:,1] >= s_min) & (LE[:,1] <= s_max)) & ((LE[:,2] >= v_min) & (LE[:,2] <= v_max)))

            valid_pixels_le = numpy.count_nonzero(mask_le)
            total_pixels_le = LE.shape[0]
            if total_pixels_le > 0:
                proportion_le = valid_pixels_le / total_pixels_le

                # ------------------ Cima ---------------------
            C = hsv_frame[y_area + 3, x_area: x_area_plus_width]
            mask_c = (((C[:,0] >= h_min) & (C[:,0] <= h_max)) & ((C[:,1] >= s_min) & (C[:,1] <= s_max)) & ((C[:,2] >= v_min) & (C[:,2] <= v_max)))

            valid_pixels_c = numpy.count_nonzero(mask_c)
            total_pixels_c = C.shape[0]
            if total_pixels_c > 0:
                proportion_c = valid_pixels_c / total_pixels_c

                # ------------ Lateral Direita ---------------
            LD = hsv_frame[y_area: y_area_plus_height, x_area_plus_width - 3]
            mask_ld = (((LD[:,0] >= h_min) & (LD[:,0] <= h_max)) & ((LD[:,1] >= s_min) & (LD[:,1] <= s_max)) & ((LD[:,2] >= v_min) & (LD[:,2] <= v_max)))

            valid_pixels_ld = numpy.count_nonzero(mask_ld)
            total_pixels_ld = LD.shape[0]
            if total_pixels_ld > 0:
                proportion_ld = valid_pixels_ld / total_pixels_ld

                # ----------------- Baixo -------------------
            B = hsv_frame[y_area_plus_height - 3, x_area: x_area_plus_width]
            mask_b = (((B[:,0] >= h_min) & (B[:,0] <= h_max)) & ((B[:,1] >= s_min) & (B[:,1] <= s_max)) & ((B[:,2] >= v_min) & (B[:,2] <= v_max)))

            valid_pixels_b = numpy.count_nonzero(mask_b)
            total_pixels_b = B.shape[0]
            if total_pixels_b > 0:
                proportion_b = valid_pixels_b / total_pixels_b

            if (proportion_le >= 0.95) and (proportion_c >= 0.95) and (proportion_ld >= 0.95) and (proportion_b >= 0.95):
                workspace_interrupted = False
                print("Proporções:", proportion_le, proportion_c, proportion_ld, proportion_b)
            else:
                workspace_interrupted = True
                print("Proporções:", proportion_le, proportion_c, proportion_ld, proportion_b)
            ####"""
            kernel = numpy.ones((3,3), numpy.uint8)
            erode_exterior = cv2.erode(mask, kernel, iterations=3)
            erode_interior = cv2.erode(erode_exterior, kernel, iterations=2)

            border = cv2.subtract(erode_exterior, erode_interior)

            border_pixels = hsv_frame[border == 255]

            mask_color = (
                (border_pixels[:,0] >= h_min) & (border_pixels[:,0] <= h_max) &
                (border_pixels[:,1] >= s_min) & (border_pixels[:,1] <= s_max) &
                (border_pixels[:,2] >= v_min) & (border_pixels[:,2] <= v_max)
            )

            proportionColor_valid = numpy.sum(mask_color) / border_pixels.shape[0]

            debug = colorToDepthFrame.copy()
            debug[border == 255] = (0, 0, 255)  # vermelho sobre a fita
            cv2.imwrite("ZED.png", debug)

            print("Sum Mask Color:", numpy.sum(mask_color))
            print("BorderPixels:", border_pixels.shape[0])
            print("Proporção Cor:", proportionColor_valid)

            if proportionColor_valid >= 0.95:
                workspace_interrupted = False
            else:
                workspace_interrupted = True

        else:
            workspace_interrupted = False

        # VERIFICAÇÃO PONTO CENTRAL

        #center_x_max = x_area + ((x_area_plus_width - x_area)/2) + 5
        #center_x_min = x_area + ((x_area_plus_width - x_area)/2) - 5
        #center_y_max = y_area + ((y_area_plus_height - y_area)/2) + 5
        #center_y_min = y_area + ((y_area_plus_height - y_area)/2) - 5

        #if (cx_d <= center_x_max) and (cx_d >= center_x_min) and (cy_d <= center_y_max) and (cy_d >= center_y_min):

        #if (cx_d <= x_area_plus_width) and (cx_d >= x_area) and (cy_d <= y_area_plus_height) and (cy_d >= y_area):
        #    center_aligned = True
        #else:
        #    center_aligned = False

        if cv2.pointPolygonTest(detection_area, (cx_d, cy_d), False) >= 0:
            center_aligned = True
        else:
            center_aligned = False

        # Depth
        
        depthFrame = cv2.resize(depthFrame, (640, 480))

        # Profundidade "Centro"

        workspace_center_neighbors = depthFrame[max(0, cy_d-3):cy_d+4, max(0, cx_d-3):cx_d+4]
        centerDepth_valid_values = workspace_center_neighbors[(workspace_center_neighbors >= 150) & (workspace_center_neighbors <= colorSlope)]
        if centerDepth_valid_values.size > 0:
            workspace_depth = numpy.mean(centerDepth_valid_values)
        
        valid_values = workspace_region[(workspace_region >= 15) & (workspace_region <= colorSlope)]
        
        if valid_values.size > 0:
            avg_depth = numpy.mean(valid_values) # média da profundidade
            print("Avg Depth:", avg_depth)
            print("Workspace Depth", workspace_depth)
            #count = numpy.sum(numpy.abs(valid_values - workspace_depth) <= 10)
            count = numpy.sum(numpy.abs(valid_values - workspace_depth) <= 50)
            print("Count:", count)
            print("Size:", valid_values.size)
            proportion_valid = round(count / valid_values.size, 2)
            print("Proporção Profundidade:", proportion_valid)

            if proportion_valid >= 0.98:
                workspace_free = True
                workspace_depth = avg_depth
            else:
                workspace_free = False
                
        #img = numpy.int32(depthFrame)
        #img = img*255/colorSlope
        #img = numpy.clip(img, 0, 255)
        #img = numpy.uint8(img)
        #depthFrame = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)

        #depthFrame_copy = depthFrame.copy()
        #cv2.rectangle(depthFrame_copy, (x_area, y_area), (x_area_plus_width, y_area_plus_height), (255, 0, 0), 2)
        #cv2.rectangle(depthFrame_copy, (x_area + 3, y_area + 3), (x_area_plus_width - 3, y_area_plus_height - 3), (0, 0, 255), 2)

        if (not workspace_interrupted) and workspace_free:
            workspace_clear = True
        else:
            workspace_clear = False

        if workspace_clear and center_aligned:
            calibrated = True
        else:
            calibrated = False
            detection_area = None
            workspace_depth = None

        key = cv2.waitKey(1)

        if calibrated is True:
            print("System calibrated successfully!")
            print("Center is aligned")
            print("Workspace is aligned! Depth:", workspace_depth, "Workspace:", detection_area)
            cv2.destroyAllWindows()
            print("---end---")
            
            return detection_area, workspace_depth, center_aligned, workspace_clear, colorFrame
        else:
            print("System isnt calibrated!")
            print("Try Again!")
            print("Remember: central point must be detected, workspace should be empty and all the yellow tape must be detected...")
            if center_aligned is True:
                print("Center Aligned!")
            else: 
                print("Center not Aligned!")
            if workspace_clear is True:
                print("Workspace is Empty!")
            else:
                print("Clear Workspace!")
                
    except Exception as e :
        print(e)
    finally :
        print('end')

    return detection_area, workspace_depth, center_aligned, workspace_clear, colorFrame