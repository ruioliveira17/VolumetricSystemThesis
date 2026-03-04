from pickle import FALSE, TRUE
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import cv2
import time

def hdr(camera, colorSlope, exposureStruct):

    exposureTime = 400

    ldr = None
    hdrDepth = None

    hdr_done = 0
    hdrColor_done = 0
    hdrDepth_done = 0
    expositionBus_done = 0

    hasDepthArray = []
    exposureTimeArray = []
    
    i = 0
    #not_aligned = 1

    DTC_can = False
    D_can = False
    firstFrame = True

    output_folderCTD = "C:/Tese/Python/FramesCTD"
    os.makedirs(output_folderCTD, exist_ok=True)

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
                hasColorToDepth =0
                hasDepth = 0

                if  frameready.color:      
                    ret,rgbframe = camera.VZ_GetFrame(VzFrameType.VzTransformColorImgToDepthSensorFrame)
                    if  ret == 0:
                        hasColorToDepth =1   
                    else:
                        print("get color frame failed:",ret)

                if  frameready.depth:      
                    ret,depthframe = camera.VZ_GetFrame(VzFrameType.VzDepthFrame)
                    if  ret == 0:
                        hasDepth=1
                    
                    else:
                        print("get depth frame failed:",ret)

                if  hasColorToDepth==1 and exposureStruct.exposureTime == exposureTime:
                    frametmp = numpy.empty((0, 0, 3), dtype=numpy.uint8)
                    frametmp = numpy.ctypeslib.as_array(rgbframe.pFrameData, (1, rgbframe.width * rgbframe.height * 3))
                    frametmp.dtype = numpy.uint8
                    frametmp.shape = (rgbframe.height, rgbframe.width,3)
                    frametmp = cv2.resize(frametmp, (640, 480))
                    #cv2.putText(frametmp, f"Exposure: {exposureStruct.exposureTime} us",
                    #            (30, 40),                   # posição (x, y)
                    #            cv2.FONT_HERSHEY_SIMPLEX,   # tipo de letra
                    #            1,                           # escala (tamanho)
                    #            (0, 255, 0),                 # cor (B, G, R)
                    #            2,                           # espessura
                    #            cv2.LINE_AA)                 # antialiasing
                    
                    if firstFrame:
                        firstFrame = False
                    else:
                        DTC_can = True
                        filename = f"CTDFrame_{i}.jpg"
                        filepath = os.path.join(output_folderCTD, filename)
                        cv2.imwrite(filepath, frametmp)

                if  hasDepth==1 and exposureStruct.exposureTime == exposureTime:
                    frametmp = numpy.empty((0, 0, 3), dtype=numpy.uint8)
                    frametmp = numpy.ctypeslib.as_array(depthframe.pFrameData, (1, depthframe.width * depthframe.height * 2))
                    frametmp.dtype = numpy.uint16
                    frametmp.shape = (depthframe.height, depthframe.width)
                    frametmp = cv2.resize(frametmp, (640, 480))
                    
                    if firstFrame:
                        firstFrame = False
                    else:
                        D_can = True
                        hasDepthArray.append(frametmp)

                if DTC_can and D_can:
                    exposureTimeArray.append(exposureTime / 1e6)
                    exposureTime += 900
                    i += 1
                
                DTC_can = False
                D_can = False

            else:
                # FAZER HDR AQUI E DEPOIS TESTAR A IMAGEM
                # ERA INCRIVEL TER ISTO POIS PERMITIRIA ANALISAR APENAS UMA VEZ A IMAGEM E OBTER TUDO O QUE É NECESSÁRIO            
                if not hdrColor_done:
                    frame_array = [os.path.join(output_folderCTD, f"CTDFrame_{i}.jpg") for i in range(len(exposureTimeArray))]
                    
                    frame_list = [cv2.imread(fn) for fn in frame_array]

                    exposureTimes = numpy.array(exposureTimeArray, dtype = numpy.float32)

                    #if not_aligned == 1:
                    #    alignMTB = cv2.createAlignMTB()
                    #    alignMTB.process(frame_list, frame_list)
                    #    not_aligned = 0

                    #calibrateDebevec = cv2.createCalibrateDebevec()
                    #responseDebevec = calibrateDebevec.process(frame_list, exposureTimes.copy())

                    mergeDebevec = cv2.createMergeDebevec()
                    hdrColor = mergeDebevec.process(frame_list, exposureTimes.copy())

                    tonemap = cv2.createTonemapDrago(gamma=1.0, saturation=0.7)
                    ldr = tonemap.process(hdrColor)
                    ldr = numpy.nan_to_num(ldr)
                    ldr = numpy.clip(ldr, 0, 1)
                    ldr = (ldr*65535).astype('uint16')
                    hdrColor_done = 1

                if not hdrDepth_done:
                    valid_frames = [numpy.where((frame > 0) & (frame <= 5000), frame, numpy.nan) for frame in hasDepthArray]

                    hdrDepth = numpy.nanmean(numpy.stack(valid_frames, axis=-1), axis=-1)

                    hdrDepth_done = 1
                    
                expositionBus_done = 1
                exposureTime = 400

                if hdrColor_done and hdrDepth_done:
                    hdr_done = 1

            if  hdr_done:
                expositionBus_done = 0
                hdr_done = 0
                i = 0
                print("HDR Processed")
                return ldr, hdrDepth
                
    except Exception as e :
        print(e)
    finally :
        print('end')