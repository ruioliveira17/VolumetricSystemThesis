import tkinter as tk
import customtkinter
import cv2

from PIL import Image, ImageTk
import ctypes
import numpy
import base64
import sys
sys.path.append('C:/Tese/Python')

from API.VzenseDS_api import *
import time
import threading

sys.path.append('C:/Tese/Python/Samples/DS86/FrameViewer')

from CameraOptions import openCamera, closeCamera, statusCamera
from HDRDef import hdrAPI

import uvicorn
import requests

def run_api():
    uvicorn.run("api:app", host="127.0.0.1", port=8000, log_level="info")

api_thread = threading.Thread(target=run_api, daemon=True)
api_thread.start()

#def hdr_thread(stop_event, pause_event):
#    while not stop_event.is_set():
#        pause_event.wait()
#        try:
#            hdrAPI()
#        except Exception as e:
#            print("Erro na thread:", repr(e))
#        finally :
#            print('Funcionou')

overlay = None

hmin_label = None
hmax_label = None
smin_label = None
smax_label = None
vmin_label = None
vmax_label = None

colorToDepthFrame = None
depthFrame = None 
colorFrame = None

hmin_slider = None
hmax_slider = None
smin_slider = None
smax_slider = None
vmin_slider = None
vmax_slider = None

res = None
colorToDepthFrame_copy = None
depthFrame_copy = None

color_shape = (1200, 1600, 3)
colorToDepth_shape = (480, 640, 3)
depth_shape = (480, 640)
colorToDepthCopy_shape = (480, 640, 3)
depthCopy_shape = (480, 640, 3)
colorToDepthObject_shape = (480, 640, 3)

#hdr_thread_started = False

#stop_event = threading.Event()
#pause_event = threading.Event()
#pause_event.set()

openCamera()

#if hdr_thread_started:
#    pause_event.set()
#    print("Thread HDR saiu de pausa!")
#else:
#    hdr_thread = threading.Thread(target=hdr_thread, args=(stop_event, pause_event))
#    hdr_thread.start()
#    hdr_thread_started = True
#    print("Thread HDR iniciada!") 

def calibrate_click():
    global calibrate_label, caliError_label
    try:
        r = requests.get("http://127.0.0.1:8000/mask", timeout=0.2)
        maskValues = r.json()

        requests.post("http://127.0.0.1:8000/calibrate", json=maskValues, timeout=0.5)

        r = requests.get("http://127.0.0.1:8000/calibrate/flags", timeout=0.2)
        data = r.json()

        center_aligned = data["Center Aligned"]
        ws_clear = data["Workspace Clear"]

        TextCalibrated = "System Calibrated"
        TextNotCalibrated = "System was not Calibrated"
        TextError = "Error"
        TextWsNotEmpty = "Workspace isn't Empty"
        TextCenterNotAligned = "Center Point isn't Aligned"
        TextWsNotEmptyAndCenterNotAligned = "Center Point isn't Aligned and Workspace isn't Empty"
        TextClear = ""

        if center_aligned and ws_clear:
            calibrate_label.configure(text=f"{TextCalibrated}")
            caliError_label.configure(text=f"{TextClear}")
        elif center_aligned and not ws_clear:
            calibrate_label.configure(text=f"{TextNotCalibrated}")
            caliError_label.configure(text=f"{TextWsNotEmpty}")
        elif not center_aligned and ws_clear:
            calibrate_label.configure(text=f"{TextNotCalibrated}")
            caliError_label.configure(text=f"{TextCenterNotAligned}")
        else:
            calibrate_label.configure(text=f"{TextNotCalibrated}")
            caliError_label.configure(text=f"{TextWsNotEmptyAndCenterNotAligned}")

    except requests.exceptions.RequestException:
        calibrate_label.configure(text=f"{TextError}")
        caliError_label.configure(text=f"{TextError}")
        pass
    
    #detection_area, workspace_depth, forced_exiting = calibrate(camState.camera, get_lower, get_upper, camState.colorSlope)

