import ctypes
import time


# ============================================================
# Configuração
# ============================================================

HDR_EXPOSURE_0 = 100
HDR_EXPOSURE_1 = 1800

SDK_PATH = (
    "/home/marques/Tese/AArch64/"
    "ScepterSDK/Lib/libScepter_api.so"
)


# ============================================================
# DLL
# ============================================================

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
# Inicializar
# ============================================================

ret = lib.scInitialize()

print("scInitialize:", ret)

if ret != 0:
    raise RuntimeError("Falha no scInitialize()")


device = ScDeviceHandle(None)
stream_started = False


try:

    # ========================================================
    # Procurar dispositivos
    # ========================================================

    device_count = ctypes.c_uint32(0)

    start_time = time.time()

    while time.time() - start_time < 20:

        ret = lib.scGetDeviceCount(
            ctypes.byref(device_count),
            ctypes.c_uint32(1000)
        )

        print(
            "scGetDeviceCount:",
            ret,
            "| câmaras:",
            device_count.value
        )

        if ret != 0:
            raise RuntimeError(
                "Falha ao procurar dispositivos"
            )

        if device_count.value > 0:
            break


    if device_count.value == 0:
        raise RuntimeError(
            "Nenhuma câmara encontrada"
        )


    # ========================================================
    # Obter informação
    # ========================================================

    devices = (
        ScDeviceInfo *
        device_count.value
    )()

    ret = lib.scGetDeviceInfoList(
        device_count.value,
        devices
    )

    print()
    print("scGetDeviceInfoList:", ret)

    if ret != 0:
        raise RuntimeError(
            "Falha ao obter informação dos dispositivos"
        )


    device_info = devices[0]

    product = (
        device_info.productName
        .decode(errors="ignore")
        .rstrip("\x00")
    )

    serial = (
        device_info.serialNumber
        .decode(errors="ignore")
        .rstrip("\x00")
    )

    ip = (
        device_info.ip
        .decode(errors="ignore")
        .rstrip("\x00")
    )


    print()
    print("Câmara")
    print("--------------------")
    print("Produto:", product)
    print("Serial:", serial)
    print("IP:", ip)
    print("Estado:", device_info.status)


    # ========================================================
    # Abrir dispositivo
    # ========================================================

    print()
    print("A abrir câmara...")

    ret = lib.scOpenDeviceBySN(
        serial.encode(),
        ctypes.byref(device)
    )

    print("scOpenDeviceBySN:", ret)
    print("Device handle:", device)

    if ret != 0 or not device:
        raise RuntimeError(
            "Falha ao abrir a câmara"
        )

    print("Câmara aberta com sucesso!")


    # ========================================================
    # Iniciar stream
    # ========================================================

    ret = lib.scStartStream(device)

    print("scStartStream:", ret)

    if ret != 0:
        raise RuntimeError(
            "Falha ao iniciar o stream"
        )

    stream_started = True


    # ========================================================
    # Estado atual do HDR
    # ========================================================

    hdr_enabled = ctypes.c_bool(False)

    ret = lib.scGetHDRModeEnabled(
        device,
        ctypes.byref(hdr_enabled)
    )

    print()
    print("scGetHDRModeEnabled:", ret)
    print("HDR ativo:", hdr_enabled.value)

    if ret != 0:
        raise RuntimeError(
            "Falha ao obter estado do HDR"
        )


    # ========================================================
    # Ativar HDR
    # ========================================================

    if not hdr_enabled.value:

        ret = lib.scSetHDRModeEnabled(
            device,
            ctypes.c_bool(True)
        )

        print(
            "scSetHDRModeEnabled:",
            ret
        )

        if ret != 0:
            raise RuntimeError(
                "Falha ao ativar o HDR"
            )


    # ========================================================
    # Confirmar HDR
    # ========================================================

    hdr_enabled = ctypes.c_bool(False)

    ret = lib.scGetHDRModeEnabled(
        device,
        ctypes.byref(hdr_enabled)
    )

    print(
        "HDR ativo depois de ativar:",
        hdr_enabled.value
    )

    if ret != 0 or not hdr_enabled.value:
        raise RuntimeError(
            "Não foi possível ativar o HDR"
        )


    # ========================================================
    # Número de frames HDR
    # ========================================================

    frame_count = ctypes.c_int32(0)

    ret = lib.scGetFrameCountOfHDRMode(
        device,
        ctypes.byref(frame_count)
    )

    print()
    print("scGetFrameCountOfHDRMode:", ret)
    print(
        "Número de frames HDR:",
        frame_count.value
    )

    if ret != 0:
        raise RuntimeError(
            "Falha ao obter número de frames HDR"
        )


    # ========================================================
    # Definir exposições
    # ========================================================

    ret = lib.scSetExposureTimeOfHDR(
        device,
        ctypes.c_uint8(0),
        ctypes.c_int32(HDR_EXPOSURE_0)
    )

    print(
        f"Frame 0 ({HDR_EXPOSURE_0} us):",
        ret
    )

    if ret != 0:
        raise RuntimeError(
            "Falha ao definir exposição do frame 0"
        )


    ret = lib.scSetExposureTimeOfHDR(
        device,
        ctypes.c_uint8(1),
        ctypes.c_int32(HDR_EXPOSURE_1)
    )

    print(
        f"Frame 1 ({HDR_EXPOSURE_1} us):",
        ret
    )

    if ret != 0:
        raise RuntimeError(
            "Falha ao definir exposição do frame 1"
        )


    # ========================================================
    # Confirmar exposições
    # ========================================================

    print()
    print("Configuração HDR")
    print("=================")

    for frame_index in range(2):

        exposure = ctypes.c_int32(-1)

        ret = lib.scGetExposureTimeOfHDR(
            device,
            ctypes.c_uint8(frame_index),
            ctypes.byref(exposure)
        )

        print(
            f"Frame {frame_index}:",
            exposure.value,
            "us | resultado:",
            ret
        )

        if ret != 0:
            raise RuntimeError(
                f"Falha ao obter exposição do frame {frame_index}"
            )


    print()
    print("HDR configurado com sucesso!")


finally:

    # ========================================================
    # Parar stream
    # ========================================================

    if stream_started and device:

        ret = lib.scStopStream(device)

        print()
        print("scStopStream:", ret)


    # ========================================================
    # Fechar dispositivo
    # ========================================================

    if device:

        ret = lib.scCloseDevice(
            ctypes.byref(device)
        )

        print("scCloseDevice:", ret)


    # ========================================================
    # Shutdown
    # ========================================================

    ret = lib.scShutdown()

    print("scShutdown:", ret)
