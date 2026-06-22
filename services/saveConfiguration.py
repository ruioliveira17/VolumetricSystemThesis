import os
import json

from CameraState import camState
from FilterState import filterState
from ModeState import modeState
from VolumeState import volumeState

def save_configuration():
    data = {
        "expositionMode":    modeState.expositionMode,
        "volumeMode":        modeState.volumeMode,
        "workingMode":       modeState.mode,
        "debugMode":         modeState.debugMode,
        "exposureTime":      int(camState.exposureTime),
        "fps":               int(camState.fps),
        "flyingPixelFilter": bool(filterState.flyingPixelFilter) if filterState.flyingPixelFilter is not None else True,
        "fillHoleFilter":    bool(filterState.fillHoleFilter)    if filterState.fillHoleFilter    is not None else True,
        "spatialFilter":     bool(filterState.spatialFilter)     if filterState.spatialFilter     is not None else True,
        "confidenceFilter":  bool(filterState.confidenceFilter)  if filterState.confidenceFilter  is not None else False,
        "countdown":         volumeState.countdown,
    }

    os.makedirs("config", exist_ok=True)

    with open("config/last_configurations.json", "w") as f:
        json.dump(data, f, indent=4)
