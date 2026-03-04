class DepthState:
    def __init__(self):
        self.not_set = 1
        self.objects_info = None
        self.threshold = 15
        self.minimum_depth = 0
        self.minimum_value = 6000

depthState = DepthState()