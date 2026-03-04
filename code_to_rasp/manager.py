import cv2 as cv
import numpy as np

# função criada para passar imagens transparentes para o fundo :)
def overlay_alpha(background, overlay, x, y):
    h, w = overlay.shape[:2]
    if overlay.shape[2] == 4:  # BGRA
        b, g, r, a = cv.split(overlay)
        alpha = a / 255.0
        rgb = cv.merge((b, g, r))
        for c in range(3):
            background[y:y+h, x:x+w, c] = alpha * rgb[:, :, c] + (1-alpha) * background[y:y+h, x:x+w, c]
    else:
        background[y:y+h, x:x+w] = overlay

# Criar uma imagem preta de 1920x1080 (largura x altura)
screen_height, screen_width = 1080, 1920
screen = np.ones((screen_height, screen_width, 3), dtype=np.uint8) * 255

#--------------------- Logo Balanças Marques ---------------------

BM_logo = cv.imread("BM_Logo.png", cv.IMREAD_UNCHANGED)
BM_logo_resized = cv.resize(BM_logo, (360,152))
x1, y1 = 10, 10
overlay_alpha(screen, BM_logo_resized, x1, y1)

#-----------------------------------------------------------------

#----------------------- Camera Interface ------------------------

# Blue rectangle
cam_height, cam_width = 300, 400
cam = np.zeros((cam_height, cam_width, 3), dtype=np.uint8)
cam[:]=(255, 178, 102)
x2, y2 = 200, 250
overlay_alpha(screen, cam, x2, y2)

# Camera Icon
cam_icon = cv.imread("cam_icon.png", cv.IMREAD_UNCHANGED)
cam_icon_resized = cv.resize(cam_icon, (350,350))
x3, y3 = int(x2 + cam_width/2 - 350/2), int(y2 + cam_height/2 - 350/2)
overlay_alpha(screen, cam_icon_resized, x3, y3)

#-----------------------------------------------------------------

#----------------------- Config Interface ------------------------

# Grey rectangle
conf_height, conf_width = 300, 400
conf = np.ones((conf_height, conf_width, 3), dtype=np.uint8) * 192
x4, y4 = 1320, 630
overlay_alpha(screen, conf, x4, y4)

# Config Icon
conf_icon = cv.imread("conf_icon.png", cv.IMREAD_UNCHANGED)
conf_icon_resized = cv.resize(conf_icon, (400,400))
x5, y5 = int(x4 + conf_width/2 - 400/2), int(y4 + conf_height/2 - 400/2)
overlay_alpha(screen, conf_icon_resized, x5, y5)

#-----------------------------------------------------------------

# Mostrar a janela
cv.namedWindow("Manager", cv.WINDOW_NORMAL)
cv.setWindowProperty("Manager", cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
cv.imshow("Manager", screen)

while True:
    if cv.waitKey(1) == 27 or cv.getWindowProperty("Manager", cv.WND_PROP_VISIBLE) < 1: #Espera que ESC seja pressionado
        break

cv.destroyAllWindows()