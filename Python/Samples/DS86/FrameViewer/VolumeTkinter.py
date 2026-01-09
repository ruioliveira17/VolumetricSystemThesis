from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2

def volumeAPI(box_ws, width, height, workspace_depth, minimum_depth):
    volume = 0
    width_meters = 0
    height_meters = 0
    i = 0

    if box_ws is not None and len(box_ws) > 0:
        while i < len(box_ws):
            ws_lim = box_ws[i]
            width_meters = width * 0.27 / (ws_lim[2] - ws_lim[0])
            height_meters = height * 0.367 / (ws_lim[3] - ws_lim[1])
            i += 1
        i = 0

        if width_meters < 0:
            width_meters = 0

        if height_meters < 0:
            height_meters = 0
        
        print(f"Width:  {(width_meters * 100):.1f} cm")
        print(f"Height:  {(height_meters * 100):.1f} cm")
        print("Workspace Depth",workspace_depth)
        print("Minimum Depth:", minimum_depth)

        volume = width_meters * height_meters * ((workspace_depth - minimum_depth) / 1000)

        print(f"Volume Total:  {volume} m^3")

    return volume, width_meters, height_meters, minimum_depth