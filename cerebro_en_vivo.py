import cv2
import numpy as np
import requests
import serial
import time
from tensorflow.keras.models import load_model

# --- 1. CONFIGURACIÓN DEL SISTEMA ---
URL_FOTO = "http://192.168.4.1/foto"
puerto_arduino = 'COM5' 
arduino_conectado = False

try:
    arduino = serial.Serial(puerto_arduino, 9600, timeout=1)
    time.sleep(2) 
    arduino_conectado = True
    print(f"✅ Músculos conectados en {puerto_arduino}")
except:
    print(f"⚠️ Arduino no conectado. Modo visual.")

session = requests.Session()

print("Cargando red convolucional...")
modelo = load_model('cerebro_rover_colapso.h5')

tracker = cv2.TrackerCSRT_create()
tracking_activado = False
bbox = None 

frames_colapso = 0
UMBRAL_ALARMA = 3 
contador_frames = 0

# ==========================================
# FUNCIONES DE DISEÑO HUD (ESTÉTICA)
# ==========================================
def dibujar_esquinas_hud(frame, x, y, w, h, color, grosor=2, longitud=15):
    cv2.line(frame, (x, y), (x + longitud, y), color, grosor)
    cv2.line(frame, (x, y), (x, y + longitud), color, grosor)
    cv2.line(frame, (x + w, y), (x + w - longitud, y), color, grosor)
    cv2.line(frame, (x + w, y), (x + w, y + longitud), color, grosor)
    cv2.line(frame, (x, y + h), (x + longitud, y + h), color, grosor)
    cv2.line(frame, (x, y + h), (x, y + h - longitud), color, grosor)
    cv2.line(frame, (x + w, y + h), (x + w - longitud, y + h), color, grosor)
    cv2.line(frame, (x + w, y + h), (x + w, y + h - longitud), color, grosor)

def dibujar_panel_texto(frame, texto, x, y, color_texto, color_fondo=(0, 0, 0), alfa=0.6):
    font = cv2.FONT_HERSHEY_SIMPLEX
    escala = 0.5
    grosor = 1
    (ancho_texto, alto_texto), baseline = cv2.getTextSize(texto, font, escala, grosor)
    overlay = frame.copy()
    cv2.rectangle(overlay, (x - 5, y - alto_texto - 5), (x + ancho_texto + 5, y + 5), color_fondo, -1)
    cv2.addWeighted(overlay, alfa, frame, 1 - alfa, 0, frame)
    cv2.putText(frame, texto, (x, y), font, escala, color_texto, grosor)

COLOR_CIAN = (255, 200, 0)
COLOR_NARANJA = (0, 165, 255)
COLOR_ROJO = (0, 0, 255)
COLOR_VERDE = (0, 255, 0)

print("\n=== SISTEMA LISTO ===")
print("1. Pon al paciente en el cuadro cian.")
print("2. Presiona la tecla 'L' para FIJAR OBJETIVO.")