def volume_click():
    global volume_value_label, x_length_value_label, y_length_value_label, height_value_label
    try:
        r = requests.post("http://127.0.0.1:8000/volumeObj", timeout=5)
        data = r.json()

        volume = data["volume"]
        width = data["width"]
        height = data["height"]
        min_depth = data["min_depth"]
        ws_depth = data["ws_depth"]

        height_obj = ws_depth - min_depth

        volume_value_label.configure(text=f"{volume:.8f} m³")
        x_length_value_label.configure(text=f"{width:.1f} cm")
        y_length_value_label.configure(text=f"{height:.1f} cm")
        height_value_label.configure(text=f"{height_obj:.1f} cm")

        data = requests.get("http://127.0.0.1:8000/getFrame/colorToDepthObject")
        colorToDepthObjectFrame = numpy.frombuffer(data.content, dtype=numpy.uint8).reshape(colorToDepth_shape)

        if colorToDepthObjectFrame.dtype != numpy.uint8:
            # Normaliza para 0-255 e converte para uint8
            frame_uint8 = (numpy.clip(colorToDepthObjectFrame, 0, 1) * 255).astype(numpy.uint8)
        else:
            frame_uint8 = colorToDepthObjectFrame

        frame_object = frame_uint8[:, :, ::-1]  # se BGR

        pil_obj = Image.fromarray(frame_object)
        pil_obj = pil_obj.resize((560, 420), Image.LANCZOS)
        objecttk_img = ImageTk.PhotoImage(pil_obj)
        canvas_volume.tk_object = objecttk_img

        current_canvas.create_image(1500, 400, image=objecttk_img, anchor="center")

        data = requests.get("http://127.0.0.1:8000/getFrame/colorToDepthObjects")
        colorToDepthObjectsFrame = numpy.frombuffer(data.content, dtype=numpy.uint8).reshape(colorToDepth_shape)

        if colorToDepthObjectsFrame.dtype != numpy.uint8:
            # Normaliza para 0-255 e converte para uint8
            frame_uint8 = (numpy.clip(colorToDepthObjectsFrame, 0, 1) * 255).astype(numpy.uint8)
        else:
            frame_uint8 = colorToDepthObjectsFrame

        frame_objects = frame_uint8[:, :, ::-1]  # se BGR

        pil_objs = Image.fromarray(frame_objects)
        pil_objs = pil_objs.resize((560, 420), Image.LANCZOS)
        objectstk_img = ImageTk.PhotoImage(pil_objs)
        canvas_volume.tk_objects = objectstk_img

        current_canvas.create_image(1500, 830, image=objectstk_img, anchor="center")

    except requests.exceptions.RequestException:
        volume_value_label.configure(text="Erro")
        x_length_value_label.configure(text="Erro")
        y_length_value_label.configure(text="Erro")
        height_value_label.configure(text="Erro")
        print("Erro ao atualizar volume:")
        pass

def capFrame():
    try:
        requests.post("http://127.0.0.1:8000/captureFrame", timeout=0.2)
    except requests.exceptions.RequestException:
        pass

    data = requests.get("http://127.0.0.1:8000/getFrame/color")
    colorFrame = numpy.frombuffer(data.content, dtype=numpy.uint8).reshape(color_shape)

    data = requests.get("http://127.0.0.1:8000/getFrame/colorToDepth")
    colorToDepthFrame   = numpy.frombuffer(data.content, dtype=numpy.uint8).reshape(colorToDepth_shape)
    
    data = requests.get("http://127.0.0.1:8000/getFrame/depth")
    depthFrame = numpy.frombuffer(data.content, dtype=numpy.uint16).reshape(depth_shape)

def StaticDynamic_toggle():
    if StaticDynamic_var.get():
        requests.post("http://127.0.0.1:8000/mode/dynamic")
    else:
        requests.post("http://127.0.0.1:8000/mode/static")

def apply_mask():
    try:
        r = requests.get("http://127.0.0.1:8000/mask", timeout=0.2)
        maskValues = r.json()
        
        requests.post("http://127.0.0.1:8000/applyMask", json=maskValues ,timeout=0.5)
    except requests.exceptions.RequestException:
        pass

def getMinDepth():
    try:
        requests.post("http://127.0.0.1:8000/depth", timeout=5)
    except requests.exceptions.RequestException:
        pass

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
last_canvas = None

label = tk.Label(canvas_main, bg='white', text="Menu", font=('Arial', 70))
label.pack(pady = 20)

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
canvas_main.create_rectangle(cam_rect, fill="turquoise1")

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
canvas_main.create_rectangle(code_rect, fill="SpringGreen2")

# Barcode Icon
code_icon = Image.open("barcode.png").resize((330, 330))
code_icon_tk = ImageTk.PhotoImage(code_icon)
code_icon_x = code_x + code_width/2 - 330/2
code_icon_y = code_y + code_height/2 - 330/2
canvas_main.create_image(code_icon_x, code_icon_y, anchor='nw', image=code_icon_tk)

#-----------------------------------------------------------------

#--------------------- Dimensions Interface ----------------------

# Blue Rectangle
dim_height, dim_width = 300, 400
dim_x, dim_y = 1320, 250
dim_rect = [dim_x, dim_y, dim_x + dim_width, dim_y + dim_height]
canvas_main.create_rectangle(dim_rect, fill="turquoise1")

# Dim Icon
dim_icon = Image.open("boxVol.png").resize((450, 450))
dim_icon_tk = ImageTk.PhotoImage(dim_icon)
dim_icon_x = dim_x + dim_width/2 - 450/2
dim_icon_y = dim_y + dim_height/2 - 450/2
canvas_main.create_image(dim_icon_x, dim_icon_y, anchor='nw', image=dim_icon_tk)

#-----------------------------------------------------------------

#---------------------- Storage Interface ------------------------

# Blue Rectangle
sto_height, sto_width = 300, 400
sto_x, sto_y = 200, 630
sto_rect = [sto_x, sto_y, sto_x + sto_width, sto_y + sto_height]
canvas_main.create_rectangle(sto_rect, fill="SpringGreen2")

