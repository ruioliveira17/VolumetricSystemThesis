import ctypes
import numpy
import threading
import time

from camera.factory import create_camera

from CameraState import camState
from FilterState import filterState
from FrameState import frameState
from ModeState import modeState
from ScepterSDK import *

hdrExposures = [
    (30, 500),      # 0-1: low
    (500, 1200),     # 2-3: medium
    (1200, 2000),    # 4-5: high
]

depthArray = [None] * 6
timestampArray = [0] * 6

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
    if camState.camera is not None and camState.cameraStatus == "online":
        print("Camera is already opened!")
        return{"message": "Nothing to Open"}
    elif camState.cameraStatus == "starting":
        print("Camera is starting!")
        return{"message": "Nothing to Open"}

    print("Opening Camera!")
    camState.cameraStatus = "starting"

    try:
        camera = create_camera()
        camera.start()

        camState.camera = camera

        setFPS(camState.fps)

        setFlyingPixelFilter(filterState.flyingPixelFilter) 
            
        setFillHoleFilter(filterState.fillHoleFilter)

        setSpatialFilter(filterState.spatialFilter)
            
        setConfidenceFilter(filterState.confidenceFilter)

        depth_intrinsics = camera.get_depth_intrinsic_parameters()
        rgb_intrinsics = camera.get_rgb_intrinsic_parameters()

        camState.fx_d = depth_intrinsics.fx
        camState.fy_d = depth_intrinsics.fy
        camState.cx_d = depth_intrinsics.cx
        camState.cy_d = depth_intrinsics.cy

        print("Cx Depth:", camState.cx_d)
        print("Cy Depth:", camState.cy_d)
        print("fx Depth:", camState.fx_d)
        print("fy Depth:", camState.fy_d)

        camState.fx_rgb = rgb_intrinsics.fx
        camState.fy_rgb = rgb_intrinsics.fy
        camState.cx_rgb = rgb_intrinsics.cx
        camState.cy_rgb = rgb_intrinsics.cy

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
        
    #     ret = lib.scInitialize()
    #     print("scInitialize:", ret)

    #     if ret != 0:
    #         raise RuntimeError("Failed to initialize Scepter SDK!")

    #     camera_count = ctypes.c_uint32(0)
    #     retry_count = 20

    #     while camera_count.value==0 and retry_count > 0:
    #         ret = lib.scGetDeviceCount(ctypes.byref(camera_count), 1000)

    #         print(
    #             "scGetDeviceCount:",
    #             ret,
    #             "| câmaras:",
    #             camera_count.value
    #         )

    #         if camera_count.value == 0:
    #             retry_count -= 1
    #             time.sleep(1)
    #             print("Scanning......   ", retry_count)

    #     if camera_count.value == 0:
    #         print("There are no cameras found")
    #         camState.cameraStatus = "error"
    #         lib.scShutdown()
    #         return {"message": "No camera detected"}

    #     device_info_list = (ScDeviceInfo * camera_count.value)()

    #     print("ANTES scGetDeviceInfoList")

    #     ret = lib.scGetDeviceInfoList(
    #         camera_count.value,
    #         device_info_list
    #     )

    #     print("DEPOIS scGetDeviceInfoList:", ret)

    #     if ret != 0:
    #         camState.cameraStatus = "error"
    #         lib.scShutdown()
    #         raise RuntimeError("Failed to get camera information!")

    #     device_info = device_info_list[0]

    #     print("Camera")
    #     print("--------------------")
    #     print("Product:", device_info.productName.decode(errors="ignore"))
    #     print("Serial:", device_info.serialNumber.decode(errors="ignore"))
    #     print("IP:", device_info.ip.decode(errors="ignore"))
    #     print("Status:", device_info.status)

    #     # Abrir câmara pelo número de série
    #     camera = ScDeviceHandle()

    #     serial = device_info.serialNumber

    #     print("Opening camera...")
    #     ret = lib.scOpenDeviceBySN(
    #         serial,
    #         ctypes.byref(camera)
    #     )

    #     print("scOpenDeviceBySN:", ret)

    #     if ret != 0:
    #         camState.cameraStatus = "error"
    #         lib.scShutdown()
    #         return {"message": "Failed"}

    #     print("Device handle:", camera)
    #     print("Camera opened successfully!")

    #     camState.camera = camera

    #     # Iniciar stream
    #     ret = lib.scStartStream(camState.camera)
    #     print("scStartStream:", ret)

    #     if ret != 0:
    #         lib.scCloseDevice(ctypes.byref(camState.camera))
    #         camState.camera = None
    #         camState.cameraStatus = "error"
    #         lib.scShutdown()
    #         raise RuntimeError("Failed to start camera stream!")

    #     params = ScTimeFilterParams()

    #     ret = lib.scGetTimeFilterParams(
    #         camState.camera,
    #         ctypes.byref(params)
    #     )

    #     if ret == 0:
    #         print("The default TimeFilter switch is " + str(params.enable))
    #     else:
    #         print("scGetTimeFilterParams failed:" + str(ret))

    #     params.enable = True

    #     ret = lib.scSetTimeFilterParams(
    #         camState.camera,
    #         params
    #     )

    #     if ret == 0:
    #         print(
    #             "Set TimeFilter switch to "
    #             + str(params.enable)
    #             + " is Ok"
    #         )
    #     else:
    #         print(
    #             "scSetTimeFilterParams failed:"
    #             + str(ret)
    #         )

    #     # Definir modo de exposição manual
    #     ret = lib.scSetExposureControlMode(
    #         camState.camera,
    #         0x01,  # SC_TOF_SENSOR
    #         1      # SC_EXPOSURE_CONTROL_MODE_MANUAL
    #     )

    #     if ret == 0:
    #         print("Set exposure control mode to manual is ok")
    #     else:
    #         print("scSetExposureControlMode failed:", ret)

    #     # Ativar transformação Color -> Depth
    #     ret = lib.scSetTransformColorImgToDepthSensorEnabled(
    #         camState.camera,
    #         True
    #     )

    #     if ret == 0:
    #         print("scSetTransformColorImgToDepthSensorEnabled ok")
    #     else:
    #         print(
    #             "scSetTransformColorImgToDepthSensorEnabled failed:",
    #             ret
    #         )

    #     setFPS()

    #     setFlyingPixelFilter(value = filterState.flyingPixelFilter) 
        
    #     setFillHoleFilter(value = filterState.fillHoleFilter)

    #     setSpatialFilter(value = filterState.spatialFilter)
            
    #     setConfidenceFilter(value = filterState.confidenceFilter)

    #     # Intrinsic Parameters Depth

    #     intrParam = ScSensorIntrinsicParameters()

    #     ret = lib.scGetSensorIntrinsicParameters(
    #         camState.camera,
    #         0x01,  # SC_TOF_SENSOR
    #         ctypes.byref(intrParam)
    #     )

    #     if ret != 0:
    #         raise RuntimeError("Error obtaining depth intrinsic parameters!")
            
    #     camState.fx_d = intrParam.fx
    #     camState.fy_d = intrParam.fy
    #     camState.cx_d = intrParam.cx
    #     camState.cy_d = intrParam.cy

    #     print("Cx Depth:", camState.cx_d)
    #     print("Cy Depth:", camState.cy_d)
    #     print("fx Depth:", camState.fx_d)
    #     print("fy Depth:", camState.fy_d)

    #     # Intrinsic Parameters RGB

    #     intrParam = ScSensorIntrinsicParameters()

    #     ret = lib.scGetSensorIntrinsicParameters(
    #         camState.camera,
    #         0x02,  # SC_COLOR_SENSOR
    #         ctypes.byref(intrParam)
    #     )

    #     if ret != 0:
    #         raise RuntimeError("Error obtaining color intrinsic parameters!")

    #     camState.fx_rgb = intrParam.fx
    #     camState.fy_rgb = intrParam.fy
    #     camState.cx_rgb = intrParam.cx
    #     camState.cy_rgb = intrParam.cy

    #     print("Cx RGB:", camState.cx_rgb)
    #     print("Cy RGB:", camState.cy_rgb)
    #     print("fx RGB:", camState.fx_rgb)
    #     print("fy RGB:", camState.fy_rgb)

    #     print("Camera ready")

    #     camState._running = True
    #     camState._thread = threading.Thread(target=captureLoop, daemon=True)
    #     camState._thread.start()

    #     camState.cameraStatus = "online"

    # except Exception as e:
    #     camState.cameraStatus = "error"
    #     print("Camera startup error:", e)

