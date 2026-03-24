from fastapi import FastAPI, Path, Query, HTTPException, status, Response, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel
from API.VzenseDS_api import *
from Bundle2 import bundleIdentifier, objIdentifier
from CalibrationDefTkinter import calibrateAPI, maskAPI, manualWorkspaceDraw
from CameraOptions import openCamera, closeCamera, statusCamera
from GetFrame import getFrame
from HDRDef import hdrAPI
from MinDepth2 import MinDepthAPI
from VolumeTkinter import volumeBundleAPI, volumeRealAPI
#from CameraState import camState
from color_presets import COLOR_PRESETS
from DepthState import depthState
from FrameState import frameState
from MaskState import maskState
from ModeState import modeState
from VolumeState import volumeState
from WorkspaceState import workspaceState

from contextlib import asynccontextmanager
import cv2
import asyncio
import io
import json
import numpy
import os
from PIL import Image
import threading
import time
import uvicorn

USER_FILE = "auth/users.json"

stop_event = threading.Event()
pause_event = threading.Event()
pause_event.set()
hdr_threadObj = None
cam = None

#----------------------------------------------------   Base Models    ----------------------------------------------------

class HSVValue(BaseModel):
    hmin: Optional[int] = None
    hmax: Optional[int] = None
    smin: Optional[int] = None
    smax: Optional[int] = None
    vmin: Optional[int] = None
    vmax: Optional[int] = None
    color: Optional[str] = None
    optionSelected: Optional[str] = None

class CamValues(BaseModel):
    colorSlope: Optional[int] = 1500
    exposureTime: Optional[int] = 700

class ManualWorkspace(BaseModel):
    detection_area: List[int] = None

class LoginData(BaseModel):
    username: str
    password: str

class RegisterData(BaseModel):
    username: str
    password: str
    role: str
    code: Optional[str] = None

class RGBPoint(BaseModel):
    r : int
    g : int
    b : int

