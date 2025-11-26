import tkinter as tk
from PIL import Image, ImageTk
import ctypes
import numpy
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import time
import threading

sys.path.append('C:/Tese/Python/Samples/DS86/FrameViewer')

from GetFrame import getFrame

camera = VzenseTofCam()

camera_count = camera.VZ_GetDeviceCount()
retry_count = 100
while camera_count==0 and retry_count > 0:
    retry_count = retry_count-1
    camera_count = camera.VZ_GetDeviceCount()
    time.sleep(1)
    print("scaning......   ",retry_count)

device_info=VzDeviceInfo()

if camera_count > 1:
    ret,device_infolist=camera.VZ_GetDeviceInfoList(camera_count)
    if ret==0:
        device_info = device_infolist[0]
        for info in device_infolist: 
            print('cam uri:  ' + str(info.uri))
    else:
        print(' failed:' , ret)  
        exit()  
elif camera_count == 1:
    ret,device_info=camera.VZ_GetDeviceInfo()
    if ret==0:
        print('cam uri:' + str(device_info.uri))
    else:
        print(' failed:', ret)   
        exit() 
else: 
    print("there are no camera found")
    exit()

print("uri: "+str(device_info.uri))
ret = camera.VZ_OpenDeviceByUri(device_info.uri)

if  ret == 0:

    ret = camera.VZ_StartStream()
    if  ret == 0:
        print("start stream successful")
    else:
        print("VZ_StartStream failed:",ret)

    colorSlope = c_uint16(1500) #distância máxima pretendida 5 metros
    
    camera.VZ_SetExposureControlMode(VzSensorType.VzToFSensor, VzExposureControlMode.VzExposureControlMode_Manual)
    camera.VZ_SetExposureTime(VzSensorType.VzToFSensor, c_int32(700))

    ret_code, exposureStruct = camera.VZ_GetExposureTime(VzSensorType.VzToFSensor)
    print('Exposure Time:', exposureStruct.exposureTime)

    # set Mapper
    ret = camera.VZ_SetTransformColorImgToDepthSensorEnabled(c_bool(True))

    if  ret == 0:
        print("VZ_SetTransformColorImgToDepthSensorEnabled ok")
    else:
        print("VZ_SetTransformColorImgToDepthSensorEnabled failed:",ret)    

    ret,enable = camera.VZ_GetSpatialFilterEnabled()
    if  ret == 0:
        print("The default SpatialFilter switch is " + str(enable))
    else:
        print("VZ_GetSpatialFilterEnabled failed:"+ str(ret))   

    enable = not enable
    ret = camera.VZ_SetSpatialFilterEnabled(enable)
    if  ret == 0:
        print("Set SpatialFilter switch to "+ str(enable) + " is Ok")   
    else:
        print("VZ_SetSpatialFilterEnabled failed:"+ str(ret))

    ret,params = camera.VZ_GetConfidenceFilterParams()
    if  ret == 0:
        print("The default ConfidenceFilter switch is " + str(params.enable))
    else:
        print("VZ_GetConfidenceFilterParams failed:"+ str(ret))

    params.enable = False
    ret = camera.VZ_SetConfidenceFilterParams(params)
    if  ret == 0:
        print("Set ConfidenceFilter switch to "+ str(params.enable) + " is Ok")   
    else:
        print("VZ_SetConfidenceFilterParams failed:"+ str(ret))

# Deactivate windows automatic dpi scale
ctypes.windll.shcore.SetProcessDpiAwareness(1)

# Create Fullscreen Window
root = tk.Tk()
root.title("Manager")
root.attributes('-fullscreen', True)  # fullscreen real
root.configure(bg='white')

#----------------------- Principal Canvas ------------------------

canvas_main = tk.Canvas(root, bg='white', highlightthickness=0)
canvas_main.pack(fill="both", expand=True)

current_canvas = canvas_main

#--------------------- Logo Balanças Marques ---------------------
BM_logo = Image.open("BM_Logo.png").resize((360, 152))
BM_logo_tk = ImageTk.PhotoImage(BM_logo)
main_rect = [0, 0, 370, 162]
canvas_main.create_image(10, 10, anchor='nw', image=BM_logo_tk)

