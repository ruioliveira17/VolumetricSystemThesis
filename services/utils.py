import numpy
import cv2

def rgb_to_hsv(r, g, b):
    rgb = numpy.uint8([[[r, g, b]]])
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    return hsv[0][0].tolist()