from fastapi import FastAPI, Path, Query, HTTPException, status, Response
from typing import Optional
from pydantic import BaseModel
from CameraOptions import openCamera, closeCamera, statusCamera
from GetFrame import getFrame
from CalibrationDefTkinter import calibrateAPI, maskAPI
from CameraState import camState
from FrameState import frameState
from MaskState import maskState
from ModeState import modeState
from WorkspaceState import workspaceState
#import base64
import numpy
import sys

app = FastAPI()

#---------------------------------------------------- Tutorial ---------------------------------------------------- 

class Item(BaseModel):
    name: str
    price: float
    brand: Optional[str] = None

class UpdateItem(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    brand: Optional[str] = None

inventory = {}

#inventory = {
#    1: {
#        "name": "Milk",
#        "price": 3.99,
#        "brand": "Regular"
#    }
#}

#Obter

@app.get("/")
def home():
    return {"Data": "Testing"}

@app.get("/about")
def about():
    return {"Data": "About"}

@app.get("/item/{item_id}")
def item(item_id: int = Path(..., description="The ID of the item you'd like to view")):
    return inventory[item_id]

#@app.get("/item/{item_id}/{name}")
#def item(item_id: int, name: str):
#    return inventory[item_id]

#@app.get("/name")
#def item(*, name: Optional[str] = None, test: int):
#    for item_id in inventory:
#        if inventory[item_id]["name"] == name:
#            return inventory[item_id]
#    return {"Data": "Not found"}

@app.get("/name")
def item(name: str = Query(None, title="Name", description="Name of item", max_length=10, min_length=2)):
    for item_id in inventory:
        if inventory[item_id].name == name:
            return inventory[item_id]
    raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="Item name not found.")

#Criar

@app.post("/create/{item_id}")
def create(item_id: int, item: Item):
    if item_id in inventory:
        return {"Error": "Item ID already exists"}
    
    inventory[item_id] = item
    return inventory[item_id]

#Atualizar

@app.put("/update/{item_id}")
def update(item_id: int, item: UpdateItem):
    if item_id not in inventory:
        return {"Error": "Item ID does not exists"}
    
    if item.name != None:
        inventory[item_id].name = item.name
    if item.price != None:
        inventory[item_id].price = item.price
    if item.brand != None:
        inventory[item_id].brand = item.brand
    return inventory[item_id]

#Apagar

@app.delete("/delete")
def delete(item_id : int = Query(..., description="The ID of the item to delete", gt=0)):
    if item_id not in inventory:
        return {"Error": "Item ID does not exists"}
    
    del inventory[item_id]
    return {"Success": "Item Deleted!"}

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

@app.get("/status")
def status():
    return statusCamera()

#-------------------------------------------------------   Frame   -------------------------------------------------------

#@app.post("/getFrame")
#def frame():
#    return getFrameAPI()

#def encode_numpy_raw(array: numpy.ndarray):
#    """Serializa NumPy array inteiro em base64"""
#    return base64.b64encode(array.tobytes()).decode("utf-8")

@app.post("/captureFrame")
def capture_frame():
    colorToDepthFrame, depthFrame, colorFrame = getFrame(camState.camera)
    frameState.colorToDepthFrame = colorToDepthFrame
    frameState.depthFrame = depthFrame
    frameState.colorFrame = colorFrame
    return {"message:": "Frame successfully achieved"}

#@app.get("/getFrame")
#def getframe():
#    return {
#        "colorToDepthFrame": frameState.colorToDepthFrame,
#        "depthFrame": frameState.depthFrame,
#        "colorFrame": frameState.colorFrame,
#    }

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

@app.get("/getFrame")
def get_frame():
    frames = []

    frames.append(frameState.colorFrame.tobytes())
    frames.append(frameState.colorToDepthFrame.tobytes())
    frames.append(frameState.depthFrame.tobytes())

    separator = b"__FRAME__"
    payload = separator.join(frames)

    return Response(content=payload, media_type="application/octet-stream")
    
    #return {
        #"colorToDepthFrame": encode_numpy_raw(frameState.colorToDepthFrame),
        #"colorToDepthShape": frameState.colorToDepthFrame.shape,
        #"colorToDepthDtype": str(frameState.colorToDepthFrame.dtype),

        #"depthFrame": encode_numpy_raw(frameState.depthFrame),
        #"depthShape": frameState.depthFrame.shape,
        #"depthDtype": str(frameState.depthFrame.dtype),

        #"colorFrame": encode_numpy_raw(frameState.colorFrame),
        #"colorShape": frameState.colorFrame.shape,
        #"colorDtype": str(frameState.colorFrame.dtype),
    #}

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

    res, colorToDepthFrame_copy, depthFrame_copy = maskAPI(camState.camera, lower, upper, camState.colorSlope)

    if res is None or colorToDepthFrame_copy is None or depthFrame_copy is None:
        return{"message:": "Mask application failed!"}

    frameState.res = res
    frameState.colorToDepthFrameCopy = colorToDepthFrame_copy
    frameState.depthFrameCopy = depthFrame_copy
    
    return{"message:": "Mask applied with success"}

#@app.get("/mask")
#def get_mask():
#    return {
#        "Result": workspaceState.detection_area,
#        "": workspaceState.workspace_depth,
#        "Forced Exit Flag": workspaceState.forced_exiting,
#    }

#------------------------------------------------------- Calibrate -------------------------------------------------------

@app.post("/calibrate")
def calibrate(data: HSVValue):
    lower = (data.hmin, data.smin, data.vmin)
    upper = (data.hmax, data.smax, data.vmax)

    detection_area, workspace_depth = calibrateAPI(camState.camera, lower, upper, camState.colorSlope)

    if detection_area is None or workspace_depth is None:
        return{"message:": "Calibration failed!"}

    workspaceState.detection_area = detection_area
    workspaceState.workspace_depth = workspace_depth

    return {"message:": "Calibration sucessfully done"}

@app.get("/calibrate/params")
def get_calibration_parameters():
    return {
        "Detection Area": workspaceState.detection_area,
        "Workspace Depth": workspaceState.workspace_depth,
    }

#--------------------------------------------------------- Mode ---------------------------------------------------------

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