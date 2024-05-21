# -*- coding: utf-8 -*-
"""
Created on Mon Oct 25 14:11:44 2021

This script retrieves data from a cryptocurrency exchange, processes it, and determines 
technical signals (MACD & RSI) according to a trading strategy. It uses the ccxt library 
to connect to the exchange, pandas to process data, ta library for technical indicators, 
and schedule to run the script periodically.

"""

import ccxt
import pandas as pd
pd.set_option('display.max_rows', None)
from datetime import datetime
from ta.trend import MACD
from ta.momentum import RSIIndicator
import warnings
warnings.filterwarnings('ignore')
import schedule
import time

# Connection to the exchange for data retrieval and order execution
exchange = ccxt.binance()

# Function for data retrieval and DataFrame processing
def technical_signals(df):
    indicator_macd = MACD(df['close'])
    df['MACD'] = indicator_macd.macd()
    df['Signal'] = indicator_macd.macd_signal()
    df['MACD Histogram'] = indicator_macd.macd_diff()
    df['MACD_Signal'] = False

    indicator_rsi = RSIIndicator(df['close'], window=14)
    df['RSI_Signal'] = False
    df['RSI'] = indicator_rsi.rsi()

    for current in range(1, len(df.index)):
        previous = current - 1
        if (df['MACD'][current] > df['Signal'][current]) and (df['MACD'][previous] < df['Signal'][previous]) and (df['MACD'][current] < 0):
            df['MACD_Signal'][current] = True
        elif (df['MACD'][current] < df['Signal'][current]) and (df['MACD'][previous] > df['Signal'][previous]):
            df['MACD_Signal'][current] = False
        else:
            df['MACD_Signal'][current] = df['MACD_Signal'][previous]
    return df

in_position = False

def reading_market(df):
    global in_position
    print("Looking for signals...")
    print(df.tail(5))
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1

    if not df['MACD_Signal'][previous_row_index] and df['MACD_Signal'][last_row_index]:
        print("Uptrend activated according MACD, BUY SIGNAL triggered")
        if not in_position:
            order_buy = 'Here goes BUY order'  # exchange.create_market_buy_order('ETH/USDT', 1)
            print(order_buy)
            in_position = True
        else:
            print("Already in position, skip BUY signal")

    if df['MACD_Signal'][previous_row_index] and not df['MACD_Signal'][last_row_index]:
        if in_position:
            print("Downtrend activated, SELL SIGNAL triggered")
            order_sell = 'Here goes SELL order'  # exchange.create_market_sell_order('ETH/USDT', 1)
            print(order_sell)
            in_position = False
        else:
            print("Not in position, skip SELL Signal")

def execute_connection(symbol='ETH/USDT', timeframe='1m'):
    raw_data = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
    df = pd.DataFrame(raw_data[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    print(f"Executing connection and data processing at... {datetime.now().isoformat()}")
    complete_df = technical_signals(df)
    reading_market(complete_df)

schedule.every(10).seconds.do(execute_connection)

while True:
    schedule.run_pending()
    time.sleep(1)
