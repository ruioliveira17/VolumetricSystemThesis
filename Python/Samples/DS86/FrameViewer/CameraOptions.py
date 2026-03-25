from pickle import FALSE, TRUE
import sys
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "Python"))

from API.VzenseDS_api import *
import time

from CameraState import camState
from FrameState import frameState
import threading

def openCamera():
    if camState.camera is not None:
        print("Camera is already opened!")
        return{"message": "Nothing to Open"}
    else:
        print("Opening Camera!")
        camState.camera = VzenseTofCam()

        camera_count = camState.camera.VZ_GetDeviceCount()
        retry_count = 100
        while camera_count==0 and retry_count > 0:
            retry_count = retry_count-1
            camera_count = camState.camera.VZ_GetDeviceCount()
            time.sleep(1)
            print("scaning......   ",retry_count)

        device_info=VzDeviceInfo()

        if camera_count > 1:
            ret,device_infolist=camState.camera.VZ_GetDeviceInfoList(camera_count)
            if ret==0:
                device_info = device_infolist[0]
                for info in device_infolist: 
                    print('cam uri:  ' + str(info.uri))
            else:
                print(' failed:' , ret)  
                exit()  
        elif camera_count == 1:
            ret,device_info=camState.camera.VZ_GetDeviceInfo()
            if ret==0:
                print('cam uri:' + str(device_info.uri))
            else:
                print(' failed:', ret)   
                exit() 
        else: 
            print("there are no camera found")
            exit()

        if  VzConnectStatus.Connected.value != device_info.status:
            print("connect status:",device_info.status)  
            print("Call VZ_OpenDeviceByIP with connect status :",VzConnectStatus.Connected.value)
            exit()
        else:
            print("uri: "+str(device_info.uri))
            print("alias: "+str(device_info.alias))
            print("ip: "+str(device_info.ip))
            print("connectStatus: "+str(device_info.status))

        ret = camState.camera.VZ_OpenDeviceByIP(device_info.ip)
        print("VZ_OpenDeviceByIP ret =", ret)
        if  ret == 0:

            ret = camState.camera.VZ_StartStream()
            if  ret == 0:
                print("start stream successful")
            else:
                print("VZ_StartStream failed:",ret)

            ret,params = camState.camera.VZ_GetTimeFilterParams()
            if  ret == 0:
                print("The default TimeFilter switch is " + str(params.enable))
            else:
                print("VZ_GetTimeFilterParams failed:"+ str(ret))   

            params.enable = True
            ret = camState.camera.VZ_SetTimeFilterParams(params)
            if  ret == 0:
                print("Set TimeFilter switch to "+ str(params.enable) + " is Ok")   
            else:
                print("VZ_SetTimeFilterParams failed:"+ str(ret))   

            camState.camera.VZ_SetExposureControlMode(VzSensorType.VzToFSensor, VzExposureControlMode.VzExposureControlMode_Manual)
            camState.camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(camState.exposureTime))

            ret_code, exposureStruct = camState.camera.VZ_GetExposureTime(VzSensorType.VzToFSensor)
            print('Exposure Time:', exposureStruct.exposureTime)

            ret = camState.camera.VZ_SetFrameRate(5)
            if  ret == 0:
                print("Set frame rate 5 is ok")   
            else:
                print("VZ_SetFrameRate failed:"+ str(ret)) 

            ret,frameRate = camState.camera.VZ_GetFrameRate()
            if  ret == 0:
                print("Get default frame rate:"+ str(frameRate))   
            else:
                print("VZ_GetFrameRate failed:"+ str(ret))  

            # set Mapper
            ret = camState.camera.VZ_SetTransformColorImgToDepthSensorEnabled(c_bool(True))

            if  ret == 0:
                print("VZ_SetTransformColorImgToDepthSensorEnabled ok")
            else:
                print("VZ_SetTransformColorImgToDepthSensorEnabled failed:",ret)    

            ret,params = camState.camera.VZ_GetFlyingPixelFilterParams()
            if  ret == 0:
                print("The default FlyingPixelFilter switch is " + str(params.enable))
            else:
                print("VZ_GetFlyingPixelFilterParams failed:"+ str(ret))   

            params.enable = True
            ret = camState.camera.VZ_SetFlyingPixelFilterParams(params)
            if  ret == 0:
                print("Set FlyingPixelFilter switch to "+ str(params.enable) + " is Ok")   
            else:
                print("VZ_SetFlyingPixelFilterParams failed:"+ str(ret))   

            ret,enable = camState.camera.VZ_GetFillHoleFilterEnabled()
            if  ret == 0:
                print("The default FillHoleFilter switch is " + str(enable))
            else:
                print("VZ_GetFillHoleFilterEnabled failed:"+ str(ret))   

            enable = True
            ret = camState.camera.VZ_SetFillHoleFilterEnabled(enable)
            if  ret == 0:
                print("Set FillHoleFilter switch to "+ str(enable) + " is Ok")   
            else:
                print("VZ_SetFillHoleFilterEnabled failed:"+ str(ret))   

            ret,enable = camState.camera.VZ_GetSpatialFilterEnabled()
            if  ret == 0:
                print("The default SpatialFilter switch is " + str(enable))
            else:
                print("VZ_GetSpatialFilterEnabled failed:"+ str(ret))   

            enable = True
            ret = camState.camera.VZ_SetSpatialFilterEnabled(enable)
            if  ret == 0:
                print("Set SpatialFilter switch to "+ str(enable) + " is Ok")   
            else:
                print("VZ_SetSpatialFilterEnabled failed:"+ str(ret))

            ret,params = camState.camera.VZ_GetConfidenceFilterParams()
            if  ret == 0:
                print("The default ConfidenceFilter switch is " + str(params.enable))
            else:
                print("VZ_GetConfidenceFilterParams failed:"+ str(ret))

            params.enable = False
            ret = camState.camera.VZ_SetConfidenceFilterParams(params)
            if  ret == 0:
                print("Set ConfidenceFilter switch to "+ str(params.enable) + " is Ok")   
            else:
                print("VZ_SetConfidenceFilterParams failed:"+ str(ret))
        
            ret, intrParam = camState.camera.VZ_GetSensorIntrinsicParameters(VzSensorType.VzToFSensor)
            if ret != 0:
                raise RuntimeError("Error obtaining intrinsic parameters!")
            
            camState.fx_d = intrParam.fx
            camState.fy_d = intrParam.fy
            camState.cx_d = intrParam.cx
            camState.cy_d = intrParam.cy

            print("Cx Depth:", camState.cx_d)
            print("Cy Depth:", camState.cy_d)
            print("fx Depth:", camState.fx_d)
            print("fy Depth:", camState.fy_d)

            ret, intrParam = camState.camera.VZ_GetSensorIntrinsicParameters(VzSensorType.VzColorSensor)
            if ret != 0:
                raise RuntimeError("Error obtaining intrinsic parameters!")

            camState.fx_rgb = intrParam.fx
            camState.fy_rgb = intrParam.fy
            camState.cx_rgb = intrParam.cx
            camState.cy_rgb = intrParam.cy

            print("Cx RGB:", camState.cx_rgb)
            print("Cy RGB:", camState.cy_rgb)
            print("fx RGB:", camState.fx_rgb)
            print("fy RGB:", camState.fy_rgb)

            #ret, extrParam = camState.camera.VZ_GetSensorExtrinsicParameters()
            #if ret != 0:
            #    raise RuntimeError("Error obtaining intrinsic parameters!")
            
            #print("Translation:", list(extrParam.translation))
            #print("Rotation:", list(extrParam.rotation))
            return{"message": "Success"}

        else:
            return{"message": "Failed"}

