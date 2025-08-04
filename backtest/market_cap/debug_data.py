#!/usr/bin/env python3
"""
Debug script to examine CoinMarketCap CSV data structure
"""

import pandas as pd
from datetime import datetime

def debug_csv_files():
    """
    Debug the CSV files to understand structure and fix alignment
    """
    print("🔍 DEBUGGING COINMARKETCAP CSV FILES")
    print("=" * 50)
    
    # Load Bitcoin data
    print("\n📊 Bitcoin Data Analysis:")
    btc_df = pd.read_csv("Bitcoin_2021_7_1-2025_7_28_historical_data_coinmarketcap.csv", delimiter=';')
    print(f"Columns: {list(btc_df.columns)}")
    print(f"Shape: {btc_df.shape}")
    print(f"Sample data:")
    print(btc_df.head(3))
    
    # Process timestamps
    btc_df['timestamp'] = pd.to_datetime(btc_df['timestamp'].str.strip('"'))
    print(f"Date range: {btc_df['timestamp'].min()} to {btc_df['timestamp'].max()}")
    print(f"Sorted dates (first 5): {btc_df['timestamp'].sort_values().head().tolist()}")
    
    # Load Ethereum data
    print("\n📊 Ethereum Data Analysis:")
    eth_df = pd.read_csv("Ethereum_2021_7_1-2025_7_28_historical_data_coinmarketcap.csv", delimiter=';')
    print(f"Columns: {list(eth_df.columns)}")
    print(f"Shape: {eth_df.shape}")
    print(f"Sample data:")
    print(eth_df.head(3))
    
    # Process timestamps
    eth_df['timestamp'] = pd.to_datetime(eth_df['timestamp'].str.strip('"'))
    print(f"Date range: {eth_df['timestamp'].min()} to {eth_df['timestamp'].max()}")
    print(f"Sorted dates (first 5): {eth_df['timestamp'].sort_values().head().tolist()}")
    
    # Check overlap
    print(f"\n🔄 Data Overlap Analysis:")
    btc_dates = set(btc_df['timestamp'])
    eth_dates = set(eth_df['timestamp'])
    common_dates = btc_dates.intersection(eth_dates)
    
    print(f"BTC unique dates: {len(btc_dates)}")
    print(f"ETH unique dates: {len(eth_dates)}")
    print(f"Common dates: {len(common_dates)}")
    
    if len(common_dates) > 0:
        common_sorted = sorted(list(common_dates))
        print(f"Common date range: {common_sorted[0]} to {common_sorted[-1]}")
        print(f"Sample common dates: {common_sorted[:5]}")
    
    # Check for monthly alignment
    print(f"\n📅 Monthly Alignment Check:")
    
    # Convert to month-end dates for alignment
    btc_df['month_end'] = btc_df['timestamp'].dt.to_period('M').dt.end_time
    eth_df['month_end'] = eth_df['timestamp'].dt.to_period('M').dt.end_time
    
    btc_months = set(btc_df['month_end'])
    eth_months = set(eth_df['month_end'])
    common_months = btc_months.intersection(eth_months)
    
    print(f"BTC months: {len(btc_months)}")
    print(f"ETH months: {len(eth_months)}")
    print(f"Common months: {len(common_months)}")
    
    if len(common_months) > 0:
        common_months_sorted = sorted(list(common_months))
        print(f"Common months range: {common_months_sorted[0]} to {common_months_sorted[-1]}")

if __name__ == "__main__":
    debug_csv_files() 