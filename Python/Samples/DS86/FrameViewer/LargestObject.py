from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2

from scipy import ndimage

def LargestObject(hdrDepth, workspace_limits, threshold, workspace, minimum_value, not_set, hdrDepth_img, hdrColor):

    framedataToF = []
    inc = 0

    objectpixelsmin_x = 0
    objectpixelsmax_x = 0
    objectpixelsmin_y = 0
    objectpixelsmax_y = 0
    sizes = 0

    try:    
        workspace_area = hdrDepth[workspace_limits[1]:workspace_limits[3], workspace_limits[0]:workspace_limits[2]]

        mask = (workspace_area >= minimum_value) & (workspace_area <= minimum_value + threshold)

        labeled_array, num_features = ndimage.label(mask)

        sizes = ndimage.sum(mask, labeled_array, range(1, num_features + 1))

        if len(sizes) == 0:
            print("Nenhuma região encontrada")
        else:
            # Encontrar região com maior número de pixels
            largest_region_index = numpy.argmax(sizes) + 1  # +1 porque labels começam em 1
            largest_region_mask = (labeled_array == largest_region_index)

            objectpixelsy, objectpixelsx = numpy.where(largest_region_mask)
            objectpixelsmin_x, objectpixelsmax_x = workspace_limits[0] + objectpixelsx.min(), workspace_limits[0] + objectpixelsx.max()
            objectpixelsmin_y, objectpixelsmax_y = workspace_limits[1] + objectpixelsy.min(), workspace_limits[1] + objectpixelsy.max()
            print("Área Coberta:", objectpixelsmin_x, objectpixelsmin_y, objectpixelsmax_x, objectpixelsmax_y)

            object_region = hdrDepth[objectpixelsmin_y:objectpixelsmax_y, objectpixelsmin_x:objectpixelsmax_x]

            valid_values = object_region[(object_region >= minimum_value) & (object_region <= minimum_value + threshold)]

            if valid_values.size > 0:
                avg_depth = numpy.mean(valid_values) # média da profundidade

                if not numpy.isnan(avg_depth):
                    framedataToF.append(avg_depth)

                    if inc < 100:
                        value = framedataToF[inc]
                    else:
                        value = int(sum(framedataToF[-100:]) / 100)

                    inc += 1
                
                    print(f"Profundidade média: {avg_depth/10:.1f} cm")

        frame_copy = hdrDepth_img
        #if len(sizes) != 0:
            #cv2.rectangle(frame_copy, (objectpixelsmin_x, objectpixelsmin_y), (objectpixelsmax_x, objectpixelsmax_y), (255, 255, 0), 2)
            #cv2.rectangle(frame_copy, (workspace[0], workspace[1]), (workspace[2], workspace[3]), (255, 0, 255), 2)
            #cv2.rectangle(frame_copy, (workspace_limits[0], workspace_limits[1]), (workspace_limits[2], workspace_limits[3]), (255, 0, 0), 2)

        not_set = 1
        minimum_value = 6000
        
        if objectpixelsmin_x != 0 and objectpixelsmax_x != 0 and objectpixelsmin_y != 0 and objectpixelsmax_y != 0 and len(sizes) != 0:
            frame_copy = hdrColor
            #cv2.rectangle(frame_copy, (objectpixelsmin_x, objectpixelsmin_y), (objectpixelsmax_x, objectpixelsmax_y), (255, 0, 255), 2)

        return not_set, minimum_value

    except Exception as e :
        print(e)
    finally :
        print('end')