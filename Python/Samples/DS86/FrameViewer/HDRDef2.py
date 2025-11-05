from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2
import time

def hdr2(camera, colorSlope, exposureStruct, intrinsics_depth, intrinsics_color, extrinsics):

    exposureTime = 200

    depth_in_color = None
    hdrDepth = None

    hdr_done = 0
    hdrDepth_done = 0
    expositionBus_done = 0

    hasDepthArray = []
    exposureTimeArray = []
    
    i = 0

    firstFrame = True

    try:
        while 1:
            while exposureTime <= 4000 and expositionBus_done == 0:
                camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(exposureTime))

                ret_code, exposureStruct = camera.VZ_GetExposureTime(VzSensorType.VzToFSensor)

                time.sleep(0.4)

                ret, frameready = camera.VZ_GetFrameReady(c_uint16(1200))
                if  ret !=0:
                    print("VZ_GetFrameReady failed:",ret)
                    continue
                hasDepth = 0

                if  frameready.depth:      
                    ret,depthframe = camera.VZ_GetFrame(VzFrameType.VzDepthFrame)
                    if  ret == 0:
                        hasDepth=1
                    
                    else:
                        print("get depth frame failed:",ret)

                if  hasDepth==1 and exposureStruct.exposureTime == exposureTime:
                    frametmp = numpy.empty((0, 0, 3), dtype=numpy.uint8)
                    frametmp = numpy.ctypeslib.as_array(depthframe.pFrameData, (1, depthframe.width * depthframe.height * 2))
                    frametmp.dtype = numpy.uint16
                    frametmp.shape = (depthframe.height, depthframe.width)
                    frametmp = cv2.resize(frametmp, (640, 480))
                    
                    if firstFrame:
                        firstFrame = False
                    else:
                        exposureTimeArray.append(exposureTime / 1e6)
                        exposureTime += 950
                        i += 1
                        hasDepthArray.append(frametmp)

            else:
                # FAZER HDR AQUI E DEPOIS TESTAR A IMAGEM
                # ERA INCRIVEL TER ISTO POIS PERMITIRIA ANALISAR APENAS UMA VEZ A IMAGEM E OBTER TUDO O QUE É NECESSÁRIO            
                if not hdrDepth_done:
                    valid_frames = [numpy.where((frame > 0) & (frame <= 5000), frame, numpy.nan) for frame in hasDepthArray]

                    hdrDepth = numpy.nanmean(numpy.stack(valid_frames, axis=-1), axis=-1)

                    hdrDepth_done = 1
                    
                expositionBus_done = 1
                exposureTime = 200

                if hdrDepth_done:
                    # 1. Obter parâmetros
                    fx_d, fy_d, cx_d, cy_d = intrinsics_depth.fx, intrinsics_depth.fy, intrinsics_depth.cx, intrinsics_depth.cy
                    fx_c, fy_c, cx_c, cy_c = intrinsics_color.fx, intrinsics_color.fy, intrinsics_color.cx, intrinsics_color.cy
                    R = extrinsics.rotation   # Matriz 3x3
                    T = extrinsics.translation # Vetor 3x1

                    R = numpy.array(extrinsics.rotation).reshape(3, 3)
                    T = numpy.array(extrinsics.translation).reshape(3, 1)

                    # 2. Criar uma imagem de saída (mesmo tamanho da cor)
                    #h_c, w_c = intrinsics_color.height, intrinsics_color.width
                    h_c, w_c = 1200, 1600
                    depth_in_color = numpy.zeros((h_c, w_c), dtype=numpy.float32)

                    # 3. Para cada píxel depth (u_d, v_d)
                    for v_d in range(hdrDepth.shape[0]):
                        for u_d in range(hdrDepth.shape[1]):
                            Z_d = hdrDepth[v_d, u_d]
                            if Z_d <= 0:
                                continue
                            
                            # Converter para coordenadas 3D do sensor depth
                            X_d = (u_d - cx_d) * Z_d / fx_d
                            Y_d = (v_d - cy_d) * Z_d / fy_d
                            P_d = numpy.array([[X_d], [Y_d], [Z_d]])

                            # Aplicar transformação extrínseca (Depth -> Color)
                            P_c = R @ P_d + T
                            
                            X_c, Y_c, Z_c = P_c.flatten()

                            if Z_c <= 0 or numpy.isnan(Z_c):
                                continue

                            # Projetar no plano de imagem do sensor de cor
                            u_c = int(fx_c * X_c / Z_c + cx_c)
                            v_c = int(fy_c * Y_c / Z_c + cy_c)

                            if 0 <= u_c < w_c and 0 <= v_c < h_c:
                                depth_in_color[v_c, u_c] = Z_c

                    depth_vis = cv2.normalize(depth_in_color, None, 0, 255, cv2.NORM_MINMAX)
                    depth_vis = depth_vis.astype(numpy.uint8)
                    depth_colormap = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)
                    depth_colormap = cv2.resize(depth_colormap, (640, 480))
                    hdr_done = 1

            if  hdr_done:
                expositionBus_done = 0
                hdr_done = 0
                i = 0
                print("HDR Processed")
                return depth_colormap, hdrDepth
                
    except Exception as e :
        print(e)
    finally :
        print('end')
        return depth_colormap, hdrDepth