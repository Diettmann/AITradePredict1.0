import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# ===========================================
# HELPER FUNCTIONS
# ===========================================

def fetch_stock_data(tickers, start_date, end_date):
    """Fetch historical stock data for a list of tickers."""
    data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date)
            if not df.empty:
                data[ticker] = df
            else:
                print(f"No data found for {ticker}")
        except Exception as e:
            print(f"Failed to fetch data for {ticker}: {e}")
    return data

def get_ticker_details(ticker, df):
    """Retrieve specific price details for a ticker."""
    try:
        # Ensure consistent time zones
        if hasattr(df.index, 'tz'):
            one_month_ago_date = (datetime.now() - timedelta(days=30)).astimezone(df.index.tz)
        else:
            one_month_ago_date = datetime.now() - timedelta(days=30)
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_price = df['Close'].iloc[-1]  # Last available closing price
        open_price = df['Open'].iloc[-1]  # Opening price of the last available day
        previous_close = df['Close'].iloc[-2] if len(df) > 1 else None  # Previous day's close

        # Locate the row closest to one_month_ago_date
        one_month_price = None
        closest_row = df[df.index <= one_month_ago_date].iloc[-1] if not df[df.index <= one_month_ago_date].empty else None
        if closest_row is not None:
            one_month_price = closest_row['Close']

        return {
            "timestamp": current_time,
            "current_price": current_price,
            "open_price": open_price,
            "previous_close": previous_close,
            "one_month_price": one_month_price
        }
    except Exception as e:
        print(f"Error retrieving details for {ticker}: {e}")
        return None

# ===========================================
# ANALYSIS FUNCTIONS
# ===========================================

def analyze_bullish_trend(data, window=5):
    """
    Analyze stocks for strict bullish trends.
    - Requires 5 consecutive days of positive returns.
    - Volume must increase every day in the window.
    """
    bullish_tickers = []
    for ticker, df in data.items():
        if len(df) > window:
            # Calculate daily returns
            df['Returns'] = df['Close'].pct_change()

            # Check for strict bullish criteria
            if df['Returns'].iloc[-window:].sum() > 0 and all(df['Volume'].iloc[-i] > df['Volume'].iloc[-i-1] for i in range(1, window)):
                bullish_tickers.append((ticker, df))
    return bullish_tickers

def analyze_soft_trend(data, window=3):
    """
    Analyze stocks for softer bullish trends.
    - Requires positive overall returns over the window.
    - Final day's volume must exceed the average volume.
    """
    soft_tickers = []
    for ticker, df in data.items():
        if len(df) > window:
            # Calculate daily returns
            df['Returns'] = df['Close'].pct_change()

            # Check for soft bullish criteria
            if df['Returns'].iloc[-window:].sum() > 0 and df['Volume'].iloc[-1] > df['Volume'].mean():
                soft_tickers.append((ticker, df))
    return soft_tickers

# ===========================================
# MAIN EXECUTION
# ===========================================

