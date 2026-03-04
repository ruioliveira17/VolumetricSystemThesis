from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2
import time

camera = VzenseTofCam()

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

camera_count = camera.VZ_GetDeviceCount()
retry_count = 100
while camera_count==0 and retry_count > 0:
    retry_count = retry_count-1
    camera_count = camera.VZ_GetDeviceCount()
    time.sleep(1)
    print("scaning......   ",retry_count)

device_info=VzDeviceInfo()

if camera_count > 1:
    ret,device_infolist=camera.VZ_GetDeviceInfoList(camera_count)
    if ret==0:
        device_info = device_infolist[0]
        for info in device_infolist: 
            print('cam uri:  ' + str(info.uri))
    else:
        print(' failed:' , ret)  
        exit()  
elif camera_count == 1:
    ret,device_info=camera.VZ_GetDeviceInfo()
    if ret==0:
        print('cam uri:' + str(device_info.uri))
    else:
        print(' failed:', ret)   
        exit() 
else: 
    print("there are no camera found")
    exit()

#print("uri: "+str(device_info.uri))
#ret = camera.VZ_OpenDeviceByUri(device_info.uri)

if  VzConnectStatus.Connected.value != device_info.status:
	print("connect statu:",device_info.status)  
	print("Call VZ_OpenDeviceByIP with connect status :",VzConnectStatus.Connected.value)
	exit()
else:
    print("uri: "+str(device_info.uri))
    print("alias: "+str(device_info.alias))
    print("ip: "+str(device_info.ip))
    print("connectStatus: "+str(device_info.status))

ret = camera.VZ_OpenDeviceByIP(device_info.ip) 

if  ret == 0:

    print("open device successful")

    ret = camera.VZ_StartStream()
    if  ret == 0:
        print("start stream successful")
    else:
        print("VZ_StartStream failed:",ret)


    colorSlope = c_uint16(1200) #distância máxima pretendida 5 metros
    
    camera.VZ_SetExposureControlMode(VzSensorType.VzToFSensor, VzExposureControlMode.VzExposureControlMode_Manual)
    camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(430))

    ret_code, exposureStruct = camera.VZ_GetExposureTime(VzSensorType.VzToFSensor)
    print('Exposure Time:', exposureStruct.exposureTime)
    
    # set Mapper
    ret = camera.VZ_SetTransformColorImgToDepthSensorEnabled(c_bool(True))

    if  ret == 0:
        print("VZ_SetTransformColorImgToDepthSensorEnabled ok")
    else:
        print("VZ_SetTransformColorImgToDepthSensorEnabled failed:",ret)  

    try:
        while 1:

            ret, frameready = camera.VZ_GetFrameReady(c_uint16(1200))
            if  ret !=0:
                print("VZ_GetFrameReady failed:",ret)
                continue
            hasColorToDepth =0
            hasDepth = 0

            if  frameready.color:      
                ret,rgbframe = camera.VZ_GetFrame(VzFrameType.VzTransformColorImgToDepthSensorFrame)
                if  ret == 0:
                    hasColorToDepth =1   
                else:
                    print("get color frame failed:",ret)

            if  frameready.depth:      
                ret,depthframe = camera.VZ_GetFrame(VzFrameType.VzDepthFrame)
                if  ret == 0:
                    hasDepth=1
                   
                else:
                    print("get depth frame failed:",ret)

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

                lower = numpy.array([21, 30, v_min])
                upper = numpy.array([151, s_max, v_max])

                mask_hsv = cv2.inRange(hsv_frame, lower, upper)

                res = cv2.bitwise_and(frametmp, frametmp, mask=mask_hsv)

                imgray = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
                ret, thresh = cv2.threshold(imgray, 127, 255, 0)

                frame_copy = frametmp
                contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
                if contours:
                    largest_contour = max(contours, key=cv2.contourArea)
                    #cv2.drawContours(frame_copy, largest_contour, -1, (0, 255, 0), 2, cv2.LINE_AA)
                    x_area, y_area, w_area, h_area = cv2.boundingRect(largest_contour)
                    x_area_plus_width = x_area + w_area
                    y_area_plus_height = y_area + h_area
                    cv2.rectangle(frame_copy, (x_area, y_area), (x_area_plus_width, y_area_plus_height), (255, 0, 0), 2)              

                cv2.rectangle(frame_copy, (319, 239), (321, 241), (0, 255, 0), 2)

                cv2.imshow("RGB Image", frametmp)
                #cv2.imshow("HSV Image", hsv_frame)
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
            if  key == 27:
                cv2.destroyAllWindows()
                print("---end---")
                break;
                   
    except Exception as e :
        print(e)
    finally :
        print('end')
else:
    #print('VZ_OpenDeviceByUri failed: ' + str(ret))
    print('VZ_OpenDeviceByIP failed: ' + str(ret))  