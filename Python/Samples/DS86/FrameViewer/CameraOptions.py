from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import time

from CameraState import camState

def openCamera():
    print("Opening Camera!")

    if camState.camera is not None:
        return{"message": "Nothing to Open"}
    else:    
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
        if  ret == 0:

            ret = camState.camera.VZ_StartStream()
            if  ret == 0:
                print("start stream successful")
            else:
                print("VZ_StartStream failed:",ret)

            camState.colorSlope = c_uint16(1500) #distância máxima pretendida 5 metros
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

            ret,enable = camState.camera.VZ_GetSpatialFilterEnabled()
            if  ret == 0:
                print("The default SpatialFilter switch is " + str(enable))
            else:
                print("VZ_GetSpatialFilterEnabled failed:"+ str(ret))   

            enable = not enable
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
        
            ret, intrParam = camState.camera.VZ_GetSensorIntrinsicParameters()
            if ret != 0:
                raise RuntimeError("Error obtaining intrinsic parameters!")
            
            camState.fx = intrParam.fx
            camState.fy = intrParam.fy
            camState.cx = intrParam.cx
            camState.cy = intrParam.cy

            print("Cx:", camState.cx)
            print("Cy:", camState.cy)
            print("fx:", camState.fx)
            print("fy:", camState.fy)

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