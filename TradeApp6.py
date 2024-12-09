import os
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")

# Fetch stock data
def fetch_stock_data(tickers, start_date, end_date):
    stock_data = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start_date, end=end_date)
            if not df.empty:
                stock_data[ticker] = df
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
    return stock_data

# Get trend based on returns and volume
def get_trend(df):
    if len(df) < 2:
        return "Neutral"  # Not enough data for trend analysis
    
    # Define window sizes and percentage change thresholds
    strict_window = 5  # Number of days for strict trend (5 days)
    soft_window = 3  # Number of days for soft trend (3 days)
    price_threshold = 0.02  # 2% price change threshold for strict trends
    volume_threshold = 0.10  # 10% volume change threshold for strict trends

    # Calculate percentage change in price and volume for strict and soft windows
    price_change_strict = (df['Close'].iloc[-1] - df['Close'].iloc[-strict_window]) / df['Close'].iloc[-strict_window]
    volume_change_strict = (df['Volume'].iloc[-1] - df['Volume'].iloc[-strict_window]) / df['Volume'].iloc[-strict_window]
    
    price_change_soft = (df['Close'].iloc[-1] - df['Close'].iloc[-soft_window]) / df['Close'].iloc[-soft_window]
    volume_change_soft = (df['Volume'].iloc[-1] - df['Volume'].iloc[-soft_window]) / df['Volume'].iloc[-soft_window]

    # Ensure we're comparing scalar values
    price_change_strict = price_change_strict.item() if isinstance(price_change_strict, pd.Series) else price_change_strict
    volume_change_strict = volume_change_strict.item() if isinstance(volume_change_strict, pd.Series) else volume_change_strict
    
    price_change_soft = price_change_soft.item() if isinstance(price_change_soft, pd.Series) else price_change_soft
    volume_change_soft = volume_change_soft.item() if isinstance(volume_change_soft, pd.Series) else volume_change_soft

    # Strict Bullish: Both price and volume increase significantly for at least 5 days
    if price_change_strict > price_threshold and volume_change_strict > volume_threshold:
        return "Strict Bullish" 

    # Soft Bullish: Either price or volume increases for at least 3 days
    elif price_change_soft > price_threshold or volume_change_soft > volume_threshold:
        return "Soft Bullish"
    
    # Strict Bearish: Both price and volume decrease significantly for at least 5 days
    elif price_change_strict < -price_threshold and volume_change_strict < -volume_threshold:
        return "Strict Bearish"
    
    # Soft Bearish: Either price or volume decreases for at least 3 days
    elif price_change_soft < -price_threshold or volume_change_soft < -volume_threshold:
        return "Soft Bearish"
    
    return "Neutral"  # If no conditions are met, the trend is Neutral




# Parse FTD data from file
def parse_ftds_file(ftd_file_path, tickers):
    ftd_data = {}
    try:
        with open(ftd_file_path, 'r') as file:
            for line in file:
                # Skip header lines or invalid data
                if "Trailer" in line or not line.strip():
                    continue

                fields = line.split('|')
                if len(fields) != 6:
                    print(f"Skipping invalid data in line: {line.strip()}")
                    continue

                settlement_date = fields[0]
                symbol = fields[2]
                quantity = fields[3]
                price = fields[5]

                # Check if ticker is one we're interested in
                if symbol in tickers:
                    try:
                        quantity = int(quantity)
                        price = float(price) if price != '.' else 0.0
                    except ValueError:
                        print(f"Skipping invalid data (price) in line: {line.strip()}")
                        continue

                    # Track the highest FTD count for each ticker
                    if symbol not in ftd_data:
                        ftd_data[symbol] = {'max_ftd': quantity, 'settlement_date': settlement_date, 'price': price}
                    else:
                        if quantity > ftd_data[symbol]['max_ftd']:
                            ftd_data[symbol] = {'max_ftd': quantity, 'settlement_date': settlement_date, 'price': price}

    except Exception as e:
        print(f"Error reading FTD file: {e}")
    
    return ftd_data






# Get share dilution
def get_share_dilution(stock_info):
    shares_outstanding = stock_info.get('sharesOutstanding', 0)
    market_cap_today = stock_info.get('marketCap', 0)
    dilution = (market_cap_today / shares_outstanding) if shares_outstanding else 0
    return dilution

