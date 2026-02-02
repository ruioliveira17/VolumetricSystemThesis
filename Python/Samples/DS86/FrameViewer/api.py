from fastapi import FastAPI, Path, Query, HTTPException, status, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel
from API.VzenseDS_api import *
from Bundle2 import bundle, depthImg
from CalibrationDefTkinter import calibrateAPI, maskAPI
from CameraOptions import statusCamera
from GetFrame import getFrame
from MinDepth2 import MinDepthAPI
from VolumeTkinter import volumeAPI
from CameraState import camState
from color_presets import COLOR_PRESETS
from DepthState import depthState
from FrameState import frameState
from MaskState import maskState
from ModeState import modeState
from VolumeState import volumeState
from WorkspaceState import workspaceState

from contextlib import asynccontextmanager
import json
import os

def save_WS_calibration():
    data = {
        "detection_area": workspaceState.detection_area,
        "workspace_depth": workspaceState.workspace_depth,
        "hmin": maskState.hmin,
        "hmax": maskState.hmax,
        "smin": maskState.smin,
        "smax": maskState.smax,
        "vmin": maskState.vmin,
        "vmax": maskState.vmax,
        "color": maskState.color
    }

    os.makedirs("config", exist_ok=True)

    with open("config/workspace_calibration.json", "w") as f:
        json.dump(data, f, indent=4)

#-----------------------------------------------------   Lifespan   -------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    path = "config/workspace_calibration.json"

    if os.path.exists(path):
        with open(path, "r") as f:
            calib = json.load(f)

        workspaceState.detection_area = calib["detection_area"]
        workspaceState.workspace_depth = calib["workspace_depth"]
        maskState.hmin = calib["hmin"]
        maskState.hmax = calib["hmax"]
        maskState.smin = calib["smin"]
        maskState.smax = calib["smax"]
        maskState.vmin = calib["vmin"]
        maskState.vmax = calib["vmax"]
        maskState.color = calib["color"]

        print("Calibração carregada!")

    else:
        print("É necessário realizar calibração!")

    yield

    #SHUTDOWN
    print("API a desligar")

#----------------------------------------------------   Criar App   -------------------------------------------------------

app = FastAPI(lifespan=lifespan)

#----------------------------------------------------   Base Models    ----------------------------------------------------

class HSVValue(BaseModel):
    hmin: Optional[int] = None
    hmax: Optional[int] = None
    smin: Optional[int] = None
    smax: Optional[int] = None
    vmin: Optional[int] = None
    vmax: Optional[int] = None
    color: Optional[str] = None

class CamValues(BaseModel):
    colorSlope: Optional[int] = 1500
    exposureTime: Optional[int] = 700

#-------------------------------------------------------   Camera   -------------------------------------------------------

@app.get("/camera/status")
def status():
    return statusCamera()

@app.get("/camera/exposureTime")
def get_exposure_Time():
    return {"Exposure Time": camState.exposureTime,}

@app.get("/camera/colorSlope")
def get_color_Slope():
    return {
            "colorSlope": camState.colorSlope.value,
        }

@app.post("/camera/setExposureTime")
def set_exposureTime(data: CamValues):
    camState.exposureTime = data.exposureTime
    return{
        "Exposure Time": camState.exposureTime
    }

@app.post("/camera/setColorSlope")
def set_color_slope(data: CamValues):
    camState.colorSlope.value = data.colorSlope
    return{
        "colorSlope": camState.colorSlope.value
    }

#-------------------------------------------------------   Frame   -------------------------------------------------------

@app.post("/captureFrame")
def capture_frame():
    getFrame(camState.camera)
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

@app.post("/mask/color")
def set_maskColor(data: HSVValue):
    maskState.color = data.color
    return{"color": maskState.color}

@app.get("/mask")
def get_mask():
    if maskState.color != "Manual":
        preset = COLOR_PRESETS[maskState.color]
        lower = numpy.array(preset["lower"])
        upper = numpy.array(preset["upper"])

        maskState.hmin, maskState.smin, maskState.vmin = map(int, lower)
        maskState.hmax, maskState.smax, maskState.vmax = map(int, upper)

    return {
        "hmin": maskState.hmin,
        "hmax": maskState.hmax,
        "smin": maskState.smin,
        "smax": maskState.smax,
        "vmin": maskState.vmin,
        "vmax": maskState.vmax,
        "color": maskState.color
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

    res, colorToDepthFrame_copy, depthFrame_copy = maskAPI(colorFrame, colorToDepthFrame, depthFrame, lower, upper, maskState.color, camState.colorSlope, int(camState.cx), int(camState.cy))

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

    save_WS_calibration()

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

#------------------------------------------------------- Volume -------------------------------------------------------

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
        if volumeState.box_limits is not None and len(volumeState.box_limits) > 0:
            volumeState.volume, volumeState.width_meters, volumeState.height_meters = volumeAPI(workspaceState.workspace_depth, depthState.minimum_depth, volumeState.box_limits, volumeState.depths, camState.fx, camState.fy, camState.cx, camState.cy)

    return{
        "volume": volumeState.volume,
        "width": volumeState.width_meters * 100,
        "height": volumeState.height_meters * 100,
        "min_depth": depthState.minimum_depth / 10,
        "ws_depth": workspaceState.workspace_depth / 10
    }