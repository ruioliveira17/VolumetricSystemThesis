#------------------------------------------------------   Imports    -------------------------------------------------------

from aiortc import RTCPeerConnection, RTCSessionDescription
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from jose import jwt # Not needed?
from jose.exceptions import JWTError, ExpiredSignatureError
from PIL import Image
from typing import Optional

import asyncio
import cv2
import io
import json
import numpy
import os
import sys
import time
import threading

#------------------------------------------------------    Paths     -------------------------------------------------------

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)

os.environ.setdefault("DATABASE_PATH", os.path.join(PROJECT, "data", "dev_app.db"))

#------------------------------------------------------   Classes    -------------------------------------------------------

from db.migrate import run_migrations
from db import measurements_repo, config_repo, calibration_repo
from db.users_repo import get_by_login, get_by_username, get_by_email, get_by_id, create_user, list_users, set_role, delete_user

from BaseModels import CamValues, ColorCoords, CropWindow, CurrentMenu, HSVValue, LoginData, ManualWorkspace, MeasurementIn, ObjectIn, RefreshData, RegisterData, RoleUpdate, SystemUpdate
from CameraState import camState
from DepthState import depthState
from FilterState import filterState
from FrameState import frameState
from MaskState import maskState
from ModeState import modeState
from VolumeState import volumeState
from WeightState import weightState
from WorkspaceState import workspaceState

#------------------------------------------------------   Preset    --------------------------------------------------------

from color_presets import COLOR_PRESETS

#-----------------------------------------------------   Functions    ------------------------------------------------------

from API.VzenseDS_api import *
from auth import create_access_token, create_refresh_token, get_password_hash, verify_password, verify_token
from Bundle2 import objIdentifier
from CalibrationDefTkinter import calibrateAPI, maskAPI
from CameraOptions import startCamera, stopCamera, setFPS, processHDR, setFlyingPixelFilter, setFillHoleFilter, setSpatialFilter, setConfidenceFilter
from MinDepth2 import MinDepthAPI
from VolumeTkinter import volumeSingleBundleAPI, volumeMultiBundleAPI, volumeRealAPI, volumeIndividualAPI
from Weight import weight_loop, weight_lock

#------------------------------------------------------   Services    ------------------------------------------------------

from services.saveCalibration import save_WS_calibration
from services.saveConfiguration import save_configuration
from services.stream import generateRGB_Stream, generateCalibrationCTD_Stream, generateCalibrationMask_Stream, CameraTrack, CTDTrack
from services.utils import rgb_to_hsv

#----------------------------------------------------   DB Migration   ----------------------------------------------------

run_migrations(hash_password=get_password_hash)

#----------------------------------------------------      OAuth2      ----------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login",
    scheme_name="OAuth2PasswordBearer",
    auto_error=True)

def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Retrieves user token.
    """
    try:
        payload = verify_token(token)
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired.")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    
    if payload["type"] != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type.")
    
    return {"username": payload["sub"], "role": payload["role"]}

def require_admin(user: dict = Depends(get_current_user)):
    """
    Dependency that checks if the current user has admin role. If not, it raises an HTTPException with status code 403.
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required.")
    return user

#----------------------------------------------------   Base Models    ----------------------------------------------------
load_dotenv()
ADMIN_REGISTER_CODE = os.environ.get("ADMIN_REGISTER_CODE")

pcs = set()

#--------------------------------------------------  Scaling Variables   --------------------------------------------------

def scale_nested(data, factor):
    if isinstance(data, list):
        return [scale_nested(x, factor) for x in data]
    return data * factor

#-----------------------------------------------------   Lifespan   -------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    calib = calibration_repo.get_calibration()
    if calib:
        try:
            workspaceState.detection_area = calib["detection_area"]
            workspaceState.workspace_warning = calib["workspace_warning"]
            workspaceState.workspace_depth = calib["workspace_depth"]
            maskState.hmin = calib["hmin"]
            maskState.hmax = calib["hmax"]
            maskState.smin = calib["smin"]
            maskState.smax = calib["smax"]
            maskState.vmin = calib["vmin"]
            maskState.vmax = calib["vmax"]
            maskState.color = calib["color"]
            maskState.colorRGB = calib["colorRGB"]
            camState.colorSlope = calib["colorSlope"]
            frameState.calibrationColorFrame = cv2.imread(calib["calibrationColorFrame_path"])
            frameState.calibrationDepthFrame = numpy.load(calib["calibrationDepthFrame_path"])

            print("Calibration loaded!")

        except Exception as e:
            print("Error loading calibration:", e)
    else:
        print("Its necessary to realize a calibration!")

    config = config_repo.get_last_configuration()
    if config:
        try:
            modeState.expositionMode = config["expositionMode"]
            modeState.volumeMode = config["volumeMode"]
            modeState.speedMode = config["speedMode"]
            modeState.workingMode = config["workingMode"]
            modeState.debugMode = config["debugMode"]
            camState.exposureTime = config["exposureTime"]
            camState.fps = config["fps"]
            camState.flyingPixelFilter = config["flyingPixelFilter"]
            camState.fillHoleFilter = config["fillHoleFilter"]
            camState.spatialFilter = config["spatialFilter"]
            camState.confidenceFilter = config["confidenceFilter"]
            volumeState.countdown = config["countdown"]

            print("Last configurations loaded!")

        except Exception as e:
            print("Error loading last configuration:", e)
    else:
        print("There arent any last configurations!")

    startCamera()

    thread = threading.Thread(
        target=weight_loop,
        daemon=True
    )
    thread.start()

    try:
        yield
    finally:
        #SHUTDOWN
        print("API a desligar")
        
        await asyncio.gather(
            *(pc.close() for pc in pcs),
            return_exceptions = True
        )
        pcs.clear()

        #stop_ObjProcessing()
        stopCamera()

#----------------------------------------------------   Criar App   -------------------------------------------------------

app = FastAPI(lifespan=lifespan, swagger_ui_init_oauth={
        "clientId": "",
        "clientSecret": "",
        "usePkceWithAuthorizationCodeGrant": False,
    })

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="/home/marques/Tese/html"), name="static")

#-------------------------------------------------------   HTML    --------------------------------------------------------

@app.get("/index")
def serve_manager():
    return FileResponse("html/index.html")

#-------------------------------------------------------   Login   --------------------------------------------------------

@app.post("/login", summary="Login Request",
         description="""
         Authenticates a user with the provided email and password. Returns the user's role if the credentials are valid. Otherwise, it returns an error message indicating invalid username or password.
         
         Restrictions:
         - All fields must be filled. If any field is missing, an error message will be returned.
         """,
         tags=["User"])
def login(login_data: LoginData):
    user = get_by_login(login_data.username)

    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")
    
    access_token = create_access_token({"sub": user["username"], "role": user["role"]})
    refresh_token = create_refresh_token({"sub": user["username"], "role": user["role"]})

    return {"role": user["role"], "username": user["username"], "access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@app.post("/register", summary="Register Request",
         description="""
         Creates a new user account with the provided email and password. Returns a message indicating that the process was successful.

         Restrictions:
         - All fields must be filled. If any field is missing, an error message will be returned.
         - Username must be unique. If the provided username already exists, an error message will be returned
         - To create an admin user, a valid admin code must be provided. If the code is invalid, an error message will be returned.
         """,
         tags=["User"])
def register(register_data: RegisterData):
    if not register_data.username or not register_data.password or not register_data.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please fill all fields!")

    if register_data.password != register_data.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match!")

    if get_by_username(register_data.username) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already used! Choose another username.")

    #if get_by_email(register_data.email) is not None:
    #    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already used! Choose another email.")

    create_user(username=register_data.username, email=register_data.email, password_hash=get_password_hash(register_data.password), role="user")

    return {"message": "Utilizador criado com sucesso!"}

@app.post("/refresh", summary="Access Token Refresh",
         description="""
         Creates a new access token if the user is active during the expiration time of the refresh token. Returns the new access token if the refresh token is valid. Otherwise, it returns an error message indicating that the token is invalid, expired or revoked.
         """,
         tags=["User"])
def refresh(data: RefreshData):
    try:
        payload = verify_token(data.refresh_token)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Invalid token. Login again.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token.")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token.")

    username = payload["sub"]
    user = get_by_username(username)

    if user is None:
        raise HTTPException(status_code=401, detail="User not found.")

    new_access_token = create_access_token({"sub": username, "role": user["role"]})
    new_refresh_token = create_refresh_token({"sub": username, "role": user["role"]})

    return {"access_token": new_access_token, "refresh_token": new_refresh_token}

#-------------------------------------------------------   Falta Aplicar   -------------------------------------------------------

