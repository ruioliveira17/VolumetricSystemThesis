class FilterState:
    def __init__(self):
        self.flyingPixelFilter = None
        self.fillHoleFilter = None
        self.spatialFilter = None
        self.confidenceFilter = None

filterState = FilterState()