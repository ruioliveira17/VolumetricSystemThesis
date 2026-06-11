import uvicorn
import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "Python"))
from API.VzenseDS_api import *

sys.path.append(os.path.join(BASE_DIR, "Python", "Samples", "DS86", "FrameViewer"))

if __name__ == "__main__":
    subprocess.run(["/usr/bin/pkill", "-f", "vite"], capture_output=True)
    frontend_dir = os.path.join(BASE_DIR, "frontend")
    subprocess.Popen(
        ["/usr/bin/npm", "run", "dev", "--", "--host", "0.0.0.0"],
        cwd=frontend_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    uvicorn.run("api:app", host="0.0.0.0", port=8000, log_level="info")