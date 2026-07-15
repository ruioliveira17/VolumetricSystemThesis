from pydantic import BaseModel, Field, StrictBool
from typing import List, Literal, Optional

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

class CropWindow(BaseModel):
    x: float
    y: float
    width: float
    height: float

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
    countdown: Optional[int] = Field(None, ge=0, le=10)
    cropWindow: Optional[CropWindow] = None
    cropArea: Optional[CropWindow] = None

class CurrentMenu(BaseModel):
    currentMenu: str