"""
##################################################################################
#    Detección de color y formas geométricas en tiempo real para Robotino        #
#                                                                                #
# Grupo: Vanguard (Robótica móvil)                                               #
# Fecha: 05/10/2026                                                              #
# Institución: Universidad Peruana de Ciencias Aplicadas                         #
# Versión: 1.0.0                                                                 #
# Proyecto: Manejo de Robotino Festo con Python                                  #
#                                                                                #
# Descripción:                                                                   #
#  Este script procesa el flujo de video en vivo del Robotino Festo para         #
#  realizar segmentación de color en espacio HSV, filtrado morfológico de ruido  #
#  y clasificación de formas geométricas (triángulos, cuadrados, rectángulos     #
#  y círculos) mediante análisis de contornos con OpenCV.                        #
##################################################################################
"""

import time
import requests
import cv2
import numpy as np

# Configuración de la dirección IP y endpoint del Robotino Festo
ROBOTINO_IP = "192.168.0.2"
url_stream = f"http://{ROBOTINO_IP}/cam0"

# Diccionario con límites en espacio de color HSV [Matiz (H), Saturación (S), Valor (V)]
# Nota: OpenCV representa H en rango [0, 180], S y V en [0, 255]
COLOR_RANGES = {
    "Rojo": [
        (np.array([0, 120, 70]), np.array([10, 255, 255])),
        (np.array([170, 120, 70]), np.array([180, 255, 255]))  # Ajuste por envoltura de tono en HSV
    ],
    "Verde": [
        (np.array([36, 100, 100]), np.array([86, 255, 255]))
    ],
    "Azul": [
        (np.array([94, 100, 100]), np.array([130, 255, 255]))
    ],
    "Amarillo": [
        (np.array([15, 100, 100]), np.array([35, 255, 255]))
    ]
}


def detect_shape(contour: np.ndarray) -> str:
    """Clasifica la forma geométrica de un contorno según su número de vértices aproximados.
    
    Args:
        contour (np.ndarray): Matriz de puntos que representan el contorno cerrado.

    Returns:
        str: Nombre de la figura geométrica detectada.
    """
    perimeter = cv2.arcLength(contour, True)
    # Aproximación poligonal Douglas-Peucker (tolerancia del 4% del perímetro)
    approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
    vertices = len(approx)

    if vertices == 3:
        return "Triangulo"
    elif vertices == 4:
        # Evaluar la relación de aspecto del rectángulo delimitador
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = float(w) / h
        # Si los lados son aproximadamente iguales, se considera un cuadrado
        if 0.95 <= aspect_ratio <= 1.05:
            return "Cuadrado"
        else:
            return "Rectangulo"
    elif vertices > 5:
        return "Circulo"

    return "Objeto"


print(f"Conectando a la cámara del Robotino en {url_stream}...")

while True:
    try:
        # Petición HTTP GET para capturar el fotograma más reciente
        response = requests.get(url_stream, timeout=2)

        if response.status_code == 200:
            # Reconstrucción de la matriz de imagen desde el flujo de bytes en memoria
            img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if frame is not None:
                # Conversión del espacio de color BGR nativo a HSV
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

                # Procesamiento por cada rango de color configurado
                for color_name, ranges in COLOR_RANGES.items():
                    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)

                    # Umbralización binaria en espacio HSV
                    for lower, upper in ranges:
                        mask_range = cv2.inRange(hsv, lower, upper)
                        mask = cv2.bitwise_or(mask, mask_range)

                    # Filtrado morfológico de apertura para eliminar el ruido especular
                    kernel = np.ones((5, 5), np.uint8)
                    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

                    # Extracción de contornos externos
                    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    for c in contours:
                        area = cv2.contourArea(c)
                        # Filtrar objetos menores a 1000 píxeles cuadrados para ignorar falsos positivos
                        if area > 1000:
                            shape_name = detect_shape(c)

                            # Dibujar el contorno del objeto en el fotograma original
                            cv2.drawContours(frame, [c], -1, (0, 255, 0), 2)

                            # Cálculo del centroide geométrico usando momentos de imagen
                            M = cv2.moments(c)
                            if M["m00"] != 0:
                                cx = int(M["m10"] / M["m00"])
                                cy = int(M["m01"] / M["m00"])

                                # Superposición del texto descriptivo (Color + Forma)
                                label = f"{color_name} {shape_name}"
                                cv2.putText(frame, label, (cx - 40, cy),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                # Renderizado de la imagen procesada
                cv2.imshow("Deteccion de Color y Forma - Robotino", frame)
            else:
                print("Error: No se pudo decodificar el fotograma recibido.")
        else:
            print(f"Error HTTP: {response.status_code}")

    except requests.exceptions.RequestException:
        print("Esperando reconexión de red con el Robotino...")
        time.sleep(1)

    # Actualización de la ventana (50 ms / ~20 FPS). Tecla 'q' para salir.
    if cv2.waitKey(50) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
print("Programa finalizado.")