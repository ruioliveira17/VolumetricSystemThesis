class CameraState:
    def __init__(self):
        self.camera = None

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

        self.flyingPixelFilter = True
        self.fillHoleFilter = True
        self.spatialFilter = True
        self.confidenceFilter = False

        self.hdrEnabled = True

        self.hdrExposuresLow_Fast = [30, 525]
        self.hdrExposuresLow_Intermedium = [30, 195, 360, 525]
        self.hdrExposuresLow_Slow = [30, 129, 228, 327, 426, 525]
        self.hdrExposuresMedium_Fast = [690, 1185]
        self.hdrExposuresMedium_Intermedium = [690, 855, 1020, 1185]
        self.hdrExposuresMedium_Slow = [690, 789, 888, 987, 1086, 1185]

        self.hdrIndex = 0

camState = CameraState()