class camState:
    def __init__(self):
        self.camera = None
        #self.target_fps = fps
        #self._frame_interval = 1.0 / fps

        self._lock = threading.Lock()

        self._running = False
        self._thread = None

        self.colorSlope = 4100
        self.exposureTime = 700
        self.cx_d = 0
        self.cy_d = 0
        self.fx_d = 0
        self.fy_d = 0
        self.cx_rgb = 0
        self.cy_rgb = 0
        self.fx_rgb = 0
        self.fy_rgb = 0

    def start(self):
        if self.camera is not None:
            print("Camera is already opened!")
            return{"message": "Nothing to Open"}
        else:
            print("Opening Camera!")
            self.camera = VzenseTofCam()

        camera_count = self.camera.VZ_GetDeviceCount()
        retry_count = 100
        while camera_count==0 and retry_count > 0:
            retry_count = retry_count-1
            camera_count = self.camera.VZ_GetDeviceCount()
            time.sleep(1)
            print("scaning......   ",retry_count)

        device_info=VzDeviceInfo()

        if camera_count > 1:
            ret,device_infolist=self.camera.VZ_GetDeviceInfoList(camera_count)
            if ret==0:
                device_info = device_infolist[0]
                for info in device_infolist: 
                    print('cam uri:  ' + str(info.uri))
            else:
                print(' failed:' , ret)  
                raise RuntimeError("Nenhuma câmera encontrada!")  
        elif camera_count == 1:
            ret,device_info=self.camera.VZ_GetDeviceInfo()
            if ret==0:
                print('cam uri:' + str(device_info.uri))
            else:
                print(' failed:', ret)   
                raise RuntimeError("Nenhuma câmera encontrada!") 
        else: 
            print("there are no camera found")
            return {"message": "No camera detected"}

        retry = 20
        while retry > 0:
            if  VzConnectStatus.Connected.value == device_info.status:
                print("uri: "+str(device_info.uri))
                print("alias: "+str(device_info.alias))
                print("ip: "+str(device_info.ip))
                print("connectStatus: "+str(device_info.status))
                break
            retry -= 1
            time.sleep(1)
            ret,device_info=self.camera.VZ_GetDeviceInfo()
        else:
            print("connect status:",device_info.status)  
            print("Call VZ_OpenDeviceByIP with connect status :",VzConnectStatus.Connected.value)
            raise RuntimeError("Connected Status Error!") 

        ret = self.camera.VZ_OpenDeviceByIP(device_info.ip)
        print("VZ_OpenDeviceByIP ret =", ret)
        if  ret != 0:
            return{"message": "Failed"}
        else:
            ret = self.camera.VZ_StartStream()
            if  ret == 0:
                print("start stream successful")
            else:
                print("VZ_StartStream failed:",ret)

            ret,params = self.camera.VZ_GetTimeFilterParams()
            if  ret == 0:
                print("The default TimeFilter switch is " + str(params.enable))
            else:
                print("VZ_GetTimeFilterParams failed:"+ str(ret))   

            params.enable = True
            ret = self.camera.VZ_SetTimeFilterParams(params)
            if  ret == 0:
                print("Set TimeFilter switch to "+ str(params.enable) + " is Ok")   
            else:
                print("VZ_SetTimeFilterParams failed:"+ str(ret))   

            self.camera.VZ_SetExposureControlMode(VzSensorType.VzToFSensor, VzExposureControlMode.VzExposureControlMode_Manual)
            self.camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(self.exposureTime))

            ret_code, exposureStruct = self.camera.VZ_GetExposureTime(VzSensorType.VzToFSensor)
            print('Exposure Time:', exposureStruct.exposureTime)

            ret = self.camera.VZ_SetFrameRate(5)
            if  ret == 0:
                print("Set frame rate 5 is ok")   
            else:
                print("VZ_SetFrameRate failed:"+ str(ret)) 

            ret,frameRate = self.camera.VZ_GetFrameRate()
            if  ret == 0:
                print("Get default frame rate:"+ str(frameRate))   
            else:
                print("VZ_GetFrameRate failed:"+ str(ret))  

            # set Mapper
            ret = self.camera.VZ_SetTransformColorImgToDepthSensorEnabled(c_bool(True))

            if  ret == 0:
                print("VZ_SetTransformColorImgToDepthSensorEnabled ok")
            else:
                print("VZ_SetTransformColorImgToDepthSensorEnabled failed:",ret)    

            ret,params = self.camera.VZ_GetFlyingPixelFilterParams()
            if  ret == 0:
                print("The default FlyingPixelFilter switch is " + str(params.enable))
            else:
                print("VZ_GetFlyingPixelFilterParams failed:"+ str(ret))   

            params.enable = True
            ret = self.camera.VZ_SetFlyingPixelFilterParams(params)
            if  ret == 0:
                print("Set FlyingPixelFilter switch to "+ str(params.enable) + " is Ok")   
            else:
                print("VZ_SetFlyingPixelFilterParams failed:"+ str(ret))   

            ret,enable = self.camera.VZ_GetFillHoleFilterEnabled()
            if  ret == 0:
                print("The default FillHoleFilter switch is " + str(enable))
            else:
                print("VZ_GetFillHoleFilterEnabled failed:"+ str(ret))   

            enable = True
            ret = self.camera.VZ_SetFillHoleFilterEnabled(enable)
            if  ret == 0:
                print("Set FillHoleFilter switch to "+ str(enable) + " is Ok")   
            else:
                print("VZ_SetFillHoleFilterEnabled failed:"+ str(ret))   

            ret,enable = self.camera.VZ_GetSpatialFilterEnabled()
            if  ret == 0:
                print("The default SpatialFilter switch is " + str(enable))
            else:
                print("VZ_GetSpatialFilterEnabled failed:"+ str(ret))   

            enable = True
            ret = self.camera.VZ_SetSpatialFilterEnabled(enable)
            if  ret == 0:
                print("Set SpatialFilter switch to "+ str(enable) + " is Ok")   
            else:
                print("VZ_SetSpatialFilterEnabled failed:"+ str(ret))

            ret,params = self.camera.VZ_GetConfidenceFilterParams()
            if  ret == 0:
                print("The default ConfidenceFilter switch is " + str(params.enable))
            else:
                print("VZ_GetConfidenceFilterParams failed:"+ str(ret))

            params.enable = False
            ret = self.camera.VZ_SetConfidenceFilterParams(params)
            if  ret == 0:
                print("Set ConfidenceFilter switch to "+ str(params.enable) + " is Ok")   
            else:
                print("VZ_SetConfidenceFilterParams failed:"+ str(ret))
        
            ret, intrParam = self.camera.VZ_GetSensorIntrinsicParameters(VzSensorType.VzToFSensor)
            if ret != 0:
                raise RuntimeError("Error obtaining intrinsic parameters!")
            
            self.fx_d = intrParam.fx
            self.fy_d = intrParam.fy
            self.cx_d = intrParam.cx
            self.cy_d = intrParam.cy

            print("Cx Depth:", self.cx_d)
            print("Cy Depth:", self.cy_d)
            print("fx Depth:", self.fx_d)
            print("fy Depth:", self.fy_d)

            ret, intrParam = self.camera.VZ_GetSensorIntrinsicParameters(VzSensorType.VzColorSensor)
            if ret != 0:
                raise RuntimeError("Error obtaining intrinsic parameters!")

            self.fx_rgb = intrParam.fx
            self.fy_rgb = intrParam.fy
            self.cx_rgb = intrParam.cx
            self.cy_rgb = intrParam.cy

            print("Cx RGB:", self.cx_rgb)
            print("Cy RGB:", self.cy_rgb)
            print("fx RGB:", self.fx_rgb)
            print("fy RGB:", self.fy_rgb)

            print("Camera ready")

            #ret, extrParam = camState.camera.VZ_GetSensorExtrinsicParameters()
            #if ret != 0:
            #    raise RuntimeError("Error obtaining intrinsic parameters!")
            
            #print("Translation:", list(extrParam.translation))
            #print("Rotation:", list(extrParam.rotation))

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        #print(f"[CameraStream] A capturar a {self.target_fps} FPS")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        if self.camera is None:
            return{"message": "Nothing to Close"}
        else:
            ret = self.camera.VZ_StopStream()       
            if  ret == 0:
                print("stop stream successful")
            else:
                print('VZ_StopStream failed: ' + str(ret))  

            ret = self.camera.VZ_CloseDevice()  
            if  ret == 0:
                self.camera = None
                print("[CameraStream] Câmara fechada.")
                return{"message": "Success"}
            else:
                return{"message": "Failed"}
        
    #def set_fps(self, fps):
    #    self.target_fps = fps
    #    self._frame_interval = 1.0 / fps
    #    if self.camera:
    #        ret = self.camera.VZ_SetFrameRate(fps)
    #        if ret != 0:
    #            print("VZ_SetFrameRate failed:", ret)

    def get_rgb(self):
        with self._lock:
            return frameState.colorFrame.copy() if self._rgb_frame is not None else None

    def get_depth(self):
        with self._lock:
            return frameState.colorToDepthFrame.copy() if self._depth_frame is not None else None

    def _capture_loop(self):
        while self._running:
            t_start = time.monotonic()

            ret, frameready = self.camera.VZ_GetFrameReady(c_uint16(33))
            if ret != 0:
                #print("VZ_GetFrameReady failed:",ret)
                continue
            else:
                hasColorToDepth =0
                hasDepth = 0
                hasColor = 0

                if  frameready.color:      
                    ret,rgbframe = self.camera.VZ_GetFrame(VzFrameType.VzTransformColorImgToDepthSensorFrame)
                    if  ret == 0:
                        hasColorToDepth = 1   
                    else:
                        print("get color frame failed:",ret)

                if  frameready.depth:      
                    ret,depthframe = self.camera.VZ_GetFrame(VzFrameType.VzDepthFrame)
                    if  ret == 0:
                        hasDepth = 1
                    else:
                        print("get depth frame failed:",ret)

                if frameready.color:
                    ret,colorframe = self.camera.VZ_GetFrame(VzFrameType.VzColorFrame)
                    if ret == 0:
                        hasColor = 1
                    else:
                        print("get Color frame failed:", ret)

                if hasColorToDepth == 1:
                    frametmp = numpy.empty((0, 0, 3), dtype=numpy.uint8)
                    frametmp = numpy.ctypeslib.as_array(rgbframe.pFrameData, (1, rgbframe.width * rgbframe.height * 3))
                    frametmp.dtype = numpy.uint8
                    frametmp.shape = (rgbframe.height, rgbframe.width,3)
                    colorToDepthFrame = frametmp.copy()

                if hasDepth == 1:
                    frametmp = numpy.empty((0, 0, 3), dtype=numpy.uint8)
                    frametmp = numpy.ctypeslib.as_array(depthframe.pFrameData, (1, depthframe.width * depthframe.height * 2))
                    frametmp.dtype = numpy.uint16
                    frametmp.shape = (depthframe.height, depthframe.width)
                    depthFrame = frametmp.copy()

                if hasColor == 1:
                    frametmp = numpy.ctypeslib.as_array(colorframe.pFrameData, (1, colorframe.width * colorframe.height * 3))
                    frametmp.dtype = numpy.uint8
                    frametmp.shape = (colorframe.height, colorframe.width,3)
                    colorFrame = frametmp.copy()
                    #colorFrame = cv2.resize(colorFrame, (640, 480))
                    #cv2.circle(colorFrame, (int(800/2.5), int(608/2.5)), radius=3, color=(255, 0, 0), thickness=1)

                if hasColorToDepth == 1 and hasDepth == 1 and hasColor == 1:
                    frameState.colorToDepthFrame = colorToDepthFrame
                    frameState.depthFrame = depthFrame
                    frameState.colorFrame = colorFrame

            elapsed = time.monotonic() - t_start
            sleep_time = (1/5) - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