#-----------------------------------------------------------------

#----------------------- Camera Interface ------------------------

# Blue Rectangle
cam_height, cam_width = 300, 400
cam_x, cam_y = 200, 250
cam_rect = [cam_x, cam_y, cam_x + cam_width, cam_y + cam_height]
canvas_main.create_rectangle(cam_rect, fill="#8FB3FC", outline="")

# Camera Icon
cam_icon = Image.open("cam_icon.png").resize((350, 350))
cam_icon_tk = ImageTk.PhotoImage(cam_icon)
cam_icon_x = cam_x + cam_width/2 - 350/2
cam_icon_y = cam_y + cam_height/2 - 350/2
canvas_main.create_image(cam_icon_x, cam_icon_y, anchor='nw', image=cam_icon_tk)

#-----------------------------------------------------------------

#-------------------- QR/Bar Code Interface ----------------------

# Blue Rectangle
code_height, code_width = 300, 400
code_x, code_y = 760, 250
code_rect = [code_x, code_y, code_x + code_width, code_y + code_height]
canvas_main.create_rectangle(code_rect, fill="#2DE4AD", outline="")

# Barcode Icon
#code_icon = Image.open("barcode.png").resize((350, 350))
#code_icon_tk = ImageTk.PhotoImage(code_icon)
#code_icon_x = code_x + code_width/2 - 350/2
#code_icon_y = code_y + code_height/2 - 350/2
#canvas_main.create_image(code_icon_x, code_icon_y, anchor='nw', image=code_icon_tk)

#-----------------------------------------------------------------

#--------------------- Dimensions Interface ----------------------

# Blue Rectangle
dim_height, dim_width = 300, 400
dim_x, dim_y = 1320, 250
dim_rect = [dim_x, dim_y, dim_x + dim_width, dim_y + dim_height]
canvas_main.create_rectangle(dim_rect, fill="#9EBEFF", outline="")

# Dim Icon
#dim_icon = Image.open("boxVol.png").resize((350, 350))
#dim_icon_tk = ImageTk.PhotoImage(dim_icon)
#dim_icon_x = dim_x + dim_width/2 - 350/2
#dim_icon_y = dim_y + dim_height/2 - 350/2
#canvas_main.create_image(dim_icon_x, dim_icon_y, anchor='nw', image=dim_icon_tk)

#-----------------------------------------------------------------

#----------------------- Config Interface ------------------------

# Grey Rectangle
conf_height, conf_width = 300, 400
conf_x, conf_y = 1320, 630
conf_rect = [conf_x, conf_y, conf_x + conf_width, conf_y + conf_height]
canvas_main.create_rectangle(conf_rect, fill="#C0C0C0", outline="")

# Config Icon
conf_icon = Image.open("conf_icon.png").resize((400, 400))
conf_icon_tk = ImageTk.PhotoImage(conf_icon)
conf_icon_x = conf_x + conf_width/2 - 400/2
conf_icon_y = conf_y + conf_height/2 - 400/2
canvas_main.create_image(conf_icon_x, conf_icon_y, anchor='nw', image=conf_icon_tk)

#-----------------------------------------------------------------

#------------------------ Camara Canvas --------------------------

canvas_camara = tk.Canvas(root, bg='white', highlightthickness=0)

#--------------------- Logo Balanças Marques ---------------------
BM_logo = Image.open("BM_Logo.png").resize((360, 152))
BM_logo_tk_cam = ImageTk.PhotoImage(BM_logo)
canvas_camara.create_image(10, 10, anchor='nw', image=BM_logo_tk_cam)

#-----------------------------------------------------------------

#-----------------------------------------------------------------

#------------------------ QR/BarCode Canvas ----------------------

#canvas_barcode = tk.Canvas(root, bg='white', highlightthickness=0)

#--------------------- Logo Balanças Marques ---------------------
#BM_logo = Image.open("BM_Logo.png").resize((360, 152))
#BM_logo_tk_cam = ImageTk.PhotoImage(BM_logo)
#canvas_barcode.create_image(10, 10, anchor='nw', image=BM_logo_tk_cam)

#-----------------------------------------------------------------

#-----------------------------------------------------------------

#------------------------ Volume Canvas --------------------------