@app.get("/users")
def get_users(current_user: dict = Depends(get_current_user)):
    return {"users": list_users()}


@app.patch("/users/{user_id}/role")
def update_role(user_id: int, data: RoleUpdate, current_user: dict = Depends(require_admin)):
    if get_by_id(user_id) is None:
        raise HTTPException(status_code=404, detail="User not found.")
    set_role(user_id, data.role)
    return {"id": user_id, "role": data.role}


@app.delete("/users/{user_id}")
def remove_user(user_id: int, current_user: dict = Depends(require_admin)):
    if get_by_id(user_id) is None:
        raise HTTPException(status_code=404, detail="User not found.")
    delete_user(user_id)
    return {"deleted": user_id}


@app.post("/saveMeasurements")
def save_measurement(data: Optional[MeasurementIn] = Body(default=None), current_user: dict = Depends(get_current_user)):
    owner = get_by_username(current_user["username"])
    if owner is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if data is None:
        raise HTTPException(status_code=400, detail="No measurement available to save.")
    else:
        volume_mode = data.volume_mode
        weight = data.weight
        objects = [o.model_dump() for o in data.objects]

    if not objects:
        raise HTTPException(status_code=400, detail="No measurement available to save.")
    total_m = round(sum(o["volume_m"] for o in objects), 6)
    total_cm = round(total_m * 1000000, 2)
    mid = measurements_repo.create_measurement(
        user_id=owner["id"], volume_mode=volume_mode, object_count=len(objects),
        total_volume_m=total_m, total_volume_cm=total_cm, weight=weight, objects=objects,
    )

    images = _snapshot_measurement_frames(mid)
    if images:
        measurements_repo.add_images(mid, images)

    return {"id": mid, "object_count": len(objects), "total_volume_cm": total_cm}


@app.get("/measurements")
def list_measurements_endpoint(current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "admin":
        return {"measurements": measurements_repo.list_measurements()}
    owner = get_by_username(current_user["username"])
    return {"measurements": measurements_repo.list_measurements(user_id=owner["id"]) if owner else []}


@app.get("/measurements/{measurement_id}")
def get_measurement_endpoint(measurement_id: int, current_user: dict = Depends(get_current_user)):
    data = measurements_repo.get_measurement(measurement_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Measurement not found.")
    return data

@app.delete("/measurements/delete/{measurement_id}")
def remove_measurements(measurement_id: int, current_user: dict = Depends(get_current_user)):
    measurements_repo.delete_measurement(measurement_id)
    return {"deleted": measurement_id}
#-------------------------------------------------------   Stream   -------------------------------------------------------

@app.post("/offer")
async def offer(request: Request, current_user: dict = Depends(get_current_user)): 
    params = await request.json() 
    streamType = params.get("stream", "volume")
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"]) 
    
    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        if pc.connectionState in ["failed", "closed", "disconnected"]:
            await pc.close()
            pcs.discard(pc)
    
    await pc.setRemoteDescription(offer)
    if streamType == "volume":
        pc.addTrack(CameraTrack())
    elif streamType == "calibration":
        pc.addTrack(CTDTrack())
    
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer) 
    
    return { 
        "sdp": pc.localDescription.sdp, 
        "type": pc.localDescription.type
    }

@app.get('/rgb', summary="RGB Stream",
          description="""
          Starts streaming the RGB feed from the camera. The RGB stream is a video capture of the scene by the RGB camera.
          """,
          tags=["Stream"])
def rgb_feed(request: Request):
    return StreamingResponse(generateRGB_Stream(), media_type='multipart/x-mixed-replace; boundary=frame')

@app.get('/calibrationCTD', summary="ColorToDepth Stream",
          description="""
          Starts streaming the ColorToDepth feed from the camera. The ColorToDepth stream is a video capture of the scene by the Depth camera and transformed into color by the software. The image shows a rectangle that represents the workspace detection area defined by the color mask.
          """,
          tags=["Stream"])
def calibrationCTD_feed(request: Request):
    return StreamingResponse(generateCalibrationCTD_Stream(), media_type='multipart/x-mixed-replace; boundary=frame')

@app.get('/calibrationMask', summary="Color Mask Stream",
          description="""
          Starts streaming the Color Mask feed from the camera. The Color Mask stream is a video capture of the scene by the Depth camera and transformed into color by the software. The image has a mask applied to only show a range of the HSV space selected by the user.
          """,
          tags=["Stream"])
def calibrationMask_feed(request: Request):
    return StreamingResponse(generateCalibrationMask_Stream(), media_type='multipart/x-mixed-replace; boundary=frame')

#-------------------------------------------------------   Frame   -------------------------------------------------------

@app.get("/getFrame/color", summary="Get Color Frame",
         description="""
         Grabs the latest color frame captured by the camera and returns it as a PNG image. If no frame is available, it returns an error message.
         """,
         tags=["Frame"])
def getColorFrame(current_user: dict = Depends(get_current_user)):
    colorFrame = frameState.colorFrame 
    if colorFrame is None:
        return {"error": "No color frame available"}
    if colorFrame.dtype != numpy.uint8:
        # Normaliza caso não seja uint8
        colorFrame = (numpy.clip(colorFrame, 0, 1) * 255).astype(numpy.uint8)
    
    # Converte BGR -> RGB
    img_rgb = colorFrame[:, :, ::-1]
    pil_img = Image.fromarray(img_rgb)

    # Salva em PNG na memória
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)

    return Response(content=buf.read(), media_type="image/png")
    #return Response(content=frameState.colorFrame.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/colorToDepth", summary="Get ColorToDepth Frame",
         description="""
         Grabs the latest depth frame converted to color captured by the camera and returns it as a PNG image. If no frame is available, it returns an error message.
         """,
         tags=["Frame"])
def getColorToDepthFrame(current_user: dict = Depends(get_current_user)):
    colorToDepthFrame = frameState.colorToDepthFrame
    if colorToDepthFrame is None:
        return {"error": "No colorToDepth frame available"}
    if colorToDepthFrame.dtype != numpy.uint8:
        # Normaliza caso não seja uint8
        colorToDepthFrame = (numpy.clip(colorToDepthFrame, 0, 1) * 255).astype(numpy.uint8)
    
    # Converte BGR -> RGB
    img_rgb = colorToDepthFrame[:, :, ::-1]
    pil_img = Image.fromarray(img_rgb)

    # Salva em PNG na memória
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)

    return Response(content=buf.read(), media_type="image/png")
    #return Response(content=frameState.colorToDepthFrame.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/depth", summary="Get Depth Frame",
         description="""
         Grabs the latest depth frame captured by the camera and returns it as a PNG image. If no frame is available, it returns an error message.
         """,
         tags=["Frame"])
def getDepthFrame(current_user: dict = Depends(get_current_user)):
    depthFrame = frameState.depthFrame
    if depthFrame is None:
        return {"error": "No depth frame available"}
    colorSlope = camState.colorSlope

    img = numpy.int32(depthFrame)
    img = img * 255 / colorSlope
    img = numpy.clip(img, 0, 255)
    img = numpy.uint8(img)
    depth_img = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)

    if depth_img.dtype != numpy.uint8:
        # Normaliza para 0-255 e converte para uint8
        frame_uint8 = (numpy.clip(depth_img, 0, 1) * 255).astype(numpy.uint8)
    else:
        frame_uint8 = depth_img

    # BGR -> RGB
    frame_depth = frame_uint8[:, :, ::-1]

    pil_img = Image.fromarray(frame_depth)

    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)

    return Response(buf.read(), media_type="image/png")
    #return Response(content=frameState.depthFrame.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/workspaceDetectedFrame", summary="Get Workspace Detected Frame",
         description="""
         Grabs the latest color to depth frame captured by the camera and applies an algorithm that makes the workspace visible to the user and returns it as a PNG image. If no frame is available, it returns an error message.
         """,
         tags=["Frame"])
def getWorkspaceDetectedFrame(current_user: dict = Depends(get_current_user)):
    workspaceDetectedFrame = frameState.workspaceDetectedFrame

    if workspaceDetectedFrame is None:
        workspaceDetectedFrame = frameState.colorToDepthFrame
        if workspaceDetectedFrame.dtype != numpy.uint8:
            # Normaliza caso não seja uint8
            workspaceDetectedFrame = (numpy.clip(workspaceDetectedFrame, 0, 1) * 255).astype(numpy.uint8)
    else:
        if workspaceDetectedFrame.dtype != numpy.uint8:
            # Normaliza caso não seja uint8
            workspaceDetectedFrame = (numpy.clip(workspaceDetectedFrame, 0, 1) * 255).astype(numpy.uint8)
    
    # Converte BGR -> RGB
    img_rgb = workspaceDetectedFrame[:, :, ::-1]
    pil_img = Image.fromarray(img_rgb)

    # Salva em PNG na memória
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)

    return Response(content=buf.read(), media_type="image/png")
    #return Response(content=frameState.workspaceDetectedFrame.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/maskFrame", summary="Get Mask Frame",
         description="""
         Grabs the latest color to depth frame captured by the camera and applies a mask that makes a color space visible to the user and returns it as a PNG image. If no frame is available, it returns an error message.
         """,
         tags=["Frame"])