#--------------------------------------------------------------------------------------------------------------------------

def load_users():
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w") as f:
            json.dump({}, f)
    with open(USER_FILE, "r") as f:
        return json.load(f)
    
def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

def save_WS_calibration():
    cv2.imwrite("config/calibrationColorFrame.png", frameState.calibrationColorFrame)

    data = {
        "detection_area": workspaceState.detection_area.tolist(),
        "workspace_depth": float(workspaceState.workspace_depth),
        "hmin": int(maskState.hmin),
        "hmax": int(maskState.hmax),
        "smin": int(maskState.smin),
        "smax": int(maskState.smax),
        "vmin": int(maskState.vmin),
        "vmax": int(maskState.vmax),
        "color": maskState.color,
        "colorSlope": float(cam.colorSlope),
        "exposureTime": float(cam.exposureTime),
        "calibrationColorFrame_path": "config/calibrationColorFrame.png"
    }

    os.makedirs("config", exist_ok=True)

    with open("config/workspace_calibration.json", "w") as f:
        json.dump(data, f, indent=4)

def rgb_to_hsv(r, g, b):
    rgb = numpy.uint8([[[r, g, b]]])
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    return hsv[0][0].tolist()

def hdr_thread(stop_event, pause_event):
    while not stop_event.is_set():
        if not pause_event.wait(timeout  = 0.1):
            continue

        if stop_event.is_set():
            break

        try:
            hdrAPI()
        except Exception as e:
            if stop_event.is_set():
                break
            print("Erro na thread:", repr(e))