# Barcode Icon
sto_icon = Image.open("storage.png").resize((330, 330))
sto_icon_tk = ImageTk.PhotoImage(sto_icon)
sto_icon_x = sto_x + sto_width/2 - 330/2
sto_icon_y = sto_y + sto_height/2 - 330/2
canvas_main.create_image(sto_icon_x, sto_icon_y, anchor='nw', image=sto_icon_tk)

#-----------------------------------------------------------------

#---------------------- Stacking Interface -----------------------

# Blue Rectangle
stack_height, stack_width = 300, 400
stack_x, stack_y = 760, 630
stack_rect = [stack_x, stack_y, stack_x + stack_width, stack_y + stack_height]
canvas_main.create_rectangle(stack_rect, fill="turquoise1")

# Dim Icon
stack_icon = Image.open("stacking.png").resize((450, 450))
stack_icon_tk = ImageTk.PhotoImage(stack_icon)
stack_icon_x = stack_x + stack_width/2 - 450/2
stack_icon_y = stack_y + stack_height/2 - 450/2
canvas_main.create_image(stack_icon_x, stack_icon_y, anchor='nw', image=stack_icon_tk)

#-----------------------------------------------------------------

#----------------------- Config Interface ------------------------

# Grey Rectangle
conf_height, conf_width = 300, 400
conf_x, conf_y = 1320, 630
conf_rect = [conf_x, conf_y, conf_x + conf_width, conf_y + conf_height]
canvas_main.create_rectangle(conf_rect, fill="SpringGreen2")

# Config Icon
conf_icon = Image.open("conf_icon.png").resize((400, 400))
conf_icon_tk = ImageTk.PhotoImage(conf_icon)
conf_icon_x = conf_x + conf_width/2 - 400/2
conf_icon_y = conf_y + conf_height/2 - 400/2
canvas_main.create_image(conf_icon_x, conf_icon_y, anchor='nw', image=conf_icon_tk)

#-----------------------------------------------------------------

#------------------------ Camara Canvas --------------------------

canvas_camara = tk.Canvas(root, bg='white', highlightthickness=0)

label = tk.Label(canvas_camara, bg='white', text="Câmara", font=('Arial', 70))
label.pack(pady = 20)

#--------------------- Logo Balanças Marques ---------------------
BM_logo = Image.open("BM_Logo.png").resize((360, 152))
BM_logo_tk_cam = ImageTk.PhotoImage(BM_logo)
canvas_camara.create_image(10, 10, anchor='nw', image=BM_logo_tk_cam)

#-----------------------------------------------------------------

#------------------------ QR/BarCode Canvas ----------------------

canvas_barcode = tk.Canvas(root, bg='white', highlightthickness=0)

label = tk.Label(canvas_barcode, bg='white', text="Code Reader", font=('Arial', 70))
label.pack(pady = 20)

#--------------------- Logo Balanças Marques ---------------------
BM_logo = Image.open("BM_Logo.png").resize((360, 152))
BM_logo_tk_barcode = ImageTk.PhotoImage(BM_logo)
canvas_barcode.create_image(10, 10, anchor='nw', image=BM_logo_tk_barcode)

#-----------------------------------------------------------------

#------------------------ Volume Canvas --------------------------

canvas_volume = tk.Canvas(root, bg='white', highlightthickness=0)

label = tk.Label(canvas_volume, bg='white', text="Dimensões", font=('Arial', 70))
label.pack(pady = 20)

#--------------------- Logo Balanças Marques ---------------------
BM_logo = Image.open("BM_Logo.png").resize((360, 152))
BM_logo_tk_volume = ImageTk.PhotoImage(BM_logo)
canvas_volume.create_image(10, 10, anchor='nw', image=BM_logo_tk_volume)

#-----------------------------------------------------------------

volume_button = tk.Button(canvas_volume, text="Volume Info", font=("Arial", 20), width=25, height=1, command=volume_click)
canvas_volume.create_window(780, 850, anchor="nw", window=volume_button)

volume_label = customtkinter.CTkLabel(canvas_volume, text="Volume:", text_color="black", font=("Arial", 36))
volume_label.place(x=800, y=280)
x_length_label = customtkinter.CTkLabel(canvas_volume, text="X:", text_color="black", font=("Arial", 36))
x_length_label.place(x=800, y=430)
y_length_label = customtkinter.CTkLabel(canvas_volume, text="Y:", text_color="black", font=("Arial", 36))
y_length_label.place(x=800, y=580)
height_label = customtkinter.CTkLabel(canvas_volume, text="Height:", text_color="black", font=("Arial", 36))
height_label.place(x=800, y=730)

volume_value_label = customtkinter.CTkLabel(canvas_volume, text="", text_color="black", font=("Arial", 36))
volume_value_label.place(x=950, y=280)
x_length_value_label = customtkinter.CTkLabel(canvas_volume, text="", text_color="black", font=("Arial", 36))
x_length_value_label.place(x=950, y=430)
y_length_value_label = customtkinter.CTkLabel(canvas_volume, text="", text_color="black", font=("Arial", 36))
y_length_value_label.place(x=950, y=580)
height_value_label = customtkinter.CTkLabel(canvas_volume, text="", text_color="black", font=("Arial", 36))
height_value_label.place(x=950, y=730)

