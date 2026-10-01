from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/system")

VERSION_FILE = Path(__file__).resolve().parent.parent.parent / "version.txt"

@router.get("/version")
def get_version():
    return {
        "version": VERSION_FILE.read_text().strip()
    }