def closeCamera():
    print("Closing Camera!")

    if camState.camera is None:
        return{"message": "Nothing to Close"}
    else:
        ret = camState.camera.VZ_StopStream()       
        if  ret == 0:
            print("stop stream successful")
        else:
            print('VZ_StopStream failed: ' + str(ret))  

        ret = camState.camera.VZ_CloseDevice()  
        if  ret == 0:
            camState.camera = None
            return{"message": "Success"}
        else:
            return{"message": "Failed"}
    
def statusCamera():
    print("Status")

    if camState.camera is not None:
        camState.status = "Opened"
        return{"status": "Camera is opened!"}
    else:
        camState.status = "Closed"
        return{"status": "Camera is closed!"}
    
def startCamera():
    if camState.camera is not None:
        print("Camera is already opened!")
        return{"message": "Nothing to Open"}
    else:
        print("Opening Camera!")
        camState.camera = VzenseTofCam()

    camera_count = camState.camera.VZ_GetDeviceCount()
    retry_count = 100
    while camera_count==0 and retry_count > 0:
        retry_count = retry_count-1
        camera_count = camState.camera.VZ_GetDeviceCount()
        time.sleep(1)
        print("scaning......   ",retry_count)

    device_info=VzDeviceInfo()

    if camera_count > 1:
        ret,device_infolist=camState.camera.VZ_GetDeviceInfoList(camera_count)
        if ret==0:
            device_info = device_infolist[0]
            for info in device_infolist: 
                print('cam uri:  ' + str(info.uri))
        else:
            print(' failed:' , ret)  
            raise RuntimeError("Nenhuma câmera encontrada!")  
    elif camera_count == 1:
        ret,device_info=camState.camera.VZ_GetDeviceInfo()
        if ret==0:
            print('cam uri:' + str(device_info.uri))
        else:
            print(' failed:', ret)   
            raise RuntimeError("Nenhuma câmera encontrada!") 
    else: 
        print("there are no camera found")
        return {"message": "No camera detected"}

    retry = 20
    while retry > 0:
        if  VzConnectStatus.Connected.value == device_info.status:
            print("uri: "+str(device_info.uri))
            print("alias: "+str(device_info.alias))
            print("ip: "+str(device_info.ip))
            print("connectStatus: "+str(device_info.status))
            break
        retry -= 1
        time.sleep(1)
        ret,device_info=camState.camera.VZ_GetDeviceInfo()
    else:
        print("connect status:",device_info.status)  
        print("Call VZ_OpenDeviceByIP with connect status :",VzConnectStatus.Connected.value)
        raise RuntimeError("Connected Status Error!") 

    ret = camState.camera.VZ_OpenDeviceByIP(device_info.ip)
    print("VZ_OpenDeviceByIP ret =", ret)
    if  ret != 0:
        return{"message": "Failed"}
    else:
        ret = camState.camera.VZ_StartStream()
        if  ret == 0:
            print("start stream successful")
        else:
            print("VZ_StartStream failed:",ret)

        ret,params = camState.camera.VZ_GetTimeFilterParams()
        if  ret == 0:
            print("The default TimeFilter switch is " + str(params.enable))
        else:
            print("VZ_GetTimeFilterParams failed:"+ str(ret))   

        params.enable = True
        ret = camState.camera.VZ_SetTimeFilterParams(params)
        if  ret == 0:
            print("Set TimeFilter switch to "+ str(params.enable) + " is Ok")   
        else:
            print("VZ_SetTimeFilterParams failed:"+ str(ret))   

        camState.camera.VZ_SetExposureControlMode(VzSensorType.VzToFSensor, VzExposureControlMode.VzExposureControlMode_Manual)
        camState.camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(camState.exposureTime))

        ret_code, exposureStruct = camState.camera.VZ_GetExposureTime(VzSensorType.VzToFSensor)
        print('Exposure Time:', exposureStruct.exposureTime)

        ret = camState.camera.VZ_SetFrameRate(5)
        if  ret == 0:
            print("Set frame rate 5 is ok")   
        else:
            print("VZ_SetFrameRate failed:"+ str(ret)) 

        ret,frameRate = camState.camera.VZ_GetFrameRate()
        if  ret == 0:
            print("Get default frame rate:"+ str(frameRate))   
        else:
            print("VZ_GetFrameRate failed:"+ str(ret))  

        # set Mapper
        ret = camState.camera.VZ_SetTransformColorImgToDepthSensorEnabled(c_bool(True))

        if  ret == 0:
            print("VZ_SetTransformColorImgToDepthSensorEnabled ok")
        else:
            print("VZ_SetTransformColorImgToDepthSensorEnabled failed:",ret)    

        ret,params = camState.camera.VZ_GetFlyingPixelFilterParams()
        if  ret == 0:
            print("The default FlyingPixelFilter switch is " + str(params.enable))
        else:
            print("VZ_GetFlyingPixelFilterParams failed:"+ str(ret))   

        params.enable = True
        ret = camState.camera.VZ_SetFlyingPixelFilterParams(params)
        if  ret == 0:
            print("Set FlyingPixelFilter switch to "+ str(params.enable) + " is Ok")   
        else:
            print("VZ_SetFlyingPixelFilterParams failed:"+ str(ret))   

        ret,enable = camState.camera.VZ_GetFillHoleFilterEnabled()
        if  ret == 0:
            print("The default FillHoleFilter switch is " + str(enable))
        else:
            print("VZ_GetFillHoleFilterEnabled failed:"+ str(ret))   

        enable = True
        ret = camState.camera.VZ_SetFillHoleFilterEnabled(enable)
        if  ret == 0:
            print("Set FillHoleFilter switch to "+ str(enable) + " is Ok")   
        else:
            print("VZ_SetFillHoleFilterEnabled failed:"+ str(ret))   

        ret,enable = camState.camera.VZ_GetSpatialFilterEnabled()
        if  ret == 0:
            print("The default SpatialFilter switch is " + str(enable))
        else:
            print("VZ_GetSpatialFilterEnabled failed:"+ str(ret))   

        enable = True
        ret = camState.camera.VZ_SetSpatialFilterEnabled(enable)
        if  ret == 0:
            print("Set SpatialFilter switch to "+ str(enable) + " is Ok")   
        else:
            print("VZ_SetSpatialFilterEnabled failed:"+ str(ret))

        ret,params = camState.camera.VZ_GetConfidenceFilterParams()
        if  ret == 0:
            print("The default ConfidenceFilter switch is " + str(params.enable))
        else:
            print("VZ_GetConfidenceFilterParams failed:"+ str(ret))

        params.enable = False
        ret = camState.camera.VZ_SetConfidenceFilterParams(params)
        if  ret == 0:
            print("Set ConfidenceFilter switch to "+ str(params.enable) + " is Ok")   
        else:
            print("VZ_SetConfidenceFilterParams failed:"+ str(ret))
    
        ret, intrParam = camState.camera.VZ_GetSensorIntrinsicParameters(VzSensorType.VzToFSensor)
        if ret != 0:
            raise RuntimeError("Error obtaining intrinsic parameters!")
        
        camState.fx_d = intrParam.fx
        camState.fy_d = intrParam.fy
        camState.cx_d = intrParam.cx
        camState.cy_d = intrParam.cy

        print("Cx Depth:", camState.cx_d)
        print("Cy Depth:", camState.cy_d)
        print("fx Depth:", camState.fx_d)
        print("fy Depth:", camState.fy_d)

        ret, intrParam = camState.camera.VZ_GetSensorIntrinsicParameters(VzSensorType.VzColorSensor)
        if ret != 0:
            raise RuntimeError("Error obtaining intrinsic parameters!")

        camState.fx_rgb = intrParam.fx
        camState.fy_rgb = intrParam.fy
        camState.cx_rgb = intrParam.cx
        camState.cy_rgb = intrParam.cy

        print("Cx RGB:", camState.cx_rgb)
        print("Cy RGB:", camState.cy_rgb)
        print("fx RGB:", camState.fx_rgb)
        print("fy RGB:", camState.fy_rgb)

        print("Camera ready")

        #ret, extrParam = camState.camera.VZ_GetSensorExtrinsicParameters()
        #if ret != 0:
        #    raise RuntimeError("Error obtaining intrinsic parameters!")
        
        #print("Translation:", list(extrParam.translation))
        #print("Rotation:", list(extrParam.rotation))

    camState._running = True
    camState._thread = threading.Thread(target=captureLoop, daemon=True)
    camState._thread.start()
    #print(f"[CameraStream] A capturar a {camState.target_fps} FPS")

