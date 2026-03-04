from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2
import time

camera = VzenseTofCam()
framedataToF = []
inc = 0

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
    camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(90))

    ret_code, exposureStruct = camera.VZ_GetExposureTime(VzSensorType.VzToFSensor)
    print('Exposure Time:', exposureStruct.exposureTime)

    # set Mapper
    ret = camera.VZ_SetTransformDepthImgToColorSensorEnabled(c_bool(True))

    if  ret == 0:
        print("VZ_SetTransformDepthImgToColorSensorEnabled ok")
    else:
        print("VZ_SetTransformDepthImgToColorSensorEnabled failed:",ret)   
    
    try:
        while 1:

            ret, frameready = camera.VZ_GetFrameReady(c_uint16(1200))
            if  ret !=0:
                print("VZ_GetFrameReady failed:",ret)
                continue
            hasDepthToColor = 0
            hasIR =0
            hasColor =0

            if  frameready.depth:      
                ret,depthframe = camera.VZ_GetFrame(VzFrameType.VzTransformDepthImgToColorSensorFrame)
                if  ret == 0:
                    hasDepthToColor=1
                   
                else:
                    print("get depth frame failed:",ret)
 
            if  frameready.ir:
                ret,irframe = camera.VZ_GetFrame(VzFrameType.VzIRFrame)
                if  ret == 0:
                    hasIR =1
                  
                else:
                    print("get ir frame failed:",ret)

            if  frameready.color:      
                ret,rgbframe = camera.VZ_GetFrame(VzFrameType.VzColorFrame)
                if  ret == 0:
                    hasColor =1   
                else:
                    print("get color frame failed:",ret)

            if  hasIR==1:
                frametmp = numpy.ctypeslib.as_array(irframe.pFrameData, (1, irframe.dataLen))
                frametmp.dtype = numpy.uint8
                frametmp.shape = (irframe.height, irframe.width)
                    
                cv2.imshow("IR Image", frametmp)

            if  hasColor==1:
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
                    #cv2.drawContours(frame_copy, largest_contour, -1, (0, 255, 0), 2, cv2.LINE_AA)
                    xbound, ybound, wbound, hbound = cv2.boundingRect(largest_contour)
                    cv2.rectangle(frame_copy, (xbound, ybound), (xbound + wbound, ybound + hbound), (255, 0, 0), 2)                    

                cv2.imshow("RGB Image", frametmp)
                #cv2.imshow("HSV Image", hsv_frame)
                cv2.imshow("Mask", res)

            if  hasDepthToColor==1:
                frametmp = numpy.ctypeslib.as_array(depthframe.pFrameData, (1, depthframe.width * depthframe.height * 2))
                frametmp.dtype = numpy.uint16
                frametmp.shape = (depthframe.height, depthframe.width)
                frametmp = cv2.resize(frametmp, (640, 480))

                # Retorna a distância em mm da câmara ao ponto

                #x1, y1 = int((xbound*640)/1600), int((ybound*640)/1600) # canto superior esquerdo 
                #x2, y2 = int(((xbound + wbound)*640)/1600), int(((ybound + hbound)*640)/1600) # canto inferior direito 
                x1, y1 = xbound + 10, ybound + 10
                x2, y2 = xbound + wbound - 10, ybound + hbound - 10
                
                region = frametmp[y1:y2, x1:x2] # recorta a região
                #avg_depth = numpy.mean(region) # média da profundidade

                valid_values = region[region < colorSlope]

                if valid_values.size > 0:
                    avg_depth = numpy.mean(valid_values) # média da profundidade
                
                    if not numpy.isnan(avg_depth):
                        framedataToF.append(avg_depth) # Recebe a informação da distância do ponto

                    if inc < 100:
                        value = framedataToF[inc]
                    else:
                        value = int(sum(framedataToF[-100:]) / 100)

                    inc += 1

                #value = frametmp[228, 291]
                #print("Profundidade média no ponto:", value/10, 'cm')

                key = cv2.waitKey(1)
                if key == ord('q'):
                    print("Profundidade média no ponto:", value/10, 'cm')

                #convert ushort value to 0xff is just for display
                img = numpy.int32(frametmp)
                img = img*255/colorSlope
                img = numpy.clip(img, 0, 255)
                img = numpy.uint8(img)
                frametmp = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)

                frame_copy = frametmp
                cv2.rectangle(frame_copy, (xbound, ybound), (xbound + wbound, ybound + hbound), (255, 0, 0), 2)

                cv2.imshow("DepthToColor Image", frametmp)

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