#------------------------- Storage Canvas ------------------------

canvas_storage = tk.Canvas(root, bg='white', highlightthickness=0)

label = tk.Label(canvas_storage, bg='white', text="Armazenamento", font=('Arial', 70))
label.pack(pady = 20)

#--------------------- Logo Balanças Marques ---------------------
BM_logo = Image.open("BM_Logo.png").resize((360, 152))
BM_logo_tk_storage = ImageTk.PhotoImage(BM_logo)
canvas_storage.create_image(10, 10, anchor='nw', image=BM_logo_tk_storage)

#-----------------------------------------------------------------

#----------------------- Stacking Canvas -------------------------

canvas_stacking = tk.Canvas(root, bg='white', highlightthickness=0)

label = tk.Label(canvas_stacking, bg='white', text="Empilhamento", font=('Arial', 70))
label.pack(pady = 20)

#--------------------- Logo Balanças Marques ---------------------
BM_logo = Image.open("BM_Logo.png").resize((360, 152))
BM_logo_tk_stacking = ImageTk.PhotoImage(BM_logo)
canvas_stacking.create_image(10, 10, anchor='nw', image=BM_logo_tk_stacking)

#-----------------------------------------------------------------

#------------------------ Config Canvas --------------------------

canvas_config = tk.Canvas(root, bg='white', highlightthickness=0)

label = tk.Label(canvas_config, bg='white', text="Configurações", font=('Arial', 70))
label.pack(pady = 20)

#--------------------- Logo Balanças Marques ---------------------

BM_logo = Image.open("BM_Logo.png").resize((360, 152))
BM_logo_tk_config = ImageTk.PhotoImage(BM_logo)
canvas_config.create_image(10, 10, anchor='nw', image=BM_logo_tk_config)

#------------------ Static / Dynamic Interface -------------------

StaticDynamic_var = customtkinter.BooleanVar(value=False)

StaticDynamic_switch = customtkinter.CTkSwitch(canvas_config, text="", variable=StaticDynamic_var, onvalue=True, offvalue=False, command=StaticDynamic_toggle, switch_width=100, switch_height=50, fg_color="turquoise1", progress_color="dark turquoise", button_color="gray65", button_hover_color="gray45")
canvas_config.create_window(290, 495, anchor="nw", window=StaticDynamic_switch)

label_static = tk.Label(canvas_config, text="Static", bg="white", font=("Arial", 20))
label_dynamic = tk.Label(canvas_config, text="Dynamic", bg="white", font=("Arial", 20))
canvas_config.create_window(200, 500, anchor="nw", window=label_static)
canvas_config.create_window(400, 500, anchor="nw", window=label_dynamic)

#-------------------- Calibration Interface ----------------------

# Blue Rectangle
cal_height, cal_width = 50, 1520
cal_x, cal_y = 200, 250
cal_rect = [cal_x, cal_y, cal_x + cal_width, cal_y + cal_height]
canvas_config.create_rectangle(cal_rect, fill="turquoise1")

label = tk.Label(canvas_config, bg = "turquoise1", text="Calibração", font=('Arial',18))
label.pack(pady = 110)

#-----------------------------------------------------------------

#--------------------- Calibration Canvas ------------------------

canvas_calibration = tk.Canvas(root, bg='white', highlightthickness=0)

label = tk.Label(canvas_calibration, bg='white', text="Calibração", font=('Arial', 70))
label.pack(pady = 20)

#--------------------- Logo Balanças Marques ---------------------
BM_logo = Image.open("BM_Logo.png").resize((360, 152))
BM_logo_tk_calibration = ImageTk.PhotoImage(BM_logo)
canvas_calibration.create_image(10, 10, anchor='nw', image=BM_logo_tk_calibration)

#----------------------------- Botão -----------------------------
calibration_button = tk.Button(canvas_calibration, text="Calibrate", font=("Arial", 20), width=30, height=1, command=calibrate_click)
canvas_calibration.create_window(1100, 850, anchor="nw", window=calibration_button)

#-----------------------------------------------------------------

calibrate_label = customtkinter.CTkLabel(canvas_calibration, text="", text_color="black", font=("Arial", 20))
calibrate_label.place(x=950, y=130, anchor="center")
caliError_label = customtkinter.CTkLabel(canvas_calibration, text="", text_color="black", font=("Arial", 20))
caliError_label.place(x=950, y=160, anchor="center")

#---------------------------- Events -----------------------------

