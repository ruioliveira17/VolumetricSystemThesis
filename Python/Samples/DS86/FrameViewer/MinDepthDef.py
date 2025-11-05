from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *

def MinDepth(hdrDepth, colorSlope, threshold, workspace, workspace_depth, minimum_value, not_set):

    valid_values = hdrDepth[(hdrDepth > 150) & (hdrDepth < 5000)]

    try:    
        while not_set == 1:

            if valid_values.size > 0:
                while True:
                    found = False
                    valid_values = hdrDepth[(hdrDepth > 150) & (hdrDepth < colorSlope)]
                    min_value = numpy.min(valid_values) # minimo da profundidade

                    if min_value < minimum_value:
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
                                    print(f"Ponto {min_idx} válido, todos vizinhos semelhantes")
                                    
                                    minimum_value = min_value
                                    point_idx = y,x
                                    found = True
                                    break

                                else:
                                    hdrDepth[y, x] = 9999

                            else:
                                hdrDepth[y, x] = 9999
                                
                    else:
                        break
                        
                    if found:
                        break

            print("Profundidade mínima:", minimum_value/10, 'cm')
            min_y = point_idx[0]
            min_x = point_idx[1]
            print("Ponto:", (min_x, min_y))

            not_set = 0

            return not_set, workspace_limits, minimum_value

    except Exception as e :
        print(e)
    finally :
        print('Min Depth end')

    return not_set, [], minimum_value