from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2
from FrameState import frameState

def MinDepth(hdrDepth, colorSlope, threshold, workspace, workspace_depth, not_set):

    valid_values = hdrDepth[(hdrDepth > 150) & (hdrDepth < (workspace_depth - threshold))]
    objects_info = []

    try:
        while True:
            valid_values = hdrDepth[(hdrDepth > 150) & (hdrDepth < (workspace_depth - threshold))]
            if valid_values.size  == 0:
                break

            else:
                min_value = numpy.min(valid_values) # minimo da profundidade

                #if min_value < minimum_value:
                index = numpy.where(hdrDepth == min_value)
                min_idx = (index[0][0], index[1][0])
                y, x = min_idx

                for y, x in zip(index[0], index[1]):
                    neighbors = hdrDepth[max(0, y-8):y+9, max(0, x-8):x+9]
                    tolerance = threshold

                    workspace_width = int((workspace[2] - workspace[0])/2)

                    workspace_height = int((workspace[3] - workspace[1])/2)

                    object_depth = min_value

                    workspace_width_max = int((workspace_width * int(workspace_depth)) / object_depth)

                    workspace_height_max = int((workspace_height * int(workspace_depth)) / object_depth)

                    workspace_limits = int(320 - (workspace_width_max)), int(240 - (workspace_height_max)), int(320 + (workspace_width_max)), int(240 + (workspace_height_max))

                    if ((x >= workspace_limits[0]) and (x <= workspace_limits[2])) and ((y >= workspace_limits[1]) and (y <= workspace_limits[3])):
                        valid_count = numpy.sum(numpy.abs(neighbors - min_value) <= tolerance)
                        total_count = neighbors.size

                        if valid_count / total_count >= 0.9:
                            neighbors = neighbors[(neighbors > (min_value - tolerance)) & (neighbors < (min_value + tolerance))]
                            min_value = numpy.mean(neighbors)
                            min_value = round(numpy.mean(neighbors), 1)
                            if len(objects_info) == 0 or abs(min_value - objects_info[-1]["depth"]) > threshold:
                                print(f"Ponto {min_idx} válido, todos vizinhos semelhantes")
                                objects_info.append({
                                            "depth": min_value,
                                            "workspace_limits": workspace_limits
                                        })

                                #minimum_value = min_value
                                point_idx = y,x

                            hdrDepth[max(0, y-8):y+9, max(0, x-8):x+9] = 9999
                            #break

                        else:
                            hdrDepth[y, x] = 9999

                    else:
                        hdrDepth[y, x] = 9999
                            
                #else:
                #    break

        if len(objects_info) > 0:
            objects_info = sorted(objects_info, key=lambda obj: obj["depth"])

            print("Profundidade mínima:", objects_info[0]["depth"]/10, 'cm')
            min_y = point_idx[0]
            min_x = point_idx[1]
            print("Ponto:", (min_x, min_y))

            not_set = 0

        else:
            print("Nenhum ponto válido encontrado dentro do workspace")

        return not_set, objects_info

    except Exception as e :
        print(e)
    finally :
        print('Min Depth end')

    return not_set, objects_info

def MinDepthAPI(depth, colorSlope, threshold, workspace, workspace_depth, not_set, cx, cy, fx, fy):
    depth_copy = depth.copy()

    valid_values = depth_copy[(depth_copy > 150) & (depth_copy < (workspace_depth - 50))]
    objects_info = []

    workspace_width_m = 0.27
    workspace_height_m = 0.37

    try:
        while True:
            valid_values = depth_copy[(depth_copy > 150) & (depth_copy < (workspace_depth - 50))]
            if valid_values.size  == 0:
                break

            else:
                min_value = numpy.min(valid_values) # minimo da profundidade

                index = numpy.where(depth_copy == min_value)
                min_idx = (index[0][0], index[1][0])
                y, x = min_idx

                for y, x in zip(index[0], index[1]):
                    neighbors = depth_copy[max(0, y-7):y+8, max(0, x-7):x+8]

                    object_depth = min_value

                    if ((x >= workspace[0]) and (x <= workspace[2])) and ((y >= workspace[1]) and (y <= workspace[3])):
                        valid_count = numpy.sum(numpy.abs(neighbors - min_value) <= threshold)
                        total_count = neighbors.size

                        if valid_count / total_count >= 0.9:
                            neighbors = neighbors[(neighbors > (min_value - threshold)) & (neighbors < (min_value + threshold))]
                            min_value = numpy.mean(neighbors)
                            min_value = round(numpy.mean(neighbors), 1)

                            if len(objects_info) == 0 or abs(min_value - objects_info[-1]["depth"]) > threshold:
                                print(f"Ponto {min_idx} válido, todos vizinhos semelhantes")
                                print("Profundidade:", min_value)
                                half_width_px = (workspace_width_m / 2) * fx / (object_depth / 1000.0)
                                half_height_px = (workspace_height_m / 2) * fy / (object_depth / 1000.0)
                                warning_half_width_px = ((workspace_width_m - 0.022) / 2) * fx / (object_depth / 1000.0)
                                warning_half_height_px = ((workspace_height_m - 0.022) / 2) * fy / (object_depth / 1000.0)

                                workspace_limits = int(cx - half_width_px), int(cy - half_height_px), int(cx + half_width_px), int(cy + half_height_px)
                                workspace_warning = int(cx - warning_half_width_px), int(cy - warning_half_height_px), int(cx + warning_half_width_px), int(cy + warning_half_height_px)
                                print("Width:", half_width_px)
                                print("Height:", half_height_px)
                                print("WS Limits:", workspace_limits)

                                objects_info.append({
                                            "depth": min_value,
                                            "workspace_limits": workspace_limits,
                                            "workspace_warning": workspace_warning
                                        })

                                point_idx = y,x

                            depth_copy[max(0, y-8):y+9, max(0, x-8):x+9] = 9999

                        else:
                            depth_copy[y, x] = 9999

                    else:
                        depth_copy[y, x] = 9999

        if len(objects_info) > 0:
            objects_info = sorted(objects_info, key=lambda obj: obj["depth"])

            print("Profundidade mínima:", objects_info[0]["depth"]/10, 'cm')
            min_y = point_idx[0]
            min_x = point_idx[1]
            print("Ponto:", (min_x, min_y))

            not_set = 0

        else:
            print("Nenhum ponto válido encontrado dentro do workspace")

        return not_set, objects_info

    except Exception as e :
        print(e)
    finally :
        print('Min Depth end')

    return not_set, objects_info