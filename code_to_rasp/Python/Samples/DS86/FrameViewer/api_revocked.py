from fastapi import FastAPI, Path, Query, HTTPException, status, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel
from API.VzenseDS_api import *
from Bundle2 import bundle, depthImg
from CalibrationDefTkinter import calibrateAPI, maskAPI
from CameraOptions import openCamera, closeCamera, statusCamera
from GetFrame import getFrame
from MinDepth2 import MinDepthAPI
from VolumeTkinter import volumeAPI
from CameraState import camState
from DepthState import depthState
from FrameState import frameState
from MaskState import maskState
from ModeState import modeState
from VolumeState import volumeState
from WorkspaceState import workspaceState
import numpy
import sys

app = FastAPI()

#-------------------------------------------------------   Tese    -------------------------------------------------------

#Start API
#python -m uvicorn api:app --reload

class HSVValue(BaseModel):
    hmin: Optional[int] = None
    hmax: Optional[int] = None
    smin: Optional[int] = None
    smax: Optional[int] = None
    vmin: Optional[int] = None
    vmax: Optional[int] = None

#-------------------------------------------------------  Camera   -------------------------------------------------------

@app.post("/openCamera")
def open():
    return openCamera()

@app.post("/closeCamera")
def close():
    return closeCamera()

@app.get("/camera/status")
def status():
    return statusCamera()

@app.get("/camera/exposureTime")
def get_exposure_Time():
    return {"colorSlope": camState.exposureTime,}

@app.get("/camera/colorSlope")
def get_color_Slope():
    return {
            "colorSlope": camState.colorSlope.value,
        }
#-------------------------------------------------------   Frame   -------------------------------------------------------

@app.post("/captureFrame")
def capture_frame():
    getFrame(camState.camera)
    #colorToDepthFrame, depthFrame, colorFrame = getFrame(camState.camera)
    #frameState.colorToDepthFrame = colorToDepthFrame
    #frameState.depthFrame = depthFrame
    #frameState.colorFrame = colorFrame
    return {"message:": "Frame successfully achieved"}

