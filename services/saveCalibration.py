import cv2
import os
import json
import numpy

from FrameState import frameState
from CameraState import camState
from WorkspaceState import workspaceState
from MaskState import maskState

def save_WS_calibration():
    cv2.imwrite("config/calibrationColorFrame.png", frameState.calibrationColorFrame)
    numpy.save("config/calibrationDepthFrame.npy", frameState.calibrationDepthFrame)

    data = {
        "detection_area": workspaceState.detection_area.tolist() if isinstance(workspaceState.detection_area, numpy.ndarray) else workspaceState.detection_area,
        "workspace_warning": workspaceState.workspace_warning.tolist() if isinstance(workspaceState.workspace_warning, numpy.ndarray) else workspaceState.workspace_warning,
        "workspace_depth": float(workspaceState.workspace_depth),
        "hmin": int(maskState.hmin),
        "hmax": int(maskState.hmax),
        "smin": int(maskState.smin),
        "smax": int(maskState.smax),
        "vmin": int(maskState.vmin),
        "vmax": int(maskState.vmax),
        "color": maskState.color,
        "colorSlope": int(camState.colorSlope),
        "exposureTime": int(camState.exposureTime),
        "calibrationColorFrame_path": "config/calibrationColorFrame.png",
        "calibrationDepthFrame_path": "config/calibrationDepthFrame.npy"
    }

    os.makedirs("config", exist_ok=True)

    with open("config/workspace_calibration.json", "w") as f:
        json.dump(data, f, indent=4)