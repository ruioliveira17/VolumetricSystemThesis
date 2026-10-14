import logging
import os

logger = logging.getLogger("qubic.camera")

def create_camera():
    camera_type = os.getenv("CAMERA_TYPE", "vzense")

    if camera_type == "vzense":
        from .vzense import VzenseCamera
        return VzenseCamera()

    logger.error("Unsupported camera type: '%s'", camera_type)

    raise ValueError(
        f"Unsupported or missing CAMERA_TYPE: {camera_type}"
    )