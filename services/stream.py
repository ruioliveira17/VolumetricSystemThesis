import asyncio
import numpy
import time
import cv2

from aiortc import VideoStreamTrack
from av import VideoFrame

from FrameState import frameState
from CameraState import camState

class CameraTrack(VideoStreamTrack):
    async def recv(self):
        frame = frameState.colorFrame
        if frame is None:
            await asyncio.sleep(0.05)
            return await self.recv()
        else:
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
        frame = frameState.workspaceDetectedFrame
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