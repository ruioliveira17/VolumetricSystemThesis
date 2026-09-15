import ctypes

SDK_PATH = (
    "/home/marques/Tese/AArch64/"
    "ScepterSDK/Lib/libScepter_api.so"
)
lib = ctypes.CDLL(SDK_PATH)

# ============================================================
# Tipos
# ============================================================

class ScDeviceInfo(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("productName", ctypes.c_char * 64),
        ("serialNumber", ctypes.c_char * 64),
        ("ip", ctypes.c_char * 17),
        ("status", ctypes.c_int32),
    ]


ScDeviceHandle = ctypes.c_void_p

class ScTimeFilterParams(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("threshold", ctypes.c_int32),
        ("enable", ctypes.c_bool),
    ]

class ScFlyingPixelFilterParams(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("threshold", ctypes.c_int32),
        ("enable", ctypes.c_bool),
    ]

class ScConfidenceFilterParams(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("threshold", ctypes.c_int32),
        ("enable", ctypes.c_bool),
    ]

class ScSensorIntrinsicParameters(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("fx", ctypes.c_double),
        ("fy", ctypes.c_double),
        ("cx", ctypes.c_double),
        ("cy", ctypes.c_double),
        ("k1", ctypes.c_double),
        ("k2", ctypes.c_double),
        ("p1", ctypes.c_double),
        ("p2", ctypes.c_double),
        ("k3", ctypes.c_double),
        ("k4", ctypes.c_double),
        ("k5", ctypes.c_double),
        ("k6", ctypes.c_double),
    ]

class ScFrame(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("frameIndex", ctypes.c_uint32),
        ("frameType", ctypes.c_int32),
        ("pixelFormat", ctypes.c_int32),
        ("pFrameData", ctypes.POINTER(ctypes.c_uint8)),
        ("dataLen", ctypes.c_uint32),
        ("width", ctypes.c_uint16),
        ("height", ctypes.c_uint16),
        ("deviceTimestamp", ctypes.c_uint64),
    ]

class ScFrameReady(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("depth", ctypes.c_uint32, 1),
        ("ir", ctypes.c_uint32, 1),
        ("color", ctypes.c_uint32, 1),
        ("transformedColor", ctypes.c_uint32, 1),
        ("transformedDepth", ctypes.c_uint32, 1),
        ("reserved", ctypes.c_uint32, 27),
    ]

# ============================================================
# Assinaturas
# ============================================================

lib.scInitialize.argtypes = []
lib.scInitialize.restype = ctypes.c_int32


lib.scShutdown.argtypes = []
lib.scShutdown.restype = ctypes.c_int32


lib.scGetDeviceCount.argtypes = [
    ctypes.POINTER(ctypes.c_uint32),
    ctypes.c_uint32
]
lib.scGetDeviceCount.restype = ctypes.c_int32


lib.scGetDeviceInfoList.argtypes = [
    ctypes.c_uint32,
    ctypes.POINTER(ScDeviceInfo)
]
lib.scGetDeviceInfoList.restype = ctypes.c_int32


lib.scOpenDeviceBySN.argtypes = [
    ctypes.c_char_p,
    ctypes.POINTER(ScDeviceHandle)
]
lib.scOpenDeviceBySN.restype = ctypes.c_int32


lib.scCloseDevice.argtypes = [
    ctypes.POINTER(ScDeviceHandle)
]
lib.scCloseDevice.restype = ctypes.c_int32


lib.scStartStream.argtypes = [
    ScDeviceHandle
]
lib.scStartStream.restype = ctypes.c_int32


lib.scStopStream.argtypes = [
    ScDeviceHandle
]
lib.scStopStream.restype = ctypes.c_int32

# ============================================================
# Filtros
# ============================================================

lib.scGetTimeFilterParams.argtypes = [
    ScDeviceHandle,
    ctypes.POINTER(ScTimeFilterParams)
]
lib.scGetTimeFilterParams.restype = ctypes.c_int32

lib.scSetTimeFilterParams.argtypes = [
    ScDeviceHandle,
    ScTimeFilterParams
]
lib.scSetTimeFilterParams.restype = ctypes.c_int32

lib.scSetFlyingPixelFilterParams.argtypes = [
    ScDeviceHandle,
    ScFlyingPixelFilterParams
]
lib.scSetFlyingPixelFilterParams.restype = ctypes.c_int32

lib.scGetFlyingPixelFilterParams.argtypes = [
    ScDeviceHandle,
    ctypes.POINTER(ScFlyingPixelFilterParams)
]
lib.scGetFlyingPixelFilterParams.restype = ctypes.c_int32

lib.scSetFillHoleFilterEnabled.argtypes = [
    ScDeviceHandle,
    ctypes.c_bool
]
lib.scSetFillHoleFilterEnabled.restype = ctypes.c_int32