def generate_rgb_stream(cam):
    while True:
        frame = frameState.colorFrame
        if frame is not None:
            if frame.dtype != numpy.uint8:
                frame = (numpy.clip(frame, 0, 1) * 255).astype(numpy.uint8)
            _, jpeg = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(0.05)

def generate_depth_stream(cam):
    while True:
        depth = frameState.depthFrame
        if depth is not None:
            img = numpy.int32(depth)
            img = img * 255 / cam.colorSlope
            img = numpy.clip(img, 0, 255).astype(numpy.uint8)
            depth_vis = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)
            _, jpeg = cv2.imencode('.jpg', depth_vis)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(0.05)
#-----------------------------------------------------   Lifespan   -------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global cam
    # STARTUP
    path = "config/workspace_calibration.json"

    #openCamera()
    cam = camState()
    cam.start()

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
            cam.colorSlope = calib["colorSlope"]
            cam.exposureTime = calib["exposureTime"]
            frameState.calibrationColorFrame = cv2.imread(calib["calibrationColorFrame_path"])

            print("Calibração carregada!")
        except Exception as e:
            print("Error loading calibration:", e)
            calib = None

    else:
        print("É necessário realizar calibração!")

    yield

    #SHUTDOWN
    print("API a desligar")
    stop_event.set()

    if hdr_threadObj and hdr_threadObj.is_alive():
        hdr_threadObj.join()

    #closeCamera()
    cam.stop()

#----------------------------------------------------   Criar App   -------------------------------------------------------

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#-------------------------------------------------------   Login   --------------------------------------------------------

@app.post("/login")
def login(login_data: LoginData):
    users = load_users()

    if login_data.username in users and users[login_data.username]["password"] == login_data.password:
        return {"role": users[login_data.username]["role"]}
    
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")

