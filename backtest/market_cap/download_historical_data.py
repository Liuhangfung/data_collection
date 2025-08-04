#!/usr/bin/env python3
"""
Download historical BTC and ETH market cap data from 2021 to present
Uses alternative data sources since CoinGecko free tier is limited to 365 days
"""

import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
import os

class HistoricalDataDownloader:
    def __init__(self):
        self.base_dir = "historical_data"
        os.makedirs(self.base_dir, exist_ok=True)
        
    def download_coinmarketcap_data(self):
        """
        Instructions for downloading data from CoinMarketCap
        """
        print("📋 Manual Download Instructions (CoinMarketCap):")
        print("=" * 60)
        print("1. Go to https://coinmarketcap.com/currencies/bitcoin/historical-data/")
        print("2. Set date range: Jan 1, 2021 to today")
        print("3. Download CSV as 'btc_historical.csv'")
        print()
        print("4. Go to https://coinmarketcap.com/currencies/ethereum/historical-data/")
        print("5. Set date range: Jan 1, 2021 to today") 
        print("6. Download CSV as 'eth_historical.csv'")
        print()
        print("7. Place both files in the 'historical_data' folder")
        print("=" * 60)
        
    def try_yahoo_finance(self):
        """
        Try to get data from Yahoo Finance using yfinance
        """
        try:
            import yfinance as yf
            
            print("📈 Downloading from Yahoo Finance...")
            
            # Download BTC and ETH data from 2021
            start_date = "2021-01-01"
            end_date = datetime.now().strftime("%Y-%m-%d")
            
            # BTC-USD
            btc = yf.download("BTC-USD", start=start_date, end=end_date, interval="1d")
            btc_file = os.path.join(self.base_dir, "btc_yahoo_finance.csv")
            btc.to_csv(btc_file)
            print(f"✅ BTC data saved to: {btc_file}")
            
            # ETH-USD  
            eth = yf.download("ETH-USD", start=start_date, end=end_date, interval="1d")
            eth_file = os.path.join(self.base_dir, "eth_yahoo_finance.csv")
            eth.to_csv(eth_file)
            print(f"✅ ETH data saved to: {eth_file}")
            
            return True
            
        except ImportError:
            print("❌ yfinance not installed. Install with: pip install yfinance")
            return False
        except Exception as e:
            print(f"❌ Error downloading from Yahoo Finance: {e}")
            return False

    def create_mock_historical_data(self):
        """
        Create extended mock data for demonstration (2021-present)
        """
        print("🔨 Creating extended mock historical data for demonstration...")
        
        # Create date range from 2021 to now
        start_date = datetime(2021, 1, 1)
        end_date = datetime.now()
        dates = pd.date_range(start_date, end_date, freq='D')
        
        # Create realistic-looking market cap data with trends
        np.random.seed(42)  # For reproducible results
        
        # BTC market cap progression (started ~600B in 2021, now ~2.4T)
        btc_mc_start = 600e9  # $600B
        btc_mc_end = 2.4e12   # $2.4T
        btc_trend = np.linspace(btc_mc_start, btc_mc_end, len(dates))
        btc_noise = np.random.normal(0, 0.1, len(dates))
        btc_market_cap = btc_trend * (1 + btc_noise)
        
        # ETH market cap progression (started ~150B in 2021, now ~470B)  
        eth_mc_start = 150e9  # $150B
        eth_mc_end = 470e9    # $470B
        eth_trend = np.linspace(eth_mc_start, eth_mc_end, len(dates))
        eth_noise = np.random.normal(0, 0.15, len(dates))  # More volatile
        eth_market_cap = eth_trend * (1 + eth_noise)
        
        # Add some major events/cycles
        # Bull run 2021 (peaks around Nov 2021)
        bull_peak = datetime(2021, 11, 1)
        bear_bottom = datetime(2022, 11, 1)
        recovery_start = datetime(2024, 1, 1)
        
        for i, date in enumerate(dates):
            # 2021 bull run
            if date <= bull_peak:
                multiplier = 1.5 + 0.5 * np.sin((date - start_date).days / 100)
                btc_market_cap[i] *= multiplier
                eth_market_cap[i] *= multiplier * 1.2  # ETH outperformed
                
            # 2022 bear market
            elif date <= bear_bottom:
                multiplier = 0.5 + 0.3 * np.cos((date - bull_peak).days / 50)
                btc_market_cap[i] *= multiplier
                eth_market_cap[i] *= multiplier * 0.8  # ETH fell more
                
            # 2024 recovery
            elif date >= recovery_start:
                multiplier = 1.2 + 0.4 * np.sin((date - recovery_start).days / 80)
                btc_market_cap[i] *= multiplier
                eth_market_cap[i] *= multiplier * 1.1
        
        # Calculate ratios
        eth_btc_ratio = eth_market_cap / btc_market_cap
        
        # Create DataFrame
        historical_df = pd.DataFrame({
            'timestamp': dates,
            'btc_market_cap': btc_market_cap,
            'eth_market_cap': eth_market_cap,
            'eth_btc_market_cap_ratio': eth_btc_ratio,
            'btc_eth_market_cap_ratio': 1 / eth_btc_ratio
        })
        
        # Save to CSV
        filename = os.path.join(self.base_dir, "extended_market_cap_data_2021_present.csv")
        historical_df.to_csv(filename, index=False)
        
        print(f"✅ Extended historical data created: {filename}")
        print(f"📊 Data range: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
        print(f"📈 Data points: {len(dates)}")
        
        return filename

def main():
    """
    Main function to download/create historical data
    """
    downloader = HistoricalDataDownloader()
    
    print("🔄 Attempting to get historical data from 2021...")
    print()
    
    # Try Yahoo Finance first
    if downloader.try_yahoo_finance():
        print("✅ Successfully downloaded from Yahoo Finance!")
        return
    
    # Show manual download instructions
    downloader.download_coinmarketcap_data()
    
    # Create mock data for demonstration
    print("\n" + "="*60)
    print("🎯 DEMONSTRATION MODE")
    print("="*60)
    print("Since APIs are limited, creating extended mock data for demonstration...")
    print("This shows what the analysis would look like with real 2021-present data.")
    print()
    
    filename = downloader.create_mock_historical_data()
    
    print("\n💡 Next steps:")
    print("1. Use the mock data file created above, OR")
    print("2. Download real data manually from CoinMarketCap, OR") 
    print("3. Install yfinance: pip install yfinance")
    print()
    print("4. Then run: python eth_btc_extended_analysis.py")

if __name__ == "__main__":
    main() 