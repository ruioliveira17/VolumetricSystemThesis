import os, sys
os.add_dll_directory(r"C:\Tese\ScepterSDK\BaseSDK\Windows\Bin\x64")
sys.path.append("ScepterSDK/MultilanguageSDK/Python/API")
from ScepterDS_api import *

cam = ScepterTofCam()
cam.scInitialize()

count = cam.scGetDeviceCount(3000)
print(f"Câmaras encontradas: {count}")

# Abre diretamente pelo IP
ret = cam.scOpenDeviceByIP(b"10.0.30.228")
print(f"scOpenDeviceByIP ret={ret}")