def getMaskFrame(current_user: dict = Depends(get_current_user)):
    maskFrame = frameState.maskFrame
    if maskFrame is None:
        maskFrame = numpy.zeros((480, 640, 3), dtype=numpy.uint8)
    
    if maskFrame.dtype != numpy.uint8:
        # Normaliza caso não seja uint8
        maskFrame = (numpy.clip(maskFrame, 0, 1) * 255).astype(numpy.uint8)
    
    # Converte BGR -> RGB
    img_rgb = maskFrame[:, :, ::-1]
    pil_img = Image.fromarray(img_rgb)

    # Salva em PNG na memória
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)

    return Response(content=buf.read(), media_type="image/png")

    #return Response(content=frameState.maskFrame.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/detectedObjectsFrame", summary="Get Detected Objects Frame",
         description="""
         Grabs the latest color frame captured by the camera and applies an algorithm that makes the detected objects visible to the user and returns it as a PNG image. If no frame is available, it returns an error message.
         """,
         tags=["Frame"])
def getDetectedObjectsFrame(current_user: dict = Depends(get_current_user)):
    detectedObjectsFrame = frameState.detectedObjectsFrame
    if detectedObjectsFrame is None:
        raise HTTPException(status_code=404, detail="Frame not available")
    
    if detectedObjectsFrame.dtype != numpy.uint8:
        # Normaliza caso não seja uint8
        detectedObjectsFrame = (numpy.clip(detectedObjectsFrame, 0, 1) * 255).astype(numpy.uint8)
    
    # Converte BGR -> RGB
    img_rgb = detectedObjectsFrame[:, :, ::-1]
    pil_img = Image.fromarray(img_rgb)

    # Salva em PNG na memória
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)

    return Response(content=buf.read(), media_type="image/png")
    #return Response(content=frameState.detectedObjectsFrame.tobytes(), media_type="application/octet-stream")


#-------------------------------------------------------   Mask    -------------------------------------------------------
@app.post("/mask/color", summary="Set Mask Color",
         description="""
         Sets the color for the mask. This color can only be one of the predefined colors in the dropdown menu.
         """,
         tags=["Mask"])
def set_maskColor(data: HSVValue, current_user: dict = Depends(get_current_user)):
    maskState.color = data.color
    return{"color": maskState.color}

@app.post("/mask/colorClick", summary="Set Mask Color Through a Click",
         description="""
         Sets the color for the mask through a click on the image. This only works if the option "Select a Point" is selected.
         """,
         tags=["Mask"])
def clickSet_maskColor(data: ColorCoords, current_user: dict = Depends(get_current_user)):
    x, y = data.x, data.y
    b, g, r = frameState.colorToDepthFrame[y, x]
    maskState.colorRGB = [int(r), int(g), int(b)]

    color_ack = False
    preset = COLOR_PRESETS

    hsv = rgb_to_hsv(r, g, b)

    for color_name, vals in preset.items():
        lower = vals["lower"]
        upper = vals["upper"]

        if lower[0] <= hsv[0] <= upper[0] and lower[1] <= hsv[1] <= upper[1] and lower[2] <= hsv[2] <= upper[2]:
            color_ack = True
            print("Color:", color_name)
            maskState.color = color_name
    if color_ack == False:
        min_dist = float("inf")
        closest_color = None
        for color_name, vals in preset.items():
            lower = numpy.array(vals["lower"])
            upper = numpy.array(vals["upper"])
            mid = (lower + upper) / 2
            dist = ((mid[0] - hsv[0])**2 + (mid[1] - hsv[1])**2 + (mid[2] - hsv[2])**2)**0.5
            if dist < min_dist:
                min_dist = dist
                closest_color = color_name
                
        print("Closest Color:", closest_color)
        maskState.color = closest_color
    return{"color": maskState.color}

@app.get("/mask", summary="Get Mask Parameters",
         description="""
         Retrieves the HSV color space parameters for the selected color.
         """,
         tags=["Mask"])
def get_mask(current_user: dict = Depends(get_current_user)):
    if maskState.color != "Select a Point":
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

@app.post("/applyMask", summary="Apply Mask",
         description="""
         It uses the HSV color space defined previously to apply a mask to the latest color to depth frame. An algorithm makes the changes necessary to the image to show correctly the workspaceDetectedFrame and the maskFrame to the user. If the mask application is successful, it returns a success message. Otherwise, it returns an error message.
         """,
         tags=["Mask"])
def apply_mask(data: HSVValue, current_user: dict = Depends(get_current_user)):
    lower = (data.hmin, data.smin, data.vmin)
    upper = (data.hmax, data.smax, data.vmax)

    if frameState.colorToDepthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        colorToDepthFrame = frameState.colorToDepthFrame
    else:
        colorToDepthFrame = frameState.colorToDepthFrameHDR

    result = maskAPI(colorToDepthFrame, lower, upper, maskState.color, int(camState.cx_d), int(camState.cy_d))

    if result is None:
        return{"message:": "Mask application failed!"}
    
    maskFrame, workspaceDetectedFrame, detection_area, workspace_warning = result

    frameState.maskFrame = maskFrame
    frameState.workspaceDetectedFrame = workspaceDetectedFrame
    if detection_area is not None:
        workspaceState.detected_area = detection_area.reshape((-1, 2)).tolist() if isinstance(detection_area, numpy.ndarray) else detection_area
    else: 
        workspaceState.detected_area = [[5, 5],[634, 5],[634, 474], [0, 474]]
    workspaceState.temp_workspace_warning = workspace_warning.reshape((-1, 2)).tolist() if isinstance(workspace_warning, numpy.ndarray) else workspace_warning
    
    return{"message:": "Mask applied with success"}

#------------------------------------------------------- Manual WS -------------------------------------------------------

@app.post("/applyManualWorkspace", summary="Applies Manual Workspace",
         description="""
         Sends the manual workspace coordinates changed on the frontend to the backend.
         """,
         tags=["Mask"])
def apply_manualWS(data: ManualWorkspace, current_user: dict = Depends(get_current_user)):
    workspaceState.detected_area = numpy.array(data.detection_area, dtype=int).reshape((-1, 2))

    return{"message:": "Mask applied with success"}

#------------------------------------------------------- Calibrate -------------------------------------------------------

@app.get("/calibration/status", summary="Obtains the information about the calibration",
         description="""
         Checks if the file that saves the calibration has some information about the previous calibration.
         """,
         tags=["Calibration"])
def get_calibration_status(current_user: dict = Depends(get_current_user)):
    data = calibration_repo.get_calibration()

    if not data or data.get("detection_area") is None:
        return {"calibrated": False}

    try:
        return {"calibrated": True, "colorRGB": data["colorRGB"]}
    except:
        return {"calibrated": False}

@app.post("/calibrate", summary="Calibrates the Workspace",
         description="""
         Calibrates the workspace using the mask obtained previously. If all the conditions are met, the workspace parameters are saved and can be used in the future without the need of recalibration. If the calibration is successful, it returns a success message. Otherwise, it returns an error message.
         """,
         tags=["Calibration"])
def calibrate(data: HSVValue, current_user: dict = Depends(get_current_user)):
    lower = (data.hmin, data.smin, data.vmin)
    upper = (data.hmax, data.smax, data.vmax)

    colorFrame = frameState.colorFrame

    if frameState.colorToDepthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        colorToDepthFrame = frameState.colorToDepthFrame
    else:
        colorToDepthFrame = frameState.colorToDepthFrameHDR

    if frameState.depthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        depthFrame = frameState.depthFrame
    else:
        depthFrame = frameState.depthFrameHDR

    detection_area, workspace_depth, center_aligned, workspace_clear, calibrationColorFrame, calibrationDepthFrame = calibrateAPI(colorToDepthFrame, depthFrame, colorFrame, workspaceState.detected_area, lower, upper, camState.colorSlope, int(camState.cx_d), int(camState.cy_d), int(camState.fx_d), int(camState.fy_d), modeState.calibrationMode)

    if detection_area is None or workspace_depth is None:
        workspaceState.center_aligned = center_aligned
        workspaceState.workspace_clear = workspace_clear
        return{"message:": "Calibration failed!"}

    workspaceState.center_aligned = center_aligned
    workspaceState.workspace_clear = workspace_clear

    workspaceState.temp_detection_area = detection_area.reshape((-1, 2)).tolist() if isinstance(detection_area, numpy.ndarray) else detection_area
    workspaceState.temp_workspace_depth = workspace_depth
    frameState.temp_calibrationColorFrame = calibrationColorFrame
    frameState.temp_calibrationDepthFrame = calibrationDepthFrame

    return {"message:": "Calibration sucessfully done"}

