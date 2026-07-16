from CameraState import camState
from FilterState import filterState
from ModeState import modeState
from VolumeState import volumeState

from db.config_repo import save_last_configuration

def save_configuration():
    data = {
        "expositionMode":    modeState.expositionMode,
        "volumeMode":        modeState.volumeMode,
        "calibrationMode":   modeState.calibrationMode,
        "speedMode":         modeState.speedMode,
        "workingMode":       modeState.mode,
        "debugMode":         modeState.debugMode,
        "exposureTime":      int(camState.exposureTime),
        "fps":               int(camState.fps),
        "flyingPixelFilter": bool(filterState.flyingPixelFilter) if filterState.flyingPixelFilter is not None else True,
        "fillHoleFilter":    bool(filterState.fillHoleFilter)    if filterState.fillHoleFilter    is not None else True,
        "spatialFilter":     bool(filterState.spatialFilter)     if filterState.spatialFilter     is not None else True,
        "confidenceFilter":  bool(filterState.confidenceFilter)  if filterState.confidenceFilter  is not None else False,
        "cropWindow":        volumeState.cropWindow.model_dump(),
        "cropArea":          volumeState.cropArea.model_dump(),
        "countdown":         volumeState.countdown,
    }

    save_last_configuration(data)