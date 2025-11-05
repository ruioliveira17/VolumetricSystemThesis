from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from CalibrationDef import calibrate
from HDRDef import hdr
from HDRDef2 import hdr2

from API.VzenseDS_api import *
import cv2
import time
import threading

from scipy import ndimage

camera = VzenseTofCam()
exposureTime = 700
framedataToF = []
inc = 0
minimum_value = 6000
workspace_not_defined = 1
not_set = 1
threshold = 15
objectpixelsmin_x = 0
objectpixelsmax_x = 0
objectpixelsmin_y = 0
objectpixelsmax_y = 0
sizes = 0
workspace_limits = []
search = 0

hdr_thread_started = False
results = {}
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

    ret, intrinsics_depth = camera.VZ_GetSensorIntrinsicParameters(VzSensorType.VzToFSensor)
    ret, intrinsics_color = camera.VZ_GetSensorIntrinsicParameters(VzSensorType.VzColorSensor)

    ret, extrinsics = camera.VZ_GetSensorExtrinsicParameters()

    #camera.VZ_SetFrameRate(c_uint8(30))

    #ret = camera.VZ_GetFrameRate()
    #print('Frame Rate:', ret)

    def hdr_thread(camera, colorSlope, exposureStruct, result_container, stop_event):
        while not stop_event.is_set():
            hdrColor, hdrDepth = hdr(camera, colorSlope, exposureStruct)  # chama a tua função
            result_container['hdrColor'] = hdrColor
            result_container['hdrDepth'] = hdrDepth

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
                
                workspace_not_defined = 0 

                if not hdr_thread_started:
                    hdr_thread = threading.Thread(target=hdr_thread, args=(camera, colorSlope, exposureStruct, results, stop_event))
                    hdr_thread.start()
                    hdr_thread_started = True
                    print("Thread HDR iniciada!")         

            if objectpixelsmin_x != 0 and objectpixelsmax_x != 0 and objectpixelsmin_y != 0 and objectpixelsmax_y != 0 and len(sizes) != 0:
                frame_copy = hdrColor
                cv2.rectangle(frame_copy, (objectpixelsmin_x, objectpixelsmin_y), (objectpixelsmax_x, objectpixelsmax_y), (255, 0, 255), 2)
                cv2.imshow("ColorToDepth RGB Image", hdrColor)

            if hdr_thread_started and 'hdrColor' in results and 'hdrDepth' in results:
                hdrColor = results['hdrColor']
                hdrDepth = results['hdrDepth']

                img = numpy.int32(hdrDepth)
                img = img*255/colorSlope
                img = numpy.clip(img, 0, 255)
                img = numpy.uint8(img)
                hdrDepth_img = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)

                valid_values = hdrDepth[(hdrDepth > 150) & (hdrDepth < colorSlope)]

                while not_set == 1:

                    if valid_values.size > 0:
                        while True:
                            found = False
                            valid_values = hdrDepth[(hdrDepth > 150) & (hdrDepth < colorSlope)]
                            min_value = numpy.min(valid_values) # minimo da profundidade

                            if min_value < minimum_value:
                                index = numpy.where(hdrDepth == min_value)
                                min_idx = (index[0][0], index[1][0])
                                y, x = min_idx

                                for y, x in zip(index[0], index[1]):
                                    neighbors = hdrDepth[max(0, y-8):y+9, max(0, x-8):x+9]
                                    tolerance = threshold

                                    workspace_width = int((workspace[2] - workspace[0])/2)

                                    workspace_height = int((workspace[3] - workspace[1])/2)

                                    object_depth = min_value

                                    workspace_width_max = int((workspace_width * int(workspace_depth)) / object_depth)

                                    workspace_height_max = int((workspace_height * int(workspace_depth)) / object_depth)

                                    workspace_limits = int(320 - (workspace_width_max)), int(240 - (workspace_height_max)), int(320 + (workspace_width_max)), int(240 + (workspace_height_max))

                                    if ((x >= workspace_limits[0]) and (x <= workspace_limits[2])) and ((y >= workspace_limits[1]) and (y <= workspace_limits[3])):
                                        valid_count = numpy.sum(numpy.abs(neighbors - min_value) <= tolerance)
                                        total_count = neighbors.size

                                        if valid_count / total_count >= 0.9:
                                            print(f"Ponto {min_idx} válido, todos vizinhos semelhantes")
                                            
                                            minimum_value = min_value
                                            point_idx = y,x
                                            found = True
                                            break

                                        else:
                                            hdrDepth[y, x] = 9999

                                    else:
                                        hdrDepth[y, x] = 9999
                                        
                            else:
                                break
                                
                            if found:
                                break

                    print("Profundidade mínima:", minimum_value/10, 'cm')
                    min_y = point_idx[0]
                    min_x = point_idx[1]
                    print("Ponto:", (min_x, min_y))

                    #exposureTime = 700
                    not_set = 0
                    search = 0

                if not_set == 0:

                    workspace_area = hdrDepth[workspace_limits[1]:workspace_limits[3], workspace_limits[0]:workspace_limits[2]]

                    mask = (workspace_area >= minimum_value) & (workspace_area <= minimum_value + threshold)

                    labeled_array, num_features = ndimage.label(mask)

                    sizes = ndimage.sum(mask, labeled_array, range(1, num_features + 1))

                    if len(sizes) == 0:
                        print("Nenhuma região encontrada")
                    else:
                        # Encontrar região com maior número de pixels
                        largest_region_index = numpy.argmax(sizes) + 1  # +1 porque labels começam em 1
                        largest_region_mask = (labeled_array == largest_region_index)

                        objectpixelsy, objectpixelsx = numpy.where(largest_region_mask)
                        objectpixelsmin_x, objectpixelsmax_x = workspace_limits[0] + objectpixelsx.min(), workspace_limits[0] + objectpixelsx.max()
                        objectpixelsmin_y, objectpixelsmax_y = workspace_limits[1] + objectpixelsy.min(), workspace_limits[1] + objectpixelsy.max()
                        print("Área Coberta:", objectpixelsmin_x, objectpixelsmin_y, objectpixelsmax_x, objectpixelsmax_y)

                        object_region = hdrDepth[objectpixelsmin_y:objectpixelsmax_y, objectpixelsmin_x:objectpixelsmax_x]

                        valid_values = object_region[(object_region >= minimum_value) & (object_region <= minimum_value + threshold)]

                        if valid_values.size > 0:
                            avg_depth = numpy.mean(valid_values) # média da profundidade

                            if not numpy.isnan(avg_depth):
                                framedataToF.append(avg_depth)

                                if inc < 100:
                                    value = framedataToF[inc]
                                else:
                                    value = int(sum(framedataToF[-100:]) / 100)

                                inc += 1
                            
                                print(f"Profundidade média: {avg_depth/10:.1f} cm")

                    frame_copy = hdrDepth_img
                    if len(sizes) != 0:
                        cv2.rectangle(frame_copy, (objectpixelsmin_x, objectpixelsmin_y), (objectpixelsmax_x, objectpixelsmax_y), (255, 255, 0), 2)
                        cv2.rectangle(frame_copy, (workspace[0], workspace[1]), (workspace[2], workspace[3]), (255, 0, 255), 2)
                        cv2.rectangle(frame_copy, (workspace_limits[0], workspace_limits[1]), (workspace_limits[2], workspace_limits[3]), (255, 0, 0), 2)
                    cv2.imshow("Depth Image", hdrDepth_img)

                    not_set = 1
                    minimum_value = 6000

            key = cv2.waitKey(1)
            if key == ord('c'):
                workspace_not_defined = 1
                stop_event.set()  # sinaliza a thread HDR para parar
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
        print('end')
else:
    print('VZ_OpenDeviceByUri failed: ' + str(ret))