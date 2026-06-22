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
        self.volume = 0
        self.objects_outOfLine = None
        self.countdown = 3

volumeState = VolumeState()