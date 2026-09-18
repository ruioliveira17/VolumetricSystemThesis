import os

from .vzense import VzenseCamera

def create_camera():
    camera_type = os.getenv("CAMERA_TYPE", "vzense")

    if camera_type == "vzense":
        return VzenseCamera()

    raise ValueError("Unsupported camera")