#canvas_volume = tk.Canvas(root, bg='white', highlightthickness=0)

#--------------------- Logo Balanças Marques ---------------------
#BM_logo = Image.open("BM_Logo.png").resize((360, 152))
#BM_logo_tk_config = ImageTk.PhotoImage(BM_logo)
#canvas_volume.create_image(10, 10, anchor='nw', image=BM_logo_tk_config)

#-----------------------------------------------------------------

#-----------------------------------------------------------------

#------------------------ Config Canvas --------------------------

canvas_config = tk.Canvas(root, bg='white', highlightthickness=0)

#--------------------- Logo Balanças Marques ---------------------
BM_logo = Image.open("BM_Logo.png").resize((360, 152))
BM_logo_tk_config = ImageTk.PhotoImage(BM_logo)
canvas_config.create_image(10, 10, anchor='nw', image=BM_logo_tk_config)

#-----------------------------------------------------------------

#-----------------------------------------------------------------

#---------------------------- Events -----------------------------

def change_canvas(event):
    global current_canvas
    x, y = event.x, event.y
    if current_canvas is canvas_main and cam_rect[0] <= x <= cam_rect[2] and cam_rect[1] <= y <= cam_rect[3]:
        # Clicou no quadrado da camera
        canvas_main.pack_forget()
        canvas_camara.pack(fill="both", expand=True)
        current_canvas = canvas_camara

        current_canvas.update()
        update_camera_feed()

    #elif current_canvas is canvas_main and code_rect[0] <= x <= code_rect[2] and code_rect[1] <= y <= code_rect[3]:
        # Clicou no quadrado de configuração
    #    canvas_main.pack_forget()
    #    canvas_config.pack(fill="both", expand=True)
    #    current_canvas = canvas_barcode

    #elif current_canvas is canvas_main and dim_rect[0] <= x <= dim_rect[2] and dim_rect[1] <= y <= dim_rect[3]:
        # Clicou no quadrado de configuração
    #    canvas_main.pack_forget()
    #    canvas_config.pack(fill="both", expand=True)
    #    current_canvas = canvas_volume

    elif current_canvas is canvas_main and conf_rect[0] <= x <= conf_rect[2] and conf_rect[1] <= y <= conf_rect[3]:
        # Clicou no quadrado de configuração
        canvas_main.pack_forget()
        canvas_config.pack(fill="both", expand=True)
        current_canvas = canvas_config
        
    elif current_canvas is not canvas_main and main_rect[0] <= x <= main_rect[2] and main_rect[1] <= y <= main_rect[3]:
        # Clicou no quadrado de configuração
        current_canvas.pack_forget()
        canvas_main.pack(fill="both", expand=True)
        current_canvas = canvas_main

def update_camera_feed():
    global colorFrame, current_canvas

    if current_canvas is canvas_camara:
        colorToDepthFrame, depthFrame, colorFrame = getFrame(camera)

        if colorFrame.dtype != numpy.uint8:
            # Normaliza para 0-255 e converte para uint8
            frame_uint8 = (numpy.clip(colorFrame, 0, 1) * 255).astype(numpy.uint8)
        else:
            frame_uint8 = colorFrame

        frame_rgb = frame_uint8[:, :, ::-1]  # se BGR

        pil_img = Image.fromarray(frame_rgb)
        pil_img = pil_img.resize((1200, 900), Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(pil_img)
        current_canvas.image = tk_img

        cw = current_canvas.winfo_width()
        ch = current_canvas.winfo_height()

        # Calcular coordenadas para centrar a imagem
        x_img = cw // 2
        y_img = ch // 2

        # Desenhar imagem centrada
        current_canvas.create_image(x_img, y_img + 50, image=tk_img, anchor="center")

        current_canvas.after(30, update_camera_feed)
#-----------------------------------------------------------------

canvas_main.bind("<Button-1>", change_canvas)
canvas_camara.bind("<Button-1>", change_canvas)
#canvas_barcode.bind("<Button-1>", change_canvas)
#canvas_volume.bind("<Button-1>", change_canvas)
canvas_config.bind("<Button-1>", change_canvas)

# ESC to Close
root.bind("<Escape>", lambda e: root.destroy())
root.mainloop()