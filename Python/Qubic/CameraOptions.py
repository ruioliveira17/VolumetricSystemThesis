import ctypes
import logging
import numpy
import threading
import time

from camera.factory import create_camera

from CameraState import camState
from FilterState import filterState
from FrameState import frameState
from ModeState import modeState
from ScepterSDK import *

logger = logging.getLogger("qubic.camera")

depthArray = [None] * 6
timestampArray = [0] * 6

bufferIndex = 0

def statusCamera():
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
        logger.info("Camera is already opened")
        return{"message": "Nothing to Open"}
    elif camState.cameraStatus == "starting":
        logger.info("Starting camera")
        return{"message": "Nothing to Open"}

    logging.info("Starting camera")
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

        if modeState.expositionMode == "HDR":
            setEnableHDR(True)

        depth_intrinsics = camera.get_depth_intrinsic_parameters()
        rgb_intrinsics = camera.get_rgb_intrinsic_parameters()

        camState.fx_d = depth_intrinsics.fx
        camState.fy_d = depth_intrinsics.fy
        camState.cx_d = depth_intrinsics.cx
        camState.cy_d = depth_intrinsics.cy

        logger.debug(
            "Depth intrinsics: fx=%s, fy=%s, cx=%s, cy=%s",
            camState.fx_d,
            camState.fy_d,
            camState.cx_d,
            camState.cy_d
        )

        camState.fx_rgb = rgb_intrinsics.fx
        camState.fy_rgb = rgb_intrinsics.fy
        camState.cx_rgb = rgb_intrinsics.cx
        camState.cy_rgb = rgb_intrinsics.cy

        logger.debug(
            "RGB intrinsics: fx=%s, fy=%s, cx=%s, cy=%s",
            camState.fx_rgb,
            camState.fy_rgb,
            camState.cx_rgb,
            camState.cy_rgb
        )

        camState._running = True
        camState._thread = threading.Thread(target=captureLoop, daemon=True)
        camState._thread.start()

        camState.cameraStatus = "online"
        logger.info("Camera started successfully")

    except Exception:
        camState.cameraStatus = "error"
        logger.exception("Camera startup error")

def stopCamera():
    camState._running = False
    if camState._thread:
        camState._thread.join(timeout=3)

    if camState.camera is None:
        logger.info("No camera instance to stop")
        return{"message": "Nothing to Close"}
    else:
        logger.info("Stopping camera")
        camState.cameraStatus = "shutting_down"

        try:
            success = camState.camera.stop()

            if success:
                camState.camera = None
                camState.cameraStatus = "offline"
                logger.info("Camera stopped its service")
                print("[CameraStream] Camera Closed.")
                return {"message": "Success"}

            camState.cameraStatus = "error"
            logger.error("Could not stop camera")
            return {"message": "Failed"}

        except Exception as e:
            camState.cameraStatus = "error"
            print("Camera shutdown error:", e)
            logger.exception("Could not stop camera")
            return {"message": "Failed"}
    
def setFPS(fps):
    try:
        camState.fps, camState.maxExposureTime, camState.hdrMaxExposureTime = camState.camera.set_fps(fps)
        return {"message": "Success"}

    except Exception:
        logger.exception("Failed to set frame rate")
        return {"message": "Failed"}
    
def setExposureTime(value: int):
    if value < camState.maxExposureTime:
        try:
            camState.camera.set_exposure_time(value)
            return True

        except Exception:
            logger.exception("Failed to set exposure time")
            return False

def setEnableHDR(value: bool):
    try:
        camState.camera.set_enable_hdr(value)
        return True

    except Exception:
        logger.exception("Failed to set HDR mode")
        return False

def setHDRInterval(low: int, high: int):
    try:
        camState.camera.set_hdr_interval(low, high)
        return True

    except Exception:
        logger.exception("Failed to set HDR interval")
        return False

def setFlyingPixelFilter(value: bool):
    try:
        filterState.flyingPixelFilter = (
            camState.camera.set_filter_flying_pixel(value)
        )

        return True

    except Exception:
        logger.exception("Failed to set Flying Pixel filter")
        
        return False

def setFillHoleFilter(value: bool):
    try:
        filterState.fillHoleFilter = (
            camState.camera.set_filter_fill_hole(value)
        )

        return True

    except Exception:
        logger.exception("Failed to set Fill Hole filter")
        return False

def setSpatialFilter(value: bool):
    try:
        filterState.spatialFilter = (
            camState.camera.set_filter_spatial(value)
        )

        return True

    except Exception:
        logger.exception("Failed to set Spatial filter")
        return False

