import os
import yfinance as yf
import pandas as pd
import datetime
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# TEST-MODUS: Nur Apple für den sofortigen Test
nasdaq_symbols = ["AAPL"]

budget_eur = 250.0

print(f"Starte TEST-Cloud-Scan für {len(nasdaq_symbols)} Aktien am {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}...")

# EUR/USD Wechselkurs einmalig vorab holen
try:
    eurusd = yf.Ticker("EURUSD=X").history(period="1d")['Close'].iloc[-1]
except Exception:
    eurusd = 1.08
print(f"Aktueller Wechselkurs EUR/USD: {eurusd:.4f}")

# Credentials aus den GitHub Secrets laden
gmail_app_pw = os.environ.get("GMAIL_APP_PW")
telegram_token = os.environ.get("TELEGRAM_TOKEN")
telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

sender = "ata.trading.de@gmail.com"
receiver = "ata.trading.de@gmail.com"

for symbol in nasdaq_symbols:
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period="6mo")
        if len(df) < 50:
            continue

        # Indikatoren berechnen
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        close_usd = df['Close'].iloc[-1]
        close_eur = close_usd / eurusd
        rsi_wert = df['RSI'].iloc[-1]
        ema_50 = df['EMA_50'].iloc[-1]

        aktien_menge = budget_eur / close_eur

        nachricht_text = (
            f"🚨 TEST-SIGNAL! 🚨\n"
            f"Aktie: {symbol}\n"
            f"Kurs: {close_eur:.2f} €\n"
            f"RSI: {rsi_wert:.2f} (Test-Modus)\n"
            f"Budget: {budget_eur} €\n"
            f"Kaufmenge ca.: {aktien_menge:.2f} Anteile"
        )

        # TEST-BEDINGUNG: Greift jetzt garantiert sofort
        if rsi_wert < 100:

            # 1. E-Mail senden
            if gmail_app_pw:
                try:
                    msg = MIMEMultipart()
                    msg['From'] = sender
                    msg['To'] = receiver
                    msg['Subject'] = f"🚨 TEST-Signal: {symbol}"
                    msg.attach(MIMEText(nachricht_text, 'plain'))

                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(sender, gmail_app_pw)
                    server.sendmail(sender, receiver, msg.as_string())
                    server.quit()
                    print(f"E-Mail erfolgreich gesendet für: {symbol}")
                except Exception as mail_err:
                    print(f"Fehler beim E-Mail-Versand für {symbol}: {mail_err}")

            # 2. Telegram senden mit genauer Status-Ausgabe
            if telegram_token and telegram_chat_id:
                try:
                    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
                    payload = {
                        "chat_id": telegram_chat_id,
                        "text": nachricht_text,
                        "parse_mode": "Markdown"
                    }
                    response = requests.post(url, json=payload)
                    print(f"Telegram API Antwort für {symbol}: {response.status_code} - {response.text}")
                except Exception as tg_err:
                    print(f"Fehler beim Telegram-Versand für {symbol}: {tg_err}")

            print(f"Treffer verarbeitet für: {symbol}")

    except Exception as e:
        continue

print("TEST-Scan erfolgreich beendet.")
