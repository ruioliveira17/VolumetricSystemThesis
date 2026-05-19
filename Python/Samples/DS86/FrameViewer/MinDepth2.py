from pickle import FALSE, TRUE
import sys
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "Python"))
import numpy

from API.VzenseDS_api import *
import cv2

def MinDepthAPI(depthFrame, detection_area, workspace_depth, threshold, not_set, cx_d, cy_d, fx_d, fy_d):
    depth_copy = depthFrame.copy()
    #threshold = 15

    objects_info = []

    workspace_width_m = 0
    workspace_height_m = 0

    workspace_limits = []
    workspace_warning = []

    pts_m = []

    prev_lower = 5000
    flag = False

    try:
        pts_pixels = detection_area

        # Converte para NumPy
        pts_flat = numpy.array(pts_pixels, dtype=numpy.float32)

        for (u,v) in pts_flat:
            X = (u - cx_d) * (workspace_depth / 1000) / fx_d
            Y = (v - cy_d) * (workspace_depth / 1000) / fy_d

            pts_m.append([X, Y])

        pts_m = numpy.array(pts_m, dtype=numpy.float32)

        rect_m = cv2.minAreaRect(pts_m)
        workspace_width_m, workspace_height_m = rect_m[1]

        if workspace_width_m < workspace_height_m:
            workspace_width_m, workspace_height_m = workspace_height_m, workspace_width_m

        xmin = pts_m[:,0].min()
        xmax = pts_m[:,0].max()
        ymin = pts_m[:,1].min()
        ymax = pts_m[:,1].max()

        if xmin < 0:
            wid = xmax + abs(xmin)
        else:
            wid = xmax - abs(xmin)
        if ymin < 0:
            hei = ymax + abs(ymin)
        else:
            hei = ymax - abs(ymin)

        if hei > wid:
            workspace_height_m, workspace_width_m = workspace_width_m, workspace_height_m

        print("Workspace Width:",workspace_width_m)
        print("Workspace Height:", workspace_height_m)

        # ys, xs = numpy.indices(depth_copy.shape)

        # Z = depth_copy.astype(numpy.float32)

        # X = (xs - cx_d) * Z / fx_d
        # Y = (ys - cy_d) * Z / fy_d

        # depth_corrected = numpy.sqrt(
        #     Z**2 - X**2 - Y**2
        # )

        # depth_vis = cv2.normalize(
        #     depth_corrected,
        #     None,
        #     0,
        #     255,
        #     cv2.NORM_MINMAX
        # ).astype(numpy.uint8)

        # depth_vis = cv2.applyColorMap(
        #     depth_vis,
        #     cv2.COLORMAP_JET
        # )

        #depth_corrected = numpy.nan_to_num(
        #    depth_corrected,
        #    nan=0.0,
        #    posinf=0.0,
        #    neginf=0.0
        #)

        #depth_copy = numpy.round(depth_corrected).astype(numpy.int32)

        while True:
            mask = numpy.zeros(depth_copy.shape, dtype = numpy.uint8)
            box = numpy.array(detection_area, dtype=numpy.int32)
            cv2.fillPoly(mask, [box], 255)
            
            valid_values = depth_copy[(depth_copy > 150) & (depth_copy < workspace_depth) & (mask > 0)]
            if valid_values.size  == 0:
                break

            else:
                min_value = numpy.min(valid_values) # minimo da profundidade

                index = numpy.where((depth_copy == min_value) & (mask > 0))
                min_idx = (index[0][0], index[1][0])
                y, x = min_idx

                for y, x in zip(index[0], index[1]):
                    x = int(x)
                    y = int(y)
                    neighbors = depth_copy[max(0, y-2):y+3, max(0, x-2):x+3]

                    if min_value + threshold > prev_lower:
                        flag = True

                    object_depth = min_value

                    detection_area_poly = numpy.array(detection_area, dtype = numpy.int32)
                    if cv2.pointPolygonTest(detection_area_poly, (x, y), False) >= 0:
                        if flag:
                            valid_mask = (neighbors >= min_value - threshold) & (neighbors <= min_value + threshold)
                        else:
                            valid_mask = (neighbors >= min_value - threshold) & (neighbors <= prev_lower)
                        valid_count = numpy.sum(valid_mask)
                        total_count = neighbors.size

                        if valid_count / total_count >= 0.9 and not (min_value - threshold <= workspace_depth <= min_value + threshold):
                            neighbors = neighbors[(neighbors > (min_value - threshold)) & (neighbors < (min_value + threshold))]
                            depth_value = round(numpy.median(neighbors), 1)

                            if len(objects_info) == 0 or abs(depth_value - objects_info[-1]["depth"]) > threshold:
                                print(f"Ponto {min_idx} válido, todos vizinhos semelhantes")
                                print("Profundidade:", depth_value)
                                print("Min Value", min_value)
                                workspace_limits = []
                                workspace_warning = []

                                prev_lower = depth_value - threshold
                                
                                pts_pixels = detection_area
                                
                                pts_flat = numpy.array(pts_pixels, dtype=numpy.float32)

                                for (u,v) in pts_flat:
                                    X = (u - cx_d) * (workspace_depth / 1000) / fx_d
                                    Y = (v - cy_d) * (workspace_depth / 1000) / fy_d

                                    X_new = (X * fx_d / (object_depth / 1000)) + cx_d
                                    Y_new = (Y * fy_d / (object_depth / 1000)) + cy_d

                                    workspace_limits.append([int(X_new), int(Y_new)])

                                    if workspace_width_m > workspace_height_m:
                                        X_warning = (X * fx_d / (object_depth / 1000)) * 0.92 + cx_d
                                        Y_warning = (Y * fy_d / (object_depth / 1000)) * 0.91 + cy_d
                                    elif workspace_width_m < workspace_height_m:
                                        X_warning = (X * fx_d / (object_depth / 1000)) * 0.91 + cx_d
                                        Y_warning = (Y * fy_d / (object_depth / 1000)) * 0.92 + cy_d
                                    else:
                                        X_warning = (X * fx_d / (object_depth / 1000)) * 0.92 + cx_d
                                        Y_warning = (Y * fy_d / (object_depth / 1000)) * 0.92 + cy_d

                                    workspace_warning.append([int(X_warning), int(Y_warning)])

                                objects_info.append({
                                            "depth": depth_value,
                                            "workspace_limits": workspace_limits,
                                            "workspace_warning": workspace_warning
                                        })

                            depth_copy[max(0, y-1):y+2, max(0, x-1):x+2] = 9999

                        else:
                            depth_copy[y, x] = 9999

                    else:
                        depth_copy[y, x] = 9999

        if len(objects_info) > 0:
            objects_info = sorted(objects_info, key=lambda obj: obj["depth"])

            print("Profundidade mínima:", objects_info[0]["depth"]/10, 'cm')

            not_set = 0

        else:
            print("Nenhum ponto válido encontrado dentro do workspace")

        return not_set, objects_info

    except Exception as e :
        print(e)
    finally :
        print('Min Depth end')

    return not_set, objects_info