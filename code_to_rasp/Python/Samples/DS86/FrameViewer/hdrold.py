from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2
import time

camera = VzenseTofCam()

exposureTime = 400
hdr_done = 0
expositionBus_done = 0
hasColorToDepthArray = []
hasDepthArray = []
exposureTimeArray = []
not_aligned = 1

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


    colorSlope = c_uint16(1500) #distância máxima pretendida 5 metros
    
    camera.VZ_SetExposureControlMode(VzSensorType.VzToFSensor, VzExposureControlMode.VzExposureControlMode_Manual)
    camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(400))

    ret_code, exposureStruct = camera.VZ_GetExposureTime(VzSensorType.VzToFSensor)
    print('Exposure Time:', exposureStruct.exposureTime)
    
    # set Mapper
    ret = camera.VZ_SetTransformColorImgToDepthSensorEnabled(c_bool(True))

    if  ret == 0:
        print("VZ_SetTransformColorImgToDepthSensorEnabled ok")
    else:
        print("VZ_SetTransformColorImgToDepthSensorEnabled failed:",ret) 

    ret,enable = camera.VZ_GetSpatialFilterEnabled()
    if  ret == 0:
        print("The default SpatialFilter switch is " + str(enable))
    else:
        print("VZ_GetSpatialFilterEnabled failed:"+ str(ret))   

    enable = not enable
    ret = camera.VZ_SetSpatialFilterEnabled(enable)
    if  ret == 0:
        print("Set SpatialFilter switch to "+ str(enable) + " is Ok")   
    else:
        print("VZ_SetSpatialFilterEnabled failed:"+ str(ret))

    ret,params = camera.VZ_GetConfidenceFilterParams()
    if  ret == 0:
        print("The default ConfidenceFilter switch is " + str(params.enable))
    else:
        print("VZ_GetConfidenceFilterParams failed:"+ str(ret))

    params.enable = False
    ret = camera.VZ_SetConfidenceFilterParams(params)
    if  ret == 0:
        print("Set ConfidenceFilter switch to "+ str(params.enable) + " is Ok")   
    else:
        print("VZ_SetConfidenceFilterParams failed:"+ str(ret)) 

    try:
        while 1:
            while exposureTime <= 4000 and expositionBus_done == 0:
                camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(exposureTime))

                ret_code, exposureStruct = camera.VZ_GetExposureTime(VzSensorType.VzToFSensor)
                print('Exposure Time:', exposureStruct.exposureTime)

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
                    cv2.imshow("RGB Image", frametmp)
                    cv2.waitKey(1)
                    hasColorToDepthArray.append(frametmp)    

                if  hasDepth==1:
                    frametmp = numpy.ctypeslib.as_array(depthframe.pFrameData, (1, depthframe.width * depthframe.height * 2))
                    frametmp.dtype = numpy.uint16
                    frametmp.shape = (depthframe.height, depthframe.width)
                    frametmp = cv2.resize(frametmp, (640, 480))
                    #cv2.imshow("Depth Image", frametmp)
                    hasDepthArray.append(frametmp)
                    
                if hasDepth==1 and hasColorToDepth==1:
                    exposureTimeArray.append(exposureTime / 1e6)
                    exposureTime += 300

            else:
                # FAZER HDR AQUI E DEPOIS TESTAR A IMAGEM
                # ERA INCRIVEL TER ISTO POIS PERMITIRIA ANALISAR APENAS UMA VEZ A IMAGEM E OBTER TUDO O QUE É NECESSÁRIO
                
                exposureTimes = numpy.array(exposureTimeArray, dtype = numpy.float32)

                #if not_aligned == 1:
                #    alignMTB = cv2.createAlignMTB()
                #    alignMTB.process(hasColorToDepthArray, hasColorToDepthArray)
                #    not_aligned = 0

                mergeDebevec = cv2.createMergeDebevec()
                hdrColor = mergeDebevec.process(hasColorToDepthArray, times = exposureTimes.copy())

                #tonemap = cv2.createTonemapReinhard(gamma = 1)
                tonemap = cv2.createTonemapDrago(gamma=1.0, saturation=1.0)
                ldr = tonemap.process(hdrColor)
                ldr = numpy.nan_to_num(ldr)
                ldr = numpy.clip(ldr, 0, 1)
                ldr = (ldr*255).astype('uint8')

                cv2.imshow("HDR Result", ldr)
                #cv2.imshow("1", hasColorToDepthArray[0])
                #cv2.imshow("2", hasColorToDepthArray[1])
                #cv2.imshow("3", hasColorToDepthArray[2])
                #cv2.imshow("4", hasColorToDepthArray[3])
                #cv2.imshow("5", hasColorToDepthArray[4])
                #cv2.imshow("6", hasColorToDepthArray[5])
                #cv2.imshow("7", hasColorToDepthArray[6])
                #cv2.imshow("8", hasColorToDepthArray[7])
                #cv2.imshow("9", hasColorToDepthArray[8])
                #cv2.imshow("10", hasColorToDepthArray[9])
                #cv2.imshow("11", hasColorToDepthArray[10])
                #cv2.imshow("12", hasColorToDepthArray[11])
                #cv2.imshow("13", hasColorToDepthArray[12])

                expositionBus_done = 1
                #hdr_done = 1
                exposureTime = 400

            if  hdr_done:
                expositionBus_done = 0
                cv2.destroyAllWindows()
                print("---end---")
                break;

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
    print('VZ_OpenDeviceByIP failed: ' + str(ret))  