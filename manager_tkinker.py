import tkinter as tk
from PIL import Image, ImageTk
import ctypes

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
canvas_main.create_rectangle(cam_rect, fill="#6699FF", outline="")

# Camera Icon
cam_icon = Image.open("cam_icon.png").resize((350, 350))
cam_icon_tk = ImageTk.PhotoImage(cam_icon)
cam_icon_x = cam_x + cam_width/2 - 350/2
cam_icon_y = cam_y + cam_height/2 - 350/2
canvas_main.create_image(cam_icon_x, cam_icon_y, anchor='nw', image=cam_icon_tk)

#-----------------------------------------------------------------

#--------------------- Dimensions Interface ----------------------

# Blue Rectangle
dim_height, dim_width = 300, 400
dim_x, dim_y = 760, 250
dim_rect = [dim_x, dim_y, dim_x + dim_width, dim_y + dim_height]
canvas_main.create_rectangle(dim_rect, fill="#6699FF", outline="")

# Dim Icon
#dim_icon = Image.open("dim_icon.png").resize((350, 350))
#dim_icon_tk = ImageTk.PhotoImage(dim_icon)
#dim_icon_x = dim_x + dim_width/2 - 350/2
#dim_icon_y = dim_y + dim_height/2 - 350/2
#canvas_main.create_image(dim_icon_x, dim_icon_y, anchor='nw', image=dim_icon_tk)

#-----------------------------------------------------------------

#-------------------- QR/Bar Code Interface ----------------------

# Blue Rectangle
code_height, code_width = 300, 400
code_x, code_y = 1320, 250
code_rect = [code_x, code_y, code_x + code_width, code_y + code_height]
canvas_main.create_rectangle(code_rect, fill="#6699FF", outline="")

# Dim Icon
#dim_icon = Image.open("dim_icon.png").resize((350, 350))
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

#------------------------ Config Canvas --------------------------

canvas_config = tk.Canvas(root, bg='white', highlightthickness=0)

#--------------------- Logo Balanças Marques ---------------------
BM_logo = Image.open("BM_Logo.png").resize((360, 152))
BM_logo_tk_config = ImageTk.PhotoImage(BM_logo)
canvas_config.create_image(10, 10, anchor='nw', image=BM_logo_tk_config)

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

#-----------------------------------------------------------------

canvas_main.bind("<Button-1>", change_canvas)
canvas_camara.bind("<Button-1>", change_canvas)
canvas_config.bind("<Button-1>", change_canvas)

# ESC to Close
root.bind("<Escape>", lambda e: root.destroy())
root.mainloop()