@app.post("/saveCalibration", summary="Saves the calibration process",
         description="""
         Saves the detection area, workspace depth and an image of the workspace when you confirm.
         """,
         tags=["Calibration"])
def saveCalibration(current_user: dict = Depends(get_current_user)):
    workspaceState.detection_area = workspaceState.temp_detection_area
    workspaceState.workspace_warning = workspaceState.temp_workspace_warning
    workspaceState.workspace_depth = workspaceState.temp_workspace_depth
    camState.colorSlope = int(workspaceState.temp_workspace_depth * 1.4)
    frameState.calibrationColorFrame = frameState.temp_calibrationColorFrame
    frameState.calibrationDepthFrame = frameState.temp_calibrationDepthFrame

    if workspaceState.center_aligned is True and workspaceState.workspace_clear is True:
        save_WS_calibration()

    return {"message:": "Calibration saved successfully"}

@app.get("/calibrate/params", summary="Gets the Calibration Parameters",
         description="""
         Retrieves the calibration parameters for the workspace. These parameters define the characteristics of the calibrated workspace.
         """,
         tags=["Calibration"])
def getCalibrationParameters(current_user: dict = Depends(get_current_user)):
    return {
        "Detected Area": [
            [int(x), int(y)] for x, y in workspaceState.detected_area
        ],
        "Workspace Depth": workspaceState.workspace_depth,
    }

@app.get("/calibrate/flags", summary="Gets the Calibration Flags",
         description="""
         Retrieves the calibration flags for the workspace. These flags indicate the status of the calibration. This information is useful to understand what failed during calibration - wether the workspace is not centered or if there are objects in the workspace during calibration, for example.
         """,
         tags=["Calibration"])
def getCalibrationFlags(current_user: dict = Depends(get_current_user)):
    return {
        "Center Aligned": workspaceState.center_aligned,
        "Workspace Clear": workspaceState.workspace_clear,
    }

#--------------------------------------------------- Calibration Mode --------------------------------------------------

@app.get("/calibrate/mode", summary="Gets the Calibration Mode",
         description="""
         Retrieves the current calibration mode. The calibration mode can be either "Automatic" or "Manual". The "Automatic" mode performs the calibration using an algorithm that detects the workspace and calibrates it without user intervention. The "Manual" mode allows the user to define the workspace detection area manually by providing a list of coordinates that represent the vertices of a polygon.
         """,
         tags=["Using Modes"])
def getCalibrationMode(current_user: dict = Depends(get_current_user)):
    return{
        "Calibrate Mode": modeState.calibrationMode,
    }

@app.post("/calibrate/mode/automatic", summary="Sets the Calibration Mode to Automatic",
         description="""
         Sets the calibration mode to "Automatic".
         """,
         tags=["Using Modes"])
def automaticCalibration(current_user: dict = Depends(get_current_user)):
    modeState.calibrationMode = "Automatic"
    return {"mode:": modeState.calibrationMode}

@app.post("/calibrate/mode/manual", summary="Sets the Calibration Mode to Manual",
         description="""
         Sets the calibration mode to "Manual".
         """,
         tags=["Using Modes"])
def manualCalibration(current_user: dict = Depends(get_current_user)):
    modeState.calibrationMode = "Manual"
    return {"mode:": modeState.calibrationMode}

#----------------------------------------------------- Speed  Mode ----------------------------------------------------

@app.post("/speed/mode/slow", summary="Sets the Speed Mode to Slow",
         description="""
         Sets the speed mode to "Slow".
         """,
         tags=["Using Modes"])
def slowSpeed(current_user: dict = Depends(require_admin)):
    modeState.speedMode = "Slow"
    return {"mode:": modeState.speedMode}

@app.post("/speed/mode/intermedium", summary="Sets the Speed Mode to Intermedium",
         description="""
         Sets the speed mode to "Intermedium".
         """,
         tags=["Using Modes"])
def intermediumSpeed(current_user: dict = Depends(require_admin)):
    modeState.speedMode = "Intermedium"
    return {"mode:": modeState.speedMode}

@app.post("/speed/mode/fast", summary="Sets the Speed Mode to Fast",
         description="""
         Sets the speed mode to "Fast".
         """,
         tags=["Using Modes"])
def fastSpeed(current_user: dict = Depends(require_admin)):
    modeState.speedMode = "Fast"
    return {"mode:": modeState.speedMode}

#---------------------------------------------------- Working Mode -----------------------------------------------------

@app.get("/working/mode", summary="Gets the Working Mode",
         description="""
         Retrieves the current working mode. The working mode can be either "Static" or "Dynamic".
         """,
         tags=["Using Modes"])
def get_mode(current_user: dict = Depends(get_current_user)):
    return{
        "Mode": modeState.mode,
    }

@app.post("/working/mode/static", summary="Sets the Working Mode to Static",
         description="""
         Sets the working mode to "Static".
         """,
         tags=["Using Modes"])
def static(current_user: dict = Depends(require_admin)):
    modeState.mode = "Static"
    return {"mode:": modeState.mode}

@app.post("/working/mode/dynamic", summary="Sets the Working Mode to Dynamic",
         description="""
         Sets the working mode to "Dynamic".
         """,
         tags=["Using Modes"])
def dynamic(current_user: dict = Depends(require_admin)):
    modeState.mode = "Dynamic"
    return {"mode:": modeState.mode}

#--------------------------------------------------- Exposition Mode --------------------------------------------------

@app.get("/exposition/mode", summary="Gets the Exposition Mode",
         description="""
         Retrieves the current exposition mode. The exposition mode can be either "Fixed Exposition" or "HDR". The "Fixed Exposition" mode captures frames with a fixed exposure time defined by the user. The "HDR" mode captures multiple frames with different exposure times and combines them to create a single frame with a higher dynamic range.
         """,
         tags=["Using Modes"])
def get_expMode(current_user: dict = Depends(get_current_user)):
    return{
        "Exposition Mode": modeState.expositionMode,
    }

@app.post("/exposition/mode/fixed", summary="Sets the Exposition Mode to Fixed Exposition",
         description="""
         Sets the exposition mode to "Fixed Exposition".
         """,
         tags=["Using Modes"])
def fixedExp(current_user: dict = Depends(require_admin)):
    modeState.expositionMode = "Fixed Exposition"
    camState.hdrEnabled = False
    camState.camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(camState.exposureTime))
    return {"Exposition Mode:": modeState.expositionMode}

@app.post("/exposition/mode/hdr", summary="Sets the Exposition Mode to HDR",
         description="""
         Sets the exposition mode to "HDR".
         """,
         tags=["Using Modes"])
def hdrExp(current_user: dict = Depends(require_admin)):
    modeState.expositionMode = "HDR"
    
    camState.hdrEnabled = True

    return {"Exposition Mode:": modeState.expositionMode}

#---------------------------------------------------- Volume Mode -----------------------------------------------------

@app.get("/volume/mode", summary="Gets the Volume Mode",
         description="""
         Retrieves the current volume mode. The volume mode can be either "Single Bundle", "Multi Bundle", "Real" or "Individual".
         """,
         tags=["Using Modes"])
def get_mode(current_user: dict = Depends(get_current_user)):
    return{
        "Volume Mode": modeState.volumeMode,
    }

@app.post("/volume/mode/singleBundle", summary="Sets the Volume Mode to Single Bundle",
         description="""
         Sets the volume mode to "Single Bundle".
         """,
         tags=["Using Modes"])
def single_bundle(current_user: dict = Depends(require_admin)):
    modeState.volumeMode = "Single Bundle"
    return {"mode:": modeState.volumeMode}

@app.post("/volume/mode/multiBundle", summary="Sets the Volume Mode to Multi Bundle",
         description="""
         Sets the volume mode to "Multi Bundle".
         """,
         tags=["Using Modes"])
def multi_bundle(current_user: dict = Depends(require_admin)):
    modeState.volumeMode = "Multi Bundle"
    return {"mode:": modeState.volumeMode}

@app.post("/volume/mode/real", summary="Sets the Volume Mode to Real",
         description="""
         Sets the volume mode to "Real".
         """,
         tags=["Using Modes"])
