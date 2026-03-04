import uvicorn
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "Python"))
from API.VzenseDS_api import *

sys.path.append(os.path.join(BASE_DIR, "Python", "Samples", "DS86", "FrameViewer"))

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, log_level="info")