#------------------------------------------------------   Imports    -------------------------------------------------------

from aiortc import RTCPeerConnection, RTCSessionDescription
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
from PIL import Image
from pydantic import BaseModel, Field, StrictBool
from typing import List, Literal, Optional

import cv2
import io
import json
import numpy
import os
import time
import threading

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "detection_logs")
os.makedirs(LOG_DIR, exist_ok=True)

#------------------------------------------------------   Classes    -------------------------------------------------------

from CameraState import camState
from DepthState import depthState
from FilterState import filterState
from FrameState import frameState
from MaskState import maskState
from ModeState import modeState
from VolumeState import volumeState
from WorkspaceState import workspaceState

#------------------------------------------------------   Preset    --------------------------------------------------------

from color_presets import COLOR_PRESETS

#-----------------------------------------------------   Functions    ------------------------------------------------------

from API.VzenseDS_api import *
from auth import create_access_token, create_refresh_token, get_password_hash, verify_password, verify_token
from Bundle2 import objIdentifier
from CalibrationDefTkinter import calibrateAPI, maskAPI, manualWorkspaceDraw
from CameraOptions import startCamera, stopCamera, setFPS, setFlyingPixelFilter, setFillHoleFilter, setSpatialFilter, setConfidenceFilter
from MinDepth2 import MinDepthAPI
from VolumeTkinter import volumeBundleAPI, volumeRealAPI

#------------------------------------------------------   Services    ------------------------------------------------------

from services.saveCalibration import save_WS_calibration
from services.saveConfiguration import save_configuration
from services.stream import generateRGB_Stream, generateCalibrationCTD_Stream, generateCalibrationMask_Stream, CameraTrack, CTDTrack
from services.utils import rgb_to_hsv
from services.users import load_users, save_users

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

#--------------------------------------------------   Object Processing   -------------------------------------------------

objProcessing_thread = None
objProcessing_thread_running = False

def object_processing():
    global objProcessing_thread_running

    print("THREAD START:", threading.get_ident())

    while objProcessing_thread_running:
        print("RUNNING:", threading.get_ident())
        if frameState.depthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
            depthFrame = frameState.depthFrame
        else:
            depthFrame = frameState.depthFrameHDR

        depthState.not_set, depthState.objects_info = MinDepthAPI(depthFrame, workspaceState.detection_area, workspaceState.workspace_warning, workspaceState.workspace_depth, depthState.threshold, depthState.not_set, camState.cx_d, camState.cy_d, camState.fx_d, camState.fy_d)

        if depthState.objects_info is not None and len(depthState.objects_info) != 0:
            depthState.minimum_depth = depthState.objects_info[0]["depth"]
            depthState.minimum_value = depthState.minimum_depth

            print("New Min Value", depthState.minimum_value)

        time.sleep(0.01)

def start_ObjProcessing():
    global objProcessing_thread
    global objProcessing_thread_running

    if objProcessing_thread_running:
        return
    
    objProcessing_thread_running = True

    objProcessing_thread = threading.Thread(
        target=object_processing,
        daemon=True
    )

    objProcessing_thread.start()

    print("Volume thread started")

def stop_ObjProcessing():
    global objProcessing_thread
    global objProcessing_thread_running

    objProcessing_thread_running = False

    if objProcessing_thread is not None:
        objProcessing_thread.join()
        objProcessing_thread = None

    print("Volume thread stopped")
#----------------------------------------------------   Base Models    ----------------------------------------------------

class CamValues(BaseModel):
    colorSlope: Optional[int] = Field(1500, ge=100, le=4000)
    exposureTime: Optional[int] = Field(700, ge=100, le=4000)

class ColorCoords(BaseModel):
    x : int
    y : int

class HSVValue(BaseModel):
    hmin: Optional[int] = None
    hmax: Optional[int] = None
    smin: Optional[int] = None
    smax: Optional[int] = None
    vmin: Optional[int] = None
    vmax: Optional[int] = None
    color: Optional[str] = None

class LoginData(BaseModel):
    username: str
    password: str

class ManualWorkspace(BaseModel):
    detection_area: List[List[float]] = None
    selected_point: Optional[int] = None

