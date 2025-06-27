import yfinance as yf
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
    "/activos": None  # comando informativo
}


# Comandos para obtener precios directamente
PRECIO_COMANDOS = {
    "/preciobtc": "BTC-USD",
    "/precioeth": "ETH-USD",
    "/precioaapl": "AAPL",
    "/preciotsla": "TSLA",
    "/precionvda": "NVDA",
    "/precioqqq": "QQQ",
    "/precioarkk": "ARKK",
    "/preciogld": "GLD",
    "/preciomstr": "MSTR",
    "/preciopltr": "PLTR",
}


# Responde al usuario con un mensaje y una imagen (si aplica)
def responder(chat_id, mensaje, imagen, nombre_archivo):
    requests.get(f"{URL}/sendMessage", params={
        "chat_id": chat_id, "text": mensaje
    })

    if imagen:
        requests.post(f"{URL}/sendPhoto",
                      data={"chat_id": chat_id},
                      files={"photo": (nombre_archivo, imagen, "image/png")}
                      )


# Procesa el comando recibido
def procesar_comando(texto, chat_id):
    texto = texto.lower()

    if texto == "/activos":
        lista = "\n".join(
            [f"{cmd} → {sym}" for cmd, sym in COMANDOS.items() if sym])
        mensaje = f"📌 *Activos disponibles para análisis:*\n\n{lista}"
        requests.get(f"{URL}/sendMessage", params={
            "chat_id": chat_id,
            "text": mensaje,
            "parse_mode": "Markdown"
        })
        return

    if texto in COMANDOS:
        simbolo = COMANDOS[texto]
        mensaje, imagen, nombre = analizar_activo(simbolo)
        if mensaje:
            responder(chat_id, mensaje, imagen, nombre)
        else:
            requests.get(f"{URL}/sendMessage", params={
                "chat_id": chat_id,
                "text": f"❌ No se pudo analizar {simbolo}. Intenta más tarde."
            })

    elif texto in PRECIO_COMANDOS:
        simbolo = PRECIO_COMANDOS[texto]
        mensaje = obtener_precio(simbolo)
        requests.get(f"{URL}/sendMessage", params={
            "chat_id": chat_id,
            "text": mensaje,
            "parse_mode": "Markdown"
        })

    else:
        requests.get(f"{URL}/sendMessage", params={
            "chat_id": chat_id,
            "text": "⚠️ Comando no reconocido. Usa /activos para ver la lista disponible."
        })


# Obtener precio de un activo usando yfinance


def obtener_precio(simbolo):
    try:
        print(f"🔍 Consultando precio para: {simbolo}")
        ticker = yf.Ticker(simbolo)
        info = ticker.info

        # Si info está vacío
        if not info:
            print("⚠️ La info está vacía.")
            return "❌ No se pudo obtener el precio del activo."

        nombre = info.get("shortName", simbolo)
        precio = round(info.get("regularMarketPrice", 0), 2)
        cambio = round(info.get("regularMarketChangePercent", 0), 2)
        volumen = info.get("volume", 0)

        mensaje = (
            f"💰 *{nombre}*\n"
            f"📈 Precio actual: ${precio:,}\n"
            f"📊 Cambio 24h: {cambio}%\n"
            f"🔁 Volumen diario: {volumen:,}"
        )
        print("✅ Mensaje generado correctamente.")
        return mensaje

    except Exception as e:
        print(f"❌ Error al obtener precio: {e}")
        return "❌ No se pudo obtener el precio del activo."


# Escucha actualizaciones de Telegram
def escuchar(duracion_maxima=6 * 60):  # 6 minutos por defecto
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