def real(current_user: dict = Depends(require_admin)):
    modeState.volumeMode = "Real"
    return {"mode:": modeState.volumeMode}

@app.post("/volume/mode/individual", summary="Sets the Volume Mode to Individual",
         description="""
         Sets the volume mode to "Individual".
         """,
         tags=["Using Modes"])
def individual(current_user: dict = Depends(require_admin)):
    modeState.volumeMode = "Individual"
    return {"mode:": modeState.volumeMode}

#------------------------------------------------------- Debug -------------------------------------------------------

@app.get("/debug/mode", summary="Gets the Debug Mode",
         description="""
         Retrieves the current debug mode. The debug mode can be either "On" or "Off". When the debug mode is "On", additional information about the system's operation is provided, which can be useful for troubleshooting and understanding the internal workings of the system. When the debug mode is "Off", only essential information is provided, which can help to improve performance and reduce clutter in the output.
         """,
         tags=["Using Modes"])
def get_debugMode(current_user: dict = Depends(get_current_user)):
    return{
        "Debug Mode": modeState.debugMode,
    }

@app.post("/debug/mode/off", summary="Sets the Debug Mode to Off",
         description="""
         Sets the debug mode to "Off".
         """,
         tags=["Using Modes"])
def debugOff(current_user: dict = Depends(require_admin)):
    modeState.debugMode = "Off"
    return {"Debug Mode:": modeState.debugMode}

@app.post("/debug/mode/on", summary="Sets the Debug Mode to On",
         description="""
         Sets the debug mode to "On".
         """,
         tags=["Using Modes"])
def debugOn(current_user: dict = Depends(require_admin)):
    modeState.debugMode = "On"
    return {"Debug Mode:": modeState.debugMode}

#------------------------------------------------------- Volume -------------------------------------------------------

@app.post("/volume/clickTimestamp")
def click_timestamp(current_user: dict = Depends(get_current_user)):
    volumeState.click_timestamp = time.monotonic()
    return {"status": "ok"}

@app.get("/volume/status")
def volumeStatus(current_user: dict = Depends(get_current_user)):
    return {
        "status": volumeState.processing
    }

@app.post("/volume/singleBundle", summary="Starts the SingleBundle Volume Algorithm",
         description="""
         Starts the bundle volume algorithm.
         """,
         tags=["Volume"])
def volume_SingleBundle(current_user: dict = Depends(get_current_user)):
    volumeState.processing = "Processing Frames..."
    while True:
        finished = processHDR(volumeState.click_timestamp)
        if finished:
            break

    colorFrame = frameState.colorFrame

    if frameState.colorToDepthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        colorToDepthFrame = frameState.colorToDepthFrame
    else:
        colorToDepthFrame = frameState.colorToDepthFrameHDR

    if frameState.depthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        depthFrame = frameState.depthFrame
    else:
        depthFrame = frameState.depthFrameHDR

    if workspaceState.workspace_warning is not None:
        volumeState.processing = "Finding Depths..."
        depthState.not_set, depthState.objects_info = MinDepthAPI(depthFrame, workspaceState.detection_area, workspaceState.workspace_warning, workspaceState.workspace_depth, depthState.threshold, depthState.not_set, camState.cx_d, camState.cy_d, camState.fx_d, camState.fy_d)
    if depthState.objects_info is not None and len(depthState.objects_info) != 0:
        depthState.minimum_depth = depthState.objects_info[0]["depth"]
        depthState.minimum_value = depthState.minimum_depth

    #depthState.not_set, depthState.objects_info = MinDepthAPI(depthFrame, workspaceState.detection_area, workspaceState.workspace_warning, workspaceState.workspace_depth, depthState.threshold, depthState.not_set, camState.cx_d, camState.cy_d, camState.fx_d, camState.fy_d)

    #if depthState.objects_info is not None and len(depthState.objects_info) != 0:
    #    depthState.minimum_value = depthState.objects_info[0]["depth"]

    #    print("New Min Value", depthState.minimum_value)

    if depthState.objects_info is not None:
        volumeState.processing = "Identifying Objects..."
        depthState.minimum_value, depthState.not_set, volumeState.box_ws, volumeState.box_limits, volumeState.depths, volumeState.objects_outOfLine, volumeState.united_contours = objIdentifier(colorFrame, colorToDepthFrame, depthFrame, frameState.calibrationColorFrame, frameState.calibrationDepthFrame, modeState.volumeMode, depthState.objects_info, workspaceState.workspace_depth, depthState.threshold, camState.colorSlope, camState.cx_d, camState.cy_d, camState.cx_rgb, camState.cy_rgb, camState.fx_d, camState.fy_d, camState.fx_rgb, camState.fy_rgb)
        if volumeState.depths:
            depthState.minimum_depth = min(volumeState.depths)
            if volumeState.box_limits is not None and len(volumeState.box_limits) > 0:
                volumeState.processing = "Calculating Volumes..."
                volumeState.volume, volumeState.width_meters, volumeState.length_meters, volumeState.height_meters = volumeSingleBundleAPI(depthFrame, workspaceState.workspace_depth, depthState.minimum_depth, volumeState.box_limits, volumeState.depths, camState.fx_d, camState.fy_d, camState.cx_d, camState.cy_d)
            else:
                volumeState.volume = [0]
                volumeState.width_meters = [0]
                volumeState.length_meters = [0]
                volumeState.height_meters = [0]
                depthState.minimum_depth = workspaceState.workspace_depth
        else:
                volumeState.volume = [0]
                volumeState.width_meters = [0]
                volumeState.length_meters = [0]
                volumeState.height_meters = [0]
                depthState.minimum_depth = workspaceState.workspace_depth
    else:
        volumeState.volume = [0]
        volumeState.width_meters = [0]
        volumeState.length_meters = [0]
        volumeState.height_meters = [0]
        depthState.minimum_depth = workspaceState.workspace_depth

    volumeState.width_meters = scale_nested(volumeState.width_meters, 100)
    volumeState.length_meters = scale_nested(volumeState.length_meters, 100)
    volumeState.height_meters = scale_nested(volumeState.height_meters, 100)
    
    volumeState.processing = ""

    print(f"volume: {volumeState.volume}, width {volumeState.width_meters}, length: {volumeState.length_meters}, height: {volumeState.height_meters}")

    return{
        "volume": volumeState.volume,
        "width": volumeState.width_meters,
        "length": volumeState.length_meters,
        "height": volumeState.height_meters,
        "depth": depthState.minimum_depth / 10,
        "ws_depth": workspaceState.workspace_depth / 10
    }

@app.get("/volume/singleBundle/results", summary="Gets the Single Bundle Volume Algorithm Results",
         description="""
         Gets the results of the bundle volume algorithm.
         """,
         tags=["Volume"])
def get_Volume_SingleBundle(current_user: dict = Depends(get_current_user)):
    response = {}

    response["Bundle"] = {
            "volume_m": round(float(volumeState.volume[0]), 6),
            "volume_cm": round(float(volumeState.volume[0] * 1000000), 2),
            "x": round(float(volumeState.width_meters[0]), 1),
            "y": round(float(volumeState.length_meters[0]), 1),
            "z": round(float(volumeState.height_meters[0]), 1)
        }
    
    return response

@app.post("/volume/multiBundle", summary="Starts the Multi Bundle Volume Algorithm",
         description="""
         Starts the multi bundle volume algorithm.
         """,
         tags=["Volume"])
