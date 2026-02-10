from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *

from CameraState import camState
from FrameState import frameState

#import cv2

def getFrame(camera):
    colorToDepthFrame = None
    depthFrame = None 
    colorFrame = None

    ret, frameready = camera.VZ_GetFrameReady(c_uint16(1200))
    if  ret !=0:
        print("VZ_GetFrameReady failed:",ret)
    else:
        hasColorToDepth =0
        hasDepth = 0
        hasColor = 0

        if  frameready.color:      
            ret,rgbframe = camera.VZ_GetFrame(VzFrameType.VzTransformColorImgToDepthSensorFrame)
            if  ret == 0:
                hasColorToDepth = 1   
            else:
                print("get color frame failed:",ret)

        if  frameready.depth:      
            ret,depthframe = camera.VZ_GetFrame(VzFrameType.VzDepthFrame)
            if  ret == 0:
                hasDepth = 1
            else:
                print("get depth frame failed:",ret)

        if frameready.color:
            ret,colorframe = camera.VZ_GetFrame(VzFrameType.VzColorFrame)
            if ret == 0:
                hasColor = 1
            else:
                print("get Color frame failed:", ret)

        if hasColorToDepth == 1:
            frametmp = numpy.empty((0, 0, 3), dtype=numpy.uint8)
            frametmp = numpy.ctypeslib.as_array(rgbframe.pFrameData, (1, rgbframe.width * rgbframe.height * 3))
            frametmp.dtype = numpy.uint8
            frametmp.shape = (rgbframe.height, rgbframe.width,3)
            colorToDepthFrame = frametmp.copy()

        if hasDepth == 1:
            frametmp = numpy.empty((0, 0, 3), dtype=numpy.uint8)
            frametmp = numpy.ctypeslib.as_array(depthframe.pFrameData, (1, depthframe.width * depthframe.height * 2))
            frametmp.dtype = numpy.uint16
            frametmp.shape = (depthframe.height, depthframe.width)
            depthFrame = frametmp.copy()

        if hasColor == 1:
            frametmp = numpy.ctypeslib.as_array(colorframe.pFrameData, (1, colorframe.width * colorframe.height * 3))
            frametmp.dtype = numpy.uint8
            frametmp.shape = (colorframe.height, colorframe.width,3)
            colorFrame = frametmp.copy()
            #colorFrame = cv2.resize(colorFrame, (640, 480))
            #cv2.circle(colorFrame, (int(800/2.5), int(608/2.5)), radius=3, color=(255, 0, 0), thickness=1)

        if hasColorToDepth == 1 and hasDepth == 1 and hasColor == 1:
            frameState.colorToDepthFrame = colorToDepthFrame
            frameState.depthFrame = depthFrame
            frameState.colorFrame = colorFrame
            