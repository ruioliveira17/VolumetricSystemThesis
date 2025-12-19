from fastapi import FastAPI, Path, Query, HTTPException, status
from typing import Optional
from pydantic import BaseModel
from CameraOptions import openCamera, closeCamera, statusCamera
from GetFrame import getFrame
from CalibrationDefTkinter import calibrateAPI
from CameraState import camState
from FrameState import frameState
from MaskState import maskState
from WorkspaceState import workspaceState
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

@app.post("/getFrame")
def postframe():
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

#-------------------------------------------------------    HSV    -------------------------------------------------------

@app.post("/mask/hmin")
def sethmin(data: HSVValue):
    if data.hmin > maskState.hmax:
        maskState.hmin = maskState.hmax
    else:
        maskState.hmin = data.hmin
    return{"hmin": maskState.hmin}

@app.post("/mask/smin")
def setsmin(data: HSVValue):
    if data.smin > maskState.smax:
        maskState.smin = maskState.smax
    else:
        maskState.smin = data.smin
    return{"smin": maskState.smin}

@app.post("/mask/vmin")
def setvmin(data: HSVValue):
    if data.vmin > maskState.vmax:
        maskState.vmin = maskState.vmax
    else:
        maskState.vmin = data.vmin
    return{"vmin": maskState.vmin}

@app.post("/mask/hmax")
def sethmax(data: HSVValue):
    if data.hmax < maskState.hmin:
        maskState.hmax = maskState.hmin
    else:
        maskState.hmax = data.hmax
    return{"hmax": maskState.hmax}

@app.post("/mask/smax")
def setsmax(data: HSVValue):
    if data.smax < maskState.smin:
        maskState.smax = maskState.smin
    else:
        maskState.smax = data.smax
    return{"smax": maskState.smax}

@app.post("/mask/vmax")
def setvmax(data: HSVValue):
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

#-------------------------------------------------------   Mask    -------------------------------------------------------

#@app.post("/mask")
#def mask(data: MaskValue):
    
#    return calibrateAPI()

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

    detection_area, workspace_depth, forced_exiting = calibrateAPI(camState.camera, lower, upper, camState.colorSlope)

    workspaceState.detection_area = detection_area
    workspaceState.workspace_depth = workspace_depth
    workspaceState.forced_exiting = forced_exiting

    return {"message:": "Calibration sucessfully done"}

@app.get("/calibrate")
def get_mask():
    return {
        "Detection Area": workspaceState.detection_area,
        "Workspace Depth": workspaceState.workspace_depth,
        "Forced Exit Flag": workspaceState.forced_exiting,
    }