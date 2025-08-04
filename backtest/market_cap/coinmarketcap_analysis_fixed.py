#!/usr/bin/env python3
"""
ETH/BTC Market Cap Analysis using CoinMarketCap Historical Data (2024-2025)
Fixed version that properly handles data alignment
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class CoinMarketCapAnalyzerFixed:
    def __init__(self):
        self.btc_file = "Bitcoin_2021_7_1-2025_7_28_historical_data_coinmarketcap.csv"
        self.eth_file = "Ethereum_2021_7_1-2025_7_28_historical_data_coinmarketcap.csv"
        
    def load_and_process_data(self):
        """
        Load and process CoinMarketCap CSV data with proper alignment
        """
        print("📂 Loading CoinMarketCap historical data...")
        
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
            
            # Create month-end periods for alignment
            btc_df['month'] = btc_df['timestamp'].dt.to_period('M')
            eth_df['month'] = eth_df['timestamp'].dt.to_period('M')
            
            # Group by month and take the last (latest) entry per month
            print("\n🔄 Processing monthly data...")
            btc_monthly = btc_df.groupby('month').last().reset_index()
            eth_monthly = eth_df.groupby('month').last().reset_index()
            
            print(f"📊 BTC monthly data: {len(btc_monthly)} months")
            print(f"📊 ETH monthly data: {len(eth_monthly)} months")
            
            # Find common months
            btc_months = set(btc_monthly['month'])
            eth_months = set(eth_monthly['month'])
            common_months = btc_months.intersection(eth_months)
            
            print(f"📅 Common months: {len(common_months)}")
            
            if len(common_months) == 0:
                print("❌ No common time periods found")
                return None
            
            # Filter to common months
            btc_common = btc_monthly[btc_monthly['month'].isin(common_months)].copy()
            eth_common = eth_monthly[eth_monthly['month'].isin(common_months)].copy()
            
            # Sort by month
            btc_common = btc_common.sort_values('month')
            eth_common = eth_common.sort_values('month')
            
            # Create aligned dataset
            combined_df = pd.DataFrame({
                'month': btc_common['month'].values,
                'timestamp': btc_common['timestamp'].values,  # Use BTC timestamps as reference
                'btc_price': btc_common['close'].values,
                'eth_price': eth_common['close'].values,
                'btc_market_cap': btc_common['marketCap'].values,
                'eth_market_cap': eth_common['marketCap'].values,
                'btc_volume': btc_common['volume'].values,
                'eth_volume': eth_common['volume'].values
            })
            
            # Set timestamp as index
            combined_df.set_index('timestamp', inplace=True)
            
            # Calculate ratios
            combined_df['eth_btc_price_ratio'] = combined_df['eth_price'] / combined_df['btc_price']
            combined_df['eth_btc_market_cap_ratio'] = combined_df['eth_market_cap'] / combined_df['btc_market_cap']
            combined_df['btc_eth_market_cap_ratio'] = combined_df['btc_market_cap'] / combined_df['eth_market_cap']
            
            print(f"✅ Final aligned dataset: {len(combined_df)} data points")
            print(f"📅 Analysis period: {combined_df.index[0].strftime('%Y-%m-%d')} to {combined_df.index[-1].strftime('%Y-%m-%d')}")
            
            return combined_df
            
        except Exception as e:
            print(f"❌ Error processing data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def analyze_market_trends(self, df):
        """
        Analyze market cap trends and key statistics
        """
        print("\n📊 MARKET CAP ANALYSIS")
        print("=" * 60)
        
        # Current values
        current_eth_btc_ratio = df['eth_btc_market_cap_ratio'].iloc[-1]
        current_btc_mc = df['btc_market_cap'].iloc[-1]
        current_eth_mc = df['eth_market_cap'].iloc[-1]
        current_price_ratio = df['eth_btc_price_ratio'].iloc[-1]
        
        # Historical statistics
        max_ratio = df['eth_btc_market_cap_ratio'].max()
        min_ratio = df['eth_btc_market_cap_ratio'].min()
        avg_ratio = df['eth_btc_market_cap_ratio'].mean()
        
        max_date = df['eth_btc_market_cap_ratio'].idxmax()
        min_date = df['eth_btc_market_cap_ratio'].idxmin()
        
        print(f"💰 Current Market Data:")
        print(f"   BTC Market Cap: ${current_btc_mc/1e12:.2f}T")
        print(f"   ETH Market Cap: ${current_eth_mc/1e12:.2f}T")
        print(f"   BTC Price: ${df['btc_price'].iloc[-1]:,.0f}")
        print(f"   ETH Price: ${df['eth_price'].iloc[-1]:,.0f}")
        
        print(f"\n📈 Market Cap Ratios:")
        print(f"   ETH/BTC Ratio: {current_eth_btc_ratio:.4f}")
        print(f"   BTC/ETH Ratio: {1/current_eth_btc_ratio:.2f}")
        
        print(f"\n📊 Price vs Market Cap Comparison:")
        print(f"   ETH/BTC Price Ratio: {current_price_ratio:.6f}")
        print(f"   ETH/BTC Market Cap Ratio: {current_eth_btc_ratio:.4f}")
        
        ratio_difference = ((current_eth_btc_ratio / current_price_ratio) - 1) * 100
        if ratio_difference > 0:
            print(f"   💡 Market cap ratio is {ratio_difference:.1f}% HIGHER than price ratio")
            print(f"      → ETH has more circulating supply relative to BTC")
        else:
            print(f"   💡 Price ratio is {abs(ratio_difference):.1f}% HIGHER than market cap ratio")
            print(f"      → BTC has more circulating supply relative to ETH")
        
        print(f"\n📈 Historical Analysis ({df.index[0].strftime('%Y-%m')} to {df.index[-1].strftime('%Y-%m')}):")
        print(f"   Average ETH/BTC Ratio: {avg_ratio:.4f}")
        print(f"   Maximum: {max_ratio:.4f} on {max_date.strftime('%Y-%m-%d')}")
        print(f"   Minimum: {min_ratio:.4f} on {min_date.strftime('%Y-%m-%d')}")
        print(f"   Volatility Range: {max_ratio/min_ratio:.2f}x")
        
        # Market position
        ratio_percentile = (current_eth_btc_ratio - min_ratio) / (max_ratio - min_ratio) * 100
        
        if current_eth_btc_ratio > avg_ratio * 1.1:
            strength = "STRONG 🔥"
        elif current_eth_btc_ratio < avg_ratio * 0.9:
            strength = "WEAK ❄️"
        else:
            strength = "NEUTRAL ⚖️"
        
        print(f"\n🔄 Market Position:")
        print(f"   ETH is {strength} vs BTC")
        print(f"   Current ratio at {ratio_percentile:.1f}% of historical range")
        
        return {
            'current_ratio': current_eth_btc_ratio,
            'avg_ratio': avg_ratio,
            'max_ratio': max_ratio,
            'min_ratio': min_ratio,
            'max_date': max_date,
            'min_date': min_date,
            'current_price_ratio': current_price_ratio,
            'ratio_difference': ratio_difference
        }
    
    def create_comprehensive_chart(self, df, stats):
        """
        Create the comprehensive chart with market caps and ETH/BTC ratio overlay
        """
        print(f"\n📊 Creating comprehensive analysis chart...")
        
        # Create 3-panel chart as requested
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(24, 8))
        fig.suptitle(f'ETH vs BTC Market Cap Analysis: {df.index[0].strftime("%Y-%m")} to {df.index[-1].strftime("%Y-%m")} ({len(df)} Months)', 
                     fontsize=16, fontweight='bold')
        
        # Chart 1: ETH/BTC Price Ratio
        ax1.plot(df.index, df['eth_btc_price_ratio'], 
                color='purple', linewidth=2.5, marker='o', markersize=4, label='ETH/BTC Price Ratio')
        ax1.set_title('ETH/BTC Price Ratio', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price Ratio', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Add current ratio line
        current_price_ratio = stats['current_price_ratio']
        ax1.axhline(y=current_price_ratio, color='red', linestyle='--', alpha=0.7)
        ax1.text(0.02, 0.98, f'Current: {current_price_ratio:.6f}', 
                transform=ax1.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        # Chart 2: BTC and ETH USD Prices
        ax2_twin = ax2.twinx()
        
        line1 = ax2.plot(df.index, df['btc_price'], 
                        color='orange', linewidth=2.5, marker='o', markersize=4, label='BTC Price (USD)')
        line2 = ax2_twin.plot(df.index, df['eth_price'], 
                             color='blue', linewidth=2.5, marker='s', markersize=4, label='ETH Price (USD)')
        
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
        
        # Chart 3: Market Caps with ETH/BTC Ratio Overlay (THE KEY REQUESTED CHART!)
        ax3_twin1 = ax3.twinx()
        ax3_twin2 = ax3.twinx()
        ax3_twin2.spines['right'].set_position(('outward', 60))
        
        # Market caps
        line1 = ax3.plot(df.index, df['btc_market_cap'] / 1e12, 
                        color='orange', linewidth=3, marker='o', markersize=5, label='BTC Market Cap (T USD)')
        line2 = ax3_twin1.plot(df.index, df['eth_market_cap'] / 1e12,
                              color='blue', linewidth=3, marker='s', markersize=5, label='ETH Market Cap (T USD)')
        
        # ETH/BTC market cap ratio overlay (THE MAIN INSIGHT!)
        line3 = ax3_twin2.plot(df.index, df['eth_btc_market_cap_ratio'],
                              color='purple', linewidth=4, alpha=0.9, linestyle='--', 
                              marker='D', markersize=6, label='ETH/BTC Market Cap Ratio')
        
        ax3.set_title('Market Caps with ETH/BTC Ratio Overlay', fontsize=14, fontweight='bold')
        ax3.set_ylabel('BTC Market Cap (T USD)', fontsize=12, color='orange')
        ax3_twin1.set_ylabel('ETH Market Cap (T USD)', fontsize=12, color='blue')
        ax3_twin2.set_ylabel('ETH/BTC Ratio', fontsize=12, color='purple')
        
        ax3.tick_params(axis='y', labelcolor='orange')
        ax3_twin1.tick_params(axis='y', labelcolor='blue')
        ax3_twin2.tick_params(axis='y', labelcolor='purple')
        ax3.grid(True, alpha=0.3)
        
        # Add ratio reference lines
        avg_ratio = stats['avg_ratio']
        ax3_twin2.axhline(y=avg_ratio, color='gray', linestyle=':', alpha=0.8, linewidth=2)
        ax3_twin2.axhline(y=stats['current_ratio'], color='red', linestyle='-', alpha=0.8, linewidth=2)
        
        # Combine all legends
        lines = line1 + line2 + line3
        labels = [l.get_label() for l in lines]
        ax3.legend(lines, labels, loc='upper left')
        
        # Add key insight annotations
        ax3.text(0.02, 0.98, f"Current ETH/BTC Ratio: {stats['current_ratio']:.4f}", 
                transform=ax3.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='plum', alpha=0.8))
        
        ax3.text(0.02, 0.85, f"Period Average: {avg_ratio:.4f}", 
                transform=ax3.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        # Format x-axes
        for ax in [ax1, ax2, ax3]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Add comprehensive statistics
        stats_text = f"""ETH/BTC Market Cap Analysis:

