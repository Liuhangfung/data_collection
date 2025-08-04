#!/usr/bin/env python3
"""
ETH/BTC Market Cap Analysis using Available CoinMarketCap Data
Works with the actual files present in the directory
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class AvailableDataAnalyzer:
    def __init__(self):
        self.btc_file = "Bitcoin_2021_7_1-2025_7_28_historical_data_coinmarketcap.csv"
        self.eth_file = "Ethereum_2021_5_12-2021_7_11_historical_data_coinmarketcap.csv"
        
    def load_and_analyze_data(self):
        """
        Load and analyze the available data
        """
        print("📂 Loading Available CoinMarketCap Data...")
        
        try:
            # Load Bitcoin data
            btc_df = pd.read_csv(self.btc_file, delimiter=';')
            btc_df['timestamp'] = pd.to_datetime(btc_df['timestamp'].str.strip('"'))
            btc_df = btc_df.sort_values('timestamp')
            print(f"✅ Bitcoin data: {len(btc_df)} points from {btc_df['timestamp'].min()} to {btc_df['timestamp'].max()}")
            
            # Load Ethereum data
            eth_df = pd.read_csv(self.eth_file, delimiter=';')
            eth_df['timestamp'] = pd.to_datetime(eth_df['timestamp'].str.strip('"'))
            eth_df = eth_df.sort_values('timestamp')
            print(f"✅ Ethereum data: {len(eth_df)} points from {eth_df['timestamp'].min()} to {eth_df['timestamp'].max()}")
            
            # Check the data frequencies
            print(f"\n🔍 Data Analysis:")
            print(f"   Bitcoin frequency: {self.detect_frequency(btc_df)}")
            print(f"   Ethereum frequency: {self.detect_frequency(eth_df)}")
            
            # Since the datasets have different time ranges, let's analyze them separately
            # and then find overlapping periods
            
            # Process Bitcoin data
            btc_df.set_index('timestamp', inplace=True)
            btc_df['btc_price'] = btc_df['close']
            btc_df['btc_market_cap'] = btc_df['marketCap']
            
            # Process Ethereum data  
            eth_df.set_index('timestamp', inplace=True)
            eth_df['eth_price'] = eth_df['close']
            eth_df['eth_market_cap'] = eth_df['marketCap']
            
            # Find overlapping time period
            btc_start, btc_end = btc_df.index.min(), btc_df.index.max()
            eth_start, eth_end = eth_df.index.min(), eth_df.index.max()
            
            overlap_start = max(btc_start, eth_start)
            overlap_end = min(btc_end, eth_end)
            
            print(f"\n📅 Time Range Analysis:")
            print(f"   BTC Range: {btc_start.strftime('%Y-%m-%d')} to {btc_end.strftime('%Y-%m-%d')}")
            print(f"   ETH Range: {eth_start.strftime('%Y-%m-%d')} to {eth_end.strftime('%Y-%m-%d')}")
            print(f"   Overlap: {overlap_start.strftime('%Y-%m-%d') if overlap_start <= overlap_end else 'No overlap'} to {overlap_end.strftime('%Y-%m-%d') if overlap_start <= overlap_end else 'No overlap'}")
            
            if overlap_start <= overlap_end:
                # Create overlapping dataset
                btc_overlap = btc_df[(btc_df.index >= overlap_start) & (btc_df.index <= overlap_end)]
                eth_overlap = eth_df[(eth_df.index >= overlap_start) & (eth_df.index <= overlap_end)]
                
                # Resample to daily frequency and align
                btc_daily = btc_overlap.resample('D').last().dropna()
                eth_daily = eth_overlap.resample('D').last().dropna()
                
                # Find common dates
                common_dates = btc_daily.index.intersection(eth_daily.index)
                
                if len(common_dates) > 0:
                    combined_df = pd.DataFrame({
                        'btc_price': btc_daily.loc[common_dates, 'btc_price'],
                        'eth_price': eth_daily.loc[common_dates, 'eth_price'],
                        'btc_market_cap': btc_daily.loc[common_dates, 'btc_market_cap'],
                        'eth_market_cap': eth_daily.loc[common_dates, 'eth_market_cap']
                    })
                    
                    # Calculate ratios
                    combined_df['eth_btc_price_ratio'] = combined_df['eth_price'] / combined_df['btc_price']
                    combined_df['eth_btc_market_cap_ratio'] = combined_df['eth_market_cap'] / combined_df['btc_market_cap']
                    combined_df['btc_eth_market_cap_ratio'] = combined_df['btc_market_cap'] / combined_df['eth_market_cap']
                    
                    print(f"✅ Overlapping dataset: {len(combined_df)} days")
                    return combined_df, btc_df, eth_df
                else:
                    print("❌ No common dates found in overlap period")
            
            # If no overlap, return individual datasets for separate analysis
            print("📊 Analyzing datasets separately due to limited overlap")
            return None, btc_df, eth_df
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            import traceback
            traceback.print_exc()
            return None, None, None
    
    def detect_frequency(self, df):
        """Detect data frequency"""
        if len(df) < 2:
            return "Unknown"
        avg_days = (df['timestamp'].max() - df['timestamp'].min()).days / (len(df) - 1)
        if avg_days <= 1.5:
            return "Daily"
        elif avg_days <= 7.5:
            return "Weekly"  
        elif avg_days <= 35:
            return "Monthly"
        else:
            return "Other"
    
    def analyze_available_data(self, combined_df, btc_df, eth_df):
        """
        Analyze the available data
        """
        print("\n📊 AVAILABLE DATA ANALYSIS")
        print("=" * 60)
        
        if combined_df is not None and len(combined_df) > 0:
            print("🔄 Overlapping Period Analysis:")
            self.analyze_overlapping_period(combined_df)
        
        print("\n📈 Individual Dataset Analysis:")
        print(f"\n🟠 Bitcoin Analysis ({len(btc_df)} data points):")
        print(f"   Period: {btc_df.index[0].strftime('%Y-%m-%d')} to {btc_df.index[-1].strftime('%Y-%m-%d')}")
        print(f"   Price Range: ${btc_df['close'].min():,.0f} to ${btc_df['close'].max():,.0f}")
        print(f"   Market Cap Range: ${btc_df['marketCap'].min()/1e12:.2f}T to ${btc_df['marketCap'].max()/1e12:.2f}T")
        print(f"   Current: ${btc_df['close'].iloc[-1]:,.0f} (${btc_df['marketCap'].iloc[-1]/1e12:.2f}T)")
        
        print(f"\n🔵 Ethereum Analysis ({len(eth_df)} data points):")
        print(f"   Period: {eth_df.index[0].strftime('%Y-%m-%d')} to {eth_df.index[-1].strftime('%Y-%m-%d')}")
        print(f"   Price Range: ${eth_df['close'].min():,.0f} to ${eth_df['close'].max():,.0f}")
        print(f"   Market Cap Range: ${eth_df['marketCap'].min()/1e12:.2f}T to ${eth_df['marketCap'].max()/1e12:.2f}T")
        print(f"   Latest in dataset: ${eth_df['close'].iloc[-1]:,.0f} (${eth_df['marketCap'].iloc[-1]/1e12:.2f}T)")
        
        return btc_df, eth_df
    
    def analyze_overlapping_period(self, df):
        """
        Analyze the overlapping period data
        """
        current_eth_btc_ratio = df['eth_btc_market_cap_ratio'].iloc[-1]
        avg_ratio = df['eth_btc_market_cap_ratio'].mean()
        max_ratio = df['eth_btc_market_cap_ratio'].max()
        min_ratio = df['eth_btc_market_cap_ratio'].min()
        
        print(f"   Period: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
        print(f"   ETH/BTC Market Cap Ratio:")
        print(f"     Latest: {current_eth_btc_ratio:.4f}")
        print(f"     Average: {avg_ratio:.4f}")
        print(f"     Range: {min_ratio:.4f} to {max_ratio:.4f}")
    
    def create_available_data_chart(self, combined_df, btc_df, eth_df):
        """
        Create charts with available data
        """
        print(f"\n📊 Creating charts with available data...")
        
        if combined_df is not None and len(combined_df) > 5:
            # Create overlapping period chart
            self.create_overlapping_chart(combined_df)
        
        # Create individual timeline chart
        self.create_timeline_chart(btc_df, eth_df)
    
    def create_overlapping_chart(self, df):
        """
        Create chart for overlapping period
        """
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(24, 8))
        fig.suptitle(f'ETH vs BTC Analysis - Overlapping Period: {df.index[0].strftime("%Y-%m-%d")} to {df.index[-1].strftime("%Y-%m-%d")} ({len(df)} Days)', 
                     fontsize=16, fontweight='bold')
        
        # Chart 1: ETH/BTC Price Ratio
        ax1.plot(df.index, df['eth_btc_price_ratio'], 
                color='purple', linewidth=2, marker='o', markersize=3, label='ETH/BTC Price Ratio')
        ax1.set_title('ETH/BTC Price Ratio', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price Ratio', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Chart 2: BTC and ETH Prices
        ax2_twin = ax2.twinx()
        
        line1 = ax2.plot(df.index, df['btc_price'], 
                        color='orange', linewidth=2, marker='o', markersize=3, label='BTC Price (USD)')
        line2 = ax2_twin.plot(df.index, df['eth_price'], 
                             color='blue', linewidth=2, marker='s', markersize=3, label='ETH Price (USD)')
        
        ax2.set_title('BTC and ETH USD Prices', fontsize=14, fontweight='bold')
        ax2.set_ylabel('BTC Price (USD)', fontsize=12, color='orange')
        ax2_twin.set_ylabel('ETH Price (USD)', fontsize=12, color='blue')
        ax2.tick_params(axis='y', labelcolor='orange')
        ax2_twin.tick_params(axis='y', labelcolor='blue')
        ax2.grid(True, alpha=0.3)
        
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Chart 3: Market Caps with ETH/BTC Ratio Overlay
        ax3_twin1 = ax3.twinx()
        ax3_twin2 = ax3.twinx()
        ax3_twin2.spines['right'].set_position(('outward', 60))
        
        line1 = ax3.plot(df.index, df['btc_market_cap'] / 1e12, 
                        color='orange', linewidth=2.5, marker='o', markersize=4, label='BTC Market Cap (T USD)')
        line2 = ax3_twin1.plot(df.index, df['eth_market_cap'] / 1e12,
                              color='blue', linewidth=2.5, marker='s', markersize=4, label='ETH Market Cap (T USD)')
        line3 = ax3_twin2.plot(df.index, df['eth_btc_market_cap_ratio'],
                              color='purple', linewidth=3, alpha=0.9, linestyle='--', 
                              marker='D', markersize=5, label='ETH/BTC Market Cap Ratio')
        
        ax3.set_title('Market Caps with ETH/BTC Ratio Overlay', fontsize=14, fontweight='bold')
        ax3.set_ylabel('BTC Market Cap (T USD)', fontsize=12, color='orange')
        ax3_twin1.set_ylabel('ETH Market Cap (T USD)', fontsize=12, color='blue')
        ax3_twin2.set_ylabel('ETH/BTC Ratio', fontsize=12, color='purple')
        
        ax3.tick_params(axis='y', labelcolor='orange')
        ax3_twin1.tick_params(axis='y', labelcolor='blue')
        ax3_twin2.tick_params(axis='y', labelcolor='purple')
        ax3.grid(True, alpha=0.3)
        
        lines = line1 + line2 + line3
        labels = [l.get_label() for l in lines]
        ax3.legend(lines, labels, loc='upper left')
        
        # Format x-axes
        for ax in [ax1, ax2, ax3]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(df)//10)))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.90, bottom=0.15)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"eth_btc_overlapping_analysis_{timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"📊 Overlapping period chart saved as: {filename}")
        plt.show()
    
    def create_timeline_chart(self, btc_df, eth_df):
        """
        Create timeline chart showing both datasets
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 12))
        fig.suptitle('Complete Timeline: Bitcoin vs Ethereum Market Caps', fontsize=16, fontweight='bold')
        
        # Chart 1: Market Cap Timeline
        ax1.plot(btc_df.index, btc_df['marketCap'] / 1e12, 
                color='orange', linewidth=3, marker='o', markersize=4, label=f'BTC Market Cap ({len(btc_df)} points)')
        ax1.plot(eth_df.index, eth_df['marketCap'] / 1e12,
                color='blue', linewidth=3, marker='s', markersize=3, label=f'ETH Market Cap ({len(eth_df)} points)')
        
        ax1.set_title('Market Capitalizations Over Time', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Market Cap (Trillion USD)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Chart 2: Price Timeline
        ax2_twin = ax2.twinx()
        
        line1 = ax2.plot(btc_df.index, btc_df['close'], 
                        color='orange', linewidth=3, marker='o', markersize=4, label='BTC Price (USD)')
        line2 = ax2_twin.plot(eth_df.index, eth_df['close'],
                             color='blue', linewidth=3, marker='s', markersize=3, label='ETH Price (USD)')
        
        ax2.set_title('Price Movements Over Time', fontsize=14, fontweight='bold')
        ax2.set_ylabel('BTC Price (USD)', fontsize=12, color='orange')
        ax2_twin.set_ylabel('ETH Price (USD)', fontsize=12, color='blue')
        ax2.tick_params(axis='y', labelcolor='orange')
        ax2_twin.tick_params(axis='y', labelcolor='blue')
        ax2.grid(True, alpha=0.3)
        
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Format x-axes
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Add summary text
        summary_text = f"""Data Summary:
        
Bitcoin Dataset: {len(btc_df)} points
  Period: {btc_df.index[0].strftime('%Y-%m-%d')} to {btc_df.index[-1].strftime('%Y-%m-%d')}
  Latest Price: ${btc_df['close'].iloc[-1]:,.0f}
  Latest Market Cap: ${btc_df['marketCap'].iloc[-1]/1e12:.2f}T
  
Ethereum Dataset: {len(eth_df)} points  
  Period: {eth_df.index[0].strftime('%Y-%m-%d')} to {eth_df.index[-1].strftime('%Y-%m-%d')}
  Latest Price: ${eth_df['close'].iloc[-1]:,.0f}
  Latest Market Cap: ${eth_df['marketCap'].iloc[-1]/1e12:.2f}T
  
Note: Limited overlap period available for direct comparison"""
        
        fig.text(0.02, 0.02, summary_text, fontsize=10, 
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8),
                verticalalignment='bottom')
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.93, bottom=0.25)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bitcoin_ethereum_timeline_{timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"📊 Timeline chart saved as: {filename}")
        plt.show()

def main():
    """
    Main function
    """
    print("🚀 ETH/BTC Analysis with Available CoinMarketCap Data")
    print("=" * 60)
    
    analyzer = AvailableDataAnalyzer()
    
    # Load and analyze data
    combined_df, btc_df, eth_df = analyzer.load_and_analyze_data()
    
    if btc_df is None and eth_df is None:
        print("❌ No data could be loaded")
        return
    
    # Analyze available data
    analyzer.analyze_available_data(combined_df, btc_df, eth_df)
    
    # Create charts
    analyzer.create_available_data_chart(combined_df, btc_df, eth_df)
    
    print("\n✅ Analysis complete with available data!")
    print("💡 Charts show both individual timelines and any overlapping periods")

if __name__ == "__main__":
    main() 