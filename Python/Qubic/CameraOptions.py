import time
import ctypes

from CameraState import camState
from FilterState import filterState
from FrameState import frameState
from ScepterSDK import *
import threading
import numpy

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

    print("Opening Camera!")

    ret = lib.scInitialize()
    print("scInitialize:", ret)

    if ret != 0:
        raise RuntimeError("Failed to initialize Scepter SDK!")

    camera_count = ctypes.c_uint32(0)
    retry_count = 100

    while camera_count.value==0 and retry_count > 0:
        ret = lib.scGetDeviceCount(ctypes.byref(camera_count), 1000)

        print(
            "scGetDeviceCount:",
            ret,
            "| câmaras:",
            camera_count.value
        )

        if camera_count.value == 0:
            retry_count -= 1
            time.sleep(1)
            print("Scanning......   ", retry_count)

    if camera_count.value == 0:
        print("There are no cameras found")
        lib.scShutdown()
        return {"message": "No camera detected"}

    device_info_list = (ScDeviceInfo * camera_count.value)()

    print("ANTES scGetDeviceInfoList")

    ret = lib.scGetDeviceInfoList(
        camera_count.value,
        device_info_list
    )

    print("DEPOIS scGetDeviceInfoList:", ret)

    if ret != 0:
        lib.scShutdown()
        raise RuntimeError("Failed to get camera information!")

    device_info = device_info_list[0]

    print("Camera")
    print("--------------------")
    print("Product:", device_info.productName.decode(errors="ignore"))
    print("Serial:", device_info.serialNumber.decode(errors="ignore"))
    print("IP:", device_info.ip.decode(errors="ignore"))
    print("Status:", device_info.status)

    # Abrir câmara pelo número de série
    camera = ScDeviceHandle()

    serial = device_info.serialNumber

    print("Opening camera...")
    ret = lib.scOpenDeviceBySN(
        serial,
        ctypes.byref(camera)
    )

    print("scOpenDeviceBySN:", ret)

    if ret != 0:
        lib.scShutdown()
        return {"message": "Failed"}

    print("Device handle:", camera)
    print("Camera opened successfully!")

    camState.camera = camera

    # Iniciar stream
    ret = lib.scStartStream(camState.camera)
    print("scStartStream:", ret)

    if ret != 0:
        lib.scCloseDevice(ctypes.byref(camState.camera))
        camState.camera = None
        lib.scShutdown()
        raise RuntimeError("Failed to start camera stream!")

    params = ScTimeFilterParams()

    ret = lib.scGetTimeFilterParams(
        camState.camera,
        ctypes.byref(params)
    )

    if ret == 0:
        print("The default TimeFilter switch is " + str(params.enable))
    else:
        print("scGetTimeFilterParams failed:" + str(ret))

    params.enable = True

    ret = lib.scSetTimeFilterParams(
        camState.camera,
        params
    )

    if ret == 0:
        print(
            "Set TimeFilter switch to "
            + str(params.enable)
            + " is Ok"
        )
    else:
        print(
            "scSetTimeFilterParams failed:"
            + str(ret)
        )

    # Definir modo de exposição manual
    ret = lib.scSetExposureControlMode(
        camState.camera,
        0x01,  # SC_TOF_SENSOR
        1      # SC_EXPOSURE_CONTROL_MODE_MANUAL
    )

    if ret == 0:
        print("Set exposure control mode to manual is ok")
    else:
        print("scSetExposureControlMode failed:", ret)

    # Definir tempo de exposição
    ret = lib.scSetExposureTime(
        camState.camera,
        0x01,  # SC_TOF_SENSOR
        ctypes.c_int32(camState.exposureTime)
    )

    if ret == 0:
        print("Set exposure time is ok")
    else:
        print("scSetExposureTime failed:", ret)

    # Confirmar tempo de exposição
    exposureTime = ctypes.c_int32()

    ret = lib.scGetExposureTime(
        camState.camera,
        0x01,  # SC_TOF_SENSOR
        ctypes.byref(exposureTime)
    )

    if ret == 0:
        print("Exposure Time:", exposureTime.value)
    else:
        print("scGetExposureTime failed:", ret)

    setFPS()

    # Ativar transformação Color -> Depth
    ret = lib.scSetTransformColorImgToDepthSensorEnabled(
        camState.camera,
        True
    )

    if ret == 0:
        print("scSetTransformColorImgToDepthSensorEnabled ok")
    else:
        print(
            "scSetTransformColorImgToDepthSensorEnabled failed:",
            ret
        )

    setFlyingPixelFilter(value = camState.flyingPixelFilter) 
    
    setFillHoleFilter(value = camState.fillHoleFilter)

    setSpatialFilter(value = camState.spatialFilter)
        
    setConfidenceFilter(value = camState.confidenceFilter)

    # Intrinsic Parameters Depth

    intrParam = ScSensorIntrinsicParameters()

    ret = lib.scGetSensorIntrinsicParameters(
        camState.camera,
        0x01,  # SC_TOF_SENSOR
        ctypes.byref(intrParam)
    )

    if ret != 0:
        raise RuntimeError("Error obtaining depth intrinsic parameters!")
        
    camState.fx_d = intrParam.fx
    camState.fy_d = intrParam.fy
    camState.cx_d = intrParam.cx
    camState.cy_d = intrParam.cy

    print("Cx Depth:", camState.cx_d)
    print("Cy Depth:", camState.cy_d)
    print("fx Depth:", camState.fx_d)
    print("fy Depth:", camState.fy_d)

    # Intrinsic Parameters RGB

    intrParam = ScSensorIntrinsicParameters()

    ret = lib.scGetSensorIntrinsicParameters(
        camState.camera,
        0x02,  # SC_COLOR_SENSOR
        ctypes.byref(intrParam)
    )

    if ret != 0:
        raise RuntimeError("Error obtaining color intrinsic parameters!")

    camState.fx_rgb = intrParam.fx
    camState.fy_rgb = intrParam.fy
    camState.cx_rgb = intrParam.cx
    camState.cy_rgb = intrParam.cy

    print("Cx RGB:", camState.cx_rgb)
    print("Cy RGB:", camState.cy_rgb)
    print("fx RGB:", camState.fx_rgb)
    print("fy RGB:", camState.fy_rgb)

    print("Camera ready")

    camState._running = True
    camState._thread = threading.Thread(target=captureLoop, daemon=True)
    camState._thread.start()