class RefreshData(BaseModel):
    refresh_token: str

class RegisterData(BaseModel):
    username: str
    password: str
    role: str
    code: Optional[str] = None

class SystemUpdate(BaseModel):
    exposureTime: Optional[int] = Field(None, ge=100, le=4000)
    colorSlope: Optional[int] = Field(None, ge=150, le=5000)
    workingMode: Optional[Literal["Static", "Dynamic"]] = None
    expositionMode: Optional[Literal["Fixed Exposition", "HDR"]] = None
    debugMode: Optional[Literal["On", "Off"]] = None
    flyingPixelFilter: Optional[StrictBool] = None
    fillHoleFilter: Optional[StrictBool] = None
    spatialFilter: Optional[StrictBool] = None
    confidenceFilter: Optional[StrictBool] = None 
    fps: Optional[int] = Field(None, ge=1, le=15)

load_dotenv()
ADMIN_REGISTER_CODE = os.environ.get("ADMIN_REGISTER_CODE")

pcs = set()

#-----------------------------------------------------   Lifespan   -------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    path = "config/workspace_calibration.json"
    conf_path = "config/last_configurations.json"

    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                calib = json.load(f)

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
            camState.colorSlope = calib["colorSlope"]
            camState.exposureTime = calib["exposureTime"]
            frameState.calibrationColorFrame = cv2.imread(calib["calibrationColorFrame_path"])
            frameState.calibrationDepthFrame = numpy.load(calib["calibrationDepthFrame_path"])
            
            print("Calibration loaded successfully!")

        except Exception as e:
            print("Error loading calibration:", e)
            calib = None
    else:
        print("É necessário realizar calibração!")
        calib = None

    saved_config = {}
    if os.path.exists(conf_path):
        try:
            with open(conf_path, "r") as f:
                config = json.load(f)

            modeState.expositionMode = config.get("expositionMode", modeState.expositionMode)
            modeState.volumeMode     = config.get("volumeMode",     modeState.volumeMode)
            modeState.mode           = config.get("workingMode",    modeState.mode)
            modeState.debugMode      = config.get("debugMode",      modeState.debugMode)
            if "exposureTime" in config: camState.exposureTime = config["exposureTime"]
            if "colorSlope"   in config: camState.colorSlope   = config["colorSlope"]
            if "fps"          in config: camState.fps          = config["fps"]
            camState.hdrEnabled = (modeState.expositionMode == "HDR")
            saved_config = config
            print("Last configurations loaded successfully!")

        except Exception as e:
            print("Error loading last configurations:", e)
    else:
        print("No last configurations found.")

    startCamera()

    if saved_config and camState.fx_d != 0:
        if "flyingPixelFilter" in saved_config: setFlyingPixelFilter(saved_config["flyingPixelFilter"])
        if "fillHoleFilter"    in saved_config: setFillHoleFilter(saved_config["fillHoleFilter"])
        if "spatialFilter"     in saved_config: setSpatialFilter(saved_config["spatialFilter"])
        if "confidenceFilter"  in saved_config: setConfidenceFilter(saved_config["confidenceFilter"])

    yield

    #SHUTDOWN
    print("API a desligar")
    save_configuration()
    stopCamera()

#----------------------------------------------------   Criar App   -------------------------------------------------------

