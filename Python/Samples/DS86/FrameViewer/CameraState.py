class CameraState:
    def __init__(self):
        self.camera = None
        self.status = None
        self.colorSlope = 1500
        self.exposureTime = 700
        self.cx = 0
        self.cy = 0
        self.fx = 0
        self.fy = 0

camState = CameraState()