@app.post("/register")
def register(register_data: RegisterData):
    users = load_users()

    if not register_data.username or not register_data.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please fill all fields!")
    
    if register_data.username in users:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already used! Choose another username.")
    
    given_role = "user"
    if register_data.role == "admin":
        if register_data.code != "ADMBM":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin code! Please provide a valid admin code to create an admin user.")
        given_role = "admin"

    users[register_data.username] = {"password": register_data.password, "role": given_role}
    save_users(users)

    return {"message": "Utilizador criado com sucesso!"}

#-------------------------------------------------------   Camera   -------------------------------------------------------

@app.get("/camera/status")
def camStatus():
    return statusCamera()

@app.get("/camera/exposureTime")
def get_exposure_Time():
    return {
            "Exposure Time": cam.exposureTime,
        }

@app.get("/camera/colorSlope")
def get_color_Slope():
    return {
            "colorSlope": cam.colorSlope,
        }

@app.post("/camera/setExposureTime")
def set_exposureTime(data: CamValues):
    cam.exposureTime = data.exposureTime
    cam.camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(cam.exposureTime))
    return{
        "Exposure Time": cam.exposureTime
    }

@app.post("/camera/setColorSlope")
def set_color_slope(data: CamValues):
    cam.colorSlope = data.colorSlope
    return{
        "colorSlope": cam.colorSlope
    }

#-------------------------------------------------------   Frame   -------------------------------------------------------
@app.get('/rgb')
def rgb_feed(request: Request):
    global cam
    return StreamingResponse(generate_rgb_stream(cam), media_type='multipart/x-mixed-replace; boundary=frame')

@app.get('/depth')
def depth_feed(request: Request):
    global cam
    return StreamingResponse(generate_depth_stream(cam), media_type='multipart/x-mixed-replace; boundary=frame')

@app.post("/captureFrame")
def capture_frame():
    getFrame(cam.camera)
    return {"message:": "Frame successfully achieved"}

@app.get("/getFrame/color")
def get_Color_Frame():
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

@app.get("/getFrame/colorToDepth")
def get_ColorToDepth_Frame():
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

@app.get("/getFrame/depth")
def get_Depth_Frame():
    depthFrame = frameState.depthFrame
    if depthFrame is None:
        return {"error": "No depth frame available"}
    colorSlope = cam.colorSlope

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

@app.get("/getFrame/colorToDepthCopy")
def get_ColorToDepth_Frame_Copy():
    colorToDepthFrameCopy = frameState.colorToDepthFrameCopy

    if colorToDepthFrameCopy is None:
        colorToDepthFrameCopy = frameState.colorToDepthFrame
        if colorToDepthFrameCopy.dtype != numpy.uint8:
            # Normaliza caso não seja uint8
            colorToDepthFrameCopy = (numpy.clip(colorToDepthFrameCopy, 0, 1) * 255).astype(numpy.uint8)
    else:
        if colorToDepthFrameCopy.dtype != numpy.uint8:
            # Normaliza caso não seja uint8
            colorToDepthFrameCopy = (numpy.clip(colorToDepthFrameCopy, 0, 1) * 255).astype(numpy.uint8)
    
    # Converte BGR -> RGB
    img_rgb = colorToDepthFrameCopy[:, :, ::-1]
    pil_img = Image.fromarray(img_rgb)

    # Salva em PNG na memória
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)

    return Response(content=buf.read(), media_type="image/png")
    #return Response(content=frameState.colorToDepthFrameCopy.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/depthCopy")
def get_Depth_Frame_Copy():
    return Response(content=frameState.depthFrameCopy.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/result")
def get_Result():
    result = frameState.res
    if result is None:
        result = numpy.zeros((480, 640, 3), dtype=numpy.uint8)
    
    if result.dtype != numpy.uint8:
        # Normaliza caso não seja uint8
        result = (numpy.clip(result, 0, 1) * 255).astype(numpy.uint8)
    
    # Converte BGR -> RGB
    img_rgb = result[:, :, ::-1]
    pil_img = Image.fromarray(img_rgb)

    # Salva em PNG na memória
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)

    return Response(content=buf.read(), media_type="image/png")

    #return Response(content=frameState.result.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/colorToDepthObject")