def change_canvas(event):
    global current_canvas, last_canvas, colorToDepthFrame, depthFrame, res
    x, y = event.x, event.y
    if current_canvas is canvas_main and cam_rect[0] <= x <= cam_rect[2] and cam_rect[1] <= y <= cam_rect[3]:
        # Clicou no quadrado da camera
        canvas_main.pack_forget()
        canvas_camara.pack(fill="both", expand=True)
        current_canvas = canvas_camara
        last_canvas = canvas_main

        current_canvas.update()
        update_camera_feed()

    elif current_canvas is canvas_main and code_rect[0] <= x <= code_rect[2] and code_rect[1] <= y <= code_rect[3]:
        # Clicou no quadrado do código de barras
        canvas_main.pack_forget()
        canvas_barcode.pack(fill="both", expand=True)
        current_canvas = canvas_barcode
        last_canvas = canvas_main

    elif current_canvas is canvas_main and dim_rect[0] <= x <= dim_rect[2] and dim_rect[1] <= y <= dim_rect[3]:
        # Clicou no quadrado do volume
        canvas_main.pack_forget()
        canvas_volume.pack(fill="both", expand=True)
        current_canvas = canvas_volume
        last_canvas = canvas_main

        current_canvas.update()
        update_camera_feed()

    elif current_canvas is canvas_main and sto_rect[0] <= x <= sto_rect[2] and sto_rect[1] <= y <= sto_rect[3]:
        # Clicou no quadrado de storaging
        canvas_main.pack_forget()
        canvas_storage.pack(fill="both", expand=True)
        current_canvas = canvas_storage
        last_canvas = canvas_main

    elif current_canvas is canvas_main and stack_rect[0] <= x <= stack_rect[2] and stack_rect[1] <= y <= stack_rect[3]:
        # Clicou no quadrado de stacking
        canvas_main.pack_forget()
        canvas_stacking.pack(fill="both", expand=True)
        current_canvas = canvas_stacking
        last_canvas = canvas_main

    elif current_canvas is canvas_main and conf_rect[0] <= x <= conf_rect[2] and conf_rect[1] <= y <= conf_rect[3]:
        # Clicou no quadrado de configuração
        canvas_main.pack_forget()
        canvas_config.pack(fill="both", expand=True)
        current_canvas = canvas_config
        last_canvas = canvas_main

        refresh_toggle()
        
    elif current_canvas is not canvas_main and main_rect[0] <= x <= main_rect[2] and main_rect[1] <= y <= main_rect[3]:
        # Clicou para regressar
        if last_canvas != None:
            current_canvas.pack_forget()
            last_canvas.pack(fill="both", expand=True)
            current_canvas = last_canvas
            if current_canvas is canvas_config:
                refresh_toggle()
            if last_canvas != canvas_main:
                last_canvas = canvas_main
            else:
                last_canvas = None

    elif current_canvas is canvas_config and cal_rect[0] <= x <= cal_rect[2] and cal_rect[1] <= y <= cal_rect[3]:
        # Clicou no quadrado de calibração
        canvas_config.pack_forget()
        canvas_calibration.pack(fill="both", expand=True)
        current_canvas = canvas_calibration
        last_canvas = canvas_config
        
        current_canvas.update()
        update_sliders()
        refresh_sliders()
        update_camera_feed()

