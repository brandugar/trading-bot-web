
import os
import io
from flask import Flask, request
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator

app = Flask(__name__)

activos_full = ["BTC-USD", "ETH-USD", "SOL-USD", "AAPL", "TSLA", "NVDA",
                "QQQ", "ARKK", "GLD", "MSTR", "PLTR"]  # Lista de activos a analizar

bot_token = os.getenv("BOT_TOKEN")
chat_id = os.getenv("CHAT_ID")


def analizar_activo(activo):
    df = yf.download(activo, period="6mo", interval="1d", auto_adjust=True)
    if df.empty or 'Close' not in df:
        return None, None, None

    df.dropna(inplace=True)
    close = df[['Close']].squeeze()

    df['SMA20'] = SMAIndicator(close=close, window=20).sma_indicator()
    df['SMA50'] = SMAIndicator(close=close, window=50).sma_indicator()
    df['RSI'] = RSIIndicator(close=close, window=14).rsi()
    macd = MACD(close=close)
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()

    def evaluar_sma(df):
        if df['SMA20'].iloc[-2] < df['SMA50'].iloc[-2] and df['SMA20'].iloc[-1] > df['SMA50'].iloc[-1]:
            return "✅ Comprar"
        elif df['SMA20'].iloc[-2] > df['SMA50'].iloc[-2] and df['SMA20'].iloc[-1] < df['SMA50'].iloc[-1]:
            return "❌ Vender"
        return "🕐 Esperar"

    def evaluar_rsi(df):
        rsi = df['RSI'].iloc[-1]
        if rsi < 30:
            return "✅ Comprar"
        elif rsi > 70:
            return "❌ Vender"
        return "🕐 Esperar"

    def evaluar_macd(df):
        if df['MACD'].iloc[-2] < df['MACD_signal'].iloc[-2] and df['MACD'].iloc[-1] > df['MACD_signal'].iloc[-1]:
            return "✅ Comprar"
        elif df['MACD'].iloc[-2] > df['MACD_signal'].iloc[-2] and df['MACD'].iloc[-1] < df['MACD_signal'].iloc[-1]:
            return "❌ Vender"
        return "🕐 Esperar"

    sma = evaluar_sma(df)
    rsi = evaluar_rsi(df)
    macd_sig = evaluar_macd(df)

    mensaje = f"""📊 Señales para {activo}
SMA: {sma}
RSI: {rsi}
MACD: {macd_sig}
"""

    fig, ax = plt.subplots(figsize=(10, 4))
    df['Close'].tail(90).plot(ax=ax, label="Precio", color="black")
    df['SMA20'].tail(90).plot(ax=ax, label="SMA20", color="blue")
    df['SMA50'].tail(90).plot(ax=ax, label="SMA50", color="red")
    ax.set_title(f"{activo} - Señales Técnicas")
    ax.legend()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)

    return mensaje, buf, f"{activo}.png"


@app.route('/')
def home():
    return "Bot activo"


@app.route('/analizar')
def analizar():
    activos = request.args.get("activos", "BTC-USD,ETH-USD").split(",")
    for activo in activos:
        mensaje, img, nombre = analizar_activo(activo)
        if mensaje:
            requests.get(f"https://api.telegram.org/bot{bot_token}/sendMessage",
                         params={"chat_id": chat_id, "text": mensaje})
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendPhoto",
                          data={"chat_id": chat_id},
                          files={"photo": (nombre, img, "image/png")})
    return "OK"
