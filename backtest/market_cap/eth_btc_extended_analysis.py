#!/usr/bin/env python3
"""
ETH/BTC Market Cap Analysis with Extended Historical Data (2021-Present)
Uses alternative data sources to bypass CoinGecko's 365-day limitation
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import ccxt
import requests
import json
import os
from typing import Optional

class ExtendedETHBTCAnalyzer:
    def __init__(self):
        self.exchange = ccxt.binance({
            'timeout': 30000,
            'rateLimit': 1200,
        })
        self.historical_data_dir = "historical_data"
        
    def load_extended_historical_data(self) -> Optional[pd.DataFrame]:
        """
        Load extended historical data from various sources
        """
        data_files = [
            "extended_market_cap_data_2021_present.csv",  # Mock data
            "btc_eth_historical_combined.csv",            # Manual download
            "yahoo_finance_combined.csv"                   # Yahoo Finance
        ]
        
        for filename in data_files:
            filepath = os.path.join(self.historical_data_dir, filename)
            if os.path.exists(filepath):
                print(f"📂 Loading historical data from: {filename}")
                try:
                    df = pd.read_csv(filepath)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                    
                    # Ensure required columns exist
                    required_cols = ['btc_market_cap', 'eth_market_cap', 'eth_btc_market_cap_ratio']
                    if all(col in df.columns for col in required_cols):
                        print(f"✅ Loaded {len(df)} data points from {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
                        return df
                    else:
                        print(f"❌ Missing required columns in {filename}")
                        
                except Exception as e:
                    print(f"❌ Error loading {filename}: {e}")
                    continue
        
        print("❌ No suitable historical data found. Run download_historical_data.py first.")
        return None

    def get_current_market_data(self):
        """Get current market data from CoinGecko"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'bitcoin,ethereum',
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_change': 'true'
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return {
                    'btc_market_cap': data['bitcoin']['usd_market_cap'],
                    'eth_market_cap': data['ethereum']['usd_market_cap'],
                    'eth_btc_market_cap_ratio': data['ethereum']['usd_market_cap'] / data['bitcoin']['usd_market_cap'],
                    'btc_price': data['bitcoin']['usd'],
                    'eth_price': data['ethereum']['usd']
                }
        except Exception as e:
            print(f"Warning: Could not fetch current data: {e}")
            return None

    def analyze_market_cap_trends(self, df: pd.DataFrame):
        """
        Analyze long-term trends in market cap ratios
        """
        print("\n📊 EXTENDED MARKET CAP ANALYSIS (2021-Present)")
        print("=" * 60)
        
        # Calculate key statistics
        current_ratio = df['eth_btc_market_cap_ratio'].iloc[-1]
        max_ratio = df['eth_btc_market_cap_ratio'].max()
        min_ratio = df['eth_btc_market_cap_ratio'].min()
        avg_ratio = df['eth_btc_market_cap_ratio'].mean()
        
        # Find significant dates
        max_date = df['eth_btc_market_cap_ratio'].idxmax()
        min_date = df['eth_btc_market_cap_ratio'].idxmin()
        
        print(f"📈 ETH/BTC Market Cap Ratio Analysis:")
        print(f"   Current:     {current_ratio:.4f}")
        print(f"   Average:     {avg_ratio:.4f}")
        print(f"   Maximum:     {max_ratio:.4f} (on {max_date.strftime('%Y-%m-%d')})")
        print(f"   Minimum:     {min_ratio:.4f} (on {min_date.strftime('%Y-%m-%d')})")
        print(f"   Range:       {max_ratio/min_ratio:.2f}x variation")
        
        # Market cycle analysis
        print(f"\n🔄 Market Cycle Insights:")
        if current_ratio > avg_ratio * 1.1:
            print(f"   🔥 ETH is relatively STRONG vs BTC ({current_ratio/avg_ratio:.1f}x above average)")
        elif current_ratio < avg_ratio * 0.9:
            print(f"   ❄️  ETH is relatively WEAK vs BTC ({avg_ratio/current_ratio:.1f}x below average)")
        else:
            print(f"   ⚖️  ETH/BTC ratio is near historical average")
            
        # Trend analysis (last 90 days vs last 365 days)
        if len(df) >= 365:
            recent_90d = df['eth_btc_market_cap_ratio'].tail(90).mean()
            year_avg = df['eth_btc_market_cap_ratio'].tail(365).mean()
            
            if recent_90d > year_avg * 1.05:
                print(f"   📈 Recent 90-day trend: UPWARD ({recent_90d/year_avg:.1f}x above year average)")
            elif recent_90d < year_avg * 0.95:
                print(f"   📉 Recent 90-day trend: DOWNWARD ({year_avg/recent_90d:.1f}x below year average)")
            else:
                print(f"   ➡️  Recent 90-day trend: SIDEWAYS")

    def create_extended_chart(self, df: pd.DataFrame):
        """
        Create comprehensive chart with 2021-present data
        """
        current_data = self.get_current_market_data()
        
        # Create 4-panel comprehensive chart
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 12))
        fig.suptitle(f'ETH vs BTC Extended Analysis: 2021 to Present ({len(df)} Days)', 
                     fontsize=16, fontweight='bold')
        
        # Chart 1: ETH/BTC Market Cap Ratio over time
        ax1.plot(df.index, df['eth_btc_market_cap_ratio'], 
                color='purple', linewidth=2, label='ETH/BTC Market Cap Ratio')
        ax1.set_title('ETH/BTC Market Cap Ratio (2021-Present)', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Market Cap Ratio', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Add horizontal lines for key levels
        avg_ratio = df['eth_btc_market_cap_ratio'].mean()
        ax1.axhline(y=avg_ratio, color='orange', linestyle='--', alpha=0.7, label=f'Average: {avg_ratio:.4f}')
        
        if current_data:
            current_ratio = current_data['eth_btc_market_cap_ratio']
            ax1.axhline(y=current_ratio, color='red', linestyle='-', alpha=0.8, label=f'Current: {current_ratio:.4f}')
        
        ax1.legend()
        
        # Chart 2: Market Caps with Ratio Overlay (your requested visualization)
        ax2_twin1 = ax2.twinx()
        ax2_twin2 = ax2.twinx()
        ax2_twin2.spines['right'].set_position(('outward', 60))
        
        # Market caps
        line1 = ax2.plot(df.index, df['btc_market_cap'] / 1e12, 
                        color='orange', linewidth=2.5, label='BTC Market Cap (T USD)')
        line2 = ax2_twin1.plot(df.index, df['eth_market_cap'] / 1e12,
                              color='blue', linewidth=2.5, label='ETH Market Cap (T USD)')
        
        # ETH/BTC ratio overlay
        line3 = ax2_twin2.plot(df.index, df['eth_btc_market_cap_ratio'],
                              color='purple', linewidth=3, alpha=0.8, linestyle='--', 
                              label='ETH/BTC Ratio')
        
        ax2.set_title('Market Caps with ETH/BTC Ratio Overlay', fontsize=14, fontweight='bold')
        ax2.set_ylabel('BTC Market Cap (T USD)', fontsize=12, color='orange')
        ax2_twin1.set_ylabel('ETH Market Cap (T USD)', fontsize=12, color='blue')
        ax2_twin2.set_ylabel('ETH/BTC Ratio', fontsize=12, color='purple')
        
        ax2.tick_params(axis='y', labelcolor='orange')
        ax2_twin1.tick_params(axis='y', labelcolor='blue')
        ax2_twin2.tick_params(axis='y', labelcolor='purple')
        ax2.grid(True, alpha=0.3)
        
        # Combine legends
        lines = line1 + line2 + line3
        labels = [l.get_label() for l in lines]
        ax2.legend(lines, labels, loc='upper left')
        
        # Chart 3: BTC/ETH Market Cap Ratio (inverted)
        ax3.plot(df.index, df['btc_eth_market_cap_ratio'], 
                color='darkorange', linewidth=2, label='BTC/ETH Market Cap Ratio')
        ax3.set_title('BTC/ETH Market Cap Ratio (Inverted)', fontsize=14, fontweight='bold')
        ax3.set_ylabel('BTC/ETH Ratio', fontsize=12)
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        
        # Chart 4: Rolling correlation and volatility analysis
        # Calculate 30-day rolling correlation and volatility
        if len(df) >= 30:
            window = 30
            df_rolling = df.rolling(window=window)
            eth_volatility = df_rolling['eth_market_cap'].std() / df_rolling['eth_market_cap'].mean()
            btc_volatility = df_rolling['btc_market_cap'].std() / df_rolling['btc_market_cap'].mean()
            
            ax4.plot(df.index, eth_volatility, color='blue', linewidth=2, label=f'ETH Volatility ({window}d)')
            ax4.plot(df.index, btc_volatility, color='orange', linewidth=2, label=f'BTC Volatility ({window}d)')
            
            ax4.set_title(f'Market Cap Volatility Comparison ({window}-day rolling)', fontsize=14, fontweight='bold')
            ax4.set_ylabel('Volatility (CV)', fontsize=12)
            ax4.grid(True, alpha=0.3)
            ax4.legend()
        
        # Format x-axes
        for ax in [ax1, ax2, ax3, ax4]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Add summary statistics
        stats_text = f"""Extended Analysis Summary (2021-Present):
        
Data Points: {len(df)} days
Date Range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}

ETH/BTC Market Cap Ratio:
  Current: {df['eth_btc_market_cap_ratio'].iloc[-1]:.4f}
  Average: {df['eth_btc_market_cap_ratio'].mean():.4f}
  Maximum: {df['eth_btc_market_cap_ratio'].max():.4f}
  Minimum: {df['eth_btc_market_cap_ratio'].min():.4f}"""
        
        if current_data:
            stats_text += f"""
            
Live Market Data:
  BTC Price: ${current_data['btc_price']:,.0f}
  ETH Price: ${current_data['eth_price']:,.0f}
  BTC Market Cap: ${current_data['btc_market_cap']/1e12:.2f}T
  ETH Market Cap: ${current_data['eth_market_cap']/1e12:.2f}T"""
        
        fig.text(0.02, 0.02, stats_text, fontsize=9, 
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8),
                verticalalignment='bottom')
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.92, bottom=0.25, right=0.88)
        
        # Save chart
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"eth_btc_extended_analysis_{timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"📊 Extended analysis chart saved as: {filename}")
        
        plt.show()

def main():
    """
    Main function to run extended analysis
    """
    print("🚀 ETH/BTC Extended Market Cap Analysis (2021-Present)")
    print("=" * 60)
    
    analyzer = ExtendedETHBTCAnalyzer()
    
    # Try to load extended historical data
    historical_df = analyzer.load_extended_historical_data()
    
    if historical_df is None:
        print("\n❌ No extended historical data found!")
        print("\n💡 To get 2021-present data, please:")
        print("1. Run: python download_historical_data.py")
        print("2. Or manually download data from CoinMarketCap")
        print("3. Or install yfinance: pip install yfinance")
        return
    
    # Analyze trends
    analyzer.analyze_market_cap_trends(historical_df)
    
    # Create comprehensive chart
    print(f"\n📊 Creating extended analysis chart...")
    analyzer.create_extended_chart(historical_df)
    
    print("\n✅ Extended analysis complete!")
    print("📈 This chart shows ETH/BTC market cap insights from 2021 to present")

if __name__ == "__main__":
    main() 