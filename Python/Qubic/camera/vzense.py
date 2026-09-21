import ctypes
import numpy
import time

from .camera import Camera
from ScepterSDK import *

class VzenseCamera(Camera):

    def __init__(self):
        self._handle = ScDeviceHandle()

    def start(self):
        ret = lib.scInitialize()
        print("scInitialize:", ret)

        if ret != 0:
            raise RuntimeError("Failed to initialize Scepter SDK!")

        camera_count = ctypes.c_uint32(0)
        retry_count = 20

        while camera_count.value==0 and retry_count > 0:
            ret = lib.scGetDeviceCount(ctypes.byref(camera_count), 1000)

            print(
                "scGetDeviceCount:",
                ret,
                "| câmaras:",
                camera_count.value
            )

            if camera_count.value == 0:
                retry_count -= 1
                time.sleep(1)
                print("Scanning......   ", retry_count)

        if camera_count.value == 0:
            print("There are no cameras found")
            lib.scShutdown()
            raise RuntimeError("No camera detected")

        device_info_list = (ScDeviceInfo * camera_count.value)()

        print("ANTES scGetDeviceInfoList")

        ret = lib.scGetDeviceInfoList(
            camera_count.value,
            device_info_list
        )

        print("DEPOIS scGetDeviceInfoList:", ret)

        if ret != 0:
            lib.scShutdown()
            raise RuntimeError("Failed to get camera information!")

        device_info = device_info_list[0]

        print("Camera")
        print("--------------------")
        print("Product:", device_info.productName.decode(errors="ignore"))
        print("Serial:", device_info.serialNumber.decode(errors="ignore"))
        print("IP:", device_info.ip.decode(errors="ignore"))
        print("Status:", device_info.status)

        serial = device_info.serialNumber

        print("Opening camera...")
        ret = lib.scOpenDeviceBySN(
            serial,
            ctypes.byref(self._handle)
        )

        print("scOpenDeviceBySN:", ret)

        if ret != 0:
            lib.scShutdown()
            raise RuntimeError("Failed to open camera")

        print("Device handle:", self._handle)
        print("Camera opened successfully!")

        # Iniciar stream
        ret = lib.scStartStream(self._handle)
        print("scStartStream:", ret)

        if ret != 0:
            lib.scCloseDevice(ctypes.byref(self._handle))
            self._handle = None
            lib.scShutdown()
            raise RuntimeError("Failed to start camera stream!")

        params = ScTimeFilterParams()

        ret = lib.scGetTimeFilterParams(
            self._handle,
            ctypes.byref(params)
        )

        if ret == 0:
            print("The default TimeFilter switch is " + str(params.enable))
        else:
            print("scGetTimeFilterParams failed:" + str(ret))

        params.enable = True

        ret = lib.scSetTimeFilterParams(
            self._handle,
            params
        )

        if ret == 0:
            print(
                "Set TimeFilter switch to "
                + str(params.enable)
                + " is Ok"
            )
        else:
            print(
                "scSetTimeFilterParams failed:"
                + str(ret)
            )

        # Definir modo de exposição manual
        ret = lib.scSetExposureControlMode(
            self._handle,
            0x01,  # SC_TOF_SENSOR
            1      # SC_EXPOSURE_CONTROL_MODE_MANUAL
        )

        if ret == 0:
            print("Set exposure control mode to manual is ok")
        else:
            print("scSetExposureControlMode failed:", ret)

        # Ativar transformação Color -> Depth
        ret = lib.scSetTransformColorImgToDepthSensorEnabled(
            self._handle,
            True
        )

        if ret == 0:
            print("scSetTransformColorImgToDepthSensorEnabled ok")
        else:
            print(
                "scSetTransformColorImgToDepthSensorEnabled failed:",
                ret
            )

    def stop(self):
        ret = lib.scStopStream(self._handle)    
        if  ret == 0:
            print("stop stream successful")
        else:
            print('VZ_StopStream failed: ' + str(ret))  

        ret = lib.scCloseDevice(
            ctypes.byref(self._handle)
        ) 
        if  ret == 0:
            self._handle = None
            return True
        else:
            return False

    def get_frames(self):
        frameReady = ScFrameReady()

        ret = lib.scGetFrameReady(
            self._handle,
            ctypes.c_uint16(33),
            ctypes.byref(frameReady)
        )

        if ret != 0:
            return None

        colorToDepthFrame = None
        depthFrame = None
        colorFrame = None

        if frameReady.transformedColor:
            rgbFrame = ScFrame()

            ret = lib.scGetFrame(
                self._handle,
                4,
                ctypes.byref(rgbFrame)
            )

            if ret == 0:
                frametmp = numpy.ctypeslib.as_array(
                    rgbFrame.pFrameData,
                    (rgbFrame.width * rgbFrame.height * 3,)
                )

                frametmp.dtype = numpy.uint8
                frametmp.shape = (
                    rgbFrame.height,
                    rgbFrame.width,
                    3
                )

                colorToDepthFrame = frametmp.copy()

        if frameReady.depth:
            depthFrameRaw = ScFrame()

            ret = lib.scGetFrame(
                self._handle,
                0,
                ctypes.byref(depthFrameRaw)
            )

            if ret == 0:
                frametmp = numpy.ctypeslib.as_array(
                    depthFrameRaw.pFrameData,
                    (depthFrameRaw.width * depthFrameRaw.height * 2,)
                )

                frametmp.dtype = numpy.uint16
                frametmp.shape = (
                    depthFrameRaw.height,
                    depthFrameRaw.width
                )

                depthFrame = frametmp.copy()

        if frameReady.color:
            colorFrameRaw = ScFrame()

            ret = lib.scGetFrame(
                self._handle,
                3,
                ctypes.byref(colorFrameRaw)
            )

            if ret == 0:
                frametmp = numpy.ctypeslib.as_array(
                    colorFrameRaw.pFrameData,
                    (colorFrameRaw.width * colorFrameRaw.height * 3,)
                )

                frametmp.dtype = numpy.uint8
                frametmp.shape = (
                    colorFrameRaw.height,
                    colorFrameRaw.width,
                    3
                )

                colorFrame = frametmp.copy()

        if (
            colorToDepthFrame is not None
            and depthFrame is not None
            and colorFrame is not None
        ):
            return {
                "colorToDepth": colorToDepthFrame,
                "depth": depthFrame,
                "color": colorFrame
            }

        return None

    def set_fps(self, fps):
        ret = lib.scSetFrameRate(
            self._handle,
            ctypes.c_int32(fps)
        )
        if  ret == 0:
            print("Set frame rate is ok")   
        else:
            raise RuntimeError(
                f"scSetFrameRate failed: {ret}"
            )
    
        frameRate = ctypes.c_int32()
    
        ret = lib.scGetFrameRate(
            self._handle,
            ctypes.byref(frameRate)
        )
    
        if  ret == 0:
            print("Get default frame rate:"+ str(frameRate.value))   
        else:
            raise RuntimeError(
                f"scGetFrameRate failed: {ret}"
            )

        return frameRate.value

    def set_exposure_time(self, value):
        ret = lib.scSetExposureTime(
            self._handle,
            0x01,  # SC_TOF_SENSOR
            ctypes.c_int32(value)
        )

        if ret != 0:
            raise RuntimeError(
                f"scSetExposureTime failed: {ret}"
            )

    def set_enable_hdr(self, value):
        ret = lib.scSetHDRModeEnabled(
            self._handle,
            value
        )
    
        if ret != 0:
            raise RuntimeError(
                f"scSetHDRModeEnabled failed: {ret}"
            )

    def set_hdr_interval(self, low, high):
        ret = lib.scSetExposureTimeOfHDR(self._handle, 0, low)
        if ret != 0:
            raise RuntimeError(
                f"scSetExposureTimeOfHDR frame 0 failed: {ret}"
            )
    
        ret = lib.scSetExposureTimeOfHDR(self._handle, 1, high)
        if ret != 0:
            raise RuntimeError(
                f"scSetExposureTimeOfHDR frame 1 failed: {ret}"
            )
        
        print(f"HDR enabled: {low}us to {high}us!")

    def get_depth_intrinsic_parameters(self):
        depthIntrParam = ScSensorIntrinsicParameters()
        
        ret = lib.scGetSensorIntrinsicParameters(
            self._handle,
            0x01,  # SC_TOF_SENSOR
            ctypes.byref(depthIntrParam)
        )

        if ret != 0:
            raise RuntimeError("Error obtaining depth intrinsic parameters!")

        return depthIntrParam

    def get_rgb_intrinsic_parameters(self):
        rgbIntrParam = ScSensorIntrinsicParameters()
        
        ret = lib.scGetSensorIntrinsicParameters(
            self._handle,
            0x02,  # SC_COLOR_SENSOR
            ctypes.byref(rgbIntrParam)
        )

        if ret != 0:
            raise RuntimeError("Error obtaining color intrinsic parameters!")

        return rgbIntrParam

    def set_filter_flying_pixel(self, value):
        params = ScFlyingPixelFilterParams()

        ret = lib.scGetFlyingPixelFilterParams(
            self._handle,
            ctypes.byref(params)
        )

        if  ret == 0:
            print("The default FlyingPixelFilter switch is " + str(params.enable))
        else:
            raise RuntimeError(
                f"scGetFlyingPixelFilterParams failed: {ret}"
            )  

        params.enable = bool(value)

        ret = lib.scSetFlyingPixelFilterParams(
            self._handle,
            params
        )

        if  ret == 0:
            print("Set FlyingPixelFilter switch to "+ str(params.enable) + " is Ok")   
            return params.enable
        else:
            raise RuntimeError(
                f"scSetFlyingPixelFilterParams failed: {ret}"
            )

    def set_filter_fill_hole(self, value):
        enable = ctypes.c_bool()
        
        ret = lib.scGetFillHoleFilterEnabled(
            self._handle,
            ctypes.byref(enable)
        )
    
        if  ret == 0:
            print("The default FillHoleFilter switch is " + str(enable.value))
        else:
            raise RuntimeError(
                f"scGetFillHoleFilterEnabled failed: {ret}"
            )
    
        enable.value = bool(value)
    
        ret = lib.scSetFillHoleFilterEnabled(
            self._handle,
            enable
        )
    
        if  ret == 0:
            print("Set FillHoleFilter switch to "+ str(enable.value) + " is Ok")   
            return enable.value
        else:
            raise RuntimeError(
                f"scSetFillHoleFilterEnabled failed: {ret}"
            )

    def set_filter_spatial(self, value):
        enable = ctypes.c_bool()
        
        ret = lib.scGetSpatialFilterEnabled(
            self._handle,
            ctypes.byref(enable)
        )
    
        if  ret == 0:
            print("The default SpatialFilter switch is " + str(enable.value))
        else:
            raise RuntimeError(
                f"scGetSpatialFilterEnabled failed: {ret}"
            ) 
    
        enable.value = bool(value)
    
        ret = lib.scSetSpatialFilterEnabled(
            self._handle,
            enable
        )
    
        if  ret == 0:
            print("Set SpatialFilter switch to "+ str(enable.value) + " is Ok")   
            return enable.value
        else:
            raise RuntimeError(
                f"scSetSpatialFilterEnabled failed: {ret}"
            )
        
    def set_filter_confidence(self, value):
        params = ScConfidenceFilterParams()
        
        ret = lib.scGetConfidenceFilterParams(
            self._handle,
            ctypes.byref(params)
        )
    
        if  ret == 0:
            print("The default ConfidenceFilter switch is " + str(params.enable))
        else:
            raise RuntimeError(
            f"scGetConfidenceFilterParams failed: {ret}"
        )
    
        params.enable = bool(value)
    
        ret = lib.scSetConfidenceFilterParams(
            self._handle,
            params
        )
    
        if  ret == 0:
            print("Set ConfidenceFilter switch to "+ str(params.enable) + " is Ok")   
            return params.enable
        else:
            raise RuntimeError(
                f"scSetConfidenceFilterParams failed: {ret}"
            )