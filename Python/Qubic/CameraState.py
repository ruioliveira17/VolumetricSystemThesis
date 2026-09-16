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

        self.hdrIndex = 0

camState = CameraState()