def volume_MultiBundle(current_user: dict = Depends(get_current_user)):
    volumeState.processing = "Processing Frames..."
    while True:
        finished = processHDR(volumeState.click_timestamp)
        if finished:
            break

    colorFrame = frameState.colorFrame

    if frameState.colorToDepthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        colorToDepthFrame = frameState.colorToDepthFrame
    else:
        colorToDepthFrame = frameState.colorToDepthFrameHDR

    if frameState.depthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        depthFrame = frameState.depthFrame
    else:
        depthFrame = frameState.depthFrameHDR

    if workspaceState.workspace_warning is not None:
        volumeState.processing = "Finding Depths..."
        depthState.not_set, depthState.objects_info = MinDepthAPI(depthFrame, workspaceState.detection_area, workspaceState.workspace_warning, workspaceState.workspace_depth, depthState.threshold, depthState.not_set, camState.cx_d, camState.cy_d, camState.fx_d, camState.fy_d)
    if depthState.objects_info is not None and len(depthState.objects_info) != 0:
        depthState.minimum_depth = depthState.objects_info[0]["depth"]
        depthState.minimum_value = depthState.minimum_depth

    if depthState.objects_info is not None:
        volumeState.processing = "Identifying Objects..."
        depthState.minimum_value, depthState.not_set, volumeState.box_ws, volumeState.box_limits, volumeState.depths, volumeState.objects_outOfLine, volumeState.united_contours = objIdentifier(colorFrame, colorToDepthFrame, depthFrame, frameState.calibrationColorFrame, frameState.calibrationDepthFrame, modeState.volumeMode, depthState.objects_info, workspaceState.workspace_depth, depthState.threshold, camState.colorSlope, camState.cx_d, camState.cy_d, camState.cx_rgb, camState.cy_rgb, camState.fx_d, camState.fy_d, camState.fx_rgb, camState.fy_rgb)
        if volumeState.depths:       
            if volumeState.box_limits is not None and len(volumeState.box_limits) > 0:
                volumeState.processing = "Calculating Volumes..."
                volumeState.volume, volumeState.width_meters, volumeState.length_meters, volumeState.height_meters = volumeMultiBundleAPI(depthFrame, frameState.calibrationDepthFrame, workspaceState.workspace_depth, volumeState.box_limits, volumeState.depths, camState.fx_d, camState.fy_d, camState.cx_d, camState.cy_d)
            else:
                volumeState.volume = [0]
                volumeState.width_meters = [0]
                volumeState.length_meters = [0]
                volumeState.height_meters = [0]
                depthState.minimum_depth = workspaceState.workspace_depth
        else:
            volumeState.volume = [0]
            volumeState.width_meters = [0]
            volumeState.length_meters = [0]
            volumeState.height_meters = [0]
            depthState.minimum_depth = workspaceState.workspace_depth
    else:
        volumeState.volume = [0]
        volumeState.width_meters = [0]
        volumeState.length_meters = [0]
        volumeState.height_meters = [0]
        depthState.minimum_depth = workspaceState.workspace_depth

    volumeState.width_meters = scale_nested(volumeState.width_meters, 100)
    volumeState.length_meters = scale_nested(volumeState.length_meters, 100)
    volumeState.height_meters = scale_nested(volumeState.height_meters, 100)

    volumeState.processing = ""

    print(f"volume: {volumeState.volume}, width {volumeState.width_meters}, length: {volumeState.length_meters}, height: {volumeState.height_meters}")

    return{
        "volume": volumeState.volume,
        "width": volumeState.width_meters,
        "length": volumeState.length_meters,
        "height": volumeState.height_meters,
        "depth": depthState.minimum_depth / 10,
        "ws_depth": workspaceState.workspace_depth / 10
    }

@app.get("/volume/multiBundle/results", summary="Gets the Multi Bundle Volume Algorithm Results",
         description="""
         Gets the results of the multi bundle volume algorithm.
         """,
         tags=["Volume"])
def get_Volume_MultiBundle(current_user: dict = Depends(get_current_user)):
    response = {}

    volumes = volumeState.volume if isinstance(volumeState.volume, list) else [volumeState.volume]
    widths = volumeState.width_meters if isinstance(volumeState.width_meters, list) else [volumeState.width_meters]
    lengths = volumeState.length_meters if isinstance(volumeState.length_meters, list) else [volumeState.length_meters]
    heights = volumeState.height_meters if isinstance(volumeState.height_meters, list) else [volumeState.height_meters]
    depths = volumeState.depths if isinstance(volumeState.depths, list) else [volumeState.depths]

    num_objects = min(
        len(volumes),
        len(widths),
        len(lengths),
        len(heights),
        len(depths)
    )

    for i in range(num_objects):
        response[f"{i+1}"] = {
            "volume_m": round(float(volumes[i]), 6),
            "volume_cm": round(float(volumes[i] * 1000000), 2),
            "x": round(float(widths[i]), 1),
            "y": round(float(lengths[i]), 1),
            "z": round(float(heights[i]), 1)
        }

    response["Total"] = {
        "volume_m": round(float(volumes[-1]), 6),
        "volume_cm": round(float(volumes[-1] * 1000000), 2)
    }
    
    return response

@app.post("/volume/real", summary="Starts the Real Volume Algorithm",
         description="""
         Starts the real volume algorithm.
         """,
         tags=["Volume"])
def volume_Real(current_user: dict = Depends(get_current_user)):
    volumeState.processing = "Processing Frames..."
    while True:
        finished = processHDR(volumeState.click_timestamp)
        if finished:
            break

    colorFrame = frameState.colorFrame

    if frameState.colorToDepthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        colorToDepthFrame = frameState.colorToDepthFrame
    else:
        colorToDepthFrame = frameState.colorToDepthFrameHDR

    if frameState.depthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        depthFrame = frameState.depthFrame
    else:
        depthFrame = frameState.depthFrameHDR

    if workspaceState.workspace_warning is not None:
        volumeState.processing = "Finding Depths..."
        depthState.not_set, depthState.objects_info = MinDepthAPI(depthFrame, workspaceState.detection_area, workspaceState.workspace_warning, workspaceState.workspace_depth, depthState.threshold, depthState.not_set, camState.cx_d, camState.cy_d, camState.fx_d, camState.fy_d)
    if depthState.objects_info is not None and len(depthState.objects_info) != 0:
        depthState.minimum_depth = depthState.objects_info[0]["depth"]
        depthState.minimum_value = depthState.minimum_depth

    if depthState.objects_info is not None:
        volumeState.processing = "Identifying Objects..."
        depthState.minimum_value, depthState.not_set, volumeState.box_ws, volumeState.box_limits, volumeState.depths, volumeState.objects_outOfLine, volumeState.united_contours = objIdentifier(colorFrame, colorToDepthFrame, depthFrame, frameState.calibrationColorFrame, frameState.calibrationDepthFrame, modeState.volumeMode, depthState.objects_info, workspaceState.workspace_depth, depthState.threshold, camState.colorSlope, camState.cx_d, camState.cy_d, camState.cx_rgb, camState.cy_rgb, camState.fx_d, camState.fy_d, camState.fx_rgb, camState.fy_rgb)
        if volumeState.depths:
            if volumeState.box_limits is not None and len(volumeState.box_limits) > 0:
                volumeState.processing = "Calculating Volumes..."
                volumeState.volume, volumeState.width_meters, volumeState.length_meters, volumeState.height_meters, volumeState.obj_center, volumeState.obj_angles = volumeRealAPI(depthFrame, frameState.calibrationDepthFrame, workspaceState.workspace_depth, volumeState.box_limits, volumeState.united_contours, volumeState.depths, camState.fx_d, camState.fy_d, camState.cx_d, camState.cy_d)
            else:
                volumeState.volume = [0]
                volumeState.width_meters = [[0]]
                volumeState.length_meters = [[0]]
                volumeState.height_meters = [[0]]
                volumeState.obj_center = [[]]
                volumeState.obj_angles = [[]]
                depthState.minimum_depth = workspaceState.workspace_depth
        else:
            volumeState.volume = [0]
            volumeState.width_meters = [[0]]
            volumeState.length_meters = [[0]]
            volumeState.height_meters = [[0]]
            volumeState.obj_center = [[]]
            volumeState.obj_angles = [[]]
            depthState.minimum_depth = workspaceState.workspace_depth
    else:
        volumeState.volume = [0]
        volumeState.width_meters = [[0]]
        volumeState.length_meters = [[0]]
        volumeState.height_meters = [[0]]
        volumeState.obj_center = [[]]
        volumeState.obj_angles = [[]]
        depthState.minimum_depth = workspaceState.workspace_depth

    volumeState.width_meters = scale_nested(volumeState.width_meters, 100)
    volumeState.length_meters = scale_nested(volumeState.length_meters, 100)
    volumeState.height_meters = scale_nested(volumeState.height_meters, 100)

    volumeState.processing = ""

    print(f"volume: {volumeState.volume}, width {volumeState.width_meters}, length: {volumeState.length_meters}, height: {volumeState.height_meters}")

    return{
        "volume": volumeState.volume,
        "width": volumeState.width_meters,
        "length": volumeState.length_meters,
        "height": volumeState.height_meters,
        "depth": depthState.minimum_depth / 10,
        "ws_depth": workspaceState.workspace_depth / 10,
        "objCenter": volumeState.obj_center,
        "objAngles": volumeState.obj_angles,
    }

