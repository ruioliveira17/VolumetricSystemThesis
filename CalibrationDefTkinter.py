from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python/Samples/DS86/FrameViewer')
from GetFrame import getFrame

import cv2
import numpy

x_area = 0
y_area = 0
x_area_plus_width = 0
y_area_plus_height = 0

detection_area = 0

def mask(camera, get_lower, get_upper, colorSlope):
    global x_area, y_area, x_area_plus_width, y_area_plus_height, detection_area
    lower = get_lower()
    upper = get_upper()

    center_x = 0
    center_y = 0

    x_area = None
    y_area = None
    x_area_plus_width = None
    y_area_plus_height = None

    colorToDepthFrame = None
    depthFrame = None 
    colorFrame = None

    try:
        colorToDepthFrame, depthFrame, colorFrame = getFrame(camera)
        colorToDepthFrame = cv2.resize(colorToDepthFrame, (640, 480))

        center_x = int((colorToDepthFrame.shape[1]) / 2)
        center_y = int((colorToDepthFrame.shape[0]) / 2)

        hsv_frame = cv2.cvtColor(colorToDepthFrame, cv2.COLOR_BGR2HSV)

        # ------------------ ÁREA EXTERIOR -------------------

        mask_hsv = cv2.inRange(hsv_frame, lower, upper)

        res = cv2.bitwise_and(colorToDepthFrame, colorToDepthFrame, mask=mask_hsv)

        imgray = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(imgray, 127, 255, 0)

        colorToDepthFrame_copy = colorToDepthFrame.copy()
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x_area, y_area, wbound, hbound = cv2.boundingRect(largest_contour)
            x_area_plus_width = x_area + wbound
            y_area_plus_height = y_area + hbound
            if x_area is not None and y_area is not None and x_area_plus_width is not None and y_area_plus_height is not None:
                cv2.rectangle(colorToDepthFrame_copy, (x_area, y_area), (x_area_plus_width, y_area_plus_height), (255, 0, 0), 2)
                detection_area =  (x_area, y_area, x_area_plus_width, y_area_plus_height)       

        # PONTO CENTRAL
        
        cv2.circle(colorToDepthFrame_copy, (center_x, center_y), radius=3, color=(255, 0, 0), thickness=1)

        depthFrame = cv2.resize(depthFrame, (640, 480))
       
        img = numpy.int32(depthFrame)
        img = img*255/colorSlope
        img = numpy.clip(img, 0, 255)
        img = numpy.uint8(img)
        depthFrame = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)

        depthFrame_copy = depthFrame.copy()
        if x_area is not None and y_area is not None and x_area_plus_width is not None and y_area_plus_height is not None:
            cv2.rectangle(depthFrame_copy, (x_area, y_area), (x_area_plus_width, y_area_plus_height), (255, 0, 0), 2)
            cv2.rectangle(depthFrame_copy, (x_area + 3, y_area + 3), (x_area_plus_width - 3, y_area_plus_height - 3), (0, 0, 255), 2)

        key = cv2.waitKey(1)
        
        return res, colorToDepthFrame_copy, depthFrame_copy  
                
    except Exception as e :
        print(e)
    finally :
        print('end')