def setConfidenceFilter(value: bool):
    try:
        filterState.confidenceFilter = (
            camState.camera.set_filter_confidence(value)
        )

        return True

    except Exception:
        logger.exception("Failed to set Confidence filter")
        return False

def captureLoop():
    global depthArray, timestampArray, bufferIndex

    logger.info("Camera capture loop started")

    try:
        while camState._running:
            frames = camState.camera.get_frames(camState.fps)

            if frames is None:
                now = time.monotonic()

                if (
                    frameState.lastFrameAt is not None
                    and now - frameState.lastFrameAt > 5
                    and now - camState.lastFrameWarnAt > 5
                ):
                    camState.lastFrameWarnAt = now

                    logger.warning(
                        "No frames received for %.1f seconds",
                        now - frameState.lastFrameAt
                    )

                continue

            logger.debug(
                "Frame received: depth=%s color=%s colorToDepth=%s",
                frames["depth"] is not None,
                frames["color"] is not None,
                frames["colorToDepth"] is not None,
            )

            now = time.monotonic()

            frameState.colorToDepthFrame = frames["colorToDepth"]
            frameState.depthFrame = frames["depth"]
            frameState.colorFrame = frames["color"]

            frameState.lastFrameAt = now

            depthArray[bufferIndex] = frames["depth"]
            timestampArray[bufferIndex] = now

            bufferIndex = (bufferIndex + 1) % 6

    except Exception:
        logger.exception("Camera capture loop error")

    finally:
        logger.info("Camera capture loop stopped")

def buildHDRDepth(depthFrames):
    stacked_d = numpy.stack(depthFrames, axis=0).astype(numpy.float32)

    mask_d = (stacked_d > 150) & (stacked_d <= 5000)
    stacked_d[~mask_d] = numpy.nan

    # sorted_d = numpy.sort(stacked_d, axis=0)

    # valid_count = numpy.sum(~numpy.isnan(sorted_d), axis=0)

    # trimmed_d = sorted_d.copy()

    # trimmed_d[0] = numpy.where(
    #     valid_count > 3,
    #     numpy.nan,
    #     trimmed_d[0]
    # )

    # trimmed_d[-1] = numpy.where(
    #     valid_count > 3,
    #     numpy.nan,
    #     trimmed_d[-1]
    # )

    # median_d = numpy.nanmedian(trimmed_d, axis=0)
    median_d = numpy.nanmedian(stacked_d, axis=0)

    # deviation = numpy.abs(trimmed_d - median_d)
    deviation = numpy.abs(stacked_d - median_d)

    valid_d = deviation <= 5

    # filtered_d = numpy.where(valid_d, trimmed_d, numpy.nan)
    filtered_d = numpy.where(valid_d, stacked_d, numpy.nan)

    hdrDepth = numpy.rint(numpy.nanmean(filtered_d, axis=0))

    return numpy.nan_to_num(
        hdrDepth,
        nan=0
    ).astype(numpy.uint16)

def processHDR(click_timestamp):
    global depthArray, timestampArray, bufferIndex
    finished = False
    finalHDRDepth = None

    if click_timestamp is None:
        click_timestamp = 0

    if any(frame is None for frame in depthArray) or any(ts <= click_timestamp for ts in timestampArray):
        if camState.hdrEnabled and modeState.currentMenu == "volume-menu":
            if bufferIndex in (0, 2, 4):
                maxExposureTimeLow = camState.hdrMaxExposureTime[0]
                maxExposureTimeHigh = camState.hdrMaxExposureTime[1]
                minExposureTime = 30

                ratioLow = (maxExposureTimeLow / minExposureTime) ** (1 / 3)
                ratioHigh = (maxExposureTimeHigh / minExposureTime) ** (1 / 3)
                k = bufferIndex // 2  # 0, 1, 2

                low = round(minExposureTime * ratioLow ** k)
                high = round(minExposureTime * ratioHigh ** (k + 1))

                setHDRInterval(low, high)

        finished = False
    else:
        finalHDRDepth = buildHDRDepth(depthArray)

        frameState.depthArrayHDR = depthArray
        frameState.hdrDepth = finalHDRDepth

        logger.info(
            "HDR processing completed successfully. Frames analyzed: %d",
            len(depthArray)
        )

        finished = True

        setHDRInterval(100, camState.hdrMaxExposureTime[1] - 200)

    return finished, finalHDRDepth
