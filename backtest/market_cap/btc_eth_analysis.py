#!/usr/bin/env python3
"""
ETH/BTC Market Cap Analysis using BTC.csv and ETH.csv
Creates the exact chart requested: Market caps with ETH/BTC ratio overlay
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class BTCETHAnalyzer:
    def __init__(self):
        self.btc_file = "BTC.csv"
        self.eth_file = "ETH.csv"
        
    def load_and_process_data(self):
        """
        Load and process both BTC and ETH CSV files
        """
        print("📂 Loading BTC.csv and ETH.csv files...")
        
        try:
            # Load Bitcoin data
            btc_df = pd.read_csv(self.btc_file, delimiter=';')
            btc_df['timestamp'] = pd.to_datetime(btc_df['timestamp'].str.strip('"'))
            btc_df = btc_df.sort_values('timestamp')
            print(f"✅ BTC data: {len(btc_df)} points from {btc_df['timestamp'].min()} to {btc_df['timestamp'].max()}")
            
            # Load Ethereum data
            eth_df = pd.read_csv(self.eth_file, delimiter=';')
            eth_df['timestamp'] = pd.to_datetime(eth_df['timestamp'].str.strip('"'))
            eth_df = eth_df.sort_values('timestamp')
            print(f"✅ ETH data: {len(eth_df)} points from {eth_df['timestamp'].min()} to {eth_df['timestamp'].max()}")
            
            # Check data alignment - both should be weekly data
            print(f"\n🔍 Data Analysis:")
            print(f"   BTC frequency: {self.detect_frequency(btc_df)}")
            print(f"   ETH frequency: {self.detect_frequency(eth_df)}")
            
            # Set timestamp as index for both
            btc_df.set_index('timestamp', inplace=True)
            eth_df.set_index('timestamp', inplace=True)
            
            # Since both are weekly data, find common timestamps
            common_timestamps = btc_df.index.intersection(eth_df.index)
            print(f"📅 Common timestamps: {len(common_timestamps)}")
            
            if len(common_timestamps) > 0:
                # Direct alignment using common timestamps
                btc_aligned = btc_df.loc[common_timestamps]
                eth_aligned = eth_df.loc[common_timestamps]
                
                combined_df = pd.DataFrame({
                    'btc_price': btc_aligned['close'],
                    'eth_price': eth_aligned['close'],
                    'btc_market_cap': btc_aligned['marketCap'],
                    'eth_market_cap': eth_aligned['marketCap'],
                    'btc_volume': btc_aligned['volume'],
                    'eth_volume': eth_aligned['volume']
                }, index=common_timestamps)
            else:
                print("❌ No exact timestamp matches. Using all available data with interpolation...")
                
                # If no exact matches, create a combined timeline with all unique timestamps
                all_timestamps = btc_df.index.union(eth_df.index).sort_values()
                
                # Reindex both dataframes to all timestamps and forward fill
                btc_reindexed = btc_df.reindex(all_timestamps).fillna(method='ffill')
                eth_reindexed = eth_df.reindex(all_timestamps).fillna(method='ffill')
                
                # Remove rows where either BTC or ETH data is missing
                valid_mask = btc_reindexed['close'].notna() & eth_reindexed['close'].notna()
                valid_timestamps = all_timestamps[valid_mask]
                
                combined_df = pd.DataFrame({
                    'btc_price': btc_reindexed.loc[valid_timestamps, 'close'],
                    'eth_price': eth_reindexed.loc[valid_timestamps, 'close'],
                    'btc_market_cap': btc_reindexed.loc[valid_timestamps, 'marketCap'],
                    'eth_market_cap': eth_reindexed.loc[valid_timestamps, 'marketCap'],
                    'btc_volume': btc_reindexed.loc[valid_timestamps, 'volume'],
                    'eth_volume': eth_reindexed.loc[valid_timestamps, 'volume']
                }, index=valid_timestamps)
            
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
    
    def analyze_market_data(self, df):
        """
        Analyze the market cap trends and ratios
        """
        print("\n📊 ETH/BTC MARKET CAP ANALYSIS")
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
        
        # Starting values
        start_eth_btc_ratio = df['eth_btc_market_cap_ratio'].iloc[0]
        start_btc_mc = df['btc_market_cap'].iloc[0]
        start_eth_mc = df['eth_market_cap'].iloc[0]
        
        print(f"💰 Current Market Data:")
        print(f"   BTC Market Cap: ${current_btc_mc/1e12:.2f}T")
        print(f"   ETH Market Cap: ${current_eth_mc/1e12:.2f}T")
        print(f"   BTC Price: ${df['btc_price'].iloc[-1]:,.0f}")
        print(f"   ETH Price: ${df['eth_price'].iloc[-1]:,.0f}")
        
        print(f"\n📈 Market Cap Ratios:")
        print(f"   Current ETH/BTC Ratio: {current_eth_btc_ratio:.4f} ({current_eth_btc_ratio*100:.1f}%)")
        print(f"   Current BTC/ETH Ratio: {1/current_eth_btc_ratio:.2f}")
        print(f"   Starting Ratio: {start_eth_btc_ratio:.4f}")
        print(f"   Change: {((current_eth_btc_ratio/start_eth_btc_ratio)-1)*100:+.1f}%")
        
        print(f"\n🔄 Market Growth (Period):")
        btc_growth = ((current_btc_mc / start_btc_mc) - 1) * 100
        eth_growth = ((current_eth_mc / start_eth_mc) - 1) * 100
        print(f"   BTC Market Cap: {btc_growth:+.1f}%")
        print(f"   ETH Market Cap: {eth_growth:+.1f}%")
        
        if eth_growth > btc_growth:
            print(f"   📈 ETH outperformed BTC by {eth_growth - btc_growth:.1f}%")
        else:
            print(f"   📉 BTC outperformed ETH by {btc_growth - eth_growth:.1f}%")
        
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
        
        print(f"\n📈 Historical Range:")
        print(f"   Average: {avg_ratio:.4f}")
        print(f"   Maximum: {max_ratio:.4f} on {max_date.strftime('%Y-%m-%d')}")
        print(f"   Minimum: {min_ratio:.4f} on {min_date.strftime('%Y-%m-%d')}")
        print(f"   Volatility Range: {max_ratio/min_ratio:.2f}x")
        
        # Current position
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
    
    def create_comprehensive_chart(self, df, stats):
        """
        Create the comprehensive chart: Market caps with ETH/BTC ratio overlay
        """
        print(f"\n📊 Creating comprehensive ETH/BTC market cap analysis chart...")
        
        # Create 3-panel chart as requested
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(24, 8))
        period_years = (df.index[-1] - df.index[0]).days / 365.25
        fig.suptitle(f'ETH vs BTC Market Cap Analysis: {df.index[0].strftime("%Y-%m-%d")} to {df.index[-1].strftime("%Y-%m-%d")} ({period_years:.1f} Years, {len(df)} Weekly Data Points)', 
                     fontsize=16, fontweight='bold')
        
        # Chart 1: ETH/BTC Price Ratio
        ax1.plot(df.index, df['eth_btc_price_ratio'], 
                color='purple', linewidth=2.5, label='ETH/BTC Price Ratio')
        ax1.set_title('ETH/BTC Price Ratio', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price Ratio', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Add reference lines
        avg_price_ratio = df['eth_btc_price_ratio'].mean()
        ax1.axhline(y=avg_price_ratio, color='gray', linestyle=':', alpha=0.7, label=f'Avg: {avg_price_ratio:.6f}')
        ax1.axhline(y=stats['current_price_ratio'], color='red', linestyle='--', alpha=0.7)
        ax1.text(0.02, 0.98, f'Current: {stats["current_price_ratio"]:.6f}', 
                transform=ax1.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        # Chart 2: BTC and ETH USD Prices
        ax2_twin = ax2.twinx()
        
        line1 = ax2.plot(df.index, df['btc_price'], 
                        color='orange', linewidth=2.5, label='BTC Price (USD)')
        line2 = ax2_twin.plot(df.index, df['eth_price'], 
                             color='blue', linewidth=2.5, label='ETH Price (USD)')
        
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
        
        # Chart 3: Market Caps with ETH/BTC Ratio Overlay (MAIN REQUESTED CHART!)
        ax3_twin1 = ax3.twinx()
        ax3_twin2 = ax3.twinx()
        ax3_twin2.spines['right'].set_position(('outward', 60))
        
        # Market caps with clean lines
        line1 = ax3.plot(df.index, df['btc_market_cap'] / 1e12, 
                        color='orange', linewidth=3, label='BTC Market Cap (T USD)')
        ax3.fill_between(df.index, 0, df['btc_market_cap'] / 1e12, color='orange', alpha=0.1)
        
        line2 = ax3_twin1.plot(df.index, df['eth_market_cap'] / 1e12,
                              color='blue', linewidth=3, label='ETH Market Cap (T USD)')
        ax3_twin1.fill_between(df.index, 0, df['eth_market_cap'] / 1e12, color='blue', alpha=0.1)
        
        # ETH/BTC market cap ratio overlay (THE KEY INSIGHT!)
        line3 = ax3_twin2.plot(df.index, df['eth_btc_market_cap_ratio'],
                              color='purple', linewidth=4, linestyle='--', 
                              label='ETH/BTC Market Cap Ratio')
        
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
        ax3_twin2.axhline(y=stats['start_ratio'], color='green', linestyle='-', alpha=0.6, linewidth=2)
        
        # Combine all legends
        lines = line1 + line2 + line3
        labels = [l.get_label() for l in lines]
        ax3.legend(lines, labels, loc='upper left')
        
        # Add comprehensive annotations
        ax3.text(0.02, 0.98, f"Current: {stats['current_ratio']:.4f}", 
                transform=ax3.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='plum', alpha=0.8))
        
        ax3.text(0.02, 0.85, f"Average: {avg_ratio:.4f}", 
                transform=ax3.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        ax3.text(0.02, 0.72, f"Start: {stats['start_ratio']:.4f}", 
                transform=ax3.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
        
        # Format x-axes for 4+ years of weekly data
        for ax in [ax1, ax2, ax3]:
            if len(df) > 100:  # For 4+ years of weekly data
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))  # Every 6 months
            elif len(df) > 20:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))  # Every 3 months
            else:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Add comprehensive statistics
        stats_text = f"""ETH/BTC Market Cap Analysis (Weekly Data):

