from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2

def volumeAPI(box_ws, width, height, workspace_depth, minimum_depth, box_limits, fx, fy):
    volume = 0
    width_meters = 0
    height_meters = 0
    i = 0

    xs = box_limits[:, 0, 0]
    ys = box_limits[:, 0, 1]

    xmin = xs.min()
    xmax = xs.max()
    ymin = ys.min()
    ymax = ys.max()

    wid = xmax - xmin
    hei = ymax - ymin

    if box_ws is not None and len(box_ws) > 0:
        print(len(box_ws))
        while i < len(box_ws):
            ws_lim = box_ws[i]
            if wid > hei:
                #width_meters = width * 0.27 / (ws_lim[2] - ws_lim[0])
                width_meters = width * (minimum_depth / 1000.0) / fx
                print("Width:", width_meters, "Width Pixels:", width, "WS Limits:", ws_lim[0], ws_lim[2])
                height_meters = height * (minimum_depth / 1000.0) / fy
                #height_meters = height * 0.37 / (ws_lim[3] - ws_lim[1])
                print("Height:", height_meters, "Height Pixels:", height, "WS Limits:", ws_lim[1], ws_lim[3])
            if hei > wid:
                #width_meters = height * 0.27 / (ws_lim[2] - ws_lim[0])
                width_meters = height * (minimum_depth / 1000.0) / fx
                print("Width:", width_meters, "Width Pixels:", height, "WS Limits:", ws_lim[0], ws_lim[2])
                #height_meters = width * 0.37 / (ws_lim[3] - ws_lim[1])
                height_meters = width * (minimum_depth / 1000.0) / fy
                print("Height:", height_meters, "Height Pixels:", width, "WS Limits:", ws_lim[1], ws_lim[3])
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