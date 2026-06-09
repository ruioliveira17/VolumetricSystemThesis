#class CameraState:
#    def __init__(self):
#        self.camera = None
#        self.status = None
#        self.colorSlope = 4100
#        self.exposureTime = 700
#        self.cx_d = 0
#        self.cy_d = 0
#        self.fx_d = 0
#        self.fy_d = 0
#        self.cx_rgb = 0
#        self.cy_rgb = 0
#        self.fx_rgb = 0
#        self.fy_rgb = 0


#camState = CameraState()

import threading

class CameraState:
    def __init__(self):
        self.camera = None
        #self.target_fps = fps
        #self._frame_interval = 1.0 / fps

        #self._lock = threading.Lock()

        self._running = False
        self._thread = None

        self.colorSlope = 4100
        self.exposureTime = 4000
        self.fps = 10
        self.cx_d = 0
        self.cy_d = 0
        self.fx_d = 0
        self.fy_d = 0
        self.cx_rgb = 0
        self.cy_rgb = 0
        self.fx_rgb = 0
        self.fy_rgb = 0

        self.hdrEnabled = True
        self.hdrExposuresLow    = [360, 525, 690, 855]
        self.hdrExposuresMedium = [855, 1020, 1185, 1350]
        #self.hdrExposuresLow = [30, 471, 942, 1353]
        #self.hdrExposuresMedium = [1700, 2030, 2360, 2700]
        #self.hdrExposuresHigh = [3040, 3370, 3710, 4000]
        self.hdrExposures = [30, 300, 824, 2412, 4000]
        #self.hdrExposures = [200, 675, 1150, 1625, 2100, 2575, 3050, 3525, 4000]
        #self.hdrExposures = [200, 2100, 4000]
        self.hdrIndex = 0

camState = CameraState()