# Analyze squeeze (stubbed out for now)
def get_squeeze(ticker, df, stock_info, ftd_data):
    """
    Analyze squeeze potential based on short interest, FTDs, volume trends, and Bollinger Bands.
    """
    try:
        if df is None or stock_info is None or ftd_data is None:
            raise ValueError("Missing data for squeeze analysis.")
        
        # Ensure the relevant columns exist
        required_columns = ['Close', 'Volume', 'Date']
        for col in required_columns:
            if col not in df.columns:
                print(f"Missing required column: {col}")
                return "Error", {}

        # Debugging: Check the structure and types of df
        print(f"Data for ticker {ticker}:")
        print(df.tail())  # Print the last few rows of df to inspect the data
        print(f"Columns: {df.columns}")
        
        # Ensure we have at least 2 data points for the price change calculation
        if len(df) < 2:
            return "Error", {}

        # Bollinger Bands Calculation (20-day window, 2 standard deviations)
        window = 20
        std_dev_multiplier = 2
        df['rolling_mean'] = df['Close'].rolling(window=window).mean()
        df['rolling_std'] = df['Close'].rolling(window=window).std()
        df['upper_band'] = df['rolling_mean'] + (df['rolling_std'] * std_dev_multiplier)
        df['lower_band'] = df['rolling_mean'] - (df['rolling_std'] * std_dev_multiplier)

        # Squeeze related data from stock_info
        float_shares = stock_info.get('floatShares', 0)
        short_interest = stock_info.get('shortPercentOfFloat', 0) * 100  # Convert to percentage
        shares_outstanding = stock_info.get('sharesOutstanding', 0)

        # Retrieve the highest FTD and percentage of float
        max_ftd_data = ftd_data.get(ticker, {})
        max_ftd = max_ftd_data.get('max_ftd', 0)
        ftds_as_percent_of_float = max_ftd_data.get('ftds_as_percent_of_float', 0)

        # Volume trends
        short_volume_spike = False  # Placeholder for short volume spike logic (can be added if needed)
        daily_volume_decreasing = all(df['Volume'].iloc[-i] < df['Volume'].iloc[-i-1] for i in range(1, 6))

        # Price movement: Current price and price change from the previous day
        current_price = df['Close'].iloc[-1]  # Last close price
        previous_price = df['Close'].iloc[-2] if len(df) > 1 else current_price  # Second last price
        price_change_pct = (current_price - previous_price) / previous_price * 100  # Price change in percentage

        # Squeeze parameters based on the provided logic
        high_squeeze = (
            short_interest > 15
            and short_volume_spike
            and daily_volume_decreasing
            and ftds_as_percent_of_float > 5
        )
        moderate_squeeze = (
            (10 <= short_interest <= 15)
            or (ftds_as_percent_of_float > 3)
            or daily_volume_decreasing
        )
        low_squeeze = (
            short_interest < 10 and ftds_as_percent_of_float <= 3 and not short_volume_spike
        )

        # Additional squeeze criteria based on Bollinger Bands and price movement
        # Ensure that we only compare the latest (last) row of the dataframe
        price_within_bands = df['lower_band'].iloc[-1] < current_price < df['upper_band'].iloc[-1]
        
        squeeze_criteria = {
            "high_squeeze": high_squeeze,
            "moderate_squeeze": moderate_squeeze,
            "low_squeeze": low_squeeze,
            "price_within_bands": price_within_bands,
            "price_change_pct": price_change_pct
        }

        # Determine squeeze potential
        if high_squeeze and price_within_bands and price_change_pct > 3:
            return "High Squeeze Potential", squeeze_criteria
        elif moderate_squeeze or (price_within_bands and price_change_pct > 1):
            return "Moderate Squeeze Potential", squeeze_criteria
        elif low_squeeze:
            return "Low Squeeze Potential", squeeze_criteria
        else:
            return "No Squeeze Potential", squeeze_criteria

    except Exception as e:
        print(f"Error analyzing squeeze for {ticker}: {e}")
        return "Error", {}



# Group by market cap and trend
def group_by_market_cap_and_trend(ticker_details):
    grouped = {'Strict Bullish': {}, 'Soft Bullish': {}, 'Strict Bearish': {}, 'Soft Bearish': {}}
    
    for ticker, details in ticker_details.items():
        trend = details['trend']
        if trend not in grouped:
            continue
        if details['market_cap_today'] not in grouped[trend]:
            grouped[trend][details['market_cap_today']] = []
        grouped[trend][details['market_cap_today']].append(ticker)
    
    return grouped

# Print trends based on grouped tickers
def print_trends(grouped_tickers, trend_filter):
    for trend, tickers in grouped_tickers.items():
        if trend != trend_filter:
            continue
        print(f"--- {trend} ---")
        for market_cap, tickers_list in tickers.items():
            print(f"Market Cap: {market_cap}")
            for ticker in tickers_list:
                print(f" - {ticker}")
