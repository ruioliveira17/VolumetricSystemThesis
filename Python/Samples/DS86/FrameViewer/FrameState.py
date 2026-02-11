class FrameState:
    def __init__(self):
        self.colorToDepthFrame = None
        self.depthFrame = None 
        self.colorFrame = None
        self.colorToDepthFrameCopy = None
        self.depthFrameCopy = None
        self.res = None
        self.colorToDepthFrameObject = None
        self.colorFrameHDR = None
        self.colorToDepthFrameHDR = None
        self.depthFrameHDR = None
frameState = FrameState()