def buildVolumeRealResponse():
    response = {}

    volumes = volumeState.volume if isinstance(volumeState.volume, list) else [volumeState.volume]
    widths = volumeState.width_meters if isinstance(volumeState.width_meters, list) else [volumeState.width_meters]
    lengths = volumeState.length_meters if isinstance(volumeState.length_meters, list) else [volumeState.length_meters]
    heights = volumeState.height_meters if isinstance(volumeState.height_meters, list) else [volumeState.height_meters]
    obj_center = volumeState.obj_center if isinstance(volumeState.obj_center, list) else [volumeState.obj_center]
    obj_angles = volumeState.obj_angles if isinstance(volumeState.obj_angles, list) else [volumeState.obj_angles]

    num_objects = min(
        len(volumes),
        len(widths),
        len(lengths),
        len(heights)
    )

    for i in range(num_objects):
        if volumes[i] is None or float(volumes[i]) <= 0:
            continue

        response[f"{i+1}"] = {
            "volume_m": round(float(volumes[i]), 6),
            "volume_cm": round(float(volumes[i] * 1000000), 2),
            "x": [round(float(w), 1) for w in widths[i]],
            "y": [round(float(l), 1) for l in lengths[i]],
            "z": [round(float(h), 1) for h in heights[i]],
            "obj_center": [[round(float(x), 3), round(float(y), 3)] for (x, y) in (obj_center[i] if obj_center[i] else [])],
            "obj_angles":  [round(float(a), 1) for a in (obj_angles[i] if obj_angles[i] else [])],
        }

    response["Total"] = {
        "volume_m": round(float(volumes[-1]), 6),
        "volume_cm": round(float(volumes[-1] * 1000000), 2)
    }
    
    return response

@app.get("/volume/real/results", summary="Gets the Real Volume Algorithm Results",
         description="""
         Gets the results of the real volume algorithm.
         """,
         tags=["Volume"])
def get_Volume_Real(current_user: dict = Depends(get_current_user)):
    return buildVolumeRealResponse()

@app.post("/volume/individual", summary="Starts the Individual Volume Algorithm",
         description="""
         Starts the individual volume algorithm.
         """,
         tags=["Volume"])
def volume_Individual(current_user: dict = Depends(get_current_user)):
    volumeState.processing = "Processing Frames..."
    while True:
        finished = processHDR(volumeState.click_timestamp)
        if finished:
            break

    colorFrame = frameState.colorFrame

    if frameState.colorToDepthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        colorToDepthFrame = frameState.colorToDepthFrame
    else:
        colorToDepthFrame = frameState.colorToDepthFrameHDR

    if frameState.depthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        depthFrame = frameState.depthFrame
    else:
        depthFrame = frameState.depthFrameHDR

    #depthState.not_set, depthState.objects_info = MinDepthAPI(depthFrame, workspaceState.detection_area, workspaceState.workspace_warning, workspaceState.workspace_depth, depthState.threshold, depthState.not_set, camState.cx_d, camState.cy_d, camState.fx_d, camState.fy_d)

    #if depthState.objects_info is not None and len(depthState.objects_info) != 0:
    #    depthState.minimum_depth = depthState.objects_info[0]["depth"]
    #    depthState.minimum_value = depthState.minimum_depth

    #    print("New Min Value", depthState.minimum_value)

    if workspaceState.workspace_warning is not None:
        volumeState.processing = "Finding Depths..."
        depthState.not_set, depthState.objects_info = MinDepthAPI(depthFrame, workspaceState.detection_area, workspaceState.workspace_warning, workspaceState.workspace_depth, depthState.threshold, depthState.not_set, camState.cx_d, camState.cy_d, camState.fx_d, camState.fy_d)
    if depthState.objects_info is not None and len(depthState.objects_info) != 0:
        depthState.minimum_depth = depthState.objects_info[0]["depth"]
        depthState.minimum_value = depthState.minimum_depth

    if depthState.not_set == 0:
        volumeState.processing = "Identifying Objects..."
        depthState.minimum_value, depthState.not_set, volumeState.box_ws, volumeState.box_limits, volumeState.depths, volumeState.objects_outOfLine, volumeState.united_contours = objIdentifier(colorFrame, colorToDepthFrame, depthFrame, frameState.calibrationColorFrame, frameState.calibrationDepthFrame, modeState.volumeMode, depthState.objects_info, workspaceState.workspace_depth, depthState.threshold, camState.colorSlope, camState.cx_d, camState.cy_d, camState.cx_rgb, camState.cy_rgb, camState.fx_d, camState.fy_d, camState.fx_rgb, camState.fy_rgb)
        if volumeState.depths:
            if volumeState.box_limits is not None and len(volumeState.box_limits) > 0:
                volumeState.processing = "Calculating Volumes..."
                volumeState.volume, volumeState.width_meters, volumeState.length_meters, volumeState.height_meters = volumeIndividualAPI(depthFrame, frameState.calibrationDepthFrame, workspaceState.workspace_depth, volumeState.box_limits, volumeState.depths, camState.fx_d, camState.fy_d, camState.cx_d, camState.cy_d)
            else:
                volumeState.volume = 0
                volumeState.width_meters = 0
                volumeState.length_meters = 0
                volumeState.height_meters = 0
                depthState.minimum_depth = workspaceState.workspace_depth
        else:
            volumeState.volume = 0
            volumeState.width_meters = 0
            volumeState.length_meters = 0
            volumeState.height_meters = 0
            depthState.minimum_depth = workspaceState.workspace_depth
    else:
        volumeState.volume = 0
        volumeState.width_meters = 0
        volumeState.length_meters = 0
        depthState.minimum_depth = workspaceState.workspace_depth

    if isinstance(volumeState.width_meters, list):
        volumeState.width_meters = [w * 100 for w in volumeState.width_meters]
    else:
        volumeState.width_meters = volumeState.width_meters * 100

    if isinstance(volumeState.length_meters, list):
        volumeState.length_meters = [w * 100 for w in volumeState.length_meters]
    else:
        volumeState.length_meters = volumeState.length_meters * 100

    if isinstance(volumeState.height_meters, list):
        volumeState.height_meters = [h * 100 for h in volumeState.height_meters]
    else:
        volumeState.height_meters = volumeState.height_meters * 100

    volumeState.processing = ""

    return{
        "volume": volumeState.volume,
        "width": volumeState.width_meters,
        "length": volumeState.length_meters,
        "height": volumeState.height_meters,
        "depth": depthState.minimum_depth / 10,
        "ws_depth": workspaceState.workspace_depth / 10
    }

@app.get("/volume/individual/results", summary="Gets the Individual Volume Algorithm Results",
         description="""
         Gets the results of the individual volume algorithm.
         """,
         tags=["Volume"])
def get_Volume_Individual(current_user: dict = Depends(get_current_user)):
    response = {}

    volumes = volumeState.volume if isinstance(volumeState.volume, list) else [volumeState.volume]
    widths = volumeState.width_meters if isinstance(volumeState.width_meters, list) else [volumeState.width_meters]
    lengths = volumeState.length_meters if isinstance(volumeState.length_meters, list) else [volumeState.length_meters]
    heights = volumeState.height_meters if isinstance(volumeState.height_meters, list) else [volumeState.height_meters]
    depths = volumeState.depths if isinstance(volumeState.depths, list) else [volumeState.depths]

    num_objects = min(
        len(volumes),
        len(widths),
        len(lengths),
        len(heights),
        len(depths)
    )

    for i in range(num_objects):
        response[f"{i+1}"] = {
            "volume_m": round(float(volumes[i]), 6),
            "volume_cm": round(float(volumes[i] * 1000000), 2),
            "x": round(float(widths[i]), 1),
            "y": round(float(lengths[i]), 1),
            "z": round(float(heights[i]), 1)
        }

    response["Total"] = {
        "volume_m": round(float(volumes[-1]), 6),
        "volume_cm": round(float(volumes[-1] * 1000000), 2)
    }
    
    return response

@app.get("/getObjectsOutOfLine", summary="Gets the array of objects that are inside or outside the workspace area",
         description="""
         If the array says "true", it means the object is outside the workspace area. If it says "false", it means the object is inside the workspace area. This information is useful to understand if the detected objects are correctly placed inside the workspace or if they are outside of it, which can affect the accuracy of the volume calculation. So the objects that are outside the workspace area are discarded, wich means they are not considered for the volume calculation. 
         """,
         tags=["Volume"])
def get_Objects_OutOfLine(current_user: dict = Depends(get_current_user)):
    return {"objects_outOfLine": volumeState.objects_outOfLine}

#--------------------------------------------------------------------------------------------------------------------------

@app.get("/systemInfo", summary="Obtain Sytem Information",
         description="Returns the value of the system parameters, such as camera settings, working mode, exposition mode, debug mode and filter states.",
         tags=["System"])
def systemInfo(current_user: dict = Depends(require_admin)):
    return {
        "Exposure Time": camState.exposureTime,
        "Color Slope": camState.colorSlope,
        "Working Mode": modeState.mode,
        "Exposition Mode": modeState.expositionMode,
        "Debug Mode": modeState.debugMode,
        "Flying Pixel Filter": filterState.flyingPixelFilter,
        "Fill Hole Filter": filterState.fillHoleFilter,
        "Spatial Filter": filterState.spatialFilter,
        "Confidence Filter": filterState.confidenceFilter,
        "FPS": camState.fps
    }