def print_ticker(ticker, stock_data, squeeze_info):
    """
    Print analysis for a ticker, including price, squeeze info, and market cap details.
    """
    try:
        current_price = round(stock_data['current_price'], 2)
        open_price = round(stock_data['open'], 2)
        previous_close = round(stock_data['previous_close'], 2)
        price_month_ago = round(stock_data['price_month_ago'], 2)
        market_cap_current = round(stock_data['market_cap'], 2)
        market_cap_month_ago = round(stock_data['market_cap_month_ago'], 2)
        timestamp = stock_data['timestamp']

        squeeze_label = squeeze_info.get('label', 'No Squeeze Info')
        squeeze_criteria = squeeze_info.get('criteria', {})

        print(
            f"{ticker} | Current Price: {current_price} (as of {timestamp}) | "
            f"Open: {open_price} | Previous Close: {previous_close} | "
            f"Price a Month Ago: {price_month_ago} | Market Cap: {market_cap_current} | "
            f"Market Cap a Month Ago: {market_cap_month_ago} | "
            f"Squeeze Potential: {squeeze_label} | Criteria: {squeeze_criteria}"
        )
    except Exception as e:
        print(f"Error displaying analysis for {ticker}: {e}")

# Main execution
if __name__ == "__main__":
    # Set the tickers you want to analyze
    tickers = ["GME", "AMC", "DJT"]  # Example tickers
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    print("Fetching stock data...")
    stock_data = fetch_stock_data(tickers, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))

    for ticker in tickers:
        try:
            stock_info = yf.Ticker(ticker).info
            df = yf.download(ticker, period="6mo")
            if not df.empty:
                stock_data[ticker] = df, stock_info
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")

    # Parsing FTD data
    print("\nParsing FTD data...")
    ftd_file_path = r"C:\Users\polid\Documents\tradingscripts\endOctFtd.txt"
    ftd_data = parse_ftds_file(ftd_file_path, stock_data)

    # Now analyze trends and prepare ticker details
    ticker_details = {}
    for ticker, (df, stock_info) in stock_data.items():
        trend = get_trend(df)
        if trend != "Neutral":
            squeeze, squeeze_criteria = get_squeeze(ticker, df, stock_info, ftd_data)
            dilution = get_share_dilution(stock_info)

            ticker_details[ticker] = {
                'df': df,
                'stock_info': stock_info,
                'trend': trend,
                'current_price': round(df['Close'].iloc[-1], 2),
                'timestamp': df.index[-1],
                'open': round(df['Open'].iloc[-1], 2),
                'previous_close': round(df['Close'].iloc[-2], 2) if len(df) > 1 else round(df['Close'].iloc[-1], 2),
                'price_month_ago': round(df['Close'].iloc[-30], 2) if len(df) > 30 else round(df['Close'].iloc[0], 2),
                'market_cap_today': stock_info.get('marketCap', 0),
                'market_cap_month_ago': stock_info.get('marketCap', 0),  # Placeholder for consistency
                'squeeze': squeeze,
                'dilution': dilution
            }

    # Group tickers by market cap and trend
    grouped_tickers = group_by_market_cap_and_trend(ticker_details)

    # Use TickerPrinter for detailed output within each group
    printer = TickerPrinter()

    print("\nAnalyzing for strict bullish trends...\n")
    print("--- Strict Bullish ---")
    if "Strict Bullish" in grouped_tickers:
        for ticker in grouped_tickers["Strict Bullish"]:
            printer.print_ticker_info(ticker, ticker_details[ticker])

    print("\nAnalyzing for soft bullish trends...\n")
    print("--- Soft Bullish ---")
    if "Soft Bullish" in grouped_tickers:
        for ticker in grouped_tickers["Soft Bullish"]:
            printer.print_ticker_info(ticker, ticker_details[ticker])

    print("\nAnalyzing for strict bearish trends...\n")
    print("--- Strict Bearish ---")
    if "Strict Bearish" in grouped_tickers:
        for ticker in grouped_tickers["Strict Bearish"]:
            printer.print_ticker_info(ticker, ticker_details[ticker])

    print("\nAnalyzing for soft bearish trends...\n")
    print("--- Soft Bearish ---")
    if "Soft Bearish" in grouped_tickers:
        for ticker in grouped_tickers["Soft Bearish"]:
            printer.print_ticker_info(ticker, ticker_details[ticker])

