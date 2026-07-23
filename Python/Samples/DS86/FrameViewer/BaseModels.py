from pydantic import BaseModel, Field, StrictBool
from typing import Any, List, Literal, Optional

class CamValues(BaseModel):
    colorSlope: Optional[int] = Field(1500, ge=100, le=4000)
    exposureTime: Optional[int] = Field(700, ge=100, le=4000)

class ColorCoords(BaseModel):
    x : int
    y : int

class CropWindow(BaseModel):
    x: float
    y: float
    width: float
    height: float

class CurrentMenu(BaseModel):
    currentMenu: str

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

class ObjectIn(BaseModel):
    # Campos numericos como Any: no modo Real vem em listas (arrays dentro de arrays).
    # O adaptador em measurements_repo.create_measurement encaminha listas -> extra_json
    # e mete escalares nas colunas, por isso o modelo so precisa de aceitar o payload.
    idx: int
    volume_m: Optional[Any] = None
    volume_cm: Optional[Any] = None
    x_cm: Optional[Any] = None
    y_cm: Optional[Any] = None
    z_cm: Optional[Any] = None
    extra: Optional[dict] = None

class MeasurementIn(BaseModel):
    volume_mode: str
    weight: Optional[Any] = None
    objects: List[ObjectIn]

class RefreshData(BaseModel):
    refresh_token: str

class RegisterData(BaseModel):
    username: str
    email: Optional[str] = None
    password: str
    confirm_password: str

class RoleUpdate(BaseModel):
    role: Literal["user", "admin"]

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