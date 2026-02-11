class CameraState:
    def __init__(self):
        self.camera = None
        self.status = None
        self.colorSlope = 1500
        self.exposureTime = 700
        self.cx_d = 0
        self.cy_d = 0
        self.fx_d = 0
        self.fy_d = 0
        self.cx_rgb = 0
        self.cy_rgb = 0
        self.fx_rgb = 0
        self.fy_rgb = 0


camState = CameraState()