def stopCamera():
    camState._running = False
    if camState._thread:
        camState._thread.join(timeout=3)

    if camState.camera is None:
        return{"message": "Nothing to Close"}
    else:
        camState.cameraStatus = "shutting_down"

        try:
            success = camState.camera.stop()

            if success:
                camState.camera = None
                camState.cameraStatus = "offline"
                print("[CameraStream] Câmara fechada.")
                return {"message": "Success"}

            camState.cameraStatus = "error"
            return {"message": "Failed"}

        except Exception as e:
            camState.cameraStatus = "error"
            print("Camera shutdown error:", e)
            return {"message": "Failed"}
    
def setFPS(fps):
    try:
        camState.fps = camState.camera.set_fps(fps)
        return {"message": "Success"}

    except Exception as e:
        print("Failed to set frame rate:", e)
        return {"message": "Failed"}

def captureLoop():
    global depthArray, timestampArray, hdrExposures

    print("[CameraStream] Iniciando captura de frames...")
    bufferIndex = 0

    while camState._running:
        if camState.hdrEnabled and modeState.currentMenu == "volume-menu":
            if bufferIndex in (0, 2, 4):
                if bufferIndex == 0:
                    low, high = hdrExposures[0]
                elif bufferIndex == 2:
                    low, high = hdrExposures[1]
                elif bufferIndex == 4:
                    low, high = hdrExposures[2]

                setHDRInterval(low, high)

        frames = camState.camera.get_frames()

        if frames is None:
            now = time.monotonic()

            if (
                frameState.lastFrameAt is not None
                and now - frameState.lastFrameAt > 5
                and now - camState.lastFrameWarnAt > 5
            ):
                camState.lastFrameWarnAt = now

                print(
                    f"[CameraStream] sem frames há "
                    f"{now - frameState.lastFrameAt:.1f}s"
                )

            continue

        now = time.monotonic()

        frameState.colorToDepthFrame = frames["colorToDepth"]
        frameState.depthFrame = frames["depth"]
        frameState.colorFrame = frames["color"]

        frameState.lastFrameAt = now

        depthArray[bufferIndex] = frames["depth"]
        timestampArray[bufferIndex] = now

        bufferIndex = (bufferIndex + 1) % 6

        # frameReady = ScFrameReady()

        # ret = lib.scGetFrameReady(
        #     camState.camera,
        #     ctypes.c_uint16(33),
        #     ctypes.byref(frameReady)
        # )

        # if ret != 0:
        #     now = time.monotonic()

        #     if (frameState.lastFrameAt is not None
        #             and now - frameState.lastFrameAt > 5
        #             and now - camState.lastFrameWarnAt > 5):
        #         camState.lastFrameWarnAt = now
        #         print(f"[CameraStream] sem frames há {now - frameState.lastFrameAt:.1f}s")

        #     continue

        # else:
        #     hasColorToDepth =0
        #     hasDepth = 0
        #     hasColor = 0

        #     colorToDepthFrame = None
        #     depthFrame = None
        #     colorFrame = None

        #     if frameReady.transformedColor:     
        #         rgbFrame = ScFrame()

        #         ret = lib.scGetFrame(
        #             camState.camera,
        #             4,  # SC_TRANSFORM_COLOR_IMG_TO_DEPTH_SENSOR_FRAME
        #             ctypes.byref(rgbFrame)
        #         )

        #         if ret == 0:
        #             hasColorToDepth = 1  
        #         else:
        #             print("get color to depth frame failed:",ret)

        #     if frameReady.depth:
        #         depthFrameRaw = ScFrame()

        #         ret = lib.scGetFrame(
        #             camState.camera,
        #             0,  # SC_DEPTH_FRAME
        #             ctypes.byref(depthFrameRaw)
        #         )

        #         if ret == 0:
        #             hasDepth = 1
        #         else:
        #             print("get depth frame failed:",ret)

        #     if frameReady.color:
        #         colorFrameRaw = ScFrame()

        #         ret = lib.scGetFrame(
        #             camState.camera,
        #             3,  # SC_COLOR_FRAME
        #             ctypes.byref(colorFrameRaw)
        #         )

        #         if ret == 0:
        #             hasColor = 1
        #         else:
        #             print("get Color frame failed:", ret)

        #     if hasColorToDepth == 1:
        #         frametmp = numpy.ctypeslib.as_array(
        #             rgbFrame.pFrameData,
        #             (rgbFrame.width * rgbFrame.height * 3,)
        #         )

        #         frametmp.dtype = numpy.uint8
        #         frametmp.shape = (
        #             rgbFrame.height,
        #             rgbFrame.width,
        #             3
        #         )

        #         colorToDepthFrame = frametmp.copy()

        #     if hasDepth == 1:
        #         frametmp = numpy.ctypeslib.as_array(
        #             depthFrameRaw.pFrameData,
        #             (depthFrameRaw.width * depthFrameRaw.height * 2,)
        #         )

        #         frametmp.dtype = numpy.uint16
        #         frametmp.shape = (
        #             depthFrameRaw.height,
        #             depthFrameRaw.width
        #         )

        #         depthFrame = frametmp.copy()

        #     if hasColor == 1:
        #         frametmp = numpy.ctypeslib.as_array(
        #             colorFrameRaw.pFrameData,
        #             (colorFrameRaw.width * colorFrameRaw.height * 3,)
        #         )

        #         frametmp.dtype = numpy.uint8
        #         frametmp.shape = (
        #             colorFrameRaw.height,
        #             colorFrameRaw.width,
        #             3
        #         )

        #         colorFrame = frametmp.copy()

        #     if hasColorToDepth == 1 and hasDepth == 1 and hasColor == 1:
        #         now = time.monotonic()
        #         frameState.colorToDepthFrame = colorToDepthFrame
        #         frameState.depthFrame = depthFrame
        #         frameState.colorFrame = colorFrame
        #         frameState.lastFrameAt = now

        #         depthArray[bufferIndex] = depthFrame
        #         timestampArray[bufferIndex] = now

        #         bufferIndex = (bufferIndex + 1) % 10

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
        valid_count > 3,
        numpy.nan,
        trimmed_d[0]
    )

    trimmed_d[-1] = numpy.where(
        valid_count > 3,
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

        frameState.depthArrayHDR = depthArray
        frameState.hdrDepth = finalHDRDepth

        print("HDR Processed (Done Building HDR)! Number of data analized", len(depthArray))

        finished = True

    return finished, finalHDRDepth

def setExposureTime(value: int):
    try:
        camState.camera.set_exposure_time(value)
        return True

    except Exception as e:
        print("Failed to set exposure time:", e)
        return False

def setEnableHDR(value: bool):
    try:
        camState.camera.set_enable_hdr(value)
        return True

    except Exception as e:
        print("Failed to set HDR mode:", e)
        return False

def setHDRInterval(low: int, high: int):
    try:
        camState.camera.set_hdr_interval(low, high)
        return True

    except Exception as e:
        print("Failed to set HDR interval:", e)
        return False

def setFlyingPixelFilter(value: bool):
    try:
        filterState.flyingPixelFilter = (
            camState.camera.set_filter_flying_pixel(value)
        )

        return True

    except Exception as e:
        print("Failed to set FlyingPixelFilter:", e)
        return False

def setFillHoleFilter(value: bool):
    try:
        filterState.fillHoleFilter = (
            camState.camera.set_filter_fill_hole(value)
        )

        return True

    except Exception as e:
        print("Failed to set FillHoleFilter:", e)
        return False

def setSpatialFilter(value: bool):
    try:
        filterState.spatialFilter = (
            camState.camera.set_filter_spatial(value)
        )

        return True

    except Exception as e:
        print("Failed to set SpatialFilter:", e)
        return False

def setConfidenceFilter(value: bool):
    try:
        filterState.confidenceFilter = (
            camState.camera.set_filter_confidence(value)
        )

        return True

    except Exception as e:
        print("Failed to set ConfidenceFilter:", e)
        return False