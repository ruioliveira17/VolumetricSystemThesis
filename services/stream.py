import asyncio
import numpy
import time
import cv2

from aiortc import VideoStreamTrack
from aiortc.mediastreams import MediaStreamError
from av import VideoFrame

from FrameState import frameState
from CameraState import camState
from ModeState import modeState

FRAME_WAIT_TIMEOUT = 5.0

async def _wait_for_frame(get_frame):
    """
    Espera por um frame sem bloquear o event loop.
    Levanta MediaStreamError se não aparecer nenhum dentro do tempo limite,
    o que termina o track em vez de o deixar em ciclo infinito.
    """
    deadline = time.monotonic() + FRAME_WAIT_TIMEOUT
    frame = get_frame()

    while frame is None:
        if time.monotonic() > deadline:
            raise MediaStreamError("Sem frames da câmara")

        await asyncio.sleep(0.05)
        frame = get_frame()

    return frame

class CameraTrack(VideoStreamTrack):
    async def recv(self):
        frame = await _wait_for_frame(lambda: frameState.colorFrame)

        if frame.dtype != numpy.uint8:
            frame = (numpy.clip(frame, 0, 1) * 255).astype(numpy.uint8)

        return VideoFrame.from_ndarray(frame, format='bgr24')
    
class CTDTrack(VideoStreamTrack):
    async def recv(self):
        if modeState.calibrationMode == "Automatic":
            frame = await _wait_for_frame(lambda: frameState.workspaceDetectedFrame)

        if modeState.calibrationMode == "Manual":
            if camState.hdrEnabled:
                frame = await _wait_for_frame(lambda: frameState.colorToDepthFrameHDR)
            else:
                frame = await _wait_for_frame(lambda: frameState.colorToDepthFrame)
            
            if frame.dtype != numpy.uint8:
                frame = (numpy.clip(frame, 0, 1) * 255).astype(numpy.uint8)

        return VideoFrame.from_ndarray(frame, format='bgr24')

def generateRGB_Stream():
    while True:
        frame = frameState.colorFrame
        if frame is not None:
            if frame.dtype != numpy.uint8:
                frame = (numpy.clip(frame, 0, 1) * 255).astype(numpy.uint8)
            _, jpeg = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(0.05)

def generateDepth_Stream():
    while True:
        if camState.hdrEnabled and frameState.depthFrameHDR is not None:
            depth = frameState.depthFrameHDR
        elif not camState.hdrEnabled:
            depth = frameState.depthFrame
        if depth is not None:
            img = numpy.int32(depth)
            img = img * 255 / camState.colorSlope
            img = numpy.clip(img, 0, 255).astype(numpy.uint8)
            depth_vis = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)
            _, jpeg = cv2.imencode('.jpg', depth_vis)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(0.05)

def generateCalibrationCTD_Stream():
    while True:
        if modeState.calibrationMode == "Automatic":
            frame = frameState.workspaceDetectedFrame
            if frame is not None:
                if frame.dtype != numpy.uint8:
                    frame = (numpy.clip(frame, 0, 1) * 255).astype(numpy.uint8)
                _, jpeg = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.05)
        if modeState.calibrationMode == "Manual":
            if camState.hdrEnabled and frameState.colorToDepthFrameHDR is not None:
                frame = frameState.colorToDepthFrameHDR
            elif not camState.hdrEnabled:
                frame = frameState.colorToDepthFrame
            if frame is not None:
                if frame.dtype != numpy.uint8:
                    frame = (numpy.clip(frame, 0, 1) * 255).astype(numpy.uint8)
                _, jpeg = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.05)

def generateCalibrationMask_Stream():
    while True:
        frame = frameState.maskFrame
        if frame is not None:
            if frame.dtype != numpy.uint8:
                frame = (numpy.clip(frame, 0, 1) * 255).astype(numpy.uint8)
            _, jpeg = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(0.05)