def get_ColorToDepth_Frame_Object():
    colorToDepthFrameObject = frameState.colorToDepthFrameObject
    if colorToDepthFrameObject is None:
        raise HTTPException(status_code=404, detail="Frame not available")
    
    if colorToDepthFrameObject.dtype != numpy.uint8:
        # Normaliza caso não seja uint8
        colorToDepthFrameObject = (numpy.clip(colorToDepthFrameObject, 0, 1) * 255).astype(numpy.uint8)
    
    # Converte BGR -> RGB
    img_rgb = colorToDepthFrameObject[:, :, ::-1]
    pil_img = Image.fromarray(img_rgb)

    # Salva em PNG na memória
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)

    return Response(content=buf.read(), media_type="image/png")
    #return Response(content=frameState.colorToDepthFrameObject.tobytes(), media_type="application/octet-stream")

@app.get("/getFrame/HDRcolor")
def get_Color_HDRFrame():
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

@app.get("/getFrame/HDRcolorToDepth")
def get_ColorToDepth_HDRFrame():
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

@app.get("/getFrame/HDRdepth")
def get_Depth_HDRFrame():
    depthFrameHDR = frameState.depthFrameHDR
    if depthFrameHDR is None:
        return Response(status_code=204)

    colorSlope = cam.colorSlope

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

@app.post("/mask/colorClick")
def clickSet_maskColor(data: RGBPoint):
    color_ack = False
    preset = COLOR_PRESETS

    hsv = rgb_to_hsv(data.r, data.g, data.b)

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

@app.post("/mask/optionSelected")
def set_maskColor(data: HSVValue):
    maskState.optionSelected = data.optionSelected
    return{"color": maskState.optionSelected}

@app.get("/mask")
def get_mask():
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
        "color": maskState.color,
        "optionSelected": maskState.optionSelected
    }

@app.post("/applyMask")
def apply_mask(data: HSVValue):
    lower = (data.hmin, data.smin, data.vmin)
    upper = (data.hmax, data.smax, data.vmax)

    if frameState.colorToDepthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        colorToDepthFrame = frameState.colorToDepthFrame
    else:
        colorToDepthFrame = frameState.colorToDepthFrameHDR

    if frameState.depthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        depthFrame = frameState.depthFrame
    else:
        depthFrame = frameState.depthFrameHDR

    result, colorToDepthFrame_copy, depthFrame_copy, detection_area = maskAPI(colorToDepthFrame, depthFrame, lower, upper, maskState.color, cam.colorSlope, int(cam.cx_d), int(cam.cy_d))

    if result is None or colorToDepthFrame_copy is None or depthFrame_copy is None:
        return{"message:": "Mask application failed!"}

    frameState.res = result
    frameState.colorToDepthFrameCopy = colorToDepthFrame_copy
    frameState.depthFrameCopy = depthFrame_copy
    workspaceState.detection_area = detection_area
    
    return{"message:": "Mask applied with success"}

#------------------------------------------------------- Manual WS -------------------------------------------------------
@app.post("/applyManualWorkspace")
def apply_manualWS(data: ManualWorkspace):
    if frameState.colorToDepthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        colorToDepthFrame = frameState.colorToDepthFrame
    else:
        colorToDepthFrame = frameState.colorToDepthFrameHDR

    if frameState.depthFrameHDR is None or modeState.expositionMode == "Fixed Exposition":
        depthFrame = frameState.depthFrame
    else:
        depthFrame = frameState.depthFrameHDR

    detection_area = data.detection_area

    colorToDepthFrame_copy, depthFrame_copy, detection_area = manualWorkspaceDraw(colorToDepthFrame, depthFrame, detection_area, cam.colorSlope, int(cam.cx_d), int(cam.cy_d))

    frameState.colorToDepthFrameCopy = colorToDepthFrame_copy
    frameState.depthFrameCopy = depthFrame_copy
    workspaceState.detection_area = detection_area

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

    detection_area, workspace_depth, center_aligned, workspace_clear, frameState.calibrationColorFrame = calibrateAPI(colorToDepthFrame, depthFrame, colorFrame, workspaceState.detection_area, lower, upper, cam.colorSlope, int(cam.cx_d), int(cam.cy_d), modeState.calibrationMode)

    if detection_area is None or workspace_depth is None:
        workspaceState.center_aligned = center_aligned
        workspaceState.workspace_clear = workspace_clear
        return{"message:": "Calibration failed!"}

    workspaceState.detection_area = detection_area
    workspaceState.workspace_depth = workspace_depth
    workspaceState.center_aligned = center_aligned
    workspaceState.workspace_clear = workspace_clear

    if center_aligned is True and workspace_clear is True:
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

