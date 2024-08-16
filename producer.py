import yfinance as yf
from datetime import datetime, timedelta

today = datetime.today()
yesterday = today - timedelta(days=1)


data = yf.download("HPG.VN", start=yesterday, end=today, interval='1d')


print(data)