while True:
    try:
        # Extraer imagen en baja resolución para que el procesamiento vuele
        respuesta = session.get(URL_FOTO, timeout=1.0)
        img_array = np.array(bytearray(respuesta.content), dtype=np.uint8)
        frame_nativo = cv2.imdecode(img_array, -1) # Viene a 320x240

        if frame_nativo is None: continue
        contador_frames += 1

        comando_movimiento = 'S' 
        estado_emergencia = False
        probabilidad = 0.0

        # --- LÓGICA DE TARGET LOCK (En baja resolución) ---
        if not tracking_activado:
            xi, yi, w_ret, h_ret = 110, 40, 100, 160 
            
            # Ampliamos a 640x480 SOLO para mostrar el HUD en grande
            frame_display = cv2.resize(frame_nativo, (640, 480), interpolation=cv2.INTER_LINEAR)
            
            # Las coordenadas se multiplican x2 para dibujarlas en el frame grande
            dibujar_esquinas_hud(frame_display, xi*2, yi*2, w_ret*2, h_ret*2, COLOR_CIAN, grosor=3, longitud=30)
            dibujar_panel_texto(frame_display, "MODO BUSQUEDA: Alinea y presiona 'L'", 10, 30, COLOR_CIAN)

            tecla = cv2.waitKey(1) & 0xFF
            if tecla == ord('l') or tecla == ord('L'):
                bbox = (xi, yi, w_ret, h_ret)
                tracker.init(frame_nativo, bbox) # El tracker se ancla a la imagen pequeña y rápida
                tracking_activado = True
        else:
            exito, bbox = tracker.update(frame_nativo)
            frame_display = cv2.resize(frame_nativo, (640, 480), interpolation=cv2.INTER_LINEAR)

            if exito:
                x, y, w, h = [int(v) for v in bbox]
                centro_x = x + (w // 2)
                area_caja = w * h

                # Coordenadas escaladas (x2) para el dibujo en HD
                xd, yd, wd, hd = x*2, y*2, w*2, h*2
                centro_xd = centro_x * 2

                dibujar_esquinas_hud(frame_display, xd, yd, wd, hd, COLOR_NARANJA, grosor=2)
                cv2.circle(frame_display, (centro_xd, yd + (hd//2)), 4, COLOR_NARANJA, -1) 
                cv2.line(frame_display, (xd - 10, yd), (xd - 10, yd + hd), COLOR_CIAN, 1)

                # Cinemática evaluada con los números originales (320x240)
                if centro_x < 130:
                    comando_movimiento = 'I'
                    dibujar_panel_texto(frame_display, "<< GIRANDO IZQ", 10, 30, COLOR_NARANJA)
                elif centro_x > 190:
                    comando_movimiento = 'D'
                    dibujar_panel_texto(frame_display, "GIRANDO DER >>", 10, 30, COLOR_NARANJA)
                else:
                    if area_caja < 13000: 
                        comando_movimiento = 'A'
                        dibujar_panel_texto(frame_display, "^^ AVANZANDO", 10, 30, COLOR_VERDE)
                    else:
                        comando_movimiento = 'S'
                        dibujar_panel_texto(frame_display, "-- DISTANCIA OPTIMA", 10, 30, COLOR_CIAN)

                # IA DE COLAPSO (Procesada en baja resolución)
                if contador_frames % 2 == 0:
                    frame_gris = cv2.cvtColor(frame_nativo, cv2.COLOR_BGR2GRAY)
                    frame_resized = cv2.resize(frame_gris, (64, 64))
                    frame_normalizado = frame_resized / 255.0
                    frame_input = np.expand_dims(frame_normalizado, axis=(0, -1))

                    probabilidad = modelo.predict(frame_input, verbose=0)[0][1]

                    if probabilidad > 0.70: frames_colapso += 1
                    else: frames_colapso = 0

                    if frames_colapso >= UMBRAL_ALARMA:
                        estado_emergencia = True
                        comando_movimiento = 'E' 
            else:
                dibujar_panel_texto(frame_display, "!! OBJETIVO PERDIDO !!", 10, 30, COLOR_ROJO)
                comando_movimiento = 'S'
                tracking_activado = False 

        # --- UI DE EMERGENCIA Y TELEMETRÍA ---
        if estado_emergencia:
            overlay_rojo = frame_display.copy()
            cv2.rectangle(overlay_rojo, (0, 0), (640, 480), COLOR_ROJO, -1)
            cv2.addWeighted(overlay_rojo, 0.3, frame_display, 0.7, 0, frame_display)
            
            dibujar_panel_texto(frame_display, "EMERGENCIA MEDICA: COLAPSO", 170, 240, COLOR_ROJO)
            if arduino_conectado: arduino.write(b'E')
        else:
            if arduino_conectado: arduino.write(comando_movimiento.encode())

        dibujar_panel_texto(frame_display, f"RIESGO COLAPSO: {probabilidad*100:.0f}%", 10, 460, COLOR_CIAN)
        dibujar_panel_texto(frame_display, f"SYS: ACTIVO | MOTOR: {comando_movimiento}", 390, 460, COLOR_CIAN)

        cv2.imshow('ROVER BIOMETRICO HUD', frame_display)

    except Exception as e:
        pass 

    tecla_salir = cv2.waitKey(1) & 0xFF
    if tecla_salir == ord('q'):
        if arduino_conectado: arduino.write(b'S')
        break

cv2.destroyAllWindows()
if arduino_conectado: arduino.close()