@app.post("/update_systemInfo", summary="Update System Information", 
          description="""
          Updates the system parameters based on the provided values.
          
          All parameters are optional, allowing for partial updates. 
          
          Restrictions: 
          - Exposure Time must be between 100 and 4000.
          - Color Slope must be between 150 and 5000.
          - FPS must be between 1 and 15.
          - Working Mode must be either 'Static' or 'Dynamic'.
          - Exposition Mode must be either 'Fixed Exposition' or 'HDR'.
          - Debug Mode must be either 'On' or 'Off'.
          - Filter states must be boolean values (true or false).

          Note: Any string value must be sent with the exact same format as specified, including capitalization and spacing. For example, to set the working mode to 'Static', the value must be exactly 'Static' and not 'static' or 'STATIC'.
          """,
          tags=["System"])
def update_systemInfo(info: SystemUpdate, current_user: dict = Depends(require_admin)):
    if info.exposureTime is not None:
        camState.exposureTime = info.exposureTime
        camState.camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(camState.exposureTime))

    if info.colorSlope is not None:
        camState.colorSlope = info.colorSlope

    if info.workingMode is not None:
        modeState.mode = info.workingMode

    if info.expositionMode is not None:
        modeState.expositionMode = info.expositionMode

    if info.debugMode is not None:
        modeState.debugMode = info.debugMode

    if info.flyingPixelFilter is not None:
        setFlyingPixelFilter(info.flyingPixelFilter)

    if info.fillHoleFilter is not None:
        setFillHoleFilter(info.fillHoleFilter)

    if info.spatialFilter is not None:
        setSpatialFilter(info.spatialFilter)

    if info.confidenceFilter is not None:
        setConfidenceFilter(info.confidenceFilter)

    if info.fps is not None:
        camState.fps = info.fps
        setFPS(info.fps)

    if info.countdown is not None:
        volumeState.countdown = info.countdown

    if info.cropWindow is not None:
        volumeState.cropWindow = info.cropWindow

    if info.cropArea is not None:
        volumeState.cropArea = info.cropArea

    return {"status": "updated"}

# --------------------------------------- Config Status ---------------------------------------
@app.get("/configuration/status", summary="Obtains the information about the configurations",
         description="""
         Checks if the file that saves the configurations has some information about the last configuration.
         """,
         tags=["Configuration"])
def get_configuration_status(current_user: dict = Depends(get_current_user)):
    data = config_repo.get_last_configuration()

    if not data:
        return {"configured": False}

    try:
        if "expositionMode" not in data or "volumeMode" not in data or "speedMode" not in data:
            return {"configured": False}

        return {"configured": True, "expositionMode": data["expositionMode"], "volumeMode": data["volumeMode"], "speedMode": data["speedMode"], "cropArea": data["cropArea"], "cropWindow": data["cropWindow"]}

    except:
        return {"configured": False}
    
@app.post("/saveInfo")
def save_state():
    save_configuration()
    return {"ok": True}

@app.get("/countdown/value", summary="Retrieves the value of the countdown timer",
         description="""
         Obtains the value of the countdown timer. 
         """,
         tags=["Configuration"])
def get_countdownTimer(current_user: dict = Depends(get_current_user)):
    return{
        "countdown": volumeState.countdown,
    }

@app.get("/cropWindow/value", summary="Retrieves the value of the crop window",
         description="""
         Obtains the value of the crop window. 
         """,
         tags=["Configuration"])
def get_cropWindow(current_user: dict = Depends(get_current_user)):
    return{
        "cropWindow": volumeState.cropWindow,
        "cropArea": volumeState.cropArea,
    }

@app.get("/depth/status")
def depth_status(current_user : dict = Depends(get_current_user)):
    return {
        "ready": depthState.objects_info is not None
    }

# --------------------------------------- Weight ---------------------------------------

@app.get("/weight", summary="Retrieves the current weight from the scale",
         description="""
         Obtains the current weight reading from the scale.
         """,
         tags=["Weight"])
def get_weight(current_user: dict = Depends(get_current_user)):
    with weight_lock:
        return weightState.weight.copy()

# --------------------------------------  Menu  ----------------------------------------

@app.post("/currentMenu", summary="Changes the currentMenu",
         description="""
         Changes the Current Menu on the backend to make it possible to processHDR in calibrationMode
         """,
         tags=["Menu"])
def updateCurrentMenu(data: CurrentMenu, current_user: dict = Depends(get_current_user)):
    modeState.currentMenu = data.currentMenu
    return{"message:": "Success"}

# --------------------------------------- Measurements ---------------------------------------

def _as_list(value):
    return value if isinstance(value, list) else [value]

def build_measurement_objects(mode):
    objects = []
    volumes = _as_list(volumeState.volume)
    widths = _as_list(volumeState.width_meters)
    lengths = _as_list(volumeState.length_meters)
    heights = _as_list(volumeState.height_meters)

    if mode == "Real":
        centers = _as_list(volumeState.obj_center)
        angles = _as_list(volumeState.obj_angles)
        count = min(len(volumes), len(widths), len(lengths), len(heights))
        for i in range(count):
            if volumes[i] is None or float(volumes[i]) <= 0:
                continue
            objects.append({
                "idx": i + 1,
                "volume_m": round(float(volumes[i]), 6),
                "volume_cm": round(float(volumes[i] * 1000000), 2),
                "x_cm": None,
                "y_cm": None,
                "z_cm": None,
                "depth_cm": None,
                "extra": {
                    "x": [round(float(w), 1) for w in widths[i]],
                    "y": [round(float(l), 1) for l in lengths[i]],
                    "z": [round(float(h), 1) for h in heights[i]],
                    "obj_center": [[round(float(x), 3), round(float(y), 3)] for (x, y) in (centers[i] if i < len(centers) and centers[i] else [])],
                    "obj_angles": [round(float(a), 1) for a in (angles[i] if i < len(angles) and angles[i] else [])],
                },
            })
    else:
        depths = _as_list(volumeState.depths)
        count = min(len(volumes), len(widths), len(lengths), len(heights))
        for i in range(count):
            if volumes[i] is None or float(volumes[i]) <= 0:
                continue
            objects.append({
                "idx": i + 1,
                "volume_m": round(float(volumes[i]), 6),
                "volume_cm": round(float(volumes[i] * 1000000), 2),
                "x_cm": round(float(widths[i]), 1),
                "y_cm": round(float(lengths[i]), 1),
                "z_cm": round(float(heights[i]), 1),
                "depth_cm": round(float(depths[i]), 1) if i < len(depths) and depths[i] is not None else None,
                "extra": None,
            })

    return objects

def _save_png(frame, path):
    if frame is None:
        return False
    if frame.dtype != numpy.uint8:
        frame = (numpy.clip(frame, 0, 1) * 255).astype(numpy.uint8)
    Image.fromarray(frame[:, :, ::-1]).save(path, format="PNG")
    return True

def _snapshot_measurement_frames(measurement_id):
    folder = os.path.join("data", "measurements", str(measurement_id))
    os.makedirs(folder, exist_ok=True)

    frames = {
        #"color": frameState.colorFrame,
        #"colorToDepth": frameState.colorToDepthFrame,
        "detectedObjects": frameState.detectedObjectsFrame,
    }

    images = []
    for kind, frame in frames.items():
        path = os.path.join(folder, kind + ".png")
        if _save_png(frame, path):
            images.append({"kind": kind, "path": path})
    return images

def _owns_measurement(current_user, measurement):
    if current_user["role"] == "admin":
        return True
    owner = get_by_username(current_user["username"])
    return owner is not None and measurement["user_id"] == owner["id"]

@app.get("/measurements/{measurement_id}/image/{kind}", summary="Gets a measurement image",
         description="""
         Returns one of the snapshot images (color, colorToDepth, detectedObjects) of a measurement.
         """,
         tags=["Measurements"])
def get_measurement_image(measurement_id: int, kind: str, current_user: dict = Depends(get_current_user)):
    data = measurements_repo.get_measurement(measurement_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Measurement not found.")

    if not _owns_measurement(current_user, data["measurement"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    for image in data["images"]:
        if image["kind"] == kind and os.path.exists(image["path"]):
            return FileResponse(image["path"], media_type="image/png")

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")


# ----------------------------------- Server  Status -----------------------------------
@app.get("/status", summary="Checks the status of the server",
         description="""
         Checks the status of the server. If it returns ok the server is live.
         """,
         tags=["Server"])
def serverStatus():
    return {"status": "ok"}