Data Source: CoinMarketCap Historical Data
Period: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}
Data Points: {len(df)} months

Current Values:
  BTC Market Cap: ${df['btc_market_cap'].iloc[-1]/1e12:.2f}T
  ETH Market Cap: ${df['eth_market_cap'].iloc[-1]/1e12:.2f}T
  BTC Price: ${df['btc_price'].iloc[-1]:,.0f}
  ETH Price: ${df['eth_price'].iloc[-1]:,.0f}

Ratios:
  ETH/BTC Market Cap: {stats['current_ratio']:.4f}
  ETH/BTC Price: {stats['current_price_ratio']:.6f}
  
Historical Stats:
  Average Ratio: {stats['avg_ratio']:.4f}
  Maximum: {stats['max_ratio']:.4f} ({stats['max_date'].strftime('%Y-%m')})
  Minimum: {stats['min_ratio']:.4f} ({stats['min_date'].strftime('%Y-%m')})
  
Key Insight:
  Market cap ratio is {stats['ratio_difference']:+.1f}% vs price ratio
  → {"ETH has more supply" if stats['ratio_difference'] > 0 else "BTC has more supply"}"""
        
        fig.text(0.02, 0.02, stats_text, fontsize=9, 
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8),
                verticalalignment='bottom')
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.88, bottom=0.30, right=0.85)
        
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
    print("🚀 ETH/BTC Market Cap Analysis using CoinMarketCap Data")
    print("=" * 60)
    
    analyzer = CoinMarketCapAnalyzerFixed()
    
    # Load and process the data
    combined_df = analyzer.load_and_process_data()
    if combined_df is None or len(combined_df) == 0:
        print("❌ Failed to load or process data")
        return
    
    # Analyze trends
    stats = analyzer.analyze_market_trends(combined_df)
    
    # Create comprehensive chart
    analyzer.create_comprehensive_chart(combined_df, stats)
    
    print("\n✅ Analysis complete!")
    print("🎯 Key Chart: Purple dashed line shows ETH/BTC market cap ratio overlaid on absolute market caps")
    print("💡 This reveals insights about relative market size vs individual asset performance")

if __name__ == "__main__":
    main() 