@app.get("/getFrame/color")
def get_Color_Frame():
    return Response(content=frameState.colorFrame.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/colorToDepth")
def get_ColorToDepth_Frame():
    return Response(content=frameState.colorToDepthFrame.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/depth")
def get_Depth_Frame():
    return Response(content=frameState.depthFrame.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/colorToDepthCopy")
def get_ColorToDepth_Frame_Copy():
    return Response(content=frameState.colorToDepthFrameCopy.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/depthCopy")
def get_Depth_Frame_Copy():
    return Response(content=frameState.depthFrameCopy.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/res")
def get_Res():
    return Response(content=frameState.res.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/colorToDepthObject")
def get_ColorToDepth_Frame_Object():
    return Response(content=frameState.colorToDepthFrameObject.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/colorToDepthObjects")
def get_ColorToDepth_Frame_Objects():
    return Response(content=frameState.colorToDepthFrameObjects.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/HDRcolor")
def get_Color_HDRFrame():
    if frameState.colorFrameHDR is None:
        return Response(status_code=204)
    return Response(content=frameState.colorFrameHDR.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/HDRcolorToDepth")
def get_ColorToDepth_HDRFrame():
    if frameState.colorToDepthFrameHDR is None:
        return Response(status_code=204)
    return Response(content=frameState.colorToDepthFrameHDR.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/HDRdepth")
def get_Depth_HDRFrame():
    if frameState.depthFrameHDR is None:
        return Response(status_code=204)
    return Response(content=frameState.depthFrameHDR.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame")
def get_frame():
    frames = []

    frames.append(frameState.colorFrame.tobytes())
    frames.append(frameState.colorToDepthFrame.tobytes())
    frames.append(frameState.depthFrame.tobytes())

    separator = b"__FRAME__"
    payload = separator.join(frames)

    return Response(content=payload, media_type="application/octet-stream")

#-------------------------------------------------------   Mask    -------------------------------------------------------

@app.post("/mask/hmin")
def set_h_min(data: HSVValue):
    if data.hmin > maskState.hmax:
        maskState.hmin = maskState.hmax
    else:
        maskState.hmin = data.hmin
    return{"hmin": maskState.hmin}

@app.post("/mask/smin")
def set_s_min(data: HSVValue):
    if data.smin > maskState.smax:
        maskState.smin = maskState.smax
    else:
        maskState.smin = data.smin
    return{"smin": maskState.smin}

@app.post("/mask/vmin")
def set_v_min(data: HSVValue):
    if data.vmin > maskState.vmax:
        maskState.vmin = maskState.vmax
    else:
        maskState.vmin = data.vmin
    return{"vmin": maskState.vmin}

@app.post("/mask/hmax")
def set_h_max(data: HSVValue):
    if data.hmax < maskState.hmin:
        maskState.hmax = maskState.hmin
    else:
        maskState.hmax = data.hmax
    return{"hmax": maskState.hmax}

@app.post("/mask/smax")
def set_s_max(data: HSVValue):
    if data.smax < maskState.smin:
        maskState.smax = maskState.smin
    else:
        maskState.smax = data.smax
    return{"smax": maskState.smax}

@app.post("/mask/vmax")
def set_v_max(data: HSVValue):
    if data.vmax < maskState.vmin:
        maskState.vmax = maskState.vmin
    else:
        maskState.vmax = data.vmax
    return{"vmax": maskState.vmax}

@app.get("/mask")
def get_mask():
    return {
        "hmin": maskState.hmin,
        "hmax": maskState.hmax,
        "smin": maskState.smin,
        "smax": maskState.smax,
        "vmin": maskState.vmin,
        "vmax": maskState.vmax,
    }

@app.post("/applyMask")
def apply_mask(data: HSVValue):
    lower = (data.hmin, data.smin, data.vmin)
    upper = (data.hmax, data.smax, data.vmax)

    if frameState.colorFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        colorFrame = frameState.colorFrame
    else:
        colorFrame = frameState.colorFrameHDR

    if frameState.colorToDepthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        colorToDepthFrame = frameState.colorToDepthFrame
    else:
        colorToDepthFrame = frameState.colorToDepthFrameHDR

    if frameState.depthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        depthFrame = frameState.depthFrame
    else:
        depthFrame = frameState.depthFrameHDR

    res, colorToDepthFrame_copy, depthFrame_copy = maskAPI(colorFrame, colorToDepthFrame, depthFrame, lower, upper, camState.colorSlope, int(camState.cx), int(camState.cy))

    if res is None or colorToDepthFrame_copy is None or depthFrame_copy is None:
        return{"message:": "Mask application failed!"}

    frameState.res = res
    frameState.colorToDepthFrameCopy = colorToDepthFrame_copy
    frameState.depthFrameCopy = depthFrame_copy
    
    return{"message:": "Mask applied with success"}

#------------------------------------------------------- Calibrate -------------------------------------------------------

@app.post("/calibrate")
def calibrate(data: HSVValue):
    lower = (data.hmin, data.smin, data.vmin)
    upper = (data.hmax, data.smax, data.vmax)

    if frameState.colorFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        colorFrame = frameState.colorFrame
    else:
        colorFrame = frameState.colorFrameHDR

    if frameState.colorToDepthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        colorToDepthFrame = frameState.colorToDepthFrame
    else:
        colorToDepthFrame = frameState.colorToDepthFrameHDR

    if frameState.depthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        depthFrame = frameState.depthFrame
    else:
        depthFrame = frameState.depthFrameHDR

    detection_area, workspace_depth, center_aligned, workspace_clear = calibrateAPI(colorFrame, colorToDepthFrame, depthFrame, lower, upper, camState.colorSlope, int(camState.cx), int(camState.cy))

    if detection_area is None or workspace_depth is None:
        workspaceState.center_aligned = center_aligned
        workspaceState.workspace_clear = workspace_clear
        return{"message:": "Calibration failed!"}

    workspaceState.detection_area = detection_area
    workspaceState.workspace_depth = workspace_depth
    workspaceState.center_aligned = center_aligned
    workspaceState.workspace_clear = workspace_clear

    return {"message:": "Calibration sucessfully done"}

@app.get("/calibrate/params")
def get_calibration_parameters():
    return {
        "Detection Area": workspaceState.detection_area,
        "Workspace Depth": workspaceState.workspace_depth,
    }

@app.get("/calibrate/flags")
def get_calibration_flags():
    return {
        "Center Aligned": workspaceState.center_aligned,
        "Workspace Clear": workspaceState.workspace_clear,
    }

#---------------------------------------------------- Working Mode -----------------------------------------------------

@app.get("/mode")
def get_mode():
    return{
        "Mode": modeState.mode,
    }

@app.post("/mode/static")
def static():
    modeState.mode = "Static"
    return {"mode:": modeState.mode}

@app.post("/mode/dynamic")
def dynamic():
    modeState.mode = "Dynamic"
    return {"mode:": modeState.mode}

#--------------------------------------------------- Exposition Mode --------------------------------------------------

@app.get("/expositionMode")
def get_mode():
    return{
        "Exposition Mode": modeState.expositionMode,
    }

@app.post("/expositionMode/fixed")
def fixedExp():
    modeState.expositionMode = "Fixed Exposition"
    return {"Exposition Mode:": modeState.expositionMode}

@app.post("/expositionMode/hdr")
def hdrExp():
    modeState.expositionMode = "HDR"
    return {"Exposition Mode:": modeState.expositionMode}

#------------------------------------------------------- Depth --------------------------------------------------------

@app.post("/depth")
def objects_depth():
    not_set, objects_info = MinDepthAPI(frameState.depthFrame, camState.colorSlope.value, depthState.threshold, workspaceState.detection_area, workspaceState.workspace_depth, depthState.not_set)
    
    if not_set  is None or objects_info is None:
        return{"message:": "Could not obtain objects depth successfully!"}
    
    depthState.not_set = not_set
    depthState.objects_info = objects_info

    return{"message:": "Objects depth obtained successfully!"}

@app.get("/depth/objectsInfo")
def get_objects_info():
    if depthState.objects_info is None:
        return{"message": "No info available"}
    
    return JSONResponse(content=jsonable_encoder(depthState.objects_info))

@app.get("/depth/notSet")
def get_min_Object_Set_Flag():
    if depthState.not_set is None:
        return{"message": "No info available"}
    
    return {
            "not_set": depthState.not_set,
        }

@app.post("/depth/min")
def min_value():
    if depthState.objects_info is not None and len(depthState.objects_info) != 0:
        depthState.minimum_depth = depthState.objects_info[0]["depth"]
        depthState.minimum_value = depthState.minimum_depth

        print("New Min Value", depthState.minimum_value)
    
    return{"message:": "Minimum Value changed successfully!"}

#------------------------------------------------------- Volume -------------------------------------------------------

@app.post("/volume")
def volume():
    depth_img = depthImg(frameState.depthFrame, camState.colorSlope)
    if depthState.not_set == 0:
        volumeState.width, volumeState.height, depthState.minimum_value, depthState.not_set, volumeState.box_limits, volumeState.box_ws = bundle(frameState.colorFrame, depth_img, depthState.objects_info, depthState.threshold, frameState.depthFrame)
    volumeState.volume, volumeState.width_meters, volumeState.height_meters, depthState.minimum_depth = volumeAPI(volumeState.box_ws, volumeState.width, volumeState.height, workspaceState.workspace_depth, depthState.minimum_depth)

    return{"message:": "Volume was successfully achieved!"}

@app.post("/volumeObj")
def volume_Obj():

    if frameState.colorFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        colorFrame = frameState.colorFrame
    else:
        colorFrame = frameState.colorFrameHDR

    if frameState.colorToDepthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        colorToDepthFrame = frameState.colorToDepthFrame
    else:
        colorToDepthFrame = frameState.colorToDepthFrameHDR

    if frameState.depthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        depthFrame = frameState.depthFrame
    else:
        depthFrame = frameState.depthFrameHDR

    depthState.not_set, depthState.objects_info = MinDepthAPI(depthFrame, camState.colorSlope.value, depthState.threshold, workspaceState.detection_area, workspaceState.workspace_depth, depthState.not_set, camState.cx, camState.cy, camState.fx, camState.fy)

    if depthState.objects_info is not None and len(depthState.objects_info) != 0:
        depthState.minimum_depth = depthState.objects_info[0]["depth"]
        depthState.minimum_value = depthState.minimum_depth

        print("New Min Value", depthState.minimum_value)

    depth_img = depthImg(depthFrame, camState.colorSlope)
    if depthState.not_set == 0:
        depthState.minimum_value, depthState.not_set, volumeState.box_limits, volumeState.box_ws, volumeState.depths = bundle(colorToDepthFrame, depth_img, depthState.objects_info, depthState.threshold, depthFrame)
        volumeState.volume, volumeState.width_meters, volumeState.height_meters = volumeAPI(workspaceState.workspace_depth, depthState.minimum_depth, volumeState.box_limits, volumeState.depths, camState.fx, camState.fy)

    #return{"message:": "Volume was successfully achieved!"}
    return{
        "volume": volumeState.volume,
        "width": volumeState.width_meters * 100,
        "height": volumeState.height_meters * 100,
        "min_depth": depthState.minimum_depth / 10,
        "ws_depth": workspaceState.workspace_depth / 10
    }