Data Period: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}
Coverage: {period_years:.1f} years ({len(df)} weekly data points)

Current Market Caps:
  BTC: ${df['btc_market_cap'].iloc[-1]/1e12:.2f}T (Growth: {stats['btc_growth']:+.1f}%)
  ETH: ${df['eth_market_cap'].iloc[-1]/1e12:.2f}T (Growth: {stats['eth_growth']:+.1f}%)

ETH/BTC Market Cap Ratios:
  Current: {stats['current_ratio']:.4f} ({stats['current_ratio']*100:.1f}%)
  Start: {stats['start_ratio']:.4f}
  Average: {stats['avg_ratio']:.4f}
  Maximum: {stats['max_ratio']:.4f} ({stats['max_date'].strftime('%Y-%m-%d')})
  Minimum: {stats['min_ratio']:.4f} ({stats['min_date'].strftime('%Y-%m-%d')})

Price vs Market Cap:
  Price Ratio: {stats['current_price_ratio']:.6f}
  MC Ratio: {stats['current_ratio']:.4f}
  Supply Effect: {stats['ratio_difference']:+.1f}%

Key Insight: 
  {"ETH has more circulating supply" if stats['ratio_difference'] > 0 else "BTC has more circulating supply"}
  {"ETH outperformed BTC" if stats['eth_growth'] > stats['btc_growth'] else "BTC outperformed ETH"} by {abs(stats['eth_growth'] - stats['btc_growth']):.1f}%"""
        
        fig.text(0.02, 0.02, stats_text, fontsize=9, 
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8),
                verticalalignment='bottom')
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.88, bottom=0.35, right=0.85)
        
        # Save chart
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"eth_btc_market_cap_final_analysis_{timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"📊 Final analysis chart saved as: {filename}")
        
        plt.show()

def main():
    """
    Main function to run the BTC/ETH analysis
    """
    print("🚀 ETH/BTC Market Cap Analysis using BTC.csv and ETH.csv")
    print("=" * 60)
    
    analyzer = BTCETHAnalyzer()
    
    # Load and process the data
    combined_df = analyzer.load_and_process_data()
    if combined_df is None or len(combined_df) == 0:
        print("❌ Failed to load or process data")
        return
    
    # Analyze market trends
    stats = analyzer.analyze_market_data(combined_df)
    
    # Create the comprehensive chart
    analyzer.create_comprehensive_chart(combined_df, stats)
    
    print("\n✅ ETH/BTC Market Cap Analysis Complete!")
    print("🎯 Key Chart: Purple dashed line shows ETH/BTC market cap ratio overlaid on market caps")
    print("💡 This reveals exactly what you requested: market cap relationship insights")

if __name__ == "__main__":
    main() 