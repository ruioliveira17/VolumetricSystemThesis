from fastapi import Depends
from pathlib import Path

from fastapi import APIRouter

from api_auth import get_current_user, get_password_change_user, require_admin

router = APIRouter(prefix="/system")

VERSION_FILE = Path(__file__).resolve().parent.parent.parent / "version.txt"

@router.get("/version")
def get_version(current_user: dict = Depends(get_current_user)):
    return {
        "version": VERSION_FILE.read_text().strip()
    }