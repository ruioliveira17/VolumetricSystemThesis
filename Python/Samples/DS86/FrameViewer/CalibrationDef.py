from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2
import time

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

def calibrate(hasColorToDepth, hasDepth, rgbframe, depthframe, colorSlope):

    try:
        while 1:
            if  hasColorToDepth==1:
                frametmp = numpy.ctypeslib.as_array(rgbframe.pFrameData, (1, rgbframe.width * rgbframe.height * 3))
                frametmp.dtype = numpy.uint8
                frametmp.shape = (rgbframe.height, rgbframe.width,3)
                frametmp = cv2.resize(frametmp, (640, 480))

                hsv_frame = cv2.cvtColor(frametmp, cv2.COLOR_BGR2HSV)

                h_min = cv2.getTrackbarPos("H min", "Trackbars")
                h_max = cv2.getTrackbarPos("H max", "Trackbars")
                s_min = cv2.getTrackbarPos("S min", "Trackbars")
                s_max = cv2.getTrackbarPos("S max", "Trackbars")
                v_min = cv2.getTrackbarPos("V min", "Trackbars")
                v_max = cv2.getTrackbarPos("V max", "Trackbars")

                lower = numpy.array([h_min, s_min, v_min])
                upper = numpy.array([h_max, s_max, v_max])

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

                cv2.rectangle(frame_copy, (319, 239), (321, 241), (0, 255, 0), 2)

                cv2.imshow("RGB Image", frametmp)
                cv2.imshow("Mask", res)     

            if  hasDepth==1:
                frametmp = numpy.ctypeslib.as_array(depthframe.pFrameData, (1, depthframe.width * depthframe.height * 2))
                frametmp.dtype = numpy.uint16
                frametmp.shape = (depthframe.height, depthframe.width)
                frametmp = cv2.resize(frametmp, (640, 480))
                
                img = numpy.int32(frametmp)
                img = img*255/colorSlope
                img = numpy.clip(img, 0, 255)
                img = numpy.uint8(img)
                frametmp = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)

                frame_copy = frametmp
                cv2.rectangle(frame_copy, (x_area, y_area), (x_area_plus_width, y_area_plus_height), (255, 0, 0), 2)

                cv2.imshow("Depth Image", frametmp)
            
            key = cv2.waitKey(1)
            if  key == ord('q'):
                cv2.destroyAllWindows()
                print("---end---")
                break;
                
    except Exception as e :
        print(e)
    finally :
        print('end')

    return detection_area