app = FastAPI(lifespan=lifespan, swagger_ui_init_oauth={
        "clientId": "",
        "clientSecret": "",
        "usePkceWithAuthorizationCodeGrant": False,
    })

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://10.0.30.151:5173", "http://localhost:5173"],
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
         Authenticates a user with the provided username and password. Returns the user's role if the credentials are valid. Otherwise, it returns an error message indicating invalid username or password.
         
         Restrictions:
         - All fields must be filled. If any field is missing, an error message will be returned.
         """,
         tags=["User"])
def login(login_data: LoginData):
    users = load_users()

    user = users.get(login_data.username)

    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")
    
    access_token = create_access_token({"sub": login_data.username, "role": user["role"]})
    refresh_token = create_refresh_token({"sub": login_data.username, "role": user["role"]})

    return {"role": user["role"], "access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@app.post("/register", summary="Register Request",
         description="""
         Creates a new user account with the provided username and password. Returns a message indicating that the process was successful.

         Restrictions:
         - All fields must be filled. If any field is missing, an error message will be returned.
         - Username must be unique. If the provided username already exists, an error message will be returned
         - To create an admin user, a valid admin code must be provided. If the code is invalid, an error message will be returned.
         """,
         tags=["User"])
def register(register_data: RegisterData):
    users = load_users()

    if not register_data.username or not register_data.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please fill all fields!")
    
    if register_data.username in users:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already used! Choose another username.")
    
    given_role = "user"
    if register_data.role == "admin":
        if register_data.code != ADMIN_REGISTER_CODE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin code! Please provide a valid admin code to create an admin user.")
        given_role = "admin"

    password_hash = get_password_hash(register_data.password)

    users[register_data.username] = {"password": password_hash, "role": given_role}
    save_users(users)

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
    users = load_users()

    if username not in users:
        raise HTTPException(status_code=401, detail="User not found.")

    new_access_token = create_access_token({"sub": username, "role": users[username]["role"]})
    new_refresh_token = create_refresh_token({"sub": username, "role": users[username]["role"]})

    return {"access_token": new_access_token, "refresh_token": new_refresh_token}

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

@app.get("/getFrame/rawDepth", summary="Get Raw Depth Frame", tags=["Frame"])
def getRawDepthFrame(current_user: dict = Depends(get_current_user)):
    depthFrame = frameState.depthFrame
    if depthFrame is None:
        return {"error": "No depth frame available"}
    arr = numpy.array(depthFrame, dtype=numpy.float32)
    buf = io.BytesIO()
    numpy.save(buf, arr)
    buf.seek(0)
    return Response(buf.read(), media_type="application/octet-stream")

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

@app.get("/getFrame/HDRcolor", summary="Get HDR Color Frame",
         description="""
         Grabs the HDR color frame provided by an algorithm that captures multiple exposures and returns it as a PNG image. If no frame is available, it returns an error message.
         """,
         tags=["Frame"])
def get_Color_HDRFrame(current_user: dict = Depends(get_current_user)):
    colorFrameHDR = frameState.colorFrameHDR
    if colorFrameHDR is None:
        return Response(status_code=204)

    if colorFrameHDR.dtype != numpy.uint8:
        # Normaliza caso não seja uint8
        colorFrameHDR = (numpy.clip(colorFrameHDR, 0, 1) * 255).astype(numpy.uint8)
    
    # Converte BGR -> RGB
    img_rgbHDR = colorFrameHDR[:, :, ::-1]
    pil_img = Image.fromarray(img_rgbHDR)

    # Salva em PNG na memória
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)

    return Response(content=buf.read(), media_type="image/png")
    #return Response(content=frameState.colorFrameHDR.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/HDRcolorToDepth", summary="Get HDR ColorToDepth Frame",
         description="""
         Grabs the HDR depth frame provided by an algorithm that captures multiple exposures converted to color and returns it as a PNG image. If no frame is available, it returns an error message.
         """,
         tags=["Frame"])
def get_ColorToDepth_HDRFrame(current_user: dict = Depends(get_current_user)):
    colorToDepthFrameHDR = frameState.colorToDepthFrameHDR
    if colorToDepthFrameHDR is None:
        return Response(status_code=204)

    if colorToDepthFrameHDR.dtype != numpy.uint8:
        # Normaliza caso não seja uint8
        colorToDepthFrameHDR = (numpy.clip(colorToDepthFrameHDR, 0, 1) * 255).astype(numpy.uint8)
    
    # Converte BGR -> RGB
    img_ctdHDR = colorToDepthFrameHDR[:, :, ::-1]
    pil_img = Image.fromarray(img_ctdHDR)

    # Salva em PNG na memória
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)

    return Response(content=buf.read(), media_type="image/png")
    #return Response(content=frameState.colorToDepthFrameHDR.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/HDRdepth", summary="Get HDR Depth Frame",
         description="""
         Grabs the HDR depth frame provided by an algorithm that captures multiple exposures and returns it as a PNG image. If no frame is available, it returns an error message.
         """,
         tags=["Frame"])
def get_Depth_HDRFrame(current_user: dict = Depends(get_current_user)):
    depthFrameHDR = frameState.depthFrameHDR
    if depthFrameHDR is None:
        return Response(status_code=204)

    colorSlope = camState.colorSlope

    img = numpy.int32(depthFrameHDR)
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

    # Salva em PNG na memória
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)

    return Response(content=buf.read(), media_type="image/png")
    #return Response(content=frameState.depthFrameHDR.tobytes(), media_type="application/octet-stream")

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

    color_ack = False
    preset = COLOR_PRESETS

    hsv = rgb_to_hsv(r, g, b)

    for color_name, vals in preset.items():
        lower = vals["lower"]
        upper = vals["upper"]

        if lower[0] <= hsv[0] <= upper[0] and lower[1] <= hsv[1] <= upper[1] and lower[2] <= hsv[2] <= upper[2]:
            color_ack = True
            print("Color:", color_name)
            if color_name == "Red2":
                color_name = "Red"
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
                
        if closest_color == "Red2":
            closest_color = "Red"
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

    maskFrame, workspaceDetectedFrame, detection_area, workspace_warning = maskAPI(colorToDepthFrame, lower, upper, maskState.color, int(camState.cx_d), int(camState.cy_d))

    if maskFrame is None or workspaceDetectedFrame is None:
        return{"message:": "Mask application failed!"}

    frameState.maskFrame = maskFrame
    frameState.workspaceDetectedFrame = workspaceDetectedFrame
    workspaceState.detected_area = detection_area.reshape((-1, 2)).tolist() if isinstance(detection_area, numpy.ndarray) else detection_area
    workspaceState.temp_workspace_warning = workspace_warning.reshape((-1, 2)).tolist() if isinstance(workspace_warning, numpy.ndarray) else workspace_warning
    
    return{"message:": "Mask applied with success"}

#------------------------------------------------------- Manual WS -------------------------------------------------------

@app.post("/applyManualWorkspace", summary="Applies Manual Workspace",
         description="""
         Allows the user to change the workspace detection area manually by providing a list of coordinates that represent the vertices of a polygon. An algorithm makes the changes necessary to the image to show correctly the workspaceDetectedFrame to the user with the new workspace defined. If the workspace application is successful, it returns a success message. Otherwise, it returns an error message.
         """,
         tags=["Mask"])
def apply_manualWS(data: ManualWorkspace, current_user: dict = Depends(get_current_user)):
    if frameState.colorToDepthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        colorToDepthFrame = frameState.colorToDepthFrame
    else:
        colorToDepthFrame = frameState.colorToDepthFrameHDR

    detection_area = numpy.array(data.detection_area, dtype=int).reshape((-1, 2))
    selected_point = data.selected_point

    workspaceDetectedFrame, detection_area = manualWorkspaceDraw(colorToDepthFrame, detection_area, selected_point, int(camState.cx_d), int(camState.cy_d))

    if workspaceDetectedFrame is None:
        return{"message:": "Mask application failed!"}

    frameState.workspaceDetectedFrame = workspaceDetectedFrame
    workspaceState.detected_area = detection_area.tolist()

    return{"message:": "Mask applied with success"}

#------------------------------------------------------- Calibrate -------------------------------------------------------

@app.get("/calibration/status", summary="Obtains the information about the calibration",
         description="""
         Checks if the file that saves the calibration has some information about the previous calibration.
         """,
         tags=["Calibration"])
def get_calibration_status(current_user: dict = Depends(get_current_user)):
    path = "config/workspace_calibration.json"

    if not os.path.exists(path):
        return {"calibrated": False}

    try:
        with open(path, "r") as f:
            data = json.load(f)

        if "detection_area" not in data or "workspace_warning" not in data:
            return {"calibrated": False}

        return {"calibrated": True}

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
        "Detection Area": [
            [int(x), int(y)] for x, y in workspaceState.detection_area
        ],
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
    save_configuration()
    return {"Exposition Mode:": modeState.expositionMode}

@app.post("/exposition/mode/hdr", summary="Sets the Exposition Mode to HDR",
         description="""
         Sets the exposition mode to "HDR".
         """,
         tags=["Using Modes"])
def hdrExp(current_user: dict = Depends(require_admin)):
    modeState.expositionMode = "HDR"
    
    camState.hdrEnabled = True

    save_configuration()
    return {"Exposition Mode:": modeState.expositionMode}

#---------------------------------------------------- Volume Mode -----------------------------------------------------

@app.get("/volume/mode", summary="Gets the Volume Mode",
         description="""
         Retrieves the current volume mode. The volume mode can be either "Static" or "Real".
         """,
         tags=["Using Modes"])
def get_mode(current_user: dict = Depends(get_current_user)):
    return{
        "Volume Mode": modeState.volumeMode,
    }

@app.post("/volume/mode/bundle", summary="Sets the Volume Mode to Bundle",
         description="""
         Sets the volume mode to "Bundle".
         """,
         tags=["Using Modes"])
def bundle(current_user: dict = Depends(require_admin)):
    modeState.volumeMode = "Bundle"
    save_configuration()
    return {"mode:": modeState.volumeMode}

@app.post("/volume/mode/real", summary="Sets the Volume Mode to Real",
         description="""
         Sets the volume mode to "Real".
         """,
         tags=["Using Modes"])
def real(current_user: dict = Depends(require_admin)):
    modeState.volumeMode = "Real"
    save_configuration()
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

@app.post("/menu/volume/open")
def open_volume_menu():
    start_ObjProcessing()

    return {"status": "ok"}

@app.post("/menu/volume/close")
def close_volume_menu():
    stop_ObjProcessing()

    return {"status": "ok"}

def _get_current_frames():
    use_hdr = (frameState.colorToDepthFrameHDR is not None and
               modeState.expositionMode != "Fixed Exposition")
    color          = frameState.colorFrameHDR        if use_hdr else frameState.colorFrame
    color_to_depth = frameState.colorToDepthFrameHDR if use_hdr else frameState.colorToDepthFrame
    depth          = frameState.depthFrameHDR        if use_hdr else frameState.depthFrame
    return color, color_to_depth, depth

@app.post("/volume/bundle", summary="Starts the Bundle Volume Algorithm",
         description="""
         Starts the bundle volume algorithm.
         """,
         tags=["Volume"])
def volume_Bundle(current_user: dict = Depends(get_current_user)):
    N_FRAMES     = 3
    WAIT_TIMEOUT = 3.0

    widths, lengths, heights = [], [], []
    last_depths, last_box_limits = [], []

    for _fi in range(N_FRAMES):
        t_deadline = time.time() + WAIT_TIMEOUT
        while depthState.not_set != 0 and time.time() < t_deadline:
            time.sleep(0.05)
        if depthState.not_set != 0:
            print(f"Frame {_fi+1}/{N_FRAMES}: timeout, skipping")
            continue

        colorFrame, colorToDepthFrame, depthFrame = _get_current_frames()
        if depthFrame is None:
            continue

        _min_val, _not_set, _box_ws, _box_limits, _depths, _out_of_line = objIdentifier(
            colorFrame, colorToDepthFrame, depthFrame,
            frameState.calibrationColorFrame, frameState.calibrationDepthFrame,
            modeState.volumeMode, depthState.objects_info,
            workspaceState.workspace_depth, depthState.threshold,
            camState.colorSlope, camState.cx_d, camState.cy_d,
            camState.cx_rgb, camState.cy_rgb,
            camState.fx_d, camState.fy_d, camState.fx_rgb, camState.fy_rgb
        )
        depthState.not_set = _not_set

        if not _box_limits or not _depths:
            continue

        _min_depth = min(_depths)
        _vol, _w, _l, _h = volumeBundleAPI(
            depthFrame, workspaceState.workspace_depth, _min_depth,
            _box_limits, _depths,
            camState.fx_d, camState.fy_d, camState.cx_d, camState.cy_d
        )

        if _w > 0 and _l > 0 and _h > 0:
            widths.append(_w)
            lengths.append(_l)
            heights.append(_h)
            last_depths        = _depths
            last_box_limits    = _box_limits
            last_out_of_line   = _out_of_line
            print(f"Frame {_fi+1}/{N_FRAMES}: W={_w*100:.1f}cm  L={_l*100:.1f}cm  H={_h*100:.1f}cm")

    if widths:
        w_med = float(numpy.median(widths))
        l_med = float(numpy.median(lengths))
        h_med = float(numpy.median(heights))
        volumeState.width_meters  = w_med * 100
        volumeState.length_meters = l_med * 100
        volumeState.height_meters = h_med * 100
        volumeState.volume        = w_med * l_med * h_med
        volumeState.depths           = last_depths
        volumeState.box_limits       = last_box_limits
        volumeState.objects_outOfLine = last_out_of_line if 'last_out_of_line' in dir() else []
        depthState.minimum_depth     = min(last_depths)
    else:
        volumeState.volume        = 0
        volumeState.width_meters  = 0
        volumeState.length_meters = 0
        volumeState.height_meters = 0
        volumeState.depths        = []
        depthState.minimum_depth  = workspaceState.workspace_depth

    try:
        _widths_log  = [volumeState.width_meters]  if widths else []
        _lengths_log = [volumeState.length_meters] if widths else []
        _heights_log = [volumeState.height_meters] if widths else []
        _volumes_log = [volumeState.volume]        if widths else []
        def _sf(v):
            try:
                f = float(v); return None if f != f else f
            except: return None
        _ts = datetime.now()
        _img_file = None
        if frameState.detectedObjectsFrame is not None:
            _img_name = _ts.strftime("%Y%m%d_%H%M%S_%f") + ".jpg"
            _img_path = os.path.join(LOG_DIR, _img_name)
            cv2.imwrite(_img_path, frameState.detectedObjectsFrame)
            _img_file = _img_name
        _log = {
            "timestamp": _ts.isoformat(),
            "workspace_depth_mm": float(workspaceState.workspace_depth),
            "n_frames": len(widths),
            "n_objects": len(last_depths),
            "image": _img_file,
            "objects": [
                {
                    "depth_mm":  _sf(last_depths[_i])  if _i < len(last_depths)  else None,
                    "height_cm": _sf(_heights_log[_i]) if _i < len(_heights_log) else None,
                    "width_cm":  _sf(_widths_log[_i])  if _i < len(_widths_log)  else None,
                    "length_cm": _sf(_lengths_log[_i]) if _i < len(_lengths_log) else None,
                    "volume_m3": _sf(_volumes_log[_i]) if _i < len(_volumes_log) else None,
                }
                for _i in range(max(len(last_depths), 1) if widths else 0)
            ]
        }
        with open(os.path.join(LOG_DIR, "detections.jsonl"), "a") as _lf:
            _lf.write(json.dumps(_log) + "\n")
    except Exception as _log_err:
        print("Log error:", _log_err)

    return {
        "volume": volumeState.volume,
        "width":  volumeState.width_meters,
        "length": volumeState.length_meters,
        "height": volumeState.height_meters,
        "depth":  depthState.minimum_depth / 10,
        "ws_depth": workspaceState.workspace_depth / 10
    }
@app.get("/volume/bundle/results", summary="Gets the Bundle Volume Algorithm Results",
         description="""
         Gets the results of the bundle volume algorithm.
         """,
         tags=["Volume"])
def get_Volume_Bundle(current_user: dict = Depends(get_current_user)):
    response = {}

    response["Bundle"] = {
            "volume_m": round(float(volumeState.volume), 6),
            "volume_cm": round(float(volumeState.volume * 1000000), 2),
            "x": round(float(volumeState.width_meters), 1),
            "y": round(float(volumeState.length_meters), 1),
            "z": round(float(volumeState.height_meters), 1)
        }
    
    return response

@app.post("/volume/real", summary="Starts the Real Volume Algorithm",
         description="""
         Starts the real volume algorithm.
         """,
         tags=["Volume"])
def volume_Real(current_user: dict = Depends(get_current_user)):
    N_FRAMES     = 3
    WAIT_TIMEOUT = 3.0
    t0 = time.perf_counter()

    # Per-object accumulators: {obj_idx: [values]}
    acc_w, acc_l, acc_h, acc_d = {}, {}, {}, {}
    last_depths, last_box_limits = [], []

    for _fi in range(N_FRAMES):
        t_deadline = time.time() + WAIT_TIMEOUT
        while depthState.not_set != 0 and time.time() < t_deadline:
            time.sleep(0.05)
        if depthState.not_set != 0:
            print(f"Real frame {_fi+1}/{N_FRAMES}: timeout, skipping")
            continue

        colorFrame, colorToDepthFrame, depthFrame = _get_current_frames()
        if depthFrame is None:
            continue

        _min_val, _not_set, _box_ws, _box_limits, _depths, _out_of_line = objIdentifier(
            colorFrame, colorToDepthFrame, depthFrame,
            frameState.calibrationColorFrame, frameState.calibrationDepthFrame,
            modeState.volumeMode, depthState.objects_info,
            workspaceState.workspace_depth, depthState.threshold,
            camState.colorSlope, camState.cx_d, camState.cy_d,
            camState.cx_rgb, camState.cy_rgb,
            camState.fx_d, camState.fy_d, camState.fx_rgb, camState.fy_rgb
        )
        depthState.not_set = _not_set

        if not _box_limits or not _depths:
            continue

        _vol_list, _w_list, _l_list, _h_list = volumeRealAPI(
            depthFrame, frameState.calibrationDepthFrame,
            workspaceState.workspace_depth, _box_limits, _depths,
            camState.fx_d, camState.fy_d, camState.cx_d, camState.cy_d
        )

        # _vol_list has totalVolume appended at end; _w/_l/_h are per-object
        n_obj = len(_w_list)
        if n_obj == 0:
            continue

        last_depths     = _depths
        last_box_limits = _box_limits
        last_out_of_line = _out_of_line

        for obj_i in range(n_obj):
            if _w_list[obj_i] > 0 and _l_list[obj_i] > 0 and _h_list[obj_i] > 0:
                acc_w.setdefault(obj_i, []).append(_w_list[obj_i])
                acc_l.setdefault(obj_i, []).append(_l_list[obj_i])
                acc_h.setdefault(obj_i, []).append(_h_list[obj_i])
                acc_d.setdefault(obj_i, []).append(_depths[obj_i] if obj_i < len(_depths) else 0)
        print(f"Real frame {_fi+1}/{N_FRAMES}: {n_obj} obj(s) detected")

    t4 = time.perf_counter()
    print(f"TOTAL /volume/real: {(t4-t0)*1000:.1f} ms")

    if acc_w:
        n_objs = max(acc_w.keys()) + 1
        final_w = [float(numpy.median(acc_w[i])) if i in acc_w else 0.0 for i in range(n_objs)]
        final_l = [float(numpy.median(acc_l[i])) if i in acc_l else 0.0 for i in range(n_objs)]
        final_h = [float(numpy.median(acc_h[i])) if i in acc_h else 0.0 for i in range(n_objs)]
        final_d = [float(numpy.median(acc_d[i])) if i in acc_d else 0.0 for i in range(n_objs)]

        # Filter ghost objects: footprint-filtered objects accumulate as 0.0
        MIN_DIM_M  = 0.01   # 1 cm minimum footprint dimension
        MIN_HEIGHT_M = 0.04  # 4 cm minimum height (filters workspace-edge artefacts)
        valid_idx = [i for i in range(n_objs) if final_w[i] > MIN_DIM_M and final_l[i] > MIN_DIM_M and final_h[i] > MIN_HEIGHT_M]
        if valid_idx:
            final_w = [final_w[i] for i in valid_idx]
            final_l = [final_l[i] for i in valid_idx]
            final_h = [final_h[i] for i in valid_idx]
            final_d = [final_d[i] for i in valid_idx]
            print(f"Ghost filter: {n_objs} -> {len(valid_idx)} object(s)")

        final_v = [final_w[i] * final_l[i] * final_h[i] for i in range(len(final_w))]
        total_v  = sum(final_v)
        final_v.append(total_v)

        volumeState.volume        = final_v
        volumeState.width_meters  = [w * 100 for w in final_w]
        volumeState.length_meters = [l * 100 for l in final_l]
        volumeState.height_meters = [h * 100 for h in final_h]
        volumeState.depths           = final_d
        volumeState.box_limits       = last_box_limits
        volumeState.objects_outOfLine = last_out_of_line if 'last_out_of_line' in dir() else []
        depthState.minimum_depth     = min(final_d) if final_d else workspaceState.workspace_depth
    else:
        volumeState.volume        = 0
        volumeState.width_meters  = 0
        volumeState.length_meters = 0
        volumeState.height_meters = 0
        volumeState.depths        = []
        depthState.minimum_depth  = workspaceState.workspace_depth

    try:
        _depths_log  = volumeState.depths        if isinstance(volumeState.depths,        list) else []
        _widths_log  = volumeState.width_meters  if isinstance(volumeState.width_meters,  list) else []
        _lengths_log = volumeState.length_meters if isinstance(volumeState.length_meters, list) else []
        _heights_log = volumeState.height_meters if isinstance(volumeState.height_meters, list) else []
        _volumes_log = volumeState.volume        if isinstance(volumeState.volume,        list) else []
        def _sf(v):
            try:
                f = float(v); return None if f != f else f
            except: return None
        _ts = datetime.now()
        _img_file = None
        if frameState.detectedObjectsFrame is not None:
            _img_name = _ts.strftime("%Y%m%d_%H%M%S_%f") + ".jpg"
            _img_path = os.path.join(LOG_DIR, _img_name)
            cv2.imwrite(_img_path, frameState.detectedObjectsFrame)
            _img_file = _img_name
        _log = {
            "timestamp": _ts.isoformat(),
            "workspace_depth_mm": float(workspaceState.workspace_depth),
            "n_frames": len(acc_w.get(0, [])),
            "n_objects": len(_depths_log),
            "image": _img_file,
            "objects": [
                {
                    "depth_mm":  _sf(_depths_log[_i])  if _i < len(_depths_log)  else None,
                    "height_cm": _sf(_heights_log[_i]) if _i < len(_heights_log) else None,
                    "width_cm":  _sf(_widths_log[_i])  if _i < len(_widths_log)  else None,
                    "length_cm": _sf(_lengths_log[_i]) if _i < len(_lengths_log) else None,
                    "volume_m3": _sf(_volumes_log[_i]) if _i < len(_volumes_log) else None,
                }
                for _i in range(len(_depths_log))
            ]
        }
        with open(os.path.join(LOG_DIR, "detections.jsonl"), "a") as _lf:
            _lf.write(json.dumps(_log) + "\n")
    except Exception as _log_err:
        print("Log error:", _log_err)

    return {
        "volume": volumeState.volume,
        "width":  volumeState.width_meters,
        "length": volumeState.length_meters,
        "height": volumeState.height_meters,
        "depth":  depthState.minimum_depth / 10,
        "ws_depth": workspaceState.workspace_depth / 10
    }
@app.get("/volume/real/results", summary="Gets the Real Volume Algorithm Results",
         description="""
         Gets the results of the real volume algorithm.
         """,
         tags=["Volume"])
def get_Volume_Real(current_user: dict = Depends(get_current_user)):
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

    save_configuration()
    return {"status": "updated"}

# --------------------------------------- Config Status ---------------------------------------
@app.get("/configuration/status", summary="Obtains the information about the configurations",
         description="""
         Checks if the file that saves the configurations has some information about the last configuration.
         """,
         tags=["Configuration"])
def get_configuration_status(current_user: dict = Depends(get_current_user)):
    path = "config/last_configurations.json"

    if not os.path.exists(path):
        return {"configured": False}

    try:
        with open(path, "r") as f:
            data = json.load(f)

        if "expositionMode" not in data or "volumeMode" not in data:
            return {"configured": False}

        return {"configured": True, "expositionMode": data["expositionMode"], "volumeMode": data["volumeMode"]}

    except:
        return {"configured": False}