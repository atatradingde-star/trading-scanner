import yfinance as yf
import pandas as pd
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Der komplette Nasdaq 100 Ticker-Pool
nasdaq_symbols = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "NVDA", "META", "TSLA", "AVGO", "COST", "NFLX",
    "AMD", "QCOM", "TMUS", "INTC", "AMAT", "ISRG", "TXN", "HON", "AMGN", "ADI",
    "SBUX", "LRCX", "GILD", "MDLZ", "ADP", "BKNG", "PANW", "VRTX", "SNPS", "CDNS",
    "CSCO", "PYPL", "MU", "ADBE", "MELI", "REGN", "ASML", "MAR", "ORLY",
    "CRWD", "CSX", "ADSK", "KLAC", "MNST", "PDD", "FTNT", "ABNB", "KDP", "CHTR",
    "AEP", "AZN", "DXCM", "KHC", "IDXX", "ROST", "EA", "ODFL", "CTAS", "LULU",
    "BKR", "GEHC", "PAYX", "PCAR", "XEL", "FAST", "CPRT", "VRSK", "ON",
    "CTSH", "ENPH", "EXC", "WBD", "MSTR", "TTWO", "DLTR", "CSGP", "GFS", "CCEP",
    "CDW", "ANET", "BIIB", "ZS", "ILMN", "TEAM", "MRVL", "DDOG", "FANG", "SIRI"
]

budget_eur = 250.0

print(f"Starte automatischen Cloud-Scan für {len(nasdaq_symbols)} Aktien am {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}...")

for symbol in nasdaq_symbols:
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period="6mo")
        if len(df) < 50:
            continue
            
        try:
            eurusd = yf.Ticker("EURUSD=X").history(period="1d")['Close'].iloc[-1]
        except:
            eurusd = 1.08
            
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
        
        if close_usd > ema_50 and rsi_wert < 30:
            aktien_menge = budget_eur / close_eur
            
            sender = "ata.trading.de@gmail.com"
            receiver = "ata.trading.de@gmail.com"
            app_pw = "apvsulwotmlaxrbc"
            
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = receiver
            msg['Subject'] = f"🚨 Trading-Signal: {symbol} kaufen! (RSI: {rsi_wert:.1f})"
            
            body = f"""
            Deine automatisierte Cloud-Strategie hat im Nasdaq 100 zugeschlagen!
            - Aktie: {symbol}
            - Kurs: {close_eur:.2f} €
            - RSI: {rsi_wert:.2f} (unter 30!)
            - Budget: {budget_eur} € auf Trade Republic
            - Kaufmenge ca.: {aktien_menge:.2f} Anteile
            """
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender, app_pw)
            server.sendmail(sender, receiver, msg.as_string())
            server.quit()
            print(f"Treffer & E-Mail gesendet für: {symbol}")
    except Exception as e:
        continue

print("Cloud-Scan erfolgreich beendet.")
