#------------------------------------------------------   Imports    -------------------------------------------------------

from aiortc import RTCPeerConnection, RTCSessionDescription
from contextlib import asynccontextmanager
from datetime import timedelta
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
from Bundle2 import bundleIdentifier, objIdentifier
from CalibrationDefTkinter import calibrateAPI, maskAPI, manualWorkspaceDraw
from CameraOptions import startCamera, stopCamera, setFPS, setFlyingPixelFilter, setFillHoleFilter, setSpatialFilter, setConfidenceFilter
from MinDepth2 import MinDepthAPI
from VolumeTkinter import volumeBundleAPI, volumeRealAPI

#------------------------------------------------------   Services    ------------------------------------------------------

from services.saveCalibration import save_WS_calibration
from services.stream import generateRGB_Stream, generateCalibrationCTD_Stream, generateCalibrationMask_Stream, CameraTrack
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

#-----------------------------------------------------   Lifespan   -------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    path = "config/workspace_calibration.json"

    if os.path.exists(path):
        try:
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
            camState.colorSlope = calib["colorSlope"]
            camState.exposureTime = calib["exposureTime"]
            frameState.calibrationColorFrame = cv2.imread(calib["calibrationColorFrame_path"])
            
            print("Calibração carregada!")

        except Exception as e:
            print("Error loading calibration:", e)
            calib = None
    else:
        print("É necessário realizar calibração!")

    startCamera()

    yield

    #SHUTDOWN
    print("API a desligar")
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
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"]) 
    
    pc = RTCPeerConnection() 
    
    await pc.setRemoteDescription(offer)
    pc.addTrack(CameraTrack())
    
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

    maskFrame, workspaceDetectedFrame, detection_area = maskAPI(colorToDepthFrame, lower, upper, maskState.color, int(camState.cx_d), int(camState.cy_d))

    if maskFrame is None or workspaceDetectedFrame is None:
        return{"message:": "Mask application failed!"}

    frameState.maskFrame = maskFrame
    frameState.workspaceDetectedFrame = workspaceDetectedFrame
    workspaceState.detected_area = detection_area.reshape((-1, 2)).tolist() if isinstance(detection_area, numpy.ndarray) else detection_area
    
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

    workspaceDetectedFrame, detection_area = manualWorkspaceDraw(colorToDepthFrame, detection_area, int(camState.cx_d), int(camState.cy_d))

    if workspaceDetectedFrame is None:
        return{"message:": "Mask application failed!"}

    frameState.workspaceDetectedFrame = workspaceDetectedFrame
    workspaceState.detected_area = detection_area.tolist()

    return{"message:": "Mask applied with success"}

#------------------------------------------------------- Calibrate -------------------------------------------------------

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

    detection_area, workspace_depth, center_aligned, workspace_clear, calibrationColorFrame = calibrateAPI(colorToDepthFrame, depthFrame, colorFrame, workspaceState.detected_area, lower, upper, camState.colorSlope, int(camState.cx_d), int(camState.cy_d), modeState.calibrationMode)

    if detection_area is None or workspace_depth is None:
        workspaceState.center_aligned = center_aligned
        workspaceState.workspace_clear = workspace_clear
        return{"message:": "Calibration failed!"}

    workspaceState.detection_area = detection_area.reshape((-1, 2)).tolist() if isinstance(detection_area, numpy.ndarray) else detection_area
    workspaceState.workspace_depth = workspace_depth
    workspaceState.center_aligned = center_aligned
    workspaceState.workspace_clear = workspace_clear
    frameState.calibrationColorFrame = calibrationColorFrame

    if center_aligned is True and workspace_clear is True:
        save_WS_calibration()

    return {"message:": "Calibration sucessfully done"}

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
    return {"mode:": modeState.volumeMode}

@app.post("/volume/mode/real", summary="Sets the Volume Mode to Real",
         description="""
         Sets the volume mode to "Real".
         """,
         tags=["Using Modes"])