@app.get("/calibrate/mode")
def get_calMode():
    return{
        "Calibrate Mode": modeState.calibrationMode,
    }

@app.post("/calibrate/mode/automatic")
def automaticCalibration():
    modeState.calibrationMode = "Automatic"
    return {"mode:": modeState.calibrationMode}

@app.post("/calibrate/mode/manual")
def manualCalibration():
    modeState.calibrationMode = "Manual"
    return {"mode:": modeState.calibrationMode}

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
def get_expMode():
    return{
        "Exposition Mode": modeState.expositionMode,
    }

@app.post("/expositionMode/fixed")
def fixedExp():
    modeState.expositionMode = "Fixed Exposition"
    pause_event.clear()
    return {"Exposition Mode:": modeState.expositionMode}

@app.post("/expositionMode/hdr")
def hdrExp():
    global hdr_threadObj

    modeState.expositionMode = "HDR"
    
    if hdr_threadObj and hdr_threadObj.is_alive():
        pause_event.set()
    else:
        stop_event.clear()
        hdr_threadObj = threading.Thread(target=hdr_thread, args=(stop_event, pause_event), daemon=True)
        hdr_threadObj.start()

    return {"Exposition Mode:": modeState.expositionMode}

#------------------------------------------------------- Volume -------------------------------------------------------

@app.post("/volumeBundle")
def volume_Bundle():
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

    depthState.not_set, depthState.objects_info = MinDepthAPI(depthFrame, workspaceState.detection_area, workspaceState.workspace_depth, depthState.threshold, depthState.not_set, cam.cx_d, cam.cy_d, cam.fx_d, cam.fy_d)

    if depthState.objects_info is not None and len(depthState.objects_info) != 0:
        depthState.minimum_depth = depthState.objects_info[0]["depth"]
        depthState.minimum_value = depthState.minimum_depth

        print("New Min Value", depthState.minimum_value)

    if depthState.not_set == 0:
        depthState.minimum_value, depthState.not_set, volumeState.box_ws, volumeState.box_limits, volumeState.depths, volumeState.objects_outOfLine = bundleIdentifier(colorFrame, colorToDepthFrame, depthFrame, frameState.calibrationColorFrame, depthState.objects_info, workspaceState.workspace_depth, depthState.threshold, cam.colorSlope, cam.cx_d, cam.cy_d, cam.cx_rgb, cam.cy_rgb)
        if volumeState.box_limits is not None and len(volumeState.box_limits) > 0:
            volumeState.volume, volumeState.width_meters, volumeState.height_meters = volumeBundleAPI(workspaceState.workspace_depth, depthState.minimum_depth, volumeState.box_limits, volumeState.depths, cam.fx_d, cam.fy_d, cam.cx_d, cam.cy_d)
        else:
            volumeState.volume = 0
            volumeState.width_meters = 0
            volumeState.height_meters = 0
            depthState.minimum_depth = workspaceState.workspace_depth
    else:
        volumeState.volume = 0
        volumeState.width_meters = 0
        volumeState.height_meters = 0
        depthState.minimum_depth = workspaceState.workspace_depth

    if isinstance(volumeState.width_meters, list):
        volumeState.width_meters = [w * 100 for w in volumeState.width_meters]
    else:
        volumeState.width_meters = volumeState.width_meters * 100

    if isinstance(volumeState.height_meters, list):
        volumeState.height_meters = [w * 100 for w in volumeState.height_meters]
    else:
        volumeState.height_meters = volumeState.height_meters * 100

    return{
        "volume": volumeState.volume,
        "width": volumeState.width_meters,
        "height": volumeState.height_meters,
        "depth": depthState.minimum_depth / 10,
        "ws_depth": workspaceState.workspace_depth / 10
    }

@app.get("/getVolumeBundle")
def get_Volume_Bundle():
    response = {}

    response["Bundle"] = {
            "volume_m": round(float(volumeState.volume), 6),
            "volume_cm": round(float(volumeState.volume * 1000000), 2),
            "x": round(float(volumeState.width_meters), 1),
            "y": round(float(volumeState.height_meters), 1),
            "z": round(float(workspaceState.workspace_depth/10 - depthState.minimum_depth/10), 1)
        }
    
    return response

