import os
import sys
import cv2
import numpy as np
import threading
import time
from flask import Flask, Response

# --- SDK ---
dll_dir = r"C:\Tese\ScepterSDK\BaseSDK\Windows\Bin\x64"
os.add_dll_directory(dll_dir)
sys.path.append("ScepterSDK/MultilanguageSDK/Python/API")
from ScepterDS_api import *

# --- Flask ---
app = Flask(__name__)

def generate_rgb(cam):
    while True:
        frame = cam.get_rgb()
        if frame is not None:
            _, jpeg = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(0.05)

def generate_depth(cam):
    while True:
        depth = cam.get_depth()
        if depth is not None:
            depth_vis = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            depth_vis = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)
            _, jpeg = cv2.imencode('.jpg', depth_vis)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(0.05)

@app.route('/rgb')
def rgb_feed():
    return Response(generate_rgb(cam), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/depth')
def depth_feed():
    return Response(generate_depth(cam), mimetype='multipart/x-mixed-replace; boundary=frame')


# --- Câmara ---
class CameraStream:
    def __init__(self, ip="10.0.30.228", fps=10):
        self.ip = ip.encode() if isinstance(ip, str) else ip
        self.target_fps = fps
        self._frame_interval = 1.0 / fps

        self.camera = ScepterTofCam()

        self._lock = threading.Lock()
        self._rgb_frame = None
        self._depth_frame = None

        self._running = False
        self._thread = None

    def start(self):
        count = self.camera.scGetDeviceCount(3000)
        print(f"Câmaras encontradas: {count}")

        ret = self.camera.scOpenDeviceByIP(self.ip)
        print(f"scOpenDeviceByIP ret: {ret}")
        if ret != 0:
            raise RuntimeError(f"Erro ao ligar à câmara ({self.ip}), código: {ret}")

        self.camera.scSetFrameRate(self.target_fps)
        self.camera.scStartStream()
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        print(f"[CameraStream] A capturar a {self.target_fps} FPS")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        self.camera.scStopStream()
        self.camera.scCloseDevice()
        print("[CameraStream] Câmara fechada.")

    def set_fps(self, fps):
        self.target_fps = fps
        self._frame_interval = 1.0 / fps
        self.camera.scSetFrameRate(fps)

    def get_rgb(self):
        with self._lock:
            return self._rgb_frame.copy() if self._rgb_frame is not None else None

    def get_depth(self):
        with self._lock:
            return self._depth_frame.copy() if self._depth_frame is not None else None

    def get_both(self):
        with self._lock:
            rgb = self._rgb_frame.copy() if self._rgb_frame is not None else None
            depth = self._depth_frame.copy() if self._depth_frame is not None else None
        return rgb, depth

    def _capture_loop(self):
        while self._running:
            t_start = time.monotonic()

            ret, frameready = self.camera.scGetFrameReady(c_uint16(33))
            if ret != 0:
                continue

            # --- RGB ---
            ret_rgb, rgb_frame = self.camera.scGetFrame(ScFrameType.SC_COLOR_FRAME)
            if ret_rgb == 0 and rgb_frame.pFrameData:
                img = np.ctypeslib.as_array(rgb_frame.pFrameData, shape=(rgb_frame.dataLen,))
                img = img.reshape((rgb_frame.height, rgb_frame.width, 3))
                with self._lock:
                    self._rgb_frame = img.copy()

            # --- Profundidade ---
            ret_d, depth_frame = self.camera.scGetFrame(ScFrameType.SC_DEPTH_FRAME)
            if ret_d == 0 and depth_frame.pFrameData:
                expected = depth_frame.height * depth_frame.width
                d = np.ctypeslib.as_array(depth_frame.pFrameData, shape=(expected,)).astype(np.uint16)
                d = d.reshape((depth_frame.height, depth_frame.width))
                with self._lock:
                    self._depth_frame = d.copy()

            elapsed = time.monotonic() - t_start
            sleep_time = self._frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)


# --- Arranque ---
cam = CameraStream(ip="10.0.30.228", fps=10)
cam.start()

# Flask numa thread separada (não bloqueia o loop principal)
flask_thread = threading.Thread(
    target=lambda: app.run(host='0.0.0.0', port=5000, threaded=True),
    daemon=True
)
flask_thread.start()
print("[Flask] A servir em http://localhost:5000/rgb e /depth")

# --- Loop principal (opcional, podes remover se não quiseres janelas locais) ---
while True:
    rgb, depth = cam.get_both()

    if rgb is not None:
        cv2.imshow("RGB", rgb)

    if depth is not None:
        depth_vis = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        depth_vis = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)
        cv2.imshow("Depth", depth_vis)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.stop()
cv2.destroyAllWindows()