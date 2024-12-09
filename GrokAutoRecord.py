"""" Groks verison
something is failing in the rsi calculation and causing issue
"""

import yfinance as yf
import pandas as pd
import os
import datetime
import time
import threading

import numpy as np

file_path = r"C:\Users\polid\Documents\tradingscripts\Data Logs\Historic Ticker Details\AutoLog1.txt"

# Ensure the file exists or create it
if not os.path.exists(file_path):
    with open(file_path, 'w') as file:
        file.write("Timestamp,Ticker,Open,High,Low,Close,Adj Close,Volume,Current Price,Price at Open,Previous Close,"
                   "50-Day MA,200-Day MA,RSI,Bollinger Upper,Bollinger Lower,ATR\n")

def safe_get(data, column, idx=-1):
    if column in data.columns and len(data) > abs(idx):
        return data[column].iloc[idx]
    elif column in data.columns:
        return data[column].iloc[-1]  # Return the last valid value if index is out of range
    else:
        return 'NA'


def calculate_indicators(data,ticker):
    # Debug Print: Check if data is empty
    print("DEBUG: Checking if data is empty...")
    if data.empty:
        print("DEBUG: Data is empty.")
        return {k: 'NA' for k in ['Current Price', 'Price at Open', 'Previous Close', '50-Day MA', '200-Day MA', 'RSI', 'Bollinger Upper', 'Bollinger Lower', 'ATR']}

    # Debug Print: Check for required columns
    required_columns = ['Open', 'High', 'Low', 'Close']
    print("DEBUG: Checking for required columns...")
    if not all(col in data.columns for col in required_columns):
        missing_columns = [col for col in required_columns if col not in data.columns]
        print("DEBUG: Missing columns:", missing_columns)
        return {k: 'NA' for k in ['Current Price', 'Price at Open', 'Previous Close', '50-Day MA', '200-Day MA', 'RSI', 'Bollinger Upper', 'Bollinger Lower', 'ATR']}

    # Current price and open price
    print("DEBUG: Fetching current price and open price...")
    current_price = safe_get(data, 'Close')
    price_at_open = safe_get(data, 'Open')
    previous_close = safe_get(data, 'Close', -2)
    print("DEBUG: Current Price:", current_price, "Price at Open:", price_at_open, "Previous Close:", previous_close)

    # Moving Averages
    print("DEBUG: Calculating 50-Day MA...")
    ma_50 = data['Close'].rolling(window=50, min_periods=1).mean().iloc[-1]
    print("DEBUG: Calculating 200-Day MA...")
    ma_200 = data['Close'].rolling(window=200, min_periods=1).mean().iloc[-1]
    print("DEBUG: 50-Day MA:", ma_50, "200-Day MA:", ma_200)
    
    # ATR CALCULATION
    print("DEBUG: Checking length for ATR calculation...")
    if len(data) >= 14:
        print("DEBUG: Calculating ATR...")
        true_range = pd.concat([data['High'] - data['Low'],
                                abs(data['High'] - data['Close'].shift()),
                                abs(data['Low'] - data['Close'].shift())], axis=1).max(axis=1)
        atr = true_range.ewm(alpha=1/14, adjust=False).mean().iloc[-1]
    else:
        print("DEBUG: Not enough data for ATR calculation.")
        atr = 'NA'
    print(atr)
    

    # RSI Calculation
    print("DEBUG: Checking length for RSI calculation...")
    print("DEBUG: Data passed to RSI calculation:")
    print(f"Columns: {data.columns}")
    print(f"Index:\n{data.index}")
    print(f"Head:\n{data.head()}")
    print("DEBUG: Inspecting initial data structure...")
    print(data.info())  # Show structure and column details

   
    # Flatten multi-level columns, if any
    if isinstance(data.columns, pd.MultiIndex):
        print("DEBUG: Data has multi-level columns. Flattening...")
        data.columns = [' '.join(col).strip() for col in data.columns.values]
        print("DEBUG: Flattened columns:", data.columns)

    # Extract the 'Close' column for the specified ticker
    
    close_column = f"Close {ticker}"
    if close_column not in data.columns:
        raise KeyError(f"DEBUG: Column '{close_column}' is missing after processing.")

    data['Close'] = data[close_column]  # Standardize the 'Close' column for further use
    print("DEBUG: After flattening and standardizing 'Close':")
    print(type(data['Close']))
    print(data['Close'].head())

    if len(data) > 14:
        print(f"DEBUG: Calculating RSI...")

        # Price differences
        delta = data['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        # Average gain/loss (EWMA)
        avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()

        # DEBUG: Print intermediate results
        print(f"DEBUG: avg_gain (last value):\n{avg_gain.iloc[-1]}")
        print(f"DEBUG: avg_loss (last value):\n{avg_loss.iloc[-1]}")

        # Extract scalar values for RSI calculation
        last_avg_gain = avg_gain.iloc[-1]
        last_avg_loss = avg_loss.iloc[-1]

        # Handle division by zero or NaN
        if pd.isna(last_avg_loss) or last_avg_loss == 0:
            print("DEBUG: avg_loss is zero or NaN. RSI cannot be calculated.")
            rs = np.nan
        else:
            rs = last_avg_gain / last_avg_loss

        rsi = 100 - (100 / (1 + rs)) if not pd.isna(rs) else np.nan
        print(f"DEBUG: rs={rs}, rsi={rsi}")
        
    else:
        print("DEBUG: Not enough data for RSI calculation.")
        return np.nan
    # BOLLINGER BANDS
    print("DEBUG: Checking length for Bollinger Bands calculation...")
    if len(data) >= 20:
        print("DEBUG: Calculating Bollinger Bands...")
        sma_20 = data['Close'].rolling(window=20, min_periods=1).mean().iloc[-1]
        std_dev = data['Close'].rolling(window=20, min_periods=1).std().iloc[-1]
        bollinger_upper = sma_20 + (2 * std_dev)
        bollinger_lower = sma_20 - (2 * std_dev)
        print(bollinger_upper)
        print(bollinger_lower)
    else:
        print("DEBUG: Not enough data for Bollinger Bands calculation.")
        bollinger_upper, bollinger_lower = 'NA', 'NA'

    

    

    print("DEBUG: Returning calculated indicators...")
    return {
        'Current Price': current_price.item(),
        'Price at Open': price_at_open.item(),
        'Previous Close': previous_close.item(),
        
        '50-Day MA': ma_50.item() if isinstance(ma_50, pd.Series) else ma_50,
        '200-Day MA': ma_200.item() if isinstance(ma_200, pd.Series) else ma_200,
        'RSI': rsi,
        'Bollinger Upper':bollinger_upper,
        'Bollinger Lower':bollinger_lower,
        'ATR':atr,
        }

def fetch_and_log_data(ticker, interval, run_duration):
    start_time = time.time()
    while time.time() - start_time < run_duration:
        try:
            data = yf.download(ticker, period='2y', interval='1d')
            print(f"DEBUG: Fetched {len(data)} rows of data for {ticker}.")
            
            if data.empty:
                print(f"No data found for {ticker}. Skipping.")
                continue
            
            
            today=datetime.datetime.now().date()
            yesterday=today-datetime.timedelta(days=1)
            # Ensure `data` index is converted to `datetime.date` for comparison
            data.index = data.index.date

            # Access today's and yesterday's volume
            today_volume = data.loc[today, 'Volume'].item() if today in data.index else 'NA'

            yesterday_volume = data.loc[yesterday, 'Volume'].item() if yesterday in data.index else 'NA'
            
            indicators = calculate_indicators(data.dropna(),ticker)
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(file_path, 'a') as file:
                file.write(f"{ticker},{timestamp},{today_volume},{yesterday_volume},"
                           f"{indicators['Current Price']},{indicators['Price at Open']},{indicators['Previous Close']},{indicators['50-Day MA']},{indicators['200-Day MA']},{indicators['RSI']}," 
                           f"{indicators['Bollinger Upper']},{indicators['Bollinger Lower']},{indicators['ATR']}\n")# removed {safe_get(data, 'High')},{safe_get(data, 'Low')},{safe_get(data, 'Close')},{safe_get(data, 'Adj Close')},{safe_get(data, 'Volume')},"
            print(f"Data logged for {ticker}.")
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            with open('error_log.txt', 'a') as error_file:
                error_file.write(f"{datetime.datetime.now()} - Error for {ticker}: {e}\n")
        time.sleep(interval)

def collect_data_for_assets():
    num_assets = int(input("How many assets would you like to record? "))
    interval = int(input("Enter the time interval in seconds (e.g., 30): "))
    run_duration = int(input("Enter total runtime in seconds (e.g., 300 for 5 minutes): "))
    threads = []

    for _ in range(num_assets):
        ticker = input("Enter the ticker symbol (e.g., AAPL, BTC-USD): ").strip().upper()
        thread = threading.Thread(target=fetch_and_log_data, args=(ticker, interval, run_duration))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    collect_data_for_assets()
