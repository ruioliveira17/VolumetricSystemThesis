from pickle import FALSE, TRUE
import sys
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "Python"))
import numpy

from API.VzenseDS_api import *
import cv2

def project_points(pts_pixels, workspace_depth, object_depth, cx_d, cy_d, fx_d, fy_d):
    pts = numpy.array(pts_pixels, dtype=numpy.float32)
    u, v = pts[:, 0], pts[:, 1]

    X = (u - cx_d) * (workspace_depth / 1000.0) / fx_d
    Y = (v - cy_d) * (workspace_depth / 1000.0) / fy_d

    scale = (object_depth / 1000.0)
    X_new = numpy.clip(X * fx_d / scale + cx_d, 0, None)
    Y_new = numpy.clip(Y * fy_d / scale + cy_d, 0, None)

    return numpy.stack([X_new, Y_new], axis=1).astype(numpy.int32).tolist()

def MinDepthAPI(depthFrame, detection_area, workspace_warning, workspace_depth, threshold, not_set, cx_d, cy_d, fx_d, fy_d):
    depth_copy = depthFrame.copy()
    objects_info = []
    #pts_m = []

    try:
        # pts_pixels = detection_area

        # # Converte para NumPy
        # pts_flat = numpy.array(pts_pixels, dtype=numpy.float32)

        # for (u,v) in pts_flat:
        #     X = (u - cx_d) * (workspace_depth / 1000) / fx_d
        #     Y = (v - cy_d) * (workspace_depth / 1000) / fy_d
        #     pts_m.append([X, Y])

        # pts_m = numpy.array(pts_m, dtype=numpy.float32)

        # rect_m = cv2.minAreaRect(pts_m)
        # workspace_width_m, workspace_height_m = rect_m[1]

        # if workspace_width_m < workspace_height_m:
        #     workspace_width_m, workspace_height_m = workspace_height_m, workspace_width_m

        # xmin, xmax = pts_m[:, 0].min(), pts_m[:, 0].max()
        # ymin, ymax = pts_m[:, 1].min(), pts_m[:, 1].max()
        # wid = xmax + abs(xmin) if xmin < 0 else xmax - abs(xmin)
        # hei = ymax + abs(ymin) if ymin < 0 else ymax - abs(ymin)

        # if hei > wid:
        #     workspace_height_m, workspace_width_m = workspace_width_m, workspace_height_m

        # print("Workspace Width:",workspace_width_m)
        # print("Workspace Height:", workspace_height_m)

        #ys, xs = numpy.indices(depth_copy.shape)

        #D = depth_copy.astype(numpy.float32)

        #depth_corrected = D / (numpy.sqrt(1 + ((xs - cx_d) / fx_d) ** 2 + ((ys - cy_d) / fy_d) ** 2))

        #depth_copy = numpy.round(depth_corrected).astype(numpy.int32)

        mask = numpy.zeros(depth_copy.shape, dtype=numpy.uint8)
        box = numpy.array(detection_area, dtype=numpy.int32)
        cv2.fillPoly(mask, [box], 255)

        kernel = numpy.ones((3, 3), dtype=numpy.uint8)

        prev_lower = 5000
        flag = False

        while True:
            valid_values = depth_copy[(depth_copy > 600 ) & (depth_copy < workspace_depth - 20) & (mask > 0)]
            if valid_values.size  == 0:
                break

            min_value = numpy.min(valid_values)

            min_mask = (depth_copy == min_value) & (mask > 0)
            ys, xs = numpy.where(min_mask)
            suppressed_any = False

            for y, x in zip(ys, xs):
                x, y = int(x), int(y)
                neighbors = depth_copy[max(0, y-2):y+3, max(0, x-2):x+3]

                if min_value + threshold > prev_lower:
                    flag = True

                object_depth = min_value

                if flag:
                    valid_mask = (neighbors >= min_value - threshold) & (neighbors <= min_value + threshold)
                else:
                    valid_mask = (neighbors >= min_value - threshold) & (neighbors <= prev_lower)
                    
                valid_count = numpy.sum(valid_mask)
                total_count = neighbors.size

                if valid_count / total_count >= 0.9 and not (min_value - threshold <= workspace_depth <= min_value + threshold):
                        
                    neighbors = neighbors[(neighbors > (min_value - threshold)) & (neighbors < (min_value + threshold))]
                    depth_value = round(float(numpy.median(neighbors)), 1)

                    is_new_object = (
                        (len(objects_info) == 0 or abs(depth_value - objects_info[-1]["depth"]) > threshold)
                        and workspace_depth - depth_value >= 50
                    )

                    if is_new_object:
                        print(f"Ponto ({x},{y}) válido | depth={depth_value} | min={min_value}")
                        print("Profundidade:", depth_value)
                        print("Min Value", min_value)

                        prev_lower = depth_value - threshold
                            
                        workspace_limits     = project_points(
                            detection_area, workspace_depth, object_depth,
                            cx_d, cy_d, fx_d, fy_d)
                        objectWorkspace_warning = project_points(
                            workspace_warning, workspace_depth, object_depth,
                            cx_d, cy_d, fx_d, fy_d)

                        objects_info.append({
                            "depth": depth_value,
                            "workspace_limits": workspace_limits,
                            "workspace_warning": objectWorkspace_warning,
                        })

                        # Suppress entire depth-band + 51px border to kill edge artefacts
                        # (visible box sides when rotated appear just outside top contour)
                        surface_band = (
                            (depth_copy >= min_value - threshold) &
                            (depth_copy <= min_value + threshold) &
                            (mask > 0)
                        ).astype(numpy.uint8) * 255
                        big_kernel = numpy.ones((51, 51), dtype=numpy.uint8)
                        dilated = cv2.dilate(surface_band, big_kernel)
                        depth_copy[dilated > 0] = 9999
                    else:
                        suppress = numpy.zeros_like(depth_copy, dtype=numpy.uint8)
                        suppress[y, x] = 1
                        suppress = cv2.dilate(suppress, kernel)
                        depth_copy[suppress > 0] = 9999

                    suppressed_any = True
                    break

                else:
                    depth_copy[y, x] = 9999

            if not suppressed_any and valid_values.size > 0:
                depth_copy[ys, xs] = 9999

        if objects_info:
            objects_info = sorted(objects_info, key=lambda obj: obj["depth"])
            print("Profundidade mínima:", objects_info[0]["depth"]/10, 'cm')
            not_set = 0

        else:
            print("Nenhum ponto válido encontrado dentro do workspace")

    except Exception as e :
        print(e)
    finally :
        print('Min Depth end')

    return not_set, objects_info