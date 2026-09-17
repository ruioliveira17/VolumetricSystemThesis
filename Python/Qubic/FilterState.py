class FilterState:
    def __init__(self):
        self.flyingPixelFilter = True
        self.fillHoleFilter = True
        self.spatialFilter = True
        self.confidenceFilter = False

filterState = FilterState()