if __name__ == "__main__":
    # ----- INPUT PARAMETERS -----
    tickers = ["AAPL", "GOOG", "MSFT", "AMZN", "FB""HOLX", "HD", "HON", "HRL", "HST", "HUM", "HBAN", "HII", "IBM", "IEX", 
"IDXX", "ITW", "ILMN", "INCY", "IR", "INTC", "ICE", "IP", "IPG", "IFF", 
"INTU", "ISRG", "IVZ", "IPGP", "IQV", "IRM", "JBHT", "JKHY", "J", "JNJ", 
"JCI", "JPM", "JNPR", "K", "KEY", "KMB", "KIM", "KMI", "KLAC", "KHC", 
"KR", "LHX", "LH", "LRCX", "LW", "LVS", "LDOS", "LEN", "LNC", "LIN", 
"LYV", "LKQ", "LMT", "L", "LOW", "LYB", "MTB", "MRO", "MPC", "MKTX", 
"MAR", "MMC", "MLM", "MAS", "MA", "MTCH", "MKC", "MCD", "MCK", "MDT", 
"MRK", "META", "MET", "MTD", "MGM", "MCHP", "MU", "MSFT", "MAA", "MRNA", 
"MHK", "MOH", "TAP", "MDLZ", "MPWR", "MNST", "MCO", "MS", "MOS", "MSI", 
"MSCI", "NDAQ", "NTAP", "NFLX", "NWL", "NEM", "NWSA", "NWS", "NEE", 
"NKE", "NI", "NDSN", "NSC", "NTRS", "NOC", "NLOK", "NCLH", "NRG", "NUE","ADM", "AFL", "AIG", "ALL", "AMGN", "APTV", "AON", "APA", "APD", "AEE", 
"AEP", "AXP", "AIG", "ALK", "ABC", "AME", "AMT", "AMP", "ADI", "ANSS", 
"AON", "APA", "APD", "ARE", "ATO", "ADSK", "AZO", "AVB", "AVGO", "AVY", 
"AEP", "BLL", "BAX", "BDX", "BRK.B", "BBY", "BIO", "BA", "BK", "BXP", 
"BSX", "BMY", "AVGO", "CAG", "CDNS", "CPB", "COF", "CAH", "CARR", "CAT", 
"CB", "CNC", "CNP", "CDW", "CE", "CERN", "CHRW", "CINF", "CTAS", "CSCO", 
"CMCSA", "CMA", "CTSH", "CL", "CME", "CMS", "KO", "CTVA", "CLX", "CME", 
"CMI", "CVS", "DHI", "DHR", "DRI", "DVA", "DE", "DAL", "XRAY", "DVN", 
"DXCM", "DLR", "DFS", "DISCA", "DISCK", "DIS", "DISH", "DG", "DLTR", 
"DUK", "DOV", "DTE", "ETSY", "EFX", "ECL", "EOG", "EPAM", "ETN", "EBAY", 
"EA", "EMN", "EMR", "ENPH", "ETR", "EIX", "RE", "EVRG", "ES", "EXC", 
"EXPE", "EXPD", "EXR", "XOM", "FFIV", "FAST", "FRT", "FDX", "FIS", "FITB",
"FRC", "FE", "FISV", "FLT", "FMC", "F", "FTNT", "FTV", "FBHS", "FOX", 
"FOXA", "BEN", "FCX", "GRMN", "IT", "GE", "GNRC", "GD", "GIS", "GPC", 
"GILD", "GL", "GS", "GWW", "HAL", "HBI", "HIG", "HAS", "HCA", "HSY","MSTR","AU","PANW","GME","AMC","DJT"]  # Add more tickers here
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # Analyze last 90 days of data

    # ----- FETCH STOCK DATA -----
    print("Fetching stock data...")
    stock_data = fetch_stock_data(tickers, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))

    # ----- STRICT BULLISH ANALYSIS -----
    print("\nAnalyzing for strict bullish trends...")
    strict_bullish_tickers = analyze_bullish_trend(stock_data, window=5)
    print("\n--- Strict Bullish Trends ---")
    if strict_bullish_tickers:
        for ticker, df in strict_bullish_tickers:
            details = get_ticker_details(ticker, df)
            if details:
                print(f"{ticker} | Current Price: {details['current_price']} (as of {details['timestamp']}) | "
                      f"Open: {details['open_price']} | Previous Close: {details['previous_close']} | "
                      f"Price a Month Ago: {details['one_month_price']}")
    else:
        print("No tickers found.")

    # ----- SOFT BULLISH ANALYSIS -----
    print("\nAnalyzing for soft bullish trends...")
    soft_bullish_tickers = analyze_soft_trend(stock_data, window=3)
    print("\n--- Soft Bullish Trends ---")
    if soft_bullish_tickers:
        for ticker, df in soft_bullish_tickers:
            details = get_ticker_details(ticker, df)
            if details:
                print(f"{ticker} | Current Price: {details['current_price']} (as of {details['timestamp']}) | "
                      f"Open: {details['open_price']} | Previous Close: {details['previous_close']} | "
                      f"Price a Month Ago: {details['one_month_price']}")
    else:
        print("No tickers found.")
