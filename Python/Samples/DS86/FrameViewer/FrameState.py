class FrameState:
    def __init__(self):
        self.colorToDepthFrame = None
        self.depthFrame = None 
        self.colorFrame = None
        self.workspaceDetectedFrame = None
        self.depthFrameCopy = None
        self.maskFrame = None
        self.detectedObjectsFrame = None
        self.colorFrameHDR = None
        self.colorToDepthFrameHDR = None
        self.depthFrameHDR = None
        self.calibrationColorFrame = None
frameState = FrameState()