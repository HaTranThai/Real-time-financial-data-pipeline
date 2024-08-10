import yfinance as yf
from datetime import datetime, timedelta

# Lấy ngày hôm nay
today = datetime.today().strftime('%Y-%m-%d')

# Tải dữ liệu từ ngày 2024-08-01 đến ngày hôm trước
data = yf.download('AAPL', start=today, end=today, interval='1d')

# In dữ liệu
print(data)