lib.scGetFillHoleFilterEnabled.argtypes = [
    ScDeviceHandle,
    ctypes.POINTER(ctypes.c_bool)
]
lib.scGetFillHoleFilterEnabled.restype = ctypes.c_int32

lib.scSetSpatialFilterEnabled.argtypes = [
    ScDeviceHandle,
    ctypes.c_bool
]
lib.scSetSpatialFilterEnabled.restype = ctypes.c_int32

lib.scGetSpatialFilterEnabled.argtypes = [
    ScDeviceHandle,
    ctypes.POINTER(ctypes.c_bool)
]
lib.scGetSpatialFilterEnabled.restype = ctypes.c_int32

lib.scSetConfidenceFilterParams.argtypes = [
    ScDeviceHandle,
    ScConfidenceFilterParams
]
lib.scSetConfidenceFilterParams.restype = ctypes.c_int32

lib.scGetConfidenceFilterParams.argtypes = [
    ScDeviceHandle,
    ctypes.POINTER(ScConfidenceFilterParams)
]
lib.scGetConfidenceFilterParams.restype = ctypes.c_int32

# ============================================================
# Tempo de Exposição
# ============================================================

lib.scSetExposureControlMode.argtypes = [
    ScDeviceHandle,
    ctypes.c_int32,
    ctypes.c_int32
]
lib.scSetExposureControlMode.restype = ctypes.c_int32

lib.scGetExposureControlMode.argtypes = [
    ScDeviceHandle,
    ctypes.c_int32,
    ctypes.POINTER(ctypes.c_int32)
]
lib.scGetExposureControlMode.restype = ctypes.c_int32

lib.scSetExposureTime.argtypes = [
    ScDeviceHandle,
    ctypes.c_int32,
    ctypes.c_int32
]
lib.scSetExposureTime.restype = ctypes.c_int32

lib.scGetExposureTime.argtypes = [
    ScDeviceHandle,
    ctypes.c_int32,
    ctypes.POINTER(ctypes.c_int32)
]
lib.scGetExposureTime.restype = ctypes.c_int32

# ============================================================
# Frame Rate
# ============================================================

lib.scSetFrameRate.argtypes = [
    ScDeviceHandle,
    ctypes.c_int32
]
lib.scSetFrameRate.restype = ctypes.c_int32

lib.scGetFrameRate.argtypes = [
    ScDeviceHandle,
    ctypes.POINTER(ctypes.c_int32)
]
lib.scGetFrameRate.restype = ctypes.c_int32

# ============================================================
# HDR
# ============================================================

lib.scGetHDRModeEnabled.argtypes = [
    ScDeviceHandle,
    ctypes.POINTER(ctypes.c_bool)
]
lib.scGetHDRModeEnabled.restype = ctypes.c_int32


lib.scSetHDRModeEnabled.argtypes = [
    ScDeviceHandle,
    ctypes.c_bool
]
lib.scSetHDRModeEnabled.restype = ctypes.c_int32


lib.scGetFrameCountOfHDRMode.argtypes = [
    ScDeviceHandle,
    ctypes.POINTER(ctypes.c_int32)
]
lib.scGetFrameCountOfHDRMode.restype = ctypes.c_int32


lib.scSetExposureTimeOfHDR.argtypes = [
    ScDeviceHandle,
    ctypes.c_uint8,
    ctypes.c_int32
]
lib.scSetExposureTimeOfHDR.restype = ctypes.c_int32


lib.scGetExposureTimeOfHDR.argtypes = [
    ScDeviceHandle,
    ctypes.c_uint8,
    ctypes.POINTER(ctypes.c_int32)
]
lib.scGetExposureTimeOfHDR.restype = ctypes.c_int32

# ============================================================
# Parâmetros
# ============================================================

lib.scGetSensorIntrinsicParameters.argtypes = [
    ScDeviceHandle,
    ctypes.c_int32,
    ctypes.POINTER(ScSensorIntrinsicParameters)
]
lib.scGetSensorIntrinsicParameters.restype = ctypes.c_int32

# ============================================================
# Frames
# ============================================================

lib.scGetFrameReady.argtypes = [
    ScDeviceHandle,
    ctypes.c_uint16,
    ctypes.POINTER(ScFrameReady)
]
lib.scGetFrameReady.restype = ctypes.c_int32

lib.scGetFrame.argtypes = [
    ScDeviceHandle,
    ctypes.c_int32,
    ctypes.POINTER(ScFrame)
]
lib.scGetFrame.restype = ctypes.c_int32

lib.scSetTransformColorImgToDepthSensorEnabled.argtypes = [
    ScDeviceHandle,
    ctypes.c_bool
]
lib.scSetTransformColorImgToDepthSensorEnabled.restype = ctypes.c_int32