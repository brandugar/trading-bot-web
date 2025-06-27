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


def escuchar():
    global OFFSET
    while True:
        try:
            res = requests.get(f"{URL}/getUpdates",
                               params={"timeout": 10, "offset": OFFSET})
            data = res.json()

            for update in data["result"]:
                OFFSET = update["update_id"] + 1
                msg = update["message"]
                texto = msg.get("text", "").lower()
                chat_id = msg["chat"]["id"]

                if texto.startswith("/"):
                    procesar_comando(texto, chat_id)

            time.sleep(5)

        except Exception as e:
            print("Error en listener:", e)
            time.sleep(10)


if __name__ == "__main__":
    escuchar()
