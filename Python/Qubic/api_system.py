import logging
import subprocess

from fastapi import APIRouter, Depends

from api_auth import get_current_user

from CameraOptions import stopCamera

logger = logging.getLogger("qubic.system")

router = APIRouter(
    prefix="/system",
    tags=["System"]
)

@router.post("/shutdown")
def shutdown_system(current_user=Depends(get_current_user)):
    logger.info("Shutdown requested")
    stopCamera()

    subprocess.Popen(["sudo", "systemctl", "poweroff"])

    return {"message": "System shutdown initiated"}


@router.post("/restart")
def restart_system(current_user=Depends(get_current_user)):
    logger.info("Restart requested")
    stopCamera()
    
    subprocess.Popen(["sudo", "systemctl", "reboot"])

    return {"message": "System restart initiated"}