import cv2 as cv
import keyboard as key

cap = cv.VideoCapture(0) # Acede à webcam

# Verifica se a câmara foi aberta
if not cap.isOpened():
    print("Erro: não foi possível aceder à câmara.")
    exit()

# Enquanto a tecla ESC (27) não for pressionada, irá apresentar o frame da câmara
while True:
    ret, frame = cap.read() #Lê o frame
    if not ret:
        print("Erro ao ler frame.")
        break

    cv.imshow('Camera', frame) # Apresenta o frame

    if cv.waitKey(1) == 27: #Espera que ESC seja pressionado
        break

cap.release()
cv.destroyAllWindows()