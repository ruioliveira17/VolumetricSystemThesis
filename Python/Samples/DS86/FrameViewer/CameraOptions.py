from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import time

from CameraState import camState

def openCamera():
    print("Opening Camera!")

    if camState.camera is not None:
        #print("Camera already opened!")
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
            print("connect statu:",device_info.status)  
            print("Call VZ_OpenDeviceByIP with connect status :",VzConnectStatus.Connected.value)
            exit()
        else:
            print("uri: "+str(device_info.uri))
            print("alias: "+str(device_info.alias))
            print("ip: "+str(device_info.ip))
            print("connectStatus: "+str(device_info.status))

        ret = camState.camera.VZ_OpenDeviceByIP(device_info.ip)
        if  ret == 0:
            #print("open device successful")

            ret = camState.camera.VZ_StartStream()
            if  ret == 0:
                print("start stream successful")
            else:
                print("VZ_StartStream failed:",ret)

            #print("ColorSlope", camState.colorSlope)
            camState.colorSlope = c_uint16(1500) #distância máxima pretendida 5 metros
            #print("ColorSlope", camState.colorSlope)
            camState.camera.VZ_SetExposureControlMode(VzSensorType.VzToFSensor, VzExposureControlMode.VzExposureControlMode_Manual)
            camState.camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(700))

            ret_code, exposureStruct = camState.camera.VZ_GetExposureTime(VzSensorType.VzToFSensor)
            print('Exposure Time:', exposureStruct.exposureTime)

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

            return{"message": "Success"}
        else:
            #print('VZ_OpenDeviceByIP failed: ' + str(ret))
            return{"message": "Failed"}

def closeCamera():
    print("Closing Camera!")

    if camState.camera is None:
        #print("Camera is already closed!")
        return{"message": "Nothing to Close"}
    else:
        ret = camState.camera.VZ_CloseDevice()  
        if  ret == 0:
            #print("close device successful")
            camState.camera = None
            return{"message": "Success"}
        else:
            #print('VZ_CloseDevice failed: ' + str(ret))
            return{"message": "Failed"}
    
def statusCamera():
    print("Status")

    if camState.camera is not None:
        camState.status = "Opened"
        return{"status": "Camera is opened!"}
    else:
        camState.status = "Closed"
        return{"status": "Camera is closed!"}