def stopCamera():
    camState._running = False
    if camState._thread:
        camState._thread.join(timeout=3)
    if camState.camera is None:
        return{"message": "Nothing to Close"}
    else:
        ret = camState.camera.VZ_StopStream()       
        if  ret == 0:
            print("stop stream successful")
        else:
            print('VZ_StopStream failed: ' + str(ret))  

        ret = camState.camera.VZ_CloseDevice()  
        if  ret == 0:
            camState.camera = None
            print("[CameraStream] Câmara fechada.")
            return{"message": "Success"}
        else:
            return{"message": "Failed"}
    
#def set_fps(camState, fps):
#    camState.target_fps = fps
#    camState._frame_interval = 1.0 / fps
#    if camState.camera:
#        ret = camState.camera.VZ_SetFrameRate(fps)
#        if ret != 0:
#            print("VZ_SetFrameRate failed:", ret)

def getRGB():
    with camState._lock:
        return frameState.colorFrame.copy() if camState._rgb_frame is not None else None

def getDepth():
    with camState._lock:
        return frameState.colorToDepthFrame.copy() if camState._depth_frame is not None else None

def captureLoop():
    while camState._running:
        t_start = time.monotonic()

        ret, frameready = camState.camera.VZ_GetFrameReady(c_uint16(33))
        if ret != 0:
            #print("VZ_GetFrameReady failed:",ret)
            continue
        else:
            hasColorToDepth =0
            hasDepth = 0
            hasColor = 0

            if  frameready.color:      
                ret,rgbframe = camState.camera.VZ_GetFrame(VzFrameType.VzTransformColorImgToDepthSensorFrame)
                if  ret == 0:
                    hasColorToDepth = 1   
                else:
                    print("get color frame failed:",ret)

            if  frameready.depth:      
                ret,depthframe = camState.camera.VZ_GetFrame(VzFrameType.VzDepthFrame)
                if  ret == 0:
                    hasDepth = 1
                else:
                    print("get depth frame failed:",ret)

            if frameready.color:
                ret,colorframe = camState.camera.VZ_GetFrame(VzFrameType.VzColorFrame)
                if ret == 0:
                    hasColor = 1
                else:
                    print("get Color frame failed:", ret)

            if hasColorToDepth == 1:
                frametmp = numpy.empty((0, 0, 3), dtype=numpy.uint8)
                frametmp = numpy.ctypeslib.as_array(rgbframe.pFrameData, (1, rgbframe.width * rgbframe.height * 3))
                frametmp.dtype = numpy.uint8
                frametmp.shape = (rgbframe.height, rgbframe.width,3)
                colorToDepthFrame = frametmp.copy()

            if hasDepth == 1:
                frametmp = numpy.empty((0, 0, 3), dtype=numpy.uint8)
                frametmp = numpy.ctypeslib.as_array(depthframe.pFrameData, (1, depthframe.width * depthframe.height * 2))
                frametmp.dtype = numpy.uint16
                frametmp.shape = (depthframe.height, depthframe.width)
                depthFrame = frametmp.copy()

            if hasColor == 1:
                frametmp = numpy.ctypeslib.as_array(colorframe.pFrameData, (1, colorframe.width * colorframe.height * 3))
                frametmp.dtype = numpy.uint8
                frametmp.shape = (colorframe.height, colorframe.width,3)
                colorFrame = frametmp.copy()
                #colorFrame = cv2.resize(colorFrame, (640, 480))
                #cv2.circle(colorFrame, (int(800/2.5), int(608/2.5)), radius=3, color=(255, 0, 0), thickness=1)

            if hasColorToDepth == 1 and hasDepth == 1 and hasColor == 1:
                frameState.colorToDepthFrame = colorToDepthFrame
                frameState.depthFrame = depthFrame
                frameState.colorFrame = colorFrame

        elapsed = time.monotonic() - t_start
        sleep_time = (1/5) - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)