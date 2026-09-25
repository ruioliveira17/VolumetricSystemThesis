import subprocess

from fastapi import APIRouter, Depends

from api_auth import get_current_user

from CameraOptions import stopCamera

router = APIRouter(
    prefix="/system",
    tags=["System"]
)

@router.post("/shutdown")
def shutdown_system(current_user=Depends(get_current_user)):
    stopCamera()

    subprocess.Popen(["sudo", "systemctl", "poweroff"])

    return {"message": "System shutdown initiated"}


@router.post("/restart")
def restart_system(current_user=Depends(get_current_user)):
    stopCamera()

    subprocess.Popen(["sudo", "systemctl", "reboot"])

    return {"message": "System restart initiated"}