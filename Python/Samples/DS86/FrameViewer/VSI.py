from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from CalibrationDef import calibrate
from HDRDef import hdr
from MinDepth2 import MinDepth
#from LargestObject import LargestObject
from Bundle2 import bundle
from Volume import volume_calc

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

#workspace_limits = []
objects_info = []
box_limits = []
box_ws = []

hdr_thread_started = False
minDepth_thread_started = False
largestObject_thread_started = False

results = {}
resultsMinDepth = {}
resultsLargestObject = {}

width = 0
height = 0

avg_depth = 0

width_meters = 0
height_meters = 0

xmin_meters = 0
xmax_meters = 0

ymin_meters = 0
ymax_meters = 0

bundle_xmin = 60
bundle_xmax = 0
bundle_ymin = 60
bundle_ymax = 0

minimum_depth = 0

static_mode = 0
dynamic_mode = 0

stop_event = threading.Event()
pause_event = threading.Event()
pause_event.set()

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

    def hdr_thread(camera, exposureStruct, result_container, stop_event, pause_event):
        while not stop_event.is_set():
            pause_event.wait()
            try:
                hdrColor, hdrDepth = hdr(camera, exposureStruct)  # chama a tua função
                result_container['hdrColor'] = hdrColor
                result_container['hdrDepth'] = hdrDepth
            except Exception as e:
                print("Erro na thread:", repr(e))
            finally :
                print('Funcionou')
    try:
        while 1:
            if workspace_not_defined == 1:
                camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(700))
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
                
                workspace_not_defined = 0

                if hdr_thread_started:
                    pause_event.set()
                    print("Thread HDR saiu de pausa!")
                else:
                    hdr_thread = threading.Thread(target=hdr_thread, args=(camera, exposureStruct, results, stop_event, pause_event))
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

                hdrDepth_copy = hdrDepth.copy()

                if dynamic_mode or (static_mode and key == ord('l')):

                    not_set, objects_info = MinDepth(hdrDepth_copy, colorSlope, threshold, workspace, workspace_depth, not_set)
                    
                    if len(objects_info) != 0:
                        minimum_depth = objects_info[0]["depth"]
                        minimum_value = minimum_depth

                    if not_set == 0:
                        width, height, minimum_value, not_set, box_limits, box_ws = bundle(hdrColor, hdrDepth_img, objects_info, threshold, hdrDepth)
                        bundle_xmin, bundle_xmax, bundle_ymin, bundle_ymax = volume_calc(box_ws, box_limits, bundle_xmin, bundle_xmax, bundle_ymin, bundle_ymax)

                    width_meters = bundle_xmax - bundle_xmin
                    height_meters = bundle_ymax - bundle_ymin

                    if width_meters < 0:
                        width_meters = 0

                    if height_meters < 0:
                        height_meters = 0
                    
                    print(f"Width:  {(width_meters * 100):.1f} cm")
                    print(f"Height:  {(height_meters * 100):.1f} cm")
                    print("Workspace Depth",workspace_depth)
                    print("Minimum Depth:", minimum_depth)

                    if bundle_xmin == 60 and bundle_ymin == 60 and bundle_xmax == 0 and bundle_ymax == 0:
                        volume = 0
                    else:
                        volume = width_meters * height_meters * ((workspace_depth - minimum_depth) / 1000)

                    print(f"Volume Total:  {volume} m^3")

                    bundle_xmin = 60
                    bundle_xmax = 0
                    bundle_ymin = 60
                    bundle_ymax = 0

                cv2.imshow("Depth Image", hdrDepth_img)
                cv2.imshow("ColorToDepth RGB Image", hdrColor)

            key = cv2.waitKey(1)
            if key == ord('s'):
                print("Static Mode Active!")
                static_mode = 1
                dynamic_mode = 0
            if key == ord('d'):
                print("Dynamic Mode Active!")
                static_mode = 0
                dynamic_mode = 1
            if key == ord('c'):
                workspace_not_defined = 1
                pause_event.clear()
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
        stop_event.set()
        cv2.destroyAllWindows()
else:
    print('VZ_OpenDeviceByUri failed: ' + str(ret))