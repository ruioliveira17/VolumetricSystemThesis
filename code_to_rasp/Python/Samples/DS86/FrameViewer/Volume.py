from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2

def volume_calc(box_ws, box_limits, bundle_xmin, bundle_xmax, bundle_ymin, bundle_ymax):

    i = 0
    contour = 0
    ws_lim = 0

    if len(box_ws) > 0:
        while i < len(box_ws):
            contour = box_limits[i]
            ws_lim = box_ws[i]

            if not contour:
                i += 1
                continue

            for arr in contour:
                xs = arr[:, 0, 0]
                ys = arr[:, 0, 1]

            xmin = xs.min()
            xmax = xs.max()
            ymin = ys.min()
            ymax = ys.max()

            xmin_meters = (xmin - ws_lim[0]) * 0.27 / (ws_lim[2] - ws_lim[0])
            xmax_meters = (xmax - ws_lim[0]) * 0.27 / (ws_lim[2] - ws_lim[0])

            ymin_meters = (ymin - ws_lim[1]) * 0.367 / (ws_lim[3] - ws_lim[1])
            ymax_meters = (ymax - ws_lim[1]) * 0.367 / (ws_lim[3] - ws_lim[1])

            if xmin_meters < bundle_xmin:
                bundle_xmin = xmin_meters

            if ymin_meters < bundle_ymin:
                bundle_ymin = ymin_meters

            if xmax_meters > bundle_xmax:
                bundle_xmax = xmax_meters

            if ymax_meters > bundle_ymax:
                bundle_ymax = ymax_meters

            i += 1
        i = 0
                    
    return bundle_xmin, bundle_xmax, bundle_ymin, bundle_ymax