from pickle import FALSE, TRUE
import sys
sys.path.append('../../../')

from API.VzenseDS_api import *
import time

camera = VzenseTofCam()


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
        print(' failed:' + ret)  
        exit()  
elif camera_count == 1:
    ret,device_info=camera.VZ_GetDeviceInfo()
    if ret==0:
        print('cam uri:' + str(device_info.uri))
    else:
        print(' failed:' + ret)   
        exit() 
else: 
    print("there are no camera found")
    exit()

if  VzConnectStatus.Connected.value != device_info.status:
	print("connect statu:",device_info.status)  
	print("Call VZ_OpenDeviceByUri with connect status :",VzConnectStatus.Connected.value)
	exit()
else:
    print('cam productName:' + str(device_info.productName))
    print('cam uri:' + str(device_info.uri))
    print('cam alias:' + str(device_info.alias))
    print('cam serialNumber:' + str(device_info.serialNumber))
    print('cam ip:' + str(device_info.ip))
    print('cam status:' + str(device_info.status))

ret = camera.VZ_OpenDeviceByUri(device_info.uri)
if  ret == 0:
    print("open device successful")
else:
    print('VZ_OpenDeviceByUri failed: ' + str(ret))   
 
 
# get FW
ret, fw = camera.VZ_GetFirmwareVersion()
if  ret == 0:
    print("VZ_GetFirmwareVersion :",str(fw))
else:
    print("VZ_GetFirmwareVersion failed:",ret)

 
ret = camera.VZ_CloseDevice()
if  ret == 0:
    print("close device successful")
else:
    print('VZ_CloseDevice failed: ' + str(ret))   
           