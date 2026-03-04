from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2
import time

camera = VzenseTofCam()

exposureTime = 400
hdr_done = 0
hdrColor_done = 0
hdrDepth_done = 0
expositionBus_done = 0
#hasColorToDepthArray = []
hasDepthArray = []
exposureTimeArray = []
DTC_can = False
D_can = False
firstFrame = True
i = 0
#not_aligned = 1

output_folderCTD = "C:/Tese/Python/FramesCTD"
os.makedirs(output_folderCTD, exist_ok=True)

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

    ret_code, exposureStruct = camera.VZ_GetExposureTime(VzSensorType.VzToFSensor)
    print('Exposure Time:', exposureStruct.exposureTime)

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
                if exposureTime != 400:
                    camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(exposureTime))

                    ret_code, exposureStruct = camera.VZ_GetExposureTime(VzSensorType.VzToFSensor)
                #    print('Exposure Time:', exposureStruct.exposureTime)
                #    print("Exposure Time Pretendido:", exposureTime)
                #else:
                #    print("Exposure Time Camera:", exposureStruct.exposureTime)
                #    print("Exposure Time Pretendido:", exposureTime)

                time.sleep(0.4)

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

                if  hasColorToDepth==1 and exposureStruct.exposureTime == exposureTime:
                    frametmp = numpy.empty((0, 0, 3), dtype=numpy.uint8)
                    frametmp = numpy.ctypeslib.as_array(rgbframe.pFrameData, (1, rgbframe.width * rgbframe.height * 3))
                    frametmp.dtype = numpy.uint8
                    frametmp.shape = (rgbframe.height, rgbframe.width,3)
                    frametmp = cv2.resize(frametmp, (640, 480))
                    #cv2.putText(frametmp, f"Exposure: {exposureStruct.exposureTime} us",
                    #            (30, 40),                   # posição (x, y)
                    #            cv2.FONT_HERSHEY_SIMPLEX,   # tipo de letra
                    #            1,                           # escala (tamanho)
                    #            (0, 255, 0),                 # cor (B, G, R)
                    #            2,                           # espessura
                    #            cv2.LINE_AA)                 # antialiasing
                    cv2.imshow("RGB Image", frametmp)
                    cv2.waitKey(1)
                    
                    if firstFrame:
                        firstFrame = False
                    else:
                        DTC_can = True
                        filename = f"CTDFrame_{i}.jpg"
                        filepath = os.path.join(output_folderCTD, filename)
                        cv2.imwrite(filepath, frametmp)
                        #cv2.imwrite(filename, frametmp)
                        #hasColorToDepthArray.append(frametmp)

                if  hasDepth==1 and exposureStruct.exposureTime == exposureTime:
                    frametmp = numpy.empty((0, 0, 3), dtype=numpy.uint8)
                    frametmp = numpy.ctypeslib.as_array(depthframe.pFrameData, (1, depthframe.width * depthframe.height * 2))
                    frametmp.dtype = numpy.uint16
                    frametmp.shape = (depthframe.height, depthframe.width)
                    frametmp = cv2.resize(frametmp, (640, 480))
                    #cv2.imshow("Depth Image", frametmp)
                    
                    if firstFrame:
                        firstFrame = False
                    else:
                        D_can = True
                        hasDepthArray.append(frametmp)

                if DTC_can and D_can:
                    exposureTimeArray.append(exposureTime / 1e6)
                    exposureTime += 300
                    i += 1
                
                DTC_can = False
                D_can = False

                if exposureTime == 4300:
                    cv2.destroyAllWindows()

            else:
                # FAZER HDR AQUI E DEPOIS TESTAR A IMAGEM
                # ERA INCRIVEL TER ISTO POIS PERMITIRIA ANALISAR APENAS UMA VEZ A IMAGEM E OBTER TUDO O QUE É NECESSÁRIO            
                if not hdrColor_done:
                    frame_array = [os.path.join(output_folderCTD, f"CTDFrame_{i}.jpg") for i in range(13)]
                    
                    frame_list = [cv2.imread(fn) for fn in frame_array]

                    exposureTimes = numpy.array(exposureTimeArray, dtype = numpy.float32)
                    print(exposureTimes)

                    #if not_aligned == 1:
                    #    alignMTB = cv2.createAlignMTB()
                    #    alignMTB.process(frame_list, frame_list)
                    #    not_aligned = 0

                    #calibrateDebevec = cv2.createCalibrateDebevec()
                    #responseDebevec = calibrateDebevec.process(frame_list, exposureTimes.copy())

                    mergeDebevec = cv2.createMergeDebevec()
                    hdrColor = mergeDebevec.process(frame_list, exposureTimes.copy())

                    #tonemap = cv2.createTonemapReinhard(gamma = 1)
                    tonemap = cv2.createTonemapDrago(gamma=1.0, saturation=0.7)
                    ldr = tonemap.process(hdrColor)
                    ldr = numpy.nan_to_num(ldr)
                    ldr = numpy.clip(ldr, 0, 1)
                    ldr = (ldr*65535).astype('uint16')
                    hdrColor_done = 1

                    cv2.imshow("HDR Color", ldr)

                if not hdrDepth_done:
                    valid_frames = [numpy.where((frame > 0) & (frame <= 5000), frame, numpy.nan) for frame in hasDepthArray]

                    hdrDepth = numpy.nanmean(numpy.stack(valid_frames, axis=-1), axis=-1)

                    img = numpy.int32(hdrDepth)
                    img = img*255/colorSlope
                    img = numpy.clip(img, 0, 255)
                    img = numpy.uint8(img)
                    hdrDepth = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)
                    hdrDepth_done = 1

                    cv2.imshow("HDR Depth", hdrDepth)
                    
                expositionBus_done = 1
                hdr_done = 1
                exposureTime = 400

            if  hdr_done:
                expositionBus_done = 0
                hdr_done = 0
                i = 0
                cv2.destroyAllWindows()
                print("---end---")
                break

            key = cv2.waitKey(1)
            if  key == 27:
                cv2.destroyAllWindows()
                print("---end---")
                break

    except Exception as e :
        print(e)
    finally :
        print('end')
else:
    print('VZ_OpenDeviceByIP failed: ' + str(ret))  