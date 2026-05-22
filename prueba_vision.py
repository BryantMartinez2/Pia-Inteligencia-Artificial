import cv2
import numpy as np
import requests
import time

# La IP del Rover en modo Access Point
URL_FOTO = "http://192.168.4.1/foto"

print("--- MODO DIAGNÓSTICO DE VISIÓN ---")
print("Verifica que tu laptop esté conectada a la red 'ROVER_FIME'")
print("Intentando conectar con los ojos del Rover...")

# Mantenemos la sesión abierta para máxima velocidad
session = requests.Session()

while True:
    try:
        # Hacemos la petición a la ESP32-CAM
        respuesta = session.get(URL_FOTO, timeout=2.0)
        
        # Si el servidor responde con éxito (HTTP 200)
        if respuesta.status_code == 200:
            img_array = np.array(bytearray(respuesta.content), dtype=np.uint8)
            frame = cv2.imdecode(img_array, -1)

            if frame is not None:
                # Escalamos un poco la ventana para verla bien
                frame_grande = cv2.resize(frame, (640, 480))
                cv2.imshow("TEST ESP32-CAM (Presiona 'q' para salir)", frame_grande)
            else:
                print("⚠️ Error: La placa envió datos, pero OpenCV no pudo leerlos como imagen.")
        else:
            print(f"⚠️ Error del servidor ESP32. Código HTTP: {respuesta.status_code}")

    except requests.exceptions.RequestException as e:
        # Si la red falla, no crashea, solo avisa
        print("Buscando señal de la cámara... Revisa tu conexión Wi-Fi.")
        time.sleep(1) # Pausa para no saturar la consola

    # Tecla de salida
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
print("Prueba finalizada.")