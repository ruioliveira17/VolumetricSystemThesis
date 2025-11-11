from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from CalibrationDef import calibrate
from HDRDef import hdr
from MinDepthDef import MinDepth
from LargestObject import LargestObject
from Bundle import bundle

from API.VzenseDS_api import *
import cv2
import time
import threading

camera = VzenseTofCam()
exposureTime = 700

minimum_value = 6000
workspace_not_defined = 1
not_set = 1
threshold = 15

workspace_limits = []

hdr_thread_started = False
minDepth_thread_started = False
largestObject_thread_started = False

results = {}
resultsMinDepth = {}
resultsLargestObject = {}

largura = 0
altura = 0

avg_depth = 0

width_meters = 0
height_meters = 0

stop_event = threading.Event()

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

print("uri: "+str(device_info.uri))
ret = camera.VZ_OpenDeviceByUri(device_info.uri)

if  ret == 0:

    ret = camera.VZ_StartStream()
    if  ret == 0:
        print("start stream successful")
    else:
        print("VZ_StartStream failed:",ret)

    colorSlope = c_uint16(1500) #distância máxima pretendida 5 metros
    
    camera.VZ_SetExposureControlMode(VzSensorType.VzToFSensor, VzExposureControlMode.VzExposureControlMode_Manual)
    camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(700))

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

    #camera.VZ_SetFrameRate(c_uint8(30))

    #ret = camera.VZ_GetFrameRate()
    #print('Frame Rate:', ret)

    def hdr_thread(camera, exposureStruct, result_container, stop_event):
        while not stop_event.is_set():
            hdrColor, hdrDepth = hdr(camera, exposureStruct)  # chama a tua função
            result_container['hdrColor'] = hdrColor
            result_container['hdrDepth'] = hdrDepth

    #def minDepth_thread(hdrDepth, colorSlope, threshold, workspace, workspace_depth, minimum_value, not_set, result_containerMinDepth, stop_event):
    #    while not stop_event.is_set():
    #        not_set, workspace_limits, minimum_value = MinDepth(hdrDepth, colorSlope, threshold, workspace, workspace_depth, minimum_value, not_set)
    #        result_containerMinDepth['not_set'] = not_set
    #        result_containerMinDepth['workspace_limits'] = workspace_limits
    #        result_containerMinDepth['minimum_value'] = minimum_value

    #def largestObject_thread(hdrDepth, workspace_limits, threshold, workspace, minimum_value, not_set, hdrDepth_img, hdrColor, result_containerLargestObject, stop_event):
    #    while not stop_event.is_set():
    #        not_set, minimum_value = LargestObject(hdrDepth, workspace_limits, threshold, workspace, minimum_value, not_set, hdrDepth_img, hdrColor)
    #        result_containerLargestObject['not_set'] = not_set
    #        result_containerLargestObject['minimum_value'] = minimum_value

    try:
        while 1:
            if workspace_not_defined == 1:
                workspace, workspace_depth, fex_flag = calibrate(camera, colorSlope)
                if fex_flag == 0:
                    old_workspace = workspace
                    old_workspace_depth = workspace_depth
                    not_set = 1
                elif fex_flag == 1:
                    workspace = old_workspace
                    workspace_depth = old_workspace_depth
                    fex_flag = 0

                print("Pontos da Area de Trabalho:", workspace)
                print("Workspace Depth:", workspace_depth)
                #colorSlope = int(round(workspace_depth)) + 100
                
                workspace_not_defined = 0 

                if not hdr_thread_started:
                    hdr_thread = threading.Thread(target=hdr_thread, args=(camera, exposureStruct, results, stop_event))
                    hdr_thread.start()
                    hdr_thread_started = True
                    print("Thread HDR iniciada!")                     

            if hdr_thread_started and 'hdrColor' in results and 'hdrDepth' in results:
                hdrColor = results['hdrColor']
                hdrDepth = results['hdrDepth']

                img = numpy.int32(hdrDepth)
                img = img*255/colorSlope
                img = numpy.clip(img, 0, 255)
                img = numpy.uint8(img)
                hdrDepth_img = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)

                not_set, workspace_limits, minimum_value = MinDepth(hdrDepth, colorSlope, threshold, workspace, workspace_depth, minimum_value, not_set)
                min_depth = minimum_value
                #if not minDepth_thread_started:
                #    minDepth_thread = threading.Thread(target=minDepth_thread, args=(hdrDepth, colorSlope, threshold, workspace, workspace_depth, minimum_value, not_set, resultsMinDepth, stop_event))
                #    minDepth_thread.start()
                #    minDepth_thread_started = True
                #    print("Thread Minimum Depth iniciada!")

                #if not_set == 0 and not largestObject_thread_started:
                    #largestObject_thread = threading.Thread(target=largestObject_thread, args=(hdrDepth, workspace_limits, threshold, workspace, minimum_value, not_set, hdrDepth_img, hdrColor, resultsLargestObject, stop_event))
                    #largestObject_thread.start()
                    #largestObject_thread_started = True
                    #print("Thread Largest Object iniciada!")

                if not_set == 0:
                    not_set, minimum_value, avg_depth = LargestObject(hdrDepth, workspace_limits, threshold, workspace, minimum_value, not_set, hdrDepth_img, hdrColor)
                    largura, altura = bundle(hdrColor, hdrDepth_img, workspace_limits)              

                width_meters = (largura) * 0.275 / (workspace_limits[2] - workspace_limits[0])
                height_meters = (altura) * 0.37 / (workspace_limits[3] - workspace_limits[1])
                
                print(f"Width:  {(width_meters * 100):.1f} cm")
                print(f"Height:  {(height_meters * 100):.1f} cm")
                #print("Workspace Depth",workspace_depth)
                #print("Averege Depth", avg_depth)

                volume = width_meters * height_meters * ((workspace_depth - avg_depth) / 1000)
                #print("Volume Total:", volume)
                print(f"Volume Total:  {volume} m^3")

                cv2.imshow("Depth Image", hdrDepth_img)
                cv2.imshow("ColorToDepth RGB Image", hdrColor)

            #if minDepth_thread_started and 'not_set' in resultsMinDepth and 'workspace_limits' in resultsMinDepth and 'minimum_value' in resultsMinDepth:
            #    not_set = resultsMinDepth['not_set']
            #    workspace_limits = resultsMinDepth['workspace_limits']
            #    minimum_value = resultsMinDepth['minimum_value']

            #if largestObject_thread_started and 'not_set' in resultsLargestObject and 'minimum_value' in resultsLargestObject:
            #    not_set = resultsLargestObject['not_set']
            #    minimum_value = resultsLargestObject['minimum_value']

            key = cv2.waitKey(1)
            if key == ord('c'):
                workspace_not_defined = 1
                stop_event.set()
                hdr_thread.join()
                cv2.destroyAllWindows()
            if  key == 27:
                stop_event.set()  # sinaliza a thread HDR para parar
                hdr_thread.join()
                cv2.destroyAllWindows()
                print("---end---")
                break;
                   
    except Exception as e :
        print(e)
    finally :
        print('Main end')
else:
    print('VZ_OpenDeviceByUri failed: ' + str(ret))