def real(current_user: dict = Depends(require_admin)):
    modeState.volumeMode = "Real"
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

@app.post("/volume/bundle", summary="Starts the Bundle Volume Algorithm",
         description="""
         Starts the bundle volume algorithm.
         """,
         tags=["Volume"])
def volume_Bundle(current_user: dict = Depends(get_current_user)):
    if frameState.colorToDepthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
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

    depthState.not_set, depthState.objects_info = MinDepthAPI(depthFrame, workspaceState.detection_area, workspaceState.workspace_depth, depthState.threshold, depthState.not_set, camState.cx_d, camState.cy_d, camState.fx_d, camState.fy_d)

    if depthState.objects_info is not None and len(depthState.objects_info) != 0:
        depthState.minimum_depth = depthState.objects_info[0]["depth"]
        depthState.minimum_value = depthState.minimum_depth

        print("New Min Value", depthState.minimum_value)

    if depthState.not_set == 0:
        depthState.minimum_value, depthState.not_set, volumeState.box_ws, volumeState.box_limits, volumeState.depths, volumeState.objects_outOfLine = bundleIdentifier(colorFrame, colorToDepthFrame, depthFrame, frameState.calibrationColorFrame, depthState.objects_info, workspaceState.workspace_depth, depthState.threshold, camState.colorSlope, camState.cx_d, camState.cy_d, camState.cx_rgb, camState.cy_rgb)
        if volumeState.box_limits is not None and len(volumeState.box_limits) > 0:
            volumeState.volume, volumeState.width_meters, volumeState.length_meters, volumeState.height_meters = volumeBundleAPI(depthFrame, workspaceState.workspace_depth, depthState.minimum_depth, volumeState.box_limits, volumeState.depths, camState.fx_d, camState.fy_d, camState.cx_d, camState.cy_d)
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

    return{
        "volume": volumeState.volume,
        "width": volumeState.width_meters,
        "length": volumeState.length_meters,
        "height": volumeState.height_meters,
        "depth": depthState.minimum_depth / 10,
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
    if frameState.colorToDepthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
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

    depthState.not_set, depthState.objects_info = MinDepthAPI(depthFrame, workspaceState.detection_area, workspaceState.workspace_depth, depthState.threshold, depthState.not_set, camState.cx_d, camState.cy_d, camState.fx_d, camState.fy_d)

    if depthState.objects_info is not None and len(depthState.objects_info) != 0:
        depthState.minimum_depth = depthState.objects_info[0]["depth"]
        depthState.minimum_value = depthState.minimum_depth

        print("New Min Value", depthState.minimum_value)

    if depthState.not_set == 0:
        depthState.minimum_value, depthState.not_set, volumeState.box_ws, volumeState.box_limits, volumeState.depths, volumeState.objects_outOfLine = objIdentifier(colorFrame, colorToDepthFrame, depthFrame, frameState.calibrationColorFrame, depthState.objects_info, workspaceState.workspace_depth, depthState.threshold, camState.colorSlope, camState.cx_d, camState.cy_d, camState.cx_rgb, camState.cy_rgb)
        if volumeState.box_limits is not None and len(volumeState.box_limits) > 0:
            volumeState.volume, volumeState.width_meters, volumeState.length_meters, volumeState.height_meters = volumeRealAPI(depthFrame, workspaceState.workspace_depth, volumeState.box_limits, volumeState.depths, camState.fx_d, camState.fy_d, camState.cx_d, camState.cy_d)
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

    return{
        "volume": volumeState.volume,
        "width": volumeState.width_meters,
        "length": volumeState.length_meters,
        "height": volumeState.height_meters,
        "depth": depthState.minimum_depth / 10,
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

    num_objects = len(depths)

    for i in range(num_objects):
        response[f"Objeto {i+1}"] = {
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

    return {"status": "updated"}