#!/usr/bin/env python3
"""
ETH/BTC Market Cap Analysis using Complete CoinMarketCap Historical Data
Uses both Ethereum files to get full coverage from May 2021 to July 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class CompleteCoinMarketCapAnalyzer:
    def __init__(self):
        self.btc_file = "Bitcoin_2021_7_1-2025_7_28_historical_data_coinmarketcap.csv"
        self.eth_file1 = "Ethereum_2021_5_12-2021_7_11_historical_data_coinmarketcap.csv"  # Earlier period
        self.eth_file2 = "Ethereum_2021_7_1-2025_7_28_historical_data_coinmarketcap.csv"   # Later period
        
    def load_and_combine_data(self):
        """
        Load and combine all CSV files to get complete coverage
        """
        print("📂 Loading Complete CoinMarketCap Historical Data...")
        
        try:
            # Load Bitcoin data
            btc_df = pd.read_csv(self.btc_file, delimiter=';')
            btc_df['timestamp'] = pd.to_datetime(btc_df['timestamp'].str.strip('"'))
            btc_df = btc_df.sort_values('timestamp')
            print(f"✅ Bitcoin data: {len(btc_df)} points from {btc_df['timestamp'].min()} to {btc_df['timestamp'].max()}")
            
            # Load Ethereum data from both files
            eth_df1 = pd.read_csv(self.eth_file1, delimiter=';')
            eth_df1['timestamp'] = pd.to_datetime(eth_df1['timestamp'].str.strip('"'))
            print(f"✅ Ethereum early data: {len(eth_df1)} points from {eth_df1['timestamp'].min()} to {eth_df1['timestamp'].max()}")
            
            eth_df2 = pd.read_csv(self.eth_file2, delimiter=';')
            eth_df2['timestamp'] = pd.to_datetime(eth_df2['timestamp'].str.strip('"'))
            print(f"✅ Ethereum later data: {len(eth_df2)} points from {eth_df2['timestamp'].min()} to {eth_df2['timestamp'].max()}")
            
            # Combine Ethereum datasets
            print("\n🔄 Combining Ethereum datasets...")
            
            # Remove any overlapping dates to avoid duplicates
            overlap_start = eth_df2['timestamp'].min()
            eth_df1_filtered = eth_df1[eth_df1['timestamp'] < overlap_start]
            
            print(f"📊 ETH early (filtered): {len(eth_df1_filtered)} points ending before {overlap_start}")
            print(f"📊 ETH later: {len(eth_df2)} points")
            
            # Combine Ethereum data
            eth_combined = pd.concat([eth_df1_filtered, eth_df2], ignore_index=True)
            eth_combined = eth_combined.sort_values('timestamp')
            
            print(f"✅ Combined Ethereum data: {len(eth_combined)} points from {eth_combined['timestamp'].min()} to {eth_combined['timestamp'].max()}")
            
            # Create month-end periods for alignment
            btc_df['month'] = btc_df['timestamp'].dt.to_period('M')
            eth_combined['month'] = eth_combined['timestamp'].dt.to_period('M')
            
            # Group by month and take the last (latest) entry per month
            print("\n🔄 Processing monthly data alignment...")
            btc_monthly = btc_df.groupby('month').last().reset_index()
            eth_monthly = eth_combined.groupby('month').last().reset_index()
            
            print(f"📊 BTC monthly data: {len(btc_monthly)} months")
            print(f"📊 ETH monthly data: {len(eth_monthly)} months")
            
            # Find common months for alignment
            btc_months = set(btc_monthly['month'])
            eth_months = set(eth_monthly['month'])
            common_months = btc_months.intersection(eth_months)
            
            print(f"📅 Common months found: {len(common_months)}")
            
            if len(common_months) == 0:
                print("❌ No common time periods found")
                return None
            
            # Filter to common months and sort
            btc_common = btc_monthly[btc_monthly['month'].isin(common_months)].copy()
            eth_common = eth_monthly[eth_monthly['month'].isin(common_months)].copy()
            
            btc_common = btc_common.sort_values('month')
            eth_common = eth_common.sort_values('month')
            
            # Create aligned dataset
            combined_df = pd.DataFrame({
                'month': btc_common['month'].values,
                'timestamp': btc_common['timestamp'].values,
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
            print(f"📅 Complete analysis period: {combined_df.index[0].strftime('%Y-%m-%d')} to {combined_df.index[-1].strftime('%Y-%m-%d')}")
            print(f"⏱️  Total coverage: {(combined_df.index[-1] - combined_df.index[0]).days / 365.25:.1f} years")
            
            return combined_df
            
        except Exception as e:
            print(f"❌ Error processing data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def analyze_complete_trends(self, df):
        """
        Analyze complete market cap trends from 2021-2025
        """
        print("\n📊 COMPLETE MARKET CAP ANALYSIS (2021-2025)")
        print("=" * 70)
        
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
        
        # Starting values (2021)
        start_eth_btc_ratio = df['eth_btc_market_cap_ratio'].iloc[0]
        start_btc_mc = df['btc_market_cap'].iloc[0]
        start_eth_mc = df['eth_market_cap'].iloc[0]
        
        print(f"💰 Current Market Data (Latest):")
        print(f"   BTC Market Cap: ${current_btc_mc/1e12:.2f}T")
        print(f"   ETH Market Cap: ${current_eth_mc/1e12:.2f}T")
        print(f"   BTC Price: ${df['btc_price'].iloc[-1]:,.0f}")
        print(f"   ETH Price: ${df['eth_price'].iloc[-1]:,.0f}")
        
        print(f"\n📈 Market Cap Ratios:")
        print(f"   Current ETH/BTC Ratio: {current_eth_btc_ratio:.4f}")
        print(f"   Starting (2021) Ratio: {start_eth_btc_ratio:.4f}")
        print(f"   Change since 2021: {((current_eth_btc_ratio/start_eth_btc_ratio)-1)*100:+.1f}%")
        
        print(f"\n🔄 Market Growth since 2021:")
        btc_growth = ((current_btc_mc / start_btc_mc) - 1) * 100
        eth_growth = ((current_eth_mc / start_eth_mc) - 1) * 100
        print(f"   BTC Market Cap: {btc_growth:+.1f}%")
        print(f"   ETH Market Cap: {eth_growth:+.1f}%")
        print(f"   Relative Performance: ETH {'outperformed' if eth_growth > btc_growth else 'underperformed'} by {abs(eth_growth - btc_growth):.1f}%")
        
        print(f"\n📊 Price vs Market Cap Analysis:")
        print(f"   ETH/BTC Price Ratio: {current_price_ratio:.6f}")
        print(f"   ETH/BTC Market Cap Ratio: {current_eth_btc_ratio:.4f}")
        
        ratio_difference = ((current_eth_btc_ratio / current_price_ratio) - 1) * 100
        if ratio_difference > 0:
            print(f"   💡 Market cap ratio is {ratio_difference:.1f}% HIGHER than price ratio")
            print(f"      → ETH has more circulating supply relative to BTC")
        else:
            print(f"   💡 Price ratio is {abs(ratio_difference):.1f}% HIGHER than market cap ratio")
            print(f"      → BTC has more circulating supply relative to ETH")
        
        print(f"\n📈 Historical Range Analysis:")
        print(f"   4-Year Average: {avg_ratio:.4f}")
        print(f"   Maximum: {max_ratio:.4f} on {max_date.strftime('%Y-%m-%d')}")
        print(f"   Minimum: {min_ratio:.4f} on {min_date.strftime('%Y-%m-%d')}")
        print(f"   Total Volatility: {max_ratio/min_ratio:.2f}x range")
        
        # Market cycle analysis
        ratio_percentile = (current_eth_btc_ratio - min_ratio) / (max_ratio - min_ratio) * 100
        
        if current_eth_btc_ratio > avg_ratio * 1.15:
            strength = "VERY STRONG 🔥🔥"
        elif current_eth_btc_ratio > avg_ratio * 1.05:
            strength = "STRONG 🔥"
        elif current_eth_btc_ratio < avg_ratio * 0.85:
            strength = "WEAK ❄️"
        elif current_eth_btc_ratio < avg_ratio * 0.95:
            strength = "SLIGHTLY WEAK ❄️"
        else:
            strength = "NEUTRAL ⚖️"
        
        print(f"\n🔄 Current Market Position:")
        print(f"   ETH is {strength} vs BTC")
        print(f"   Current ratio at {ratio_percentile:.1f}% of 4-year range")
        
        return {
            'current_ratio': current_eth_btc_ratio,
            'start_ratio': start_eth_btc_ratio,
            'avg_ratio': avg_ratio,
            'max_ratio': max_ratio,
            'min_ratio': min_ratio,
            'max_date': max_date,
            'min_date': min_date,
            'current_price_ratio': current_price_ratio,
            'ratio_difference': ratio_difference,
            'btc_growth': btc_growth,
            'eth_growth': eth_growth
        }
    
    def create_complete_chart(self, df, stats):
        """
        Create comprehensive chart showing the complete 2021-2025 analysis
        """
        print(f"\n📊 Creating complete 2021-2025 analysis chart...")
        
        # Create 3-panel chart as requested
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(24, 8))
        years_span = (df.index[-1] - df.index[0]).days / 365.25
        fig.suptitle(f'ETH vs BTC Complete Market Cap Analysis: {df.index[0].strftime("%Y-%m")} to {df.index[-1].strftime("%Y-%m")} ({years_span:.1f} Years, {len(df)} Months)', 
                     fontsize=16, fontweight='bold')
        
        # Chart 1: ETH/BTC Price Ratio
        ax1.plot(df.index, df['eth_btc_price_ratio'], 
                color='purple', linewidth=2.5, marker='o', markersize=3, alpha=0.8, label='ETH/BTC Price Ratio')
        ax1.set_title('ETH/BTC Price Ratio (2021-2025)', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price Ratio', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Add reference lines
        avg_price_ratio = df['eth_btc_price_ratio'].mean()
        ax1.axhline(y=avg_price_ratio, color='gray', linestyle=':', alpha=0.7)
        ax1.axhline(y=stats['current_price_ratio'], color='red', linestyle='--', alpha=0.7)
        ax1.text(0.02, 0.98, f'Current: {stats["current_price_ratio"]:.6f}', 
                transform=ax1.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        # Chart 2: BTC and ETH USD Prices
        ax2_twin = ax2.twinx()
        
        line1 = ax2.plot(df.index, df['btc_price'], 
                        color='orange', linewidth=2.5, marker='o', markersize=3, alpha=0.8, label='BTC Price (USD)')
        line2 = ax2_twin.plot(df.index, df['eth_price'], 
                             color='blue', linewidth=2.5, marker='s', markersize=3, alpha=0.8, label='ETH Price (USD)')
        
        ax2.set_title('BTC and ETH USD Prices (2021-2025)', fontsize=14, fontweight='bold')
        ax2.set_ylabel('BTC Price (USD)', fontsize=12, color='orange')
        ax2_twin.set_ylabel('ETH Price (USD)', fontsize=12, color='blue')
        ax2.tick_params(axis='y', labelcolor='orange')
        ax2_twin.tick_params(axis='y', labelcolor='blue')
        ax2.grid(True, alpha=0.3)
        
        # Combine legends
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Chart 3: Market Caps with ETH/BTC Ratio Overlay (MAIN REQUESTED CHART!)
        ax3_twin1 = ax3.twinx()
        ax3_twin2 = ax3.twinx()
        ax3_twin2.spines['right'].set_position(('outward', 60))
        
        # Market caps with filled areas
        line1 = ax3.plot(df.index, df['btc_market_cap'] / 1e12, 
                        color='orange', linewidth=3, marker='o', markersize=4, label='BTC Market Cap (T USD)')
        ax3.fill_between(df.index, 0, df['btc_market_cap'] / 1e12, color='orange', alpha=0.1)
        
        line2 = ax3_twin1.plot(df.index, df['eth_market_cap'] / 1e12,
                              color='blue', linewidth=3, marker='s', markersize=4, label='ETH Market Cap (T USD)')
        ax3_twin1.fill_between(df.index, 0, df['eth_market_cap'] / 1e12, color='blue', alpha=0.1)
        
        # ETH/BTC market cap ratio overlay (THE KEY INSIGHT!)
        line3 = ax3_twin2.plot(df.index, df['eth_btc_market_cap_ratio'],
                              color='purple', linewidth=4, alpha=0.9, linestyle='--', 
                              marker='D', markersize=5, label='ETH/BTC Market Cap Ratio')
        
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
        ax3_twin2.axhline(y=avg_ratio, color='gray', linestyle=':', alpha=0.8, linewidth=2)
        ax3_twin2.axhline(y=stats['current_ratio'], color='red', linestyle='-', alpha=0.8, linewidth=2)
        ax3_twin2.axhline(y=stats['start_ratio'], color='green', linestyle='-', alpha=0.6, linewidth=2)
        
        # Combine all legends
        lines = line1 + line2 + line3
        labels = [l.get_label() for l in lines]
        ax3.legend(lines, labels, loc='upper left')
        
        # Add comprehensive annotations
        ax3.text(0.02, 0.98, f"Current: {stats['current_ratio']:.4f}", 
                transform=ax3.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='plum', alpha=0.8))
        
        ax3.text(0.02, 0.85, f"4Y Average: {avg_ratio:.4f}", 
                transform=ax3.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        ax3.text(0.02, 0.72, f"2021 Start: {stats['start_ratio']:.4f}", 
                transform=ax3.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
        
        # Format x-axes
        for ax in [ax1, ax2, ax3]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Add comprehensive statistics
        stats_text = f"""Complete ETH/BTC Market Cap Analysis (2021-2025):