def update_camera_feed():
    global colorFrame, current_canvas, colorToDepthFrame, depthFrame, colorFrame, res, color_shape, colorToDepth_shape, depth_shape

    #-------------------------------------------------------------  Camara  ------------------------------------------------------------------------

    if current_canvas is canvas_camara:
        try:
            requests.post("http://127.0.0.1:8000/captureFrame", timeout=0.5)
        except requests.exceptions.RequestException:
            pass

        data = requests.get("http://127.0.0.1:8000/getFrame/color")
        colorFrame = numpy.frombuffer(data.content, dtype=numpy.uint8).reshape(color_shape)

        #data = requests.get("http://127.0.0.1:8000/getFrame/colorToDepth")
        #colorToDepthFrame   = numpy.frombuffer(data.content, dtype=numpy.uint8).reshape(colorToDepth_shape)
        
        #data = requests.get("http://127.0.0.1:8000/getFrame/depth")
        #depthFrame = numpy.frombuffer(data.content, dtype=numpy.uint16).reshape(depth_shape)

        #data = requests.get("http://localhost:8000/getFrame")
        #frames_bytes = data.content.split(b"__FRAME__")

        #colorFrame = numpy.frombuffer(frames_bytes[0], dtype=numpy.uint8).reshape(color_shape)
        #colorToDepthFrame   = numpy.frombuffer(frames_bytes[1], dtype=numpy.uint8).reshape(colorToDepth_shape)
        #depthFrame = numpy.frombuffer(frames_bytes[2], dtype=numpy.uint8).reshape(depth_shape)

        #colorToDepthFrame, depthFrame, colorFrame = getFrame(camState.camera)

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

        current_canvas.after(10, update_camera_feed)

    #-------------------------------------------------------------  Volume  ------------------------------------------------------------------------

    if current_canvas is canvas_volume:
        try:
            requests.post("http://127.0.0.1:8000/captureFrame", timeout=0.5)
        except requests.exceptions.RequestException:
            pass

        data = requests.get("http://127.0.0.1:8000/getFrame/color")
        colorFrame = numpy.frombuffer(data.content, dtype=numpy.uint8).reshape(color_shape)

        data = requests.get("http://127.0.0.1:8000/getFrame/colorToDepth")
        colorToDepthFrame = numpy.frombuffer(data.content, dtype=numpy.uint8).reshape(colorToDepth_shape)
        
        data = requests.get("http://127.0.0.1:8000/getFrame/depth")
        depthFrame = numpy.frombuffer(data.content, dtype=numpy.uint16).reshape(depth_shape)

        data = requests.get("http://127.0.0.1:8000/camera/colorSlope", timeout=1)
        colorSlope = data.json()["colorSlope"]

        if colorToDepthFrame.dtype != numpy.uint8:
            # Normaliza para 0-255 e converte para uint8
            frame_uint8 = (numpy.clip(colorToDepthFrame, 0, 1) * 255).astype(numpy.uint8)
        else:
            frame_uint8 = colorToDepthFrame

        frame_rgb = frame_uint8[:, :, ::-1]  # se BGR

        pil_img = Image.fromarray(frame_rgb)
        pil_img = pil_img.resize((560, 420), Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(pil_img)
        current_canvas.tk_image = tk_img

        img = numpy.int32(depthFrame)
        img = img*255/colorSlope
        img = numpy.clip(img, 0, 255)
        img = numpy.uint8(img)
        depth_img = cv2.applyColorMap(img, cv2.COLORMAP_RAINBOW)

        if depth_img.dtype != numpy.uint8:
            # Normaliza para 0-255 e converte para uint8
            frame_uint8 = (numpy.clip(depth_img, 0, 1) * 255).astype(numpy.uint8)
        else:
            frame_uint8 = depth_img

        frame_depth = frame_uint8[:, :, ::-1]  # se BGR

        pil_depth = Image.fromarray(frame_depth)
        pil_depth = pil_depth.resize((560, 420), Image.LANCZOS)
        tk_depth = ImageTk.PhotoImage(pil_depth)
        current_canvas.tk_depth = tk_depth

        cw = current_canvas.winfo_width()
        ch = current_canvas.winfo_height()

        # Calcular coordenadas para centrar a imagem
        x_img = cw // 2
        y_img = ch // 2

        # Desenhar imagem centrada
        #current_canvas.create_image(x_img, y_img + 50, image=tk_img, anchor="center")
        current_canvas.create_image(480, 400, image=tk_depth, anchor="center")
        current_canvas.create_image(480, 830, image=tk_img, anchor="center")

        #getMinDepth()

        #try:
        #    requests.post("http://127.0.0.1:8000/depth/min", timeout=0.2)
        #except requests.exceptions.RequestException:
        #    pass

        #r = requests.get("http://127.0.0.1:8000/depth/notSet")
        #not_set = r.json()["not_set"]

        #try:
        #    requests.post("http://127.0.0.1:8000/volume", timeout=2)
        #except requests.exceptions.RequestException:
        #    pass

        #try:
        #    requests.post("http://127.0.0.1:8000/volumeObj", timeout=5)
        #except requests.exceptions.RequestException:
        #    pass

        #current_canvas.after(50, getMinDepth)
        current_canvas.after(70, update_camera_feed)

    #-----------------------------------------------------------  Calibração  ----------------------------------------------------------------------

    if current_canvas is canvas_calibration:
        try:
            requests.post("http://127.0.0.1:8000/captureFrame", timeout=0.5)
        except requests.exceptions.RequestException:
            pass

        data = requests.get("http://127.0.0.1:8000/getFrame/color")
        colorFrame = numpy.frombuffer(data.content, dtype=numpy.uint8).reshape(color_shape)

        data = requests.get("http://127.0.0.1:8000/getFrame/colorToDepth")
        colorToDepthFrame   = numpy.frombuffer(data.content, dtype=numpy.uint8).reshape(colorToDepth_shape)
        
        data = requests.get("http://127.0.0.1:8000/getFrame/depth")
        depthFrame = numpy.frombuffer(data.content, dtype=numpy.uint16).reshape(depth_shape)

        #APLICAR MASCARA
        apply_mask()

        data = requests.get("http://127.0.0.1:8000/getFrame/colorToDepthCopy")
        colorToDepthFrame_copy = numpy.frombuffer(data.content, dtype=numpy.uint8).reshape(colorToDepthCopy_shape)

        data = requests.get("http://127.0.0.1:8000/getFrame/depthCopy")
        depthFrame_copy = numpy.frombuffer(data.content, dtype=numpy.uint8).reshape(depthCopy_shape)

        data = requests.get("http://127.0.0.1:8000/getFrame/res")
        res = numpy.frombuffer(data.content, dtype=numpy.uint8).reshape(depthCopy_shape)
        #res, colorToDepthFrame_copy, depthFrame_copy = maskAPI(camState.camera, lambda: get_lower(), lambda: get_upper(), camState.colorSlope)

        if colorToDepthFrame_copy is None:
            if colorToDepthFrame.dtype != numpy.uint8:
                # Normaliza para 0-255 e converte para uint8
                frame_uint8 = (numpy.clip(colorToDepthFrame, 0, 1) * 255).astype(numpy.uint8)
            else:
                frame_uint8 = colorToDepthFrame

        else: 
            if colorToDepthFrame_copy.dtype != numpy.uint8:
                # Normaliza para 0-255 e converte para uint8
                frame_uint8 = (numpy.clip(colorToDepthFrame_copy, 0, 1) * 255).astype(numpy.uint8)
            else:
                frame_uint8 = colorToDepthFrame_copy

        frame_rgb = frame_uint8[:, :, ::-1]  # se BGR

        pil_img = Image.fromarray(frame_rgb)
        pil_img = pil_img.resize((560, 420), Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(pil_img)
        current_canvas.tk_image = tk_img

        if res is None:
            res = numpy.zeros((480, 640, 3), dtype=numpy.uint8)

        if res.dtype != numpy.uint8:
            # Normaliza para 0-255 e converte para uint8
            frame_uint8 = (numpy.clip(res, 0, 1) * 255).astype(numpy.uint8)
        else:
            frame_uint8 = res

        frame_mask = frame_uint8[:, :, ::-1]  # se BGR

        pil_mask = Image.fromarray(frame_mask)
        pil_mask = pil_mask.resize((560, 420), Image.LANCZOS)
        tk_mask = ImageTk.PhotoImage(pil_mask)
        current_canvas.tk_mask = tk_mask

        cw = current_canvas.winfo_width()
        ch = current_canvas.winfo_height()

        # Calcular coordenadas para centrar a imagem
        x_img = cw // 2
        y_img = ch // 2

        # Desenhar imagem centrada
        current_canvas.create_image(480, 400, image=tk_img, anchor="center")
        current_canvas.create_image(480, 830, image=tk_mask, anchor="center")

        current_canvas.after(10, refresh_sliders)
        current_canvas.after(50, apply_mask)
        #current_canvas.after(50, maskAPI, camState.camera, get_lower, get_upper, camState.colorSlope)
        current_canvas.after(70, update_camera_feed)

        #workspace, workspace_depth, fex_flag = calibrate(camera, colorSlope)

def update_sliders():
    global current_canvas, hmin_label, hmax_label, smin_label, smax_label, vmin_label, vmax_label, hmin_slider, smin_slider, vmin_slider, hmax_slider, smax_slider, vmax_slider
    if current_canvas is canvas_calibration:
        #MIN HUE SLIDER

        hmin_slider = customtkinter.CTkSlider(current_canvas, from_= 0, to = 179, command = sliding_hmin, width = 500, height = 50)
        hmin_slider.place(x=1100, y=250)
        hmin_slider.set(0)
        hmin_label = customtkinter.CTkLabel(current_canvas, text="Minimum Hue:", text_color="black", font=("Arial", 18))
        hmin_label.place(x=1650, y=260)
        hmin_label = customtkinter.CTkLabel(current_canvas, text=hmin_slider.get(), text_color="black", font=("Arial", 18))
        hmin_label.place(x=1820, y=260)

        #MAX HUE SLIDER

        hmax_slider = customtkinter.CTkSlider(current_canvas, from_= 0, to = 179, command = sliding_hmax, width = 500, height = 50)
        hmax_slider.place(x=1100, y=350)
        hmax_slider.set(179)
        hmax_label = customtkinter.CTkLabel(current_canvas, text="Maximum Hue:", text_color="black", font=("Arial", 18))
        hmax_label.place(x=1650, y=360)
        hmax_label = customtkinter.CTkLabel(current_canvas, text=hmax_slider.get(), text_color="black", font=("Arial", 18))
        hmax_label.place(x=1820, y=360)

        #MIN SATURATION SLIDER

        smin_slider = customtkinter.CTkSlider(current_canvas, from_= 0, to = 255, command = sliding_smin, width = 500, height = 50)
        smin_slider.place(x=1100, y=450)
        smin_slider.set(0)
        smin_label = customtkinter.CTkLabel(current_canvas, text="Minimum Saturation:", text_color="black", font=("Arial", 18))
        smin_label.place(x=1650, y=460)
        smin_label = customtkinter.CTkLabel(current_canvas, text=smin_slider.get(), text_color="black", font=("Arial", 18))
        smin_label.place(x=1820, y=460)

        #MAX SATURATION SLIDER

        smax_slider = customtkinter.CTkSlider(current_canvas, from_= 0, to = 255, command = sliding_smax, width = 500, height = 50)
        smax_slider.place(x=1100, y=550)
        smax_slider.set(255)
        smax_label = customtkinter.CTkLabel(current_canvas, text="Maximum Saturation:", text_color="black", font=("Arial", 18))
        smax_label.place(x=1650, y=560)
        smax_label = customtkinter.CTkLabel(current_canvas, text=smax_slider.get(), text_color="black", font=("Arial", 18))
        smax_label.place(x=1820, y=560)

        #MIN VALUE SLIDER

        vmin_slider = customtkinter.CTkSlider(current_canvas, from_= 0, to = 255, command = sliding_vmin, width = 500, height = 50)
        vmin_slider.place(x=1100, y=650)
        vmin_slider.set(0)
        vmin_label = customtkinter.CTkLabel(current_canvas, text="Minimum Value:", text_color="black", font=("Arial", 18))
        vmin_label.place(x=1650, y=660)
        vmin_label = customtkinter.CTkLabel(current_canvas, text=vmin_slider.get(), text_color="black", font=("Arial", 18))
        vmin_label.place(x=1820, y=660)

        #MAX VALUE SLIDER

        vmax_slider = customtkinter.CTkSlider(current_canvas, from_= 0, to = 255, command = sliding_vmax, width = 500, height = 50)
        vmax_slider.place(x=1100, y=750)
        vmax_slider.set(255)
        vmax_label = customtkinter.CTkLabel(current_canvas, text="Maximum Value:", text_color="black", font=("Arial", 18))
        vmax_label.place(x=1650, y=760)
        vmax_label = customtkinter.CTkLabel(current_canvas, text=vmax_slider.get(), text_color="black", font=("Arial", 18))
        vmax_label.place(x=1820, y=760)

def confirm_exit_overlay(event = None):
    global overlay

    if overlay is not None:
        return

    overlay = tk.Frame(root, bg="", highlightthickness=0, bd=0)
    overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

    box = tk.Frame(overlay, bg="lightgrey", padx=40, pady=30, highlightbackground="black", highlightthickness=1)
    box.place(relx=0.5, rely=0.5, anchor="center")

    label = tk.Label(box, text="Queres mesmo sair? :(",
                     fg="black", bg="lightgrey", font=("Arial", 14))
    label.pack(pady=(0, 20))

    btn_yes = tk.Button(box, text="Sim!", width=10, command=exit_app)
    btn_yes.pack(side="left", padx=10)

    btn_no = tk.Button(box, text="Não!", width=10, command=close_overlay)
    btn_no.pack(side="right", padx=10)

def close_overlay():
    global overlay
    if overlay is not None:
        overlay.destroy()
        overlay = None

def exit_app():
    #stop_event.set()
    #pause_event.set()
    root.destroy()
    closeCamera()

def sliding_hmin(value):
    hmin = int(value)
    try:
        requests.post("http://127.0.0.1:8000/mask/hmin",json={"hmin":hmin}, timeout=0.1)
    except requests.exceptions.RequestException:
        pass

def sliding_hmax(value):
    hmax = int(value)
    try:
        requests.post("http://127.0.0.1:8000/mask/hmax",json={"hmax":hmax}, timeout=0.1)
    except requests.exceptions.RequestException:
        pass

def sliding_smin(value):
    smin = int(value)
    try:
        requests.post("http://127.0.0.1:8000/mask/smin",json={"smin":smin}, timeout=0.1)
    except requests.exceptions.RequestException:
        pass

def sliding_smax(value):
    smax = int(value)
    try:
        requests.post("http://127.0.0.1:8000/mask/smax",json={"smax":smax}, timeout=0.1)
    except requests.exceptions.RequestException:
        pass

def sliding_vmin(value):
    vmin = int(value)
    try:
        requests.post("http://127.0.0.1:8000/mask/vmin",json={"vmin":vmin}, timeout=0.1)
    except requests.exceptions.RequestException:
        pass

def sliding_vmax(value):
    vmax = int(value)
    try:
        requests.post("http://127.0.0.1:8000/mask/vmax",json={"vmax":vmax}, timeout=0.1)
    except requests.exceptions.RequestException:
        pass

def refresh_sliders():
    try:
        r = requests.get("http://127.0.0.1:8000/mask", timeout = 0.2)
        data = r.json()

        hmin_slider.set(int(data["hmin"]))
        hmin_label.configure(text=str(int(data["hmin"])))
        hmax_slider.set(int(data["hmax"]))
        hmax_label.configure(text=str(int(data["hmax"])))
        smin_slider.set(int(data["smin"]))
        smin_label.configure(text=str(int(data["smin"])))
        smax_slider.set(int(data["smax"]))
        smax_label.configure(text=str(int(data["smax"])))
        vmin_slider.set(int(data["vmin"]))
        vmin_label.configure(text=str(int(data["vmin"])))
        vmax_slider.set(int(data["vmax"]))
        vmax_label.configure(text=str(int(data["vmax"])))

    except requests.exceptions.RequestException:
        pass

def refresh_toggle():
    try:
        r = requests.get("http://127.0.0.1:8000/mode", timeout=0.2)
        mode = r.json()["Mode"]

        if mode == "Dynamic":
            StaticDynamic_var.set(True)
            volume_button.place_forget()
        else:
            StaticDynamic_var.set(False)
            volume_button.place(x=780, y=850)

    except requests.exceptions.RequestException:
        pass

    if current_canvas is canvas_config:
        current_canvas.after(100, refresh_toggle)

#-----------------------------------------------------------------

canvas_main.bind("<Button-1>", change_canvas)
canvas_camara.bind("<Button-1>", change_canvas)
canvas_barcode.bind("<Button-1>", change_canvas)
canvas_volume.bind("<Button-1>", change_canvas)
canvas_storage.bind("<Button-1>", change_canvas)
canvas_stacking.bind("<Button-1>", change_canvas)
canvas_config.bind("<Button-1>", change_canvas)
canvas_calibration.bind("<Button-1>", change_canvas)

# ESC to Close
root.bind("<Escape>", confirm_exit_overlay)
root.mainloop()