def stopCamera():
    camState._running = False
    if camState._thread:
        camState._thread.join(timeout=3)
    if camState.camera is None:
        return{"message": "Nothing to Close"}
    else:
        ret = lib.scStopStream(camState.camera)    
        if  ret == 0:
            print("stop stream successful")
        else:
            print('VZ_StopStream failed: ' + str(ret))  

        ret = lib.scCloseDevice(
            ctypes.byref(camState.camera)
        ) 
        if  ret == 0:
            camState.camera = None
            print("[CameraStream] Câmara fechada.")
            return{"message": "Success"}
        else:
            return{"message": "Failed"}
    
def setFPS():
    ret = lib.scSetFrameRate(
        camState.camera,
        ctypes.c_int32(camState.fps)
    )
    if  ret == 0:
        print("Set frame rate is ok")   
    else:
        print("scSetFrameRate failed:"+ str(ret)) 

    frameRate = ctypes.c_int32()

    ret = lib.scGetFrameRate(
        camState.camera,
        ctypes.byref(frameRate)
    )

    if  ret == 0:
        print("Get default frame rate:"+ str(frameRate.value))   
    else:
        print("scGetFrameRate failed:"+ str(ret))  

def captureLoop():
    print("[CameraStream] Iniciando captura de frames...")

    while camState._running:

        frameReady = ScFrameReady()

        ret = lib.scGetFrameReady(
            camState.camera,
            ctypes.c_uint16(33),
            ctypes.byref(frameReady)
        )

        if ret != 0:
            continue

        else:
            hasColorToDepth =0
            hasDepth = 0
            hasColor = 0

            colorToDepthFrame = None
            depthFrame = None
            colorFrame = None

            if frameReady.transformedColor:     
                rgbFrame = ScFrame()

                ret = lib.scGetFrame(
                    camState.camera,
                    4,  # SC_TRANSFORM_COLOR_IMG_TO_DEPTH_SENSOR_FRAME
                    ctypes.byref(rgbFrame)
                )

                if ret == 0:
                    hasColorToDepth = 1  
                else:
                    print("get color to depth frame failed:",ret)

            if frameReady.depth:
                depthFrameRaw = ScFrame()

                ret = lib.scGetFrame(
                    camState.camera,
                    0,  # SC_DEPTH_FRAME
                    ctypes.byref(depthFrameRaw)
                )

                if ret == 0:
                    hasDepth = 1
                else:
                    print("get depth frame failed:",ret)

            if frameReady.color:
                colorFrameRaw = ScFrame()

                ret = lib.scGetFrame(
                    camState.camera,
                    3,  # SC_COLOR_FRAME
                    ctypes.byref(colorFrameRaw)
                )

                if ret == 0:
                    hasColor = 1
                else:
                    print("get Color frame failed:", ret)

            if hasColorToDepth == 1:
                frametmp = numpy.ctypeslib.as_array(
                    rgbFrame.pFrameData,
                    (rgbFrame.width * rgbFrame.height * 3,)
                )

                frametmp.dtype = numpy.uint8
                frametmp.shape = (
                    rgbFrame.height,
                    rgbFrame.width,
                    3
                )

                colorToDepthFrame = frametmp.copy()

            if hasDepth == 1:
                frametmp = numpy.ctypeslib.as_array(
                    depthFrameRaw.pFrameData,
                    (depthFrameRaw.width * depthFrameRaw.height * 2,)
                )

                frametmp.dtype = numpy.uint16
                frametmp.shape = (
                    depthFrameRaw.height,
                    depthFrameRaw.width
                )

                depthFrame = frametmp.copy()

            if hasColor == 1:
                frametmp = numpy.ctypeslib.as_array(
                    colorFrameRaw.pFrameData,
                    (colorFrameRaw.width * colorFrameRaw.height * 3,)
                )

                frametmp.dtype = numpy.uint8
                frametmp.shape = (
                    colorFrameRaw.height,
                    colorFrameRaw.width,
                    3
                )

                colorFrame = frametmp.copy()

            if hasColorToDepth == 1 and hasDepth == 1 and hasColor == 1:
                frameState.colorToDepthFrame = colorToDepthFrame
                frameState.depthFrame = depthFrame
                frameState.colorFrame = colorFrame
                frameState.colorToDepthFrameHDR = colorToDepthFrame
                frameState.depthFrameHDR = depthFrame

