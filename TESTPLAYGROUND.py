"""

TEST PLAYGROUND FOR DEBUGGING

"""
import yfinance as yf
import pandas as pd
import datetime
import os
import threading
import time
import numpy as np



def main():
    print("Test playground\n")
    test_data = pd.DataFrame({
    'Close': [100, 101, 102, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92]
    })
    print(f"DEBUG: Test RSI calculation with data:\n{test_data}")
    rsi = calculate_rsi(test_data)
    print(f"DEBUG: Calculated RSI: {rsi}")

if __name__ == "__main__":
    main()