@app.post("/volumeReal")
def volume_Real():
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

    depthState.not_set, depthState.objects_info = MinDepthAPI(depthFrame, workspaceState.detection_area, workspaceState.workspace_depth, depthState.threshold, depthState.not_set, cam.cx_d, cam.cy_d, cam.fx_d, cam.fy_d)

    if depthState.objects_info is not None and len(depthState.objects_info) != 0:
        depthState.minimum_depth = depthState.objects_info[0]["depth"]
        depthState.minimum_value = depthState.minimum_depth

        print("New Min Value", depthState.minimum_value)

    if depthState.not_set == 0:
        depthState.minimum_value, depthState.not_set, volumeState.box_ws, volumeState.box_limits, volumeState.depths, volumeState.objects_outOfLine = objIdentifier(colorFrame, colorToDepthFrame, depthFrame, frameState.calibrationColorFrame, depthState.objects_info, workspaceState.workspace_depth, depthState.threshold, cam.colorSlope, cam.cx_d, cam.cy_d, cam.cx_rgb, cam.cy_rgb)
        if volumeState.box_limits is not None and len(volumeState.box_limits) > 0:
            volumeState.volume, volumeState.width_meters, volumeState.height_meters = volumeRealAPI(workspaceState.workspace_depth, volumeState.box_limits, volumeState.depths, cam.fx_d, cam.fy_d, cam.cx_d, cam.cy_d)
        else:
            volumeState.volume = 0
            volumeState.width_meters = 0
            volumeState.height_meters = 0
            depthState.minimum_depth = workspaceState.workspace_depth
    else:
        volumeState.volume = 0
        volumeState.width_meters = 0
        volumeState.height_meters = 0
        depthState.minimum_depth = workspaceState.workspace_depth

    if isinstance(volumeState.width_meters, list):
        volumeState.width_meters = [w * 100 for w in volumeState.width_meters]
    else:
        volumeState.width_meters = volumeState.width_meters * 100

    if isinstance(volumeState.height_meters, list):
        volumeState.height_meters = [w * 100 for w in volumeState.height_meters]
    else:
        volumeState.height_meters = volumeState.height_meters * 100

    return{
        "volume": volumeState.volume,
        "width": volumeState.width_meters,
        "height": volumeState.height_meters,
        "depth": depthState.minimum_depth / 10,
        "ws_depth": workspaceState.workspace_depth / 10
    }

@app.get("/getVolumeReal")
def get_Volume_Real():
    response = {}

    volumes = volumeState.volume if isinstance(volumeState.volume, list) else [volumeState.volume]
    widths = volumeState.width_meters if isinstance(volumeState.width_meters, list) else [volumeState.width_meters]
    heights = volumeState.height_meters if isinstance(volumeState.height_meters, list) else [volumeState.height_meters]
    depths = volumeState.depths if isinstance(volumeState.depths, list) else [volumeState.depths]

    num_objects = len(depths)

    for i in range(num_objects):
        response[f"Objeto {i+1}"] = {
            "volume_m": round(float(volumes[i]), 6),
            "volume_cm": round(float(volumes[i] * 1000000), 2),
            "x": round(float(widths[i]), 1),
            "y": round(float(heights[i]), 1),
            "z": round(float(workspaceState.workspace_depth/10 - depths[i]/10), 1)
        }

    response["Total"] = {
        "volume_m": round(float(volumes[-1]), 6),
        "volume_cm": round(float(volumes[-1] * 1000000), 2)
    }
    
    return response

@app.get("/getObjectsOutOfLine")
def get_Objects_OutOfLine():
    return {"objects_outOfLine": volumeState.objects_outOfLine}

#------------------------------------------------------- Debug -------------------------------------------------------

@app.get("/debugMode")
def get_debugMode():
    return{
        "Debug Mode": modeState.debugMode,
    }

@app.post("/debugMode/off")
def debugOff():
    modeState.debugMode = "Off"
    return {"Debug Mode:": modeState.debugMode}

@app.post("/debugMode/on")
def debugOn():
    modeState.debugMode = "On"
    return {"Debug Mode:": modeState.debugMode}