# def buildHDRDepth(depthFrames):
#     stacked_d = numpy.stack(depthFrames, axis=0).astype(numpy.float32)

#     mask_d = (stacked_d > 150) & (stacked_d <= 5000)
#     stacked_d[~mask_d] = numpy.nan

#     median_d = numpy.nanmedian(stacked_d, axis=0)

#     mad_d = numpy.nanmedian(
#         numpy.abs(stacked_d - median_d),
#         axis=0
#     )

#     unstable = mad_d > 15

#     hdrDepth = median_d.copy()

#     min_d = numpy.nanmin(stacked_d, axis=0)
#     hdrDepth[unstable] = min_d[unstable]

#     return numpy.nan_to_num(
#         hdrDepth,
#         nan=0
#     ).astype(numpy.uint16)

# def buildHDRColor(colorFrames):
#     stacked = numpy.stack(colorFrames, axis=0).astype(numpy.float32)

#     mask = stacked > 0
#     stacked[~mask] = 0

#     count = mask.sum(axis=0).clip(min=1)

#     return (
#         stacked.sum(axis=0) / count
#     ).astype(numpy.uint8)

# def processHDR(click_timestamp):
#     global colorArray, depthArray, timestampArray
#     finished = False

#     if click_timestamp is None:
#         click_timestamp = 0

#     if (any(frame is None for frame in colorArray) or any(frame is None for frame in depthArray)) or any(ts <= click_timestamp for ts in timestampArray):
#         #print("Não tem frames suficientes")
#         finished = False
#     else:
#         #lowHDRColor = colorArray[:4]
#         #lowHDRDepth = depthArray[:4]

