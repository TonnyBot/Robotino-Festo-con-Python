"""
Robotino Festo - Captura e Integración de Cámara en Vivo con OpenCV

Este script realiza peticiones HTTP GET periódicas al endpoint de la cámara 
del Robotino Festo, decodifica el flujo de bytes recibido en memoria y proyecta
la señal de video en una ventana interactiva de OpenCV.
"""

import time
import requests
import cv2
import numpy as np

# Configuración de red e IP del Robotino Festo
ROBOTINO_IP = "192.168.0.2"

# Endpoint HTTP para obtener la captura de la cámara
url_stream = f"http://{ROBOTINO_IP}/cam0" 

print(f"Conectando a la cámara del Robotino en {url_stream}...")

while True:
    try:
        # 1. Petición GET para obtener la imagen actual (timeout de 2 segundos para evitar congelamiento)
        response = requests.get(url_stream, timeout=2)

        # Validar el estado de la respuesta HTTP:
        # 200: Petición exitosa
        # 404: El recurso o la URL no fue encontrada
        # 403: Acceso denegado por el servidor
        if response.status_code == 200:
            
            # 2. Convertir los bytes crudos (0s y 1s) a una secuencia de datos de 8 bits (0 a 255)
            img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            
            # 3. Decodificar la matriz en un mapa de píxeles a color (BGR) procesable por OpenCV
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            # Validar que la imagen exista y se haya decodificado correctamente
            if frame is not None:
                # Mostrar el fotograma en la ventana flotante
                cv2.imshow("Camara en Vivo - Robotino Festo", frame)
            else:
                print("Error: No se pudo decodificar el fotograma (matriz vacía).")
        else:
            print(f"Error HTTP: {response.status_code}")

    except requests.exceptions.RequestException:
        # Manejo de fallos de red o pérdida temporal de conexión con el Robotino
        print("Esperando conexión de red o fotograma perdido...")
        time.sleep(1)
        
    # Retardo de 50 ms para mantener aproximadamente 20 FPS y liberar uso del CPU.
    # Presionar la tecla 'q' para romper el ciclo y finalizar la ejecución.
    if cv2.waitKey(50) & 0xFF == ord('q'):
        break

# Liberar los recursos de las ventanas abiertas al finalizar el bucle
cv2.destroyAllWindows()
print("Programa finalizado.")