Data Sources: CoinMarketCap Historical Data
Period: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}
Coverage: {years_span:.1f} years, {len(df)} months

Current Market Caps:
  BTC: ${df['btc_market_cap'].iloc[-1]/1e12:.2f}T (Growth: {stats['btc_growth']:+.1f}%)
  ETH: ${df['eth_market_cap'].iloc[-1]/1e12:.2f}T (Growth: {stats['eth_growth']:+.1f}%)

ETH/BTC Market Cap Ratios:
  Current: {stats['current_ratio']:.4f}
  2021 Start: {stats['start_ratio']:.4f}
  4-Year Avg: {stats['avg_ratio']:.4f}
  Maximum: {stats['max_ratio']:.4f} ({stats['max_date'].strftime('%Y-%m')})
  Minimum: {stats['min_ratio']:.4f} ({stats['min_date'].strftime('%Y-%m')})

Price vs Market Cap:
  Price Ratio: {stats['current_price_ratio']:.6f}
  MC Ratio: {stats['current_ratio']:.4f}
  Supply Effect: {stats['ratio_difference']:+.1f}%

Key Insight: 
  {"ETH has more circulating supply" if stats['ratio_difference'] > 0 else "BTC has more circulating supply"}
  ETH {"outperformed" if stats['eth_growth'] > stats['btc_growth'] else "underperformed"} BTC by {abs(stats['eth_growth'] - stats['btc_growth']):.1f}%"""
        
        fig.text(0.02, 0.02, stats_text, fontsize=9, 
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8),
                verticalalignment='bottom')
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.88, bottom=0.35, right=0.85)
        
        # Save chart
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"eth_btc_complete_2021_2025_analysis_{timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"📊 Complete analysis chart saved as: {filename}")
        
        plt.show()

def main():
    """
    Main function to run the complete 2021-2025 analysis
    """
    print("🚀 COMPLETE ETH/BTC Market Cap Analysis (2021-2025)")
    print("=" * 70)
    print("📋 Using complete CoinMarketCap dataset:")
    print("   • Bitcoin: July 2021 - July 2025")
    print("   • Ethereum: May 2021 - July 2025 (combined datasets)")
    print()
    
    analyzer = CompleteCoinMarketCapAnalyzer()
    
    # Load and process the complete data
    combined_df = analyzer.load_and_combine_data()
    if combined_df is None or len(combined_df) == 0:
        print("❌ Failed to load or process data")
        return
    
    # Analyze complete trends
    stats = analyzer.analyze_complete_trends(combined_df)
    
    # Create comprehensive chart
    analyzer.create_complete_chart(combined_df, stats)
    
    print("\n✅ Complete 2021-2025 Analysis Finished!")
    print("🎯 Key Chart: Purple dashed line shows ETH/BTC market cap ratio from 2021-2025")
    print("💡 This reveals 4+ years of market cap evolution and relative performance")
    print("📊 The chart shows exactly what you requested: market caps with ETH/BTC ratio overlay")

if __name__ == "__main__":
    main() 