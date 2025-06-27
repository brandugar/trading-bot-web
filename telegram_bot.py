import os
import time
import requests
from app import analizar_activo  # usamos tu función existente

BOT_TOKEN = os.getenv("BOT_TOKEN")
URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
OFFSET = None

# Mapeamos comandos a símbolos
COMANDOS = {
    "/btc": "BTC-USD",
    "/eth": "ETH-USD",
    "/sol": "SOL-USD",
    "/aapl": "AAPL",
    "/tsla": "TSLA",
    "/nvda": "NVDA",
    "/qqq": "QQQ",
    "/arkk": "ARKK",
    "/gld": "GLD",
    "/mstr": "MSTR",
    "/pltr": "PLTR",
}


def responder(chat_id, mensaje, imagen, nombre_archivo):
    requests.get(f"{URL}/sendMessage", params={
        "chat_id": chat_id, "text": mensaje
    })

    if imagen:
        requests.post(f"{URL}/sendPhoto",
                      data={"chat_id": chat_id},
                      files={"photo": (nombre_archivo, imagen, "image/png")}
                      )


def procesar_comando(texto, chat_id):
    simbolo = COMANDOS.get(texto.lower())
    if not simbolo:
        requests.get(f"{URL}/sendMessage", params={
            "chat_id": chat_id,
            "text": "⚠️ Comando no reconocido. Usa /btc, /eth, /aapl, etc."
        })
        return

    mensaje, imagen, nombre = analizar_activo(simbolo)
    if mensaje:
        responder(chat_id, mensaje, imagen, nombre)
    else:
        requests.get(f"{URL}/sendMessage", params={
            "chat_id": chat_id,
            "text": f"❌ No se pudo analizar {simbolo}. Intenta más tarde."
        })


def escuchar(duracion_maxima=5 * 60):  # 5 minutos por defecto
    global OFFSET
    inicio = time.time()

    while time.time() - inicio < duracion_maxima:
        try:
            res = requests.get(
                f"{URL}/getUpdates",
                params={"timeout": 10, "offset": OFFSET},
                timeout=15  # Evita bloqueos eternos
            )
            res.raise_for_status()
            data = res.json()

            for update in data.get("result", []):
                OFFSET = update["update_id"] + 1
                msg = update.get("message", {})
                texto = msg.get("text", "").lower()
                chat_id = msg.get("chat", {}).get("id")

                if texto.startswith("/") and chat_id:
                    procesar_comando(texto, chat_id)

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error de red: {e}")
            time.sleep(5)
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            time.sleep(5)

        time.sleep(2)  # Delay para no saturar la API


if __name__ == "__main__":
    escuchar()  # Por defecto escucha por 5 minutos
