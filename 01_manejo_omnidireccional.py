import time
import requests

# Configuración de conexión
# Establecer la IP del robotino Festo
IP_ROBOTINO = "127.0.0.1:12080"  
URL_OMNIDRIVE = f"http://{IP_ROBOTINO}/data/omnidrive"

# Formato de velocidad: [Vx (m/s), Vy (m/s), Omega (rad/s)]
# Vx positivo = adelante, Vy = lateral, Omega = rotación
velocidad_avance = [0.2, 0.0, 0.0]  # 0.2 m/s hacia adelante
velocidad_freno = [0.0, 0.0, 0.0]   # Detener motores

def mover_robotino():
    try:
        print("Iniciando movimiento en línea recta...")
        tiempo_inicio = time.time()
        
        # Bucle de 2 segundos. Se envía el comando cada 100ms para mantener vivo el watchdog
        while (time.time() - tiempo_inicio) < 2.0:
            requests.post(URL_OMNIDRIVE, json=velocidad_avance, timeout=1)
            time.sleep(0.1)

        print("Tiempo cumplido. Deteniendo el Robotino...")
        # Enviar comando de freno varias veces para asegurar que se detenga

        for _ in range(3):
            requests.post(URL_OMNIDRIVE, json=velocidad_freno, timeout=1)
            time.sleep(0.1)

        print("Robotino detenido exitosamente.")

    except requests.exceptions.RequestException as e:
        print(f"Error de conexión con el Robotino. Verifica la red y la IP.\nDetalles: {e}")

if __name__ == "__main__":
    mover_robotino()

