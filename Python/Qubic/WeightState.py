class WeightState:
    def __init__(self):
        self.weight = {
                        "prefix": None,
                        "weight": 0,
                        "flags": {
                            "stable": False,
                            "tare": False,
                            "zero": False,
                            "negative": False,
                            "min_weight": False,
                            "fixed_tare": False,
                            "adc_error": False,
                        }
                    }
                        
weightState = WeightState()