#         #mediumHDRColor = colorArray[4:]
#         #mediumHDRDepth = depthArray[4:]

#         #hdrLowColor = buildHDRColor(lowHDRColor)
#         #hdrMediumColor = buildHDRColor(mediumHDRColor)
 
#         #hdrLowDepth = buildHDRDepth(lowHDRDepth)
#         #hdrMediumDepth = buildHDRDepth(mediumHDRDepth)

#         #finalColor = buildHDRColor([hdrLowColor, hdrMediumColor])
#         #finalDepth = buildHDRDepth([hdrLowDepth, hdrMediumDepth])

#         finalColor = buildHDRColor(colorArray)
#         finalDepth = buildHDRDepth(depthArray)

#         print("HDR Processed")

#         frameState.colorToDepthFrameHDR = finalColor
#         frameState.depthFrameHDR = finalDepth

#         finished = True

#     return finished

# def processHDR2():
#     global colorArray, depthArray, timestampArray

#     finalColor = buildHDRColor(colorArray)
#     finalDepth = buildHDRDepth(depthArray)

#     print("HDR Processed")

#     frameState.colorToDepthFrameHDR = finalColor
#     frameState.depthFrameHDR = finalDepth

def setFlyingPixelFilter(value: bool):
    params = ScFlyingPixelFilterParams()

    ret = lib.scGetFlyingPixelFilterParams(
        camState.camera,
        ctypes.byref(params)
    )

    if  ret == 0:
        print("The default FlyingPixelFilter switch is " + str(params.enable))
    else:
        print("scGetFlyingPixelFilterParams failed:"+ str(ret))   

    params.enable = bool(value)

    ret = lib.scSetFlyingPixelFilterParams(
        camState.camera,
        params
    )

    if  ret == 0:
        filterState.flyingPixelFilter = params.enable
        print("Set FlyingPixelFilter switch to "+ str(params.enable) + " is Ok")   
    else:
        print("scSetFlyingPixelFilterParams failed:"+ str(ret))

def setFillHoleFilter(value: bool):
    enable = ctypes.c_bool()

    ret = lib.scGetFillHoleFilterEnabled(
        camState.camera,
        ctypes.byref(enable)
    )

    if  ret == 0:
        print("The default FillHoleFilter switch is " + str(enable.value))
    else:
        print("scGetFillHoleFilterEnabled failed:"+ str(ret))   

    enable.value = bool(value)

    ret = lib.scSetFillHoleFilterEnabled(
        camState.camera,
        enable
    )

    if  ret == 0:
        filterState.fillHoleFilter = enable.value
        print("Set FillHoleFilter switch to "+ str(enable.value) + " is Ok")   
    else:
        print("scSetFillHoleFilterEnabled failed:"+ str(ret)) 

def setSpatialFilter(value: bool):
    enable = ctypes.c_bool()

    ret = lib.scGetSpatialFilterEnabled(
        camState.camera,
        ctypes.byref(enable)
    )

    if  ret == 0:
        print("The default SpatialFilter switch is " + str(enable.value))
    else:
        print("scGetSpatialFilterEnabled failed:"+ str(ret))   

    enable.value = bool(value)

    ret = lib.scSetSpatialFilterEnabled(
        camState.camera,
        enable
    )

    if  ret == 0:
        filterState.spatialFilter = enable.value
        print("Set SpatialFilter switch to "+ str(enable.value) + " is Ok")   
    else:
        print("scSetSpatialFilterEnabled failed:"+ str(ret))

def setConfidenceFilter(value: bool):
    params = ScConfidenceFilterParams()

    ret = lib.scGetConfidenceFilterParams(
        camState.camera,
        ctypes.byref(params)
    )

    if  ret == 0:
        print("The default ConfidenceFilter switch is " + str(params.enable))
    else:
        print("scGetConfidenceFilterParams failed:"+ str(ret))

    params.enable = bool(value)

    ret = lib.scSetConfidenceFilterParams(
        camState.camera,
        params
    )

    if  ret == 0:
        filterState.confidenceFilter = params.enable
        print("Set ConfidenceFilter switch to "+ str(params.enable) + " is Ok")   
    else:
        print("scSetConfidenceFilterParams failed:"+ str(ret))