def calibrate(camera, get_lower, get_upper, colorSlope):
    global x_area, y_area, x_area_plus_width, y_area_plus_height, detection_area
    lower = get_lower()
    upper = get_upper()

    center_aligned = False # Ponto central tem a cor da calibração

    workspace_interrupted = True # Fita não é interrompida
    workspace_free = False # Toda a área tem a mesma profundidade
    workspace_clear = False # Profundidade é igual em toda a workspace e borda amarela totalmente detetada

    workspace_depth = 0
    center_y = 0

    forced_exiting = None
    
    calibrated = False

    colorToDepthFrame = None
    depthFrame = None 
    colorFrame = None

    try:
        colorToDepthFrame, depthFrame, colorFrame = getFrame(camera)
        
        colorToDepthFrame = cv2.resize(colorToDepthFrame, (640, 480))

        center_x = int((colorToDepthFrame.shape[1]) / 2)
        center_y = int((colorToDepthFrame.shape[0]) / 2)

        hsv_frame = cv2.cvtColor(colorToDepthFrame, cv2.COLOR_BGR2HSV)

        h_min, s_min, v_min = lower
        h_max, s_max, v_max = upper

        # VERIFICAÇÃO ÁREA WORKSPACE DETETÁVEL NÃO INTERROMPIDA   

        # ---------------- VERIFICAÇÃO COR ------------------

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

        # VERIFICAÇÃO PONTO CENTRAL

        neighbors = hsv_frame[max(0, center_y-3):center_y+4, max(0, center_x-3):center_x+4]
        mask_center = (((neighbors[:,:,0] >= h_min) & (neighbors[:,:,0] <= h_max)) & ((neighbors[:,:,1] >= s_min) & (neighbors[:,:,1] <= s_max)) & ((neighbors[:,:,2] >= v_min) & (neighbors[:,:,2] <= v_max)))

        center_x_max = x_area + ((x_area_plus_width - x_area)/2) + 5
        center_x_min = x_area + ((x_area_plus_width - x_area)/2) - 5
        center_y_max = y_area + ((y_area_plus_height - y_area)/2) + 5
        center_y_min = y_area + ((y_area_plus_height - y_area)/2) - 5

        if numpy.any(mask_center) and (center_x <= center_x_max) and (center_x >= center_x_min) and (center_y <= center_y_max) and (center_y >= center_y_min):
            center_aligned = True
        else:
            center_aligned = False

        # DEPTH
        
        depthFrame = cv2.resize(depthFrame, (640, 480))
        
        # Profundidade "Centro"

        workspace_center_neighbors = depthFrame[max(0, center_y-3):center_y+4, max(0, center_x-3):center_x+4]
        centerDepth_valid_values = workspace_center_neighbors[(workspace_center_neighbors >= 150) & (workspace_center_neighbors <= colorSlope)]
        if centerDepth_valid_values.size > 0:
            workspace_depth = numpy.mean(centerDepth_valid_values)

        workspace_region = depthFrame[y_area:y_area_plus_height, x_area:x_area_plus_width]
        
        valid_values = workspace_region[(workspace_region >= 150) & (workspace_region <= colorSlope)]
        
        if valid_values.size > 0:
            avg_depth = numpy.mean(valid_values) # média da profundidade
            print("Avg Depth:", avg_depth)
            print("Workspace Depth", workspace_depth)
            count = numpy.sum(numpy.abs(valid_values - workspace_depth) <= 10)
            proportion_valid = count / valid_values.size
            print("Proporção Profundidade:", proportion_valid)

            if proportion_valid >= 0.9:
                workspace_free = True
                workspace_depth = avg_depth
            else:
                workspace_free = False
                
        img = numpy.int32(depthFrame)
        img = img*255/colorSlope
        img = numpy.clip(img, 0, 255)
        img = numpy.uint8(img)
        depthFrame = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)

        depthFrame_copy = depthFrame.copy()
        cv2.rectangle(depthFrame_copy, (x_area, y_area), (x_area_plus_width, y_area_plus_height), (255, 0, 0), 2)
        cv2.rectangle(depthFrame_copy, (x_area + 3, y_area + 3), (x_area_plus_width - 3, y_area_plus_height - 3), (0, 0, 255), 2)

        #cv2.imshow("Depth Image", depthFrame)

        if (not workspace_interrupted) and workspace_free:
            workspace_clear = True
        else:
            workspace_clear = False

        if workspace_clear and center_aligned:
            calibrated = True
        else:
            calibrated = False

        key = cv2.waitKey(1)
        #return detection_area, workspace_depth, forced_exiting
        #if  key == ord('c'):
        #    print("----------------------------------------------------------------")
        if calibrated is True:
            print("System calibrated successfully!")
            print("Center is aligned")
            print("Workspace is aligned! Depth:", workspace_depth, "Workspace:", detection_area)
            forced_exiting = 0
            cv2.destroyAllWindows()
            print("---end---")
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

        return detection_area, workspace_depth, forced_exiting
        #elif key == 27:
        #    print("----------------------------------------------------------------")
        #    print("Forced exiting calibration")
        #    forced_exiting = 1
        #    cv2.destroyAllWindows()
        #    print("---end---")
        #    return detection_area, workspace_depth, forced_exiting
        #else:
        #    current_canvas.after(50, calibrate, camera, get_lower, get_upper, colorSlope, current_canvas)   
                
    except Exception as e :
        print(e)
    finally :
        print('end')

    #return detection_area, workspace_depth, forced_exiting