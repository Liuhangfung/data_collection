#!/usr/bin/env python3
"""
ETH/BTC Market Cap Analysis using CoinMarketCap Historical Data (2021-2025)
Uses the provided CSV files with 4+ years of real market cap data
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class CoinMarketCapAnalyzer:
    def __init__(self):
        self.btc_file = "Bitcoin_2021_7_1-2025_7_28_historical_data_coinmarketcap.csv"
        self.eth_file = "Ethereum_2021_7_1-2025_7_28_historical_data_coinmarketcap.csv"
        
    def load_data(self):
        """
        Load and process CoinMarketCap CSV data
        """
        print("📂 Loading CoinMarketCap historical data...")
        
        try:
            # Load Bitcoin data
            btc_df = pd.read_csv(self.btc_file, delimiter=';')
            print(f"✅ Bitcoin data loaded: {len(btc_df)} data points")
            
            # Load Ethereum data  
            eth_df = pd.read_csv(self.eth_file, delimiter=';')
            print(f"✅ Ethereum data loaded: {len(eth_df)} data points")
            
            # Process Bitcoin data
            btc_df['timestamp'] = pd.to_datetime(btc_df['timestamp'].str.strip('"'))
            btc_df = btc_df.sort_values('timestamp')
            btc_df.set_index('timestamp', inplace=True)
            
            # Process Ethereum data
            eth_df['timestamp'] = pd.to_datetime(eth_df['timestamp'].str.strip('"'))
            eth_df = eth_df.sort_values('timestamp')
            eth_df.set_index('timestamp', inplace=True)
            
            print(f"📅 Bitcoin date range: {btc_df.index[0].strftime('%Y-%m-%d')} to {btc_df.index[-1].strftime('%Y-%m-%d')}")
            print(f"📅 Ethereum date range: {eth_df.index[0].strftime('%Y-%m-%d')} to {eth_df.index[-1].strftime('%Y-%m-%d')}")
            
            return btc_df, eth_df
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return None, None
    
    def process_and_align_data(self, btc_df, eth_df):
        """
        Process and align the Bitcoin and Ethereum data for analysis
        """
        print("\n🔄 Processing and aligning data...")
        
        # Since Bitcoin data appears to be monthly and Ethereum daily,
        # we need to resample or align them properly
        
        # Check data frequency
        btc_freq = self.detect_frequency(btc_df)
        eth_freq = self.detect_frequency(eth_df)
        
        print(f"📊 Bitcoin data frequency: {btc_freq}")
        print(f"📊 Ethereum data frequency: {eth_freq}")
        
        # If frequencies are different, resample to monthly
        if len(btc_df) != len(eth_df):
            print("🔄 Resampling to monthly frequency for alignment...")
            
            # Resample Ethereum to monthly (last day of month)
            eth_monthly = eth_df.resample('M').last()
            
            # Use Bitcoin monthly data as-is or resample if needed
            if btc_freq == "Monthly":
                btc_monthly = btc_df.copy()
            else:
                btc_monthly = btc_df.resample('M').last()
            
            # Align the datasets on common dates
            common_dates = btc_monthly.index.intersection(eth_monthly.index)
            btc_aligned = btc_monthly.loc[common_dates]
            eth_aligned = eth_monthly.loc[common_dates]
            
        else:
            # Data is already aligned
            btc_aligned = btc_df.copy()
            eth_aligned = eth_df.copy()
        
        # Create combined dataset
        combined_df = pd.DataFrame({
            'btc_price': btc_aligned['close'],
            'eth_price': eth_aligned['close'],
            'btc_market_cap': btc_aligned['marketCap'],
            'eth_market_cap': eth_aligned['marketCap'],
            'btc_volume': btc_aligned['volume'],
            'eth_volume': eth_aligned['volume']
        })
        
        # Calculate ratios
        combined_df['eth_btc_price_ratio'] = combined_df['eth_price'] / combined_df['btc_price']
        combined_df['eth_btc_market_cap_ratio'] = combined_df['eth_market_cap'] / combined_df['btc_market_cap']
        combined_df['btc_eth_market_cap_ratio'] = combined_df['btc_market_cap'] / combined_df['eth_market_cap']
        
        print(f"✅ Final dataset: {len(combined_df)} aligned data points")
        print(f"📅 Analysis period: {combined_df.index[0].strftime('%Y-%m-%d')} to {combined_df.index[-1].strftime('%Y-%m-%d')}")
        
        return combined_df
    
    def detect_frequency(self, df):
        """
        Detect the frequency of the data (daily, weekly, monthly)
        """
        if len(df) < 2:
            return "Unknown"
        
        avg_days = (df.index[-1] - df.index[0]).days / (len(df) - 1)
        
        if avg_days <= 1.5:
            return "Daily"
        elif avg_days <= 7.5:
            return "Weekly"
        elif avg_days <= 35:
            return "Monthly"
        else:
            return "Other"
    
    def analyze_market_trends(self, df):
        """
        Analyze market cap trends and key statistics
        """
        print("\n📊 MARKET CAP ANALYSIS (2021-2025)")
        print("=" * 60)
        
        # Current values
        current_eth_btc_ratio = df['eth_btc_market_cap_ratio'].iloc[-1]
        current_btc_mc = df['btc_market_cap'].iloc[-1]
        current_eth_mc = df['eth_market_cap'].iloc[-1]
        
        # Historical statistics
        max_ratio = df['eth_btc_market_cap_ratio'].max()
        min_ratio = df['eth_btc_market_cap_ratio'].min()
        avg_ratio = df['eth_btc_market_cap_ratio'].mean()
        
        max_date = df['eth_btc_market_cap_ratio'].idxmax()
        min_date = df['eth_btc_market_cap_ratio'].idxmin()
        
        print(f"💰 Current Market Data:")
        print(f"   BTC Market Cap: ${current_btc_mc/1e12:.2f}T")
        print(f"   ETH Market Cap: ${current_eth_mc/1e12:.2f}T")
        print(f"   ETH/BTC Ratio: {current_eth_btc_ratio:.4f}")
        print(f"   BTC/ETH Ratio: {1/current_eth_btc_ratio:.2f}")
        
        print(f"\n📈 Historical ETH/BTC Market Cap Ratio:")
        print(f"   Average (2021-2025): {avg_ratio:.4f}")
        print(f"   Maximum: {max_ratio:.4f} on {max_date.strftime('%Y-%m-%d')}")
        print(f"   Minimum: {min_ratio:.4f} on {min_date.strftime('%Y-%m-%d')}")
        print(f"   Total Range: {max_ratio/min_ratio:.2f}x variation")
        
        # Market cycle analysis
        print(f"\n🔄 Market Cycle Position:")
        ratio_percentile = (current_eth_btc_ratio - min_ratio) / (max_ratio - min_ratio) * 100
        
        if current_eth_btc_ratio > avg_ratio * 1.1:
            strength = "STRONG"
            emoji = "🔥"
        elif current_eth_btc_ratio < avg_ratio * 0.9:
            strength = "WEAK"
            emoji = "❄️"
        else:
            strength = "NEUTRAL"
            emoji = "⚖️"
        
        print(f"   {emoji} ETH is {strength} vs BTC")
        print(f"   Current ratio is at {ratio_percentile:.1f}% of historical range")
        
        # Recent trends
        if len(df) >= 12:  # Last 12 data points
            recent_avg = df['eth_btc_market_cap_ratio'].tail(12).mean()
            older_avg = df['eth_btc_market_cap_ratio'].iloc[-24:-12].mean() if len(df) >= 24 else avg_ratio
            
            trend_direction = "UP" if recent_avg > older_avg else "DOWN"
            trend_strength = abs(recent_avg - older_avg) / older_avg * 100
            
            print(f"   📈 Recent trend: {trend_direction} ({trend_strength:.1f}% change)")
        
        return {
            'current_ratio': current_eth_btc_ratio,
            'avg_ratio': avg_ratio,
            'max_ratio': max_ratio,
            'min_ratio': min_ratio,
            'max_date': max_date,
            'min_date': min_date
        }
    
    def create_comprehensive_chart(self, df, stats):
        """
        Create the comprehensive chart with market caps and ETH/BTC ratio overlay
        """
        print(f"\n📊 Creating comprehensive analysis chart...")
        
        # Create 3-panel chart as requested
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(24, 8))
        fig.suptitle(f'ETH vs BTC Market Cap Analysis: 2021-2025 ({len(df)} Data Points)', 
                     fontsize=16, fontweight='bold')
        
        # Chart 1: ETH/BTC Price Ratio
        ax1.plot(df.index, df['eth_btc_price_ratio'], 
                color='purple', linewidth=2, label='ETH/BTC Price Ratio')
        ax1.set_title('ETH/BTC Price Ratio (2021-2025)', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price Ratio', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Add current ratio line
        current_price_ratio = df['eth_btc_price_ratio'].iloc[-1]
        ax1.axhline(y=current_price_ratio, color='red', linestyle='--', alpha=0.7)
        ax1.text(0.02, 0.98, f'Current: {current_price_ratio:.6f}', 
                transform=ax1.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        # Chart 2: BTC and ETH USD Prices
        ax2_twin = ax2.twinx()
        
        line1 = ax2.plot(df.index, df['btc_price'], 
                        color='orange', linewidth=2, label='BTC Price (USD)')
        line2 = ax2_twin.plot(df.index, df['eth_price'], 
                             color='blue', linewidth=2, label='ETH Price (USD)')
        
        ax2.set_title('BTC and ETH USD Prices', fontsize=14, fontweight='bold')
        ax2.set_ylabel('BTC Price (USD)', fontsize=12, color='orange')
        ax2_twin.set_ylabel('ETH Price (USD)', fontsize=12, color='blue')
        ax2.tick_params(axis='y', labelcolor='orange')
        ax2_twin.tick_params(axis='y', labelcolor='blue')
        ax2.grid(True, alpha=0.3)
        
        # Combine legends
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Chart 3: Market Caps with ETH/BTC Ratio Overlay (THE KEY CHART YOU REQUESTED!)
        ax3_twin1 = ax3.twinx()
        ax3_twin2 = ax3.twinx()
        ax3_twin2.spines['right'].set_position(('outward', 60))
        
        # Market caps
        line1 = ax3.plot(df.index, df['btc_market_cap'] / 1e12, 
                        color='orange', linewidth=2.5, label='BTC Market Cap (T USD)')
        line2 = ax3_twin1.plot(df.index, df['eth_market_cap'] / 1e12,
                              color='blue', linewidth=2.5, label='ETH Market Cap (T USD)')
        
        # ETH/BTC market cap ratio overlay (THE MAIN INSIGHT!)
        line3 = ax3_twin2.plot(df.index, df['eth_btc_market_cap_ratio'],
                              color='purple', linewidth=3, alpha=0.9, linestyle='--', 
                              label='ETH/BTC Market Cap Ratio')
        
        ax3.set_title('Market Caps with ETH/BTC Ratio Overlay (2021-2025)', fontsize=14, fontweight='bold')
        ax3.set_ylabel('BTC Market Cap (T USD)', fontsize=12, color='orange')
        ax3_twin1.set_ylabel('ETH Market Cap (T USD)', fontsize=12, color='blue')
        ax3_twin2.set_ylabel('ETH/BTC Ratio', fontsize=12, color='purple')
        
        ax3.tick_params(axis='y', labelcolor='orange')
        ax3_twin1.tick_params(axis='y', labelcolor='blue')
        ax3_twin2.tick_params(axis='y', labelcolor='purple')
        ax3.grid(True, alpha=0.3)
        
        # Add ratio reference lines
        avg_ratio = stats['avg_ratio']
        ax3_twin2.axhline(y=avg_ratio, color='gray', linestyle=':', alpha=0.7, label=f'Avg: {avg_ratio:.4f}')
        ax3_twin2.axhline(y=stats['current_ratio'], color='red', linestyle='-', alpha=0.8)
        
        # Combine all legends
        lines = line1 + line2 + line3
        labels = [l.get_label() for l in lines]
        ax3.legend(lines, labels, loc='upper left')
        
        # Add key insight annotations
        ax3.text(0.02, 0.98, f"Current ETH/BTC Ratio: {stats['current_ratio']:.4f}", 
                transform=ax3.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='plum', alpha=0.7))
        
        ax3.text(0.02, 0.85, f"Historical Average: {avg_ratio:.4f}", 
                transform=ax3.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.7))
        
        # Format x-axes
        for ax in [ax1, ax2, ax3]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Add comprehensive statistics
        stats_text = f"""ETH/BTC Market Cap Analysis (2021-2025):

Data Source: CoinMarketCap Historical Data
Time Period: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}
Data Points: {len(df)}

Current Market Caps:
  BTC: ${df['btc_market_cap'].iloc[-1]/1e12:.2f}T
  ETH: ${df['eth_market_cap'].iloc[-1]/1e12:.2f}T

ETH/BTC Market Cap Ratio:
  Current: {stats['current_ratio']:.4f}
  4-Year Average: {stats['avg_ratio']:.4f}
  Maximum: {stats['max_ratio']:.4f} ({stats['max_date'].strftime('%Y-%m')})
  Minimum: {stats['min_ratio']:.4f} ({stats['min_date'].strftime('%Y-%m')})
  
Price vs Market Cap:
  ETH/BTC Price Ratio: {df['eth_btc_price_ratio'].iloc[-1]:.6f}
  Market Cap Ratio: {stats['current_ratio']:.4f}
  Difference: {((stats['current_ratio'] / df['eth_btc_price_ratio'].iloc[-1]) - 1) * 100:+.1f}%"""
        
        fig.text(0.02, 0.02, stats_text, fontsize=9, 
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8),
                verticalalignment='bottom')
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.90, bottom=0.25, right=0.85)
        
        # Save chart
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"eth_btc_coinmarketcap_analysis_{timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"📊 Chart saved as: {filename}")
        
        plt.show()

def main():
    """
    Main function to run the comprehensive analysis
    """
    print("🚀 ETH/BTC Market Cap Analysis using CoinMarketCap Data (2021-2025)")
    print("=" * 70)
    
    analyzer = CoinMarketCapAnalyzer()
    
    # Load the data
    btc_df, eth_df = analyzer.load_data()
    if btc_df is None or eth_df is None:
        print("❌ Failed to load data files")
        return
    
    # Process and align data
    combined_df = analyzer.process_and_align_data(btc_df, eth_df)
    if combined_df is None:
        print("❌ Failed to process data")
        return
    
    # Analyze trends
    stats = analyzer.analyze_market_trends(combined_df)
    
    # Create comprehensive chart
    analyzer.create_comprehensive_chart(combined_df, stats)
    
    print("\n✅ Analysis complete!")
    print("📈 This chart shows ETH/BTC market cap insights using real CoinMarketCap data from 2021-2025")
    print("🎯 Key insight: Purple dashed line shows ETH/BTC market cap ratio overlaid on absolute market caps")

if __name__ == "__main__":
    main() 