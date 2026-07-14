class VolumeState:
    def __init__(self):
        self.width = 0
        self.box_limits = None
        self.box_ws = None
        self.ws_limits = None
        self.depths = None
        self.width_meters = 0
        self.length_meters = 0
        self.height_meters = 0
        self.obj_center = 0
        self.obj_angles = 0
        self.objOverlappedHeights = 0
        self.objContours = 0
        self.volume = 0
        self.objects_outOfLine = []
        self.countdown = 3
        self.cropWindow = {"x": 0, "y": 0, "width": 1600, "height": 1200}
        self.cropArea = {"x": 15, "y": 15, "width": 1570, "height": 1170}
        self.click_timestamp = None
        self.hdrFinished = False
        self.united_contours = None
        self.processing = ""

volumeState = VolumeState()