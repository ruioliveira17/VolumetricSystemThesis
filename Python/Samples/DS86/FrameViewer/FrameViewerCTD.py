from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from CalibrationDef import calibrate

from API.VzenseDS_api import *
import cv2
import time

from scipy import ndimage

camera = VzenseTofCam()
exposureTime = 400
framedataToF = []
inc = 0
minimum_value = 6000
workspace_not_defined = 1
not_set = 1
exposureArray = []
threshold = 15
objectpixelsmin_x = 0
objectpixelsmax_x = 0
objectpixelsmin_y = 0
objectpixelsmax_y = 0
search = 0

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
    
    try:
        while 1:

            ret, frameready = camera.VZ_GetFrameReady(c_uint16(1200))
            if  ret !=0:
                print("VZ_GetFrameReady failed:",ret)
                continue
            hasDepth=0
            hasIR =0
            hasColorToDepth = 0

            if  frameready.depth:      
                ret,depthframe = camera.VZ_GetFrame(VzFrameType.VzDepthFrame)
                if  ret == 0:
                    hasDepth=1
                   
                else:
                    print("get depth frame failed:",ret)
 
            if  frameready.ir:
                ret,irframe = camera.VZ_GetFrame(VzFrameType.VzIRFrame)
                if  ret == 0:
                    hasIR =1
                  
                else:
                    print("get ir frame failed:",ret)

            if  frameready.color:      
                ret,rgbframe = camera.VZ_GetFrame(VzFrameType.VzTransformColorImgToDepthSensorFrame)
                if  ret == 0:
                    hasColorToDepth =1   
                else:
                    print("get color frame failed:",ret)

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
                print("workspace Depth:", workspace_depth)
                
                workspace_not_defined = 0

            #if  hasIR==1:
            #    frametmp = numpy.ctypeslib.as_array(irframe.pFrameData, (1, irframe.dataLen))
            #    frametmp.dtype = numpy.uint8
            #    frametmp.shape = (irframe.height, irframe.width)
                    
            #    cv2.imshow("IR Image", frametmp)

            if  hasColorToDepth==1:
                frametmp = numpy.ctypeslib.as_array(rgbframe.pFrameData, (1, rgbframe.width * rgbframe.height * 3))
                frametmp.dtype = numpy.uint8
                frametmp.shape = (rgbframe.height, rgbframe.width,3)
                frametmp = cv2.resize(frametmp, (640, 480))

                #hsv_frame = cv2.cvtColor(frametmp, cv2.COLOR_BGR2HSV)

                #h_min = cv2.getTrackbarPos("H min", "Trackbars")
                #h_max = cv2.getTrackbarPos("H max", "Trackbars")
                #s_min = cv2.getTrackbarPos("S min", "Trackbars")
                #s_max = cv2.getTrackbarPos("S max", "Trackbars")
                #v_min = cv2.getTrackbarPos("V min", "Trackbars")
                #v_max = cv2.getTrackbarPos("V max", "Trackbars")

                #lower = numpy.array([23, s_min, v_min])
                #upper = numpy.array([87, s_max, v_max])

                #mask_hsv = cv2.inRange(hsv_frame, lower, upper)

                #res = cv2.bitwise_and(frametmp, frametmp, mask=mask_hsv)

                #imgray = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
                #ret, thresh = cv2.threshold(imgray, 127, 255, 0)

                #frame_copy = frametmp
                #contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
                #if contours:
                #    largest_contour = max(contours, key=cv2.contourArea)
                    #cv2.drawContours(frame_copy, largest_contour, -1, (0, 255, 0), 2, cv2.LINE_AA)
                #    xbound, ybound, wbound, hbound = cv2.boundingRect(largest_contour)
                #    cv2.rectangle(frame_copy, (xbound, ybound), (xbound + wbound, ybound + hbound), (255, 0, 0), 2)                    

                if objectpixelsmin_x != 0 and objectpixelsmax_x != 0 and objectpixelsmin_y != 0 and objectpixelsmax_y != 0:
                    frame_copy = frametmp
                    cv2.rectangle(frame_copy, (objectpixelsmin_x, objectpixelsmin_y), (objectpixelsmax_x, objectpixelsmax_y), (255, 0, 255), 2)
                cv2.imshow("ColorToDepth RGB Image", frametmp)
                #cv2.imshow("HSV Image", hsv_frame)
                #cv2.imshow("ColorToDepth Mask", res)

            if  hasDepth==1:
                frametmp = numpy.ctypeslib.as_array(depthframe.pFrameData, (1, depthframe.width * depthframe.height * 2))
                frametmp.dtype = numpy.uint16
                frametmp.shape = (depthframe.height, depthframe.width)
                frametmp = cv2.resize(frametmp, (640, 480))

                # Retorna a distância em mm da câmara ao ponto

                #x1, y1 = int((xbound*640)/1600), int((ybound*640)/1600) # canto superior esquerdo 
                #x2, y2 = int(((xbound + wbound)*640)/1600), int(((ybound + hbound)*640)/1600) # canto inferior direito 
                #x1, y1 = xbound + 10, ybound + 10
                #x2, y2 = xbound + wbound - 10, ybound + hbound - 10
                
                #region = frametmp[y1:y2, x1:x2] # recorta a região 

                #valid_values = region[region > 0]

                #if valid_values.size > 0:
                #    min_value = numpy.min(region) # média da profundidade
                #    if min_value < minimum_value:
                #        minimum_value = min_value
                #        min_idx = numpy.unravel_index(numpy.argmin(region), region.shape)

                #        min_y = y1 + min_idx[0]
                #        min_x = x1 + min_idx[1]
                    
                #        print("Profundidade mínima:", min_value/10, 'cm')
                #        print("Ponto:", (min_x, min_y))

                #value = frametmp[356, 290]
                #print("Profundidade média no ponto:", value/10, 'cm')

                #key = cv2.waitKey(1)
                #if key == ord('q'):
                #    print("Profundidade média no ponto:", value/10, 'cm')

                #inc += 1

                while not_set == 1 or search == 1:
                    camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(exposureTime))

                    ret_code, exposureStruct = camera.VZ_GetExposureTime(VzSensorType.VzToFSensor)
                    print('Exposure Time:', exposureStruct.exposureTime)

                    if exposureTime < 4000:

                        ret, frameready = camera.VZ_GetFrameReady(c_uint16(1200))
                        if  ret !=0:
                            print("VZ_GetFrameReady failed:",ret)
                            continue
                        hasDepth=0

                        if  frameready.depth:      
                            ret,depthframe = camera.VZ_GetFrame(VzFrameType.VzDepthFrame)
                            if  ret == 0:
                                hasDepth=1
                                frametmp = numpy.ctypeslib.as_array(depthframe.pFrameData, (1, depthframe.width * depthframe.height * 2))
                                frametmp.dtype = numpy.uint16
                                frametmp.shape = (depthframe.height, depthframe.width)
                                frametmp = cv2.resize(frametmp, (640, 480))
                            
                            else:
                                print("get depth frame failed:",ret)

                        #a = 30

                        #workspace_region = frametmp[workspace[1]:workspace[3], workspace[0]:workspace[2]]
                        #workspace_region = frametmp[workspace[1] - a:workspace[3] + a, workspace[0] - a:workspace[2] + a]

                        #valid_values = workspace_region[(workspace_region > 150) & (workspace_region < colorSlope)]
                        valid_values = frametmp[(frametmp > 150) & (frametmp < colorSlope)]

                        #if valid_values.size > 0:
                        #    min_value = numpy.min(valid_values) # minimo da profundidade
                        #    if min_value <= minimum_value:
                        #        minimum_value = min_value
                        #        index = numpy.where(workspace_region == minimum_value)
                        #        min_idx = (index[0][0], index[1][0])
                        #        #min_idx = numpy.unravel_index(index, workspace_region.shape)

                        #        exposureArray.append(exposureTime)

                        if valid_values.size > 0:
                            while True:
                            #min_value = numpy.min(valid_values) # minimo da profundidade
                            #if min_value <= minimum_value:
                                found = False
                                valid_values = frametmp[(frametmp > 150) & (frametmp < colorSlope)]
                                min_value = numpy.min(valid_values) # minimo da profundidade

                                if min_value < minimum_value:
                                    #print("Possível Ponto Menor")
                                    #index = numpy.where(workspace_region == min_value)
                                    index = numpy.where(frametmp == min_value)
                                    min_idx = (index[0][0], index[1][0])
                                    y, x = min_idx

                                    for y, x in zip(index[0], index[1]):
                                        #minimum_value = min_value
                                        #index = numpy.where(workspace_region == minimum_value)
                                        #min_idx = (index[0][0], index[1][0])
                                        #min_idx = numpy.unravel_index(index, workspace_region.shape)
                                        #neighbors = workspace_region[max(0, y-1):y+2, max(0, x-1):x+2]
                                        neighbors = frametmp[max(0, y-8):y+9, max(0, x-8):x+9]
                                        tolerance = threshold
                                        #if numpy.all(numpy.abs(neighbors - min_value) <= tolerance):
                                        #    print(f"Ponto {min_idx} válido, todos vizinhos semelhantes")
                                        #    minimum_value = min_value
                                        #    exposureArray.append(exposureTime)
                                        #    found = True

                                        #    print("width workspace:", int((workspace[2] - workspace[0])/2))
                                        #    print("height workspace:", int((workspace[3] - workspace[1])/2))
                                        #    print("depth object:", min_value)
                                        #    print("width object:", int(x))
                                        #    print("width_mm object:", int((int(x)*135)/int((workspace[2] - workspace[0])/2)))
                                        #    print("height object:", int(y))
                                        #    print("height_mm object:", int((int(y)*185)/int((workspace[3] - workspace[1])/2)))

                                        #    break

                                        workspace_width = int((workspace[2] - workspace[0])/2)
                                        #workspace_width_mm = 135

                                        workspace_height = int((workspace[3] - workspace[1])/2)
                                        #workspace_height_mm = 185

                                        #workspace_depth = 960
                                        object_depth = min_value

                                        #object_width = abs(320 - x)
                                        #object_width_mm = int((object_width*workspace_width_mm)/workspace_width)
                                        workspace_width_max = int((workspace_width * int(workspace_depth)) / object_depth)
                                        #print(x)
                                        #print(object_width)
                                        #print(workspace_width_max)

                                        #object_height = abs(240 - y)
                                        #object_height_mm = int((object_height*workspace_height_mm)/workspace_height)
                                        workspace_height_max = int((workspace_height * int(workspace_depth)) / object_depth)
                                        #print(y)
                                        #print(object_height)
                                        #print(workspace_height_max)
                                        #if object_width <= workspace_width_max and object_height <= workspace_height_max:
                                        if ((x >= (320 - (int(workspace_width_max)/2))) and (x <= (320 + (int(workspace_width_max)/2)))) and ((y >= (240 - (int(workspace_height_max)/2))) and (y <= (240 + (int(workspace_height_max)/2)))):
                                            valid_count = numpy.sum(numpy.abs(neighbors - min_value) <= tolerance)
                                            total_count = neighbors.size

                                            if valid_count / total_count >= 0.9:

                                                print(f"Ponto {min_idx} válido, todos vizinhos semelhantes")
                                                #print(x)
                                                #print(object_width)
                                                #print(workspace_width_max)
                                                #print(y)
                                                #print(object_height)
                                                #print(workspace_height_max)
                                                
                                                minimum_value = min_value
                                                point_idx = y,x
                                                exposureArray.append(exposureTime)
                                                found = True
                                                break

                                            else:
                                                #print("Não serve:", x, y, min_value)
                                                frametmp[y, x] = 9999

                                        else:
                                            #print(f"Ponto {min_idx} descartado, vizinhos diferentes")
                                            #workspace_region[y, x] = 9999
                                            frametmp[y, x] = 9999
                                else:
                                    break
                                    
                                if found:
                                    break

                        #convert ushort value to 0xff is just for display
                        img = numpy.int32(frametmp)
                        img = img*255/colorSlope
                        img = numpy.clip(img, 0, 255)
                        img = numpy.uint8(img)
                        frametmp = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)

                        frame_copy = frametmp
                        cv2.rectangle(frame_copy, (workspace[0], workspace[1]), (workspace[2], workspace[3]), (255, 0, 0), 2)
                        #cv2.rectangle(frame_copy, (workspace[0] - a, workspace[1] - a), (workspace[2] + a, workspace[3] + a), (255, 0, 0), 2)

                        cv2.imshow("Depth Image", frametmp)
                        cv2.waitKey(1)
                        
                        #exposureTime = 4000
                        exposureTime += 300
                    else:
                        print("Profundidade mínima:", minimum_value/10, 'cm')
                        #min_y = workspace[1] + min_idx[0]
                        #min_x = workspace[0] + min_idx[1]
                        #min_y = workspace[1] - a + min_idx[0]
                        #min_x = workspace[0] - a + min_idx[1]
                        min_y = point_idx[0]
                        min_x = point_idx[1]
                        print("Ponto:", (min_x, min_y))
                        print("Exposure Times", exposureArray)

                        exposureTime = 400
                        not_set = 0
                        search = 0

                if not_set == 0:
                    camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(exposureTime))

                    ret_code, exposureStruct = camera.VZ_GetExposureTime(VzSensorType.VzToFSensor)
                    #print('Exposure Time:', exposureStruct.exposureTime)

                    ret, frameready = camera.VZ_GetFrameReady(c_uint16(1200))
                    if  ret !=0:
                        print("VZ_GetFrameReady failed:",ret)
                        continue
                    hasDepth=0

                    if  frameready.depth:      
                        ret,depthframe = camera.VZ_GetFrame(VzFrameType.VzDepthFrame)
                        if  ret == 0:
                            hasDepth=1
                            frametmp = numpy.ctypeslib.as_array(depthframe.pFrameData, (1, depthframe.width * depthframe.height * 2))
                            frametmp.dtype = numpy.uint16
                            frametmp.shape = (depthframe.height, depthframe.width)
                            frametmp = cv2.resize(frametmp, (640, 480))
                        
                        else:
                            print("get depth frame failed:",ret)

                    mask = (frametmp >= minimum_value) & (frametmp <= minimum_value + threshold)

                    labeled_array, num_features = ndimage.label(mask)

                    sizes = ndimage.sum(mask, labeled_array, range(1, num_features + 1))

                    if len(sizes) == 0:
                        print("Nenhuma região encontrada")
                    else:
                        # Encontrar região com maior número de pixels
                        largest_region_index = numpy.argmax(sizes) + 1  # +1 porque labels começam em 1
                        largest_region_mask = (labeled_array == largest_region_index)

                        objectpixelsy, objectpixelsx = numpy.where(largest_region_mask)
                        objectpixelsmin_x, objectpixelsmax_x = objectpixelsx.min(), objectpixelsx.max()
                        objectpixelsmin_y, objectpixelsmax_y = objectpixelsy.min(), objectpixelsy.max()
                        #print("Área Coberta:", objectpixelsmin_x, objectpixelsmin_y, objectpixelsmax_x, objectpixelsmax_y)

                        object_region = frametmp[objectpixelsmin_y:objectpixelsmax_y, objectpixelsmin_x:objectpixelsmax_x]

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

                    #convert ushort value to 0xff is just for display
                    img = numpy.int32(frametmp)
                    img = img*255/colorSlope
                    img = numpy.clip(img, 0, 255)
                    img = numpy.uint8(img)
                    frametmp = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)

                    frame_copy = frametmp
                    cv2.rectangle(frame_copy, (objectpixelsmin_x, objectpixelsmin_y), (objectpixelsmax_x, objectpixelsmax_y), (255, 0, 0), 2)
                    cv2.imshow("Depth Image", frametmp)

            key = cv2.waitKey(1)
            if key == ord('c'):
                workspace_not_defined = 1
                cv2.destroyAllWindows()
            if key == ord('s'):
                search = 1
                cv2.destroyAllWindows()
            if  key == 27:
                cv2.destroyAllWindows()
                print("---end---")
                break;
                   
    except Exception as e :
        print(e)
    finally :
        print('end')
else:
    print('VZ_OpenDeviceByUri failed: ' + str(ret))