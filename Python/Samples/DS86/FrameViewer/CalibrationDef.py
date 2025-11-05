from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2

def calibrate(camera, colorSlope):

    center_aligned = False # Ponto central tem a cor da calibração

    workspace_interrupted = True # Fita não é interrompida
    workspace_free = False # Toda a área tem a mesma profundidade
    workspace_clear = False # Profundidade é igual em toda a workspace e borda amarela totalmente detetada

    workspace_depth = 0
    
    calibrated = False
    x_area = None

    def nothing(x):
        pass

    # Define os limites HSV
    cv2.namedWindow("Trackbars")
    cv2.createTrackbar("H min", "Trackbars", 0, 179, nothing)
    cv2.createTrackbar("H max", "Trackbars", 179, 179, nothing)
    cv2.createTrackbar("S min", "Trackbars", 0, 255, nothing)
    cv2.createTrackbar("S max", "Trackbars", 255, 255, nothing)
    cv2.createTrackbar("V min", "Trackbars", 0, 255, nothing)
    cv2.createTrackbar("V max", "Trackbars", 255, 255, nothing)

    try:
        while 1:
            ret, frameready = camera.VZ_GetFrameReady(c_uint16(1200))
            if  ret !=0:
                print("VZ_GetFrameReady failed:",ret)
                continue
            hasDepth=0
            hasColorToDepth = 0

            if  frameready.depth:      
                ret,depthframe = camera.VZ_GetFrame(VzFrameType.VzDepthFrame)
                if  ret == 0:
                    hasDepth=1
                   
                else:
                    print("get depth frame failed:",ret)

            if  frameready.color:      
                ret,rgbframe = camera.VZ_GetFrame(VzFrameType.VzTransformColorImgToDepthSensorFrame)
                if  ret == 0:
                    hasColorToDepth =1   
                else:
                    print("get color frame failed:",ret)

            if  hasColorToDepth==1:
                frametmp = numpy.ctypeslib.as_array(rgbframe.pFrameData, (1, rgbframe.width * rgbframe.height * 3))
                frametmp.dtype = numpy.uint8
                frametmp.shape = (rgbframe.height, rgbframe.width,3)
                frametmp = cv2.resize(frametmp, (640, 480))

                center_x = int((frametmp.shape[1]) / 2)
                center_y = int((frametmp.shape[0]) / 2)

                hsv_frame = cv2.cvtColor(frametmp, cv2.COLOR_BGR2HSV)

                h_min = cv2.getTrackbarPos("H min", "Trackbars")
                h_max = cv2.getTrackbarPos("H max", "Trackbars")
                s_min = cv2.getTrackbarPos("S min", "Trackbars")
                s_max = cv2.getTrackbarPos("S max", "Trackbars")
                v_min = cv2.getTrackbarPos("V min", "Trackbars")
                v_max = cv2.getTrackbarPos("V max", "Trackbars")

                lower = numpy.array([h_min, s_min, v_min])
                upper = numpy.array([h_max, s_max, v_max])

                # VERIFICAÇÃO ÁREA WORKSPACE DETETÁVEL NÃO INTERROMPIDA

                # ------------------ ÁREA EXTERIOR -------------------

                mask_hsv = cv2.inRange(hsv_frame, lower, upper)

                res = cv2.bitwise_and(frametmp, frametmp, mask=mask_hsv)

                imgray = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
                ret, thresh = cv2.threshold(imgray, 127, 255, 0)

                frame_copy = frametmp
                contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
                if contours:
                    largest_contour = max(contours, key=cv2.contourArea)
                    x_area, y_area, wbound, hbound = cv2.boundingRect(largest_contour)
                    x_area_plus_width = x_area + wbound
                    y_area_plus_height = y_area + hbound
                    cv2.rectangle(frame_copy, (x_area, y_area), (x_area_plus_width, y_area_plus_height), (255, 0, 0), 2)
                    detection_area =  (x_area, y_area, x_area_plus_width, y_area_plus_height)       

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

                cv2.circle(frametmp, (center_x, center_y), radius=3, color=(255, 0, 0), thickness=1)
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

                cv2.imshow("RGB Image", frametmp)
                cv2.imshow("Mask", res) 

            if  hasDepth==1:

                frametmp = numpy.ctypeslib.as_array(depthframe.pFrameData, (1, depthframe.width * depthframe.height * 2))
                frametmp.dtype = numpy.uint16
                frametmp.shape = (depthframe.height, depthframe.width)
                frametmp = cv2.resize(frametmp, (640, 480))
                
                # Profundidade "Centro"

                workspace_center_neighbors = frametmp[max(0, center_y-3):center_y+4, max(0, center_x-3):center_x+4]
                centerDepth_valid_values = workspace_center_neighbors[(workspace_center_neighbors >= 150) & (workspace_center_neighbors <= colorSlope)]
                if centerDepth_valid_values.size > 0:
                    workspace_depth = numpy.mean(centerDepth_valid_values)

                workspace_region = frametmp[y_area:y_area_plus_height, x_area:x_area_plus_width]
                
                valid_values = workspace_region[(workspace_region >= 150) & (workspace_region <= colorSlope)]
                
                if valid_values.size > 0:
                    avg_depth = numpy.mean(valid_values) # média da profundidade
                    print("Avg Depth:", avg_depth)
                    print("Workspace Depth", workspace_depth)
                    count = numpy.sum(numpy.abs(valid_values - workspace_depth) <= 10)
                    proportion_valid = count / valid_values.size
                    print("Proporção Profundidade:", proportion_valid)

                    if proportion_valid >= 0.85:
                        workspace_free = True
                        workspace_depth = avg_depth
                    else:
                        workspace_free = False
                        
                img = numpy.int32(frametmp)
                img = img*255/colorSlope
                img = numpy.clip(img, 0, 255)
                img = numpy.uint8(img)
                frametmp = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)

                frame_copy = frametmp
                cv2.rectangle(frame_copy, (x_area, y_area), (x_area_plus_width, y_area_plus_height), (255, 0, 0), 2)
                cv2.rectangle(frame_copy, (x_area + 3, y_area + 3), (x_area_plus_width - 3, y_area_plus_height - 3), (0, 0, 255), 2)

                cv2.imshow("Depth Image", frametmp)

            if (not workspace_interrupted) and workspace_free:
                workspace_clear = True
            else:
                workspace_clear = False

            if workspace_clear and center_aligned:
                calibrated = True
            else:
                calibrated = False

            key = cv2.waitKey(1)
            if  key == ord('c'):
                print("----------------------------------------------------------------")
                if calibrated is True:
                    print("System calibrated successfully!")
                    print("Center is aligned")
                    print("Workspace is aligned! Depth:", workspace_depth, "Workspace:", detection_area)
                    forced_exiting = 0
                    cv2.destroyAllWindows()
                    print("---end---")
                    break
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
            elif key == 27:
                print("----------------------------------------------------------------")
                print("Forced exiting calibration")
                forced_exiting = 1
                cv2.destroyAllWindows()
                print("---end---")
                break
                
    except Exception as e :
        print(e)
    finally :
        print('end')

    return detection_area, workspace_depth, forced_exiting