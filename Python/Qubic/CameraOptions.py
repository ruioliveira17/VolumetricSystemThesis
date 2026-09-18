import ctypes
import numpy
import threading
import time

from CameraState import camState
from FilterState import filterState
from FrameState import frameState
from ModeState import modeState
from ScepterSDK import *

hdrExposures = [
    (30, 500),      # 0-2: low
    (500, 1200),     # 3-5: medium
    (1200, 2000),    # 6-8: high
    (100, 1800)      # 9: all
]

depthArray = [None] * 10
timestampArray = [0] * 10

def statusCamera():
    print("Status")

    if camState.camera is not None and camState.cameraStatus == "online":
        return{"status": "Camera is already opened!"}
    elif camState.cameraStatus == "starting":
        return{"status": "Camera is starting!"}
    elif camState.cameraStatus == "shutting_down":
        return{"status": "Camera is closing!"}
    elif camState.camera is None:
        return{"status": "Camera is closed!"}
    
def startCamera():
    try:
        if camState.camera is not None and camState.cameraStatus == "online":
            print("Camera is already opened!")
            return{"message": "Nothing to Open"}
        elif camState.cameraStatus == "starting":
            print("Camera is starting!")
            return{"message": "Nothing to Open"}

        print("Opening Camera!")

        camState.cameraStatus = "starting"

        ret = lib.scInitialize()
        print("scInitialize:", ret)

        if ret != 0:
            raise RuntimeError("Failed to initialize Scepter SDK!")

        camera_count = ctypes.c_uint32(0)
        retry_count = 20

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
            camState.cameraStatus = "error"
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
            camState.cameraStatus = "error"
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
            camState.cameraStatus = "error"
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
            camState.cameraStatus = "error"
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

        setFlyingPixelFilter(value = filterState.flyingPixelFilter) 
        
        setFillHoleFilter(value = filterState.fillHoleFilter)

        setSpatialFilter(value = filterState.spatialFilter)
            
        setConfidenceFilter(value = filterState.confidenceFilter)

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

        camState.cameraStatus = "online"

    except Exception as e:
        camState.cameraStatus = "error"
        print("Camera startup error:", e)

def stopCamera():
    camState._running = False
    if camState._thread:
        camState._thread.join(timeout=3)

    if camState.camera is None:
        return{"message": "Nothing to Close"}
    else:
        camState.cameraStatus = "shutting_down"

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
            camState.cameraStatus = "offline"
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
    global depthArray, timestampArray, hdrExposures

    print("[CameraStream] Iniciando captura de frames...")
    bufferIndex = 0

    while camState._running:
        if camState.hdrEnabled and modeState.currentMenu == "volume-menu":
            if bufferIndex in (0, 3, 6, 9):
                if bufferIndex == 0:
                    low, high = hdrExposures[0]
                elif bufferIndex == 3:
                    low, high = hdrExposures[1]
                elif bufferIndex == 6:
                    low, high = hdrExposures[2]
                else:
                    low, high = hdrExposures[3]

                ret = lib.scSetExposureTimeOfHDR(camState.camera, 0, low)
                if ret != 0:
                    print("scSetExposureTimeOfHDR frame 0 failed:", ret)
                    return {"message": "Failed"}
            
                ret = lib.scSetExposureTimeOfHDR(camState.camera, 1, high)
                if ret != 0:
                    print("scSetExposureTimeOfHDR frame 1 failed:", ret)
                    return {"message": "Failed"}
            
                print(f"HDR enabled: {low}us to {high}us!")

        # print("Did the HDR interval really change?")

        # exposure0 = ctypes.c_int32()
        # exposure1 = ctypes.c_int32()

        # ret = lib.scGetExposureTimeOfHDR(
        #     camState.camera,
        #     0,
        #     ctypes.byref(exposure0)
        # )

        # if ret != 0:
        #     print("scGetExposureTimeOfHDR frame 0 failed:", ret)
        # else:
        #     print(f"HDR frame 0 exposure: {exposure0.value} us")

        # ret = lib.scGetExposureTimeOfHDR(
        #     camState.camera,
        #     1,
        #     ctypes.byref(exposure1)
        # )

        # if ret != 0:
        #     print("scGetExposureTimeOfHDR frame 1 failed:", ret)
        # else:
        #     print(f"HDR frame 1 exposure: {exposure1.value} us")

        frameReady = ScFrameReady()

        ret = lib.scGetFrameReady(
            camState.camera,
            ctypes.c_uint16(33),
            ctypes.byref(frameReady)
        )

        if ret != 0:
            now = time.monotonic()

            if (frameState.lastFrameAt is not None
                    and now - frameState.lastFrameAt > 5
                    and now - camState.lastFrameWarnAt > 5):
                camState.lastFrameWarnAt = now
                print(f"[CameraStream] sem frames há {now - frameState.lastFrameAt:.1f}s")

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
                now = time.monotonic()
                frameState.colorToDepthFrame = colorToDepthFrame
                frameState.depthFrame = depthFrame
                frameState.colorFrame = colorFrame
                frameState.lastFrameAt = now

                depthArray[bufferIndex] = depthFrame
                timestampArray[bufferIndex] = now

                bufferIndex = (bufferIndex + 1) % 10

# BUILD HDR ANTIGO (PODE SER IMPORTANTE)
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

def buildHDRDepth(depthFrames):
    stacked_d = numpy.stack(depthFrames, axis=0).astype(numpy.float32)

    mask_d = (stacked_d > 150) & (stacked_d <= 5000)
    stacked_d[~mask_d] = numpy.nan

    sorted_d = numpy.sort(stacked_d, axis=0)

    valid_count = numpy.sum(~numpy.isnan(sorted_d), axis=0)

    trimmed_d = sorted_d.copy()

    trimmed_d[0] = numpy.where(
        valid_count > 4,
        numpy.nan,
        trimmed_d[0]
    )

    trimmed_d[-1] = numpy.where(
        valid_count > 4,
        numpy.nan,
        trimmed_d[-1]
    )

    median_d = numpy.nanmedian(trimmed_d, axis=0)

    deviation = numpy.abs(trimmed_d - median_d)

    valid_d = deviation <= 5

    filtered_d = numpy.where(valid_d, trimmed_d, numpy.nan)

    hdrDepth = numpy.rint(numpy.nanmean(filtered_d, axis=0))

    return numpy.nan_to_num(
        hdrDepth,
        nan=0
    ).astype(numpy.uint16)

def processHDR(click_timestamp):
    global depthArray, timestampArray
    finished = False
    finalHDRDepth = None

    if click_timestamp is None:
        click_timestamp = 0

    if any(frame is None for frame in depthArray) or any(ts <= click_timestamp for ts in timestampArray):
        finished = False
    else:
        finalHDRDepth = buildHDRDepth(depthArray)

        frameState.hdrDepth = finalHDRDepth

        print("HDR Processed (Done Building HDR)! Number of data analized", len(depthArray))

        finished = True

    return finished, finalHDRDepth

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