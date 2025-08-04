#!/usr/bin/env python3
"""
ARB/BTC All-Time Chart Generator
Creates comprehensive charts showing the ARB/BTC ratio over time with yearly ATH/ATL points
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import ccxt
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class ARBBTCChartGenerator:
    """Generate all-time ARB/BTC ratio charts"""
    
    def __init__(self):
        self.exchange = ccxt.binance({
            'rateLimit': 1200,
            'enableRateLimit': True,
        })
        
    def fetch_historical_data(self, symbol, timeframe='1d', years_back=3):
        """
        Fetch historical data for a given symbol
        
        Args:
            symbol: Trading pair (e.g., 'ARB/USDT', 'BTC/USDT')
            timeframe: Timeframe ('1d', '1w', '1M')
            years_back: How many years back to fetch data
        """
        print(f"📊 Fetching {years_back} years of {symbol} data ({timeframe})...")
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=365 * years_back)
        
        try:
            all_ohlcv = []
            current_since = int(start_time.timestamp() * 1000)
            chunk_count = 0
            
            while current_since < int(end_time.timestamp() * 1000):
                try:
                    # Fetch data in chunks
                    ohlcv = self.exchange.fetch_ohlcv(
                        symbol, 
                        timeframe, 
                        current_since, 
                        1000
                    )
                    
                    if not ohlcv or len(ohlcv) == 0:
                        break
                    
                    all_ohlcv.extend(ohlcv)
                    chunk_count += 1
                    
                    # Update since timestamp
                    last_timestamp = max(candle[0] for candle in ohlcv)
                    
                    # Calculate period in milliseconds
                    if timeframe == '1d':
                        period_ms = 24 * 60 * 60 * 1000
                    elif timeframe == '1w':
                        period_ms = 7 * 24 * 60 * 60 * 1000
                    elif timeframe == '1M':
                        period_ms = 30 * 24 * 60 * 60 * 1000
                    else:
                        period_ms = 24 * 60 * 60 * 1000  # Default to daily
                    
                    current_since = last_timestamp + period_ms
                    
                    # Rate limiting
                    time.sleep(0.1)
                    
                    # Safety limit
                    if chunk_count > 200:
                        print(f"   Reached safety limit of {chunk_count} chunks")
                        break
                        
                except Exception as e:
                    print(f"❌ Error in chunk {chunk_count + 1}: {e}")
                    if "rate limit" in str(e).lower():
                        print("   Rate limit hit, waiting 5 seconds...")
                        time.sleep(5)
                        continue
                    break
            
            if not all_ohlcv:
                print(f"❌ No data retrieved for {symbol}")
                return None
            
            # Remove duplicates and sort
            unique_ohlcv = []
            seen_timestamps = set()
            for candle in all_ohlcv:
                if candle[0] not in seen_timestamps:
                    unique_ohlcv.append(candle)
                    seen_timestamps.add(candle[0])
            
            unique_ohlcv.sort(key=lambda x: x[0])
            
            # Convert to DataFrame
            df = pd.DataFrame(unique_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Calculate years of data
            total_days = (df.index[-1] - df.index[0]).days
            years = total_days / 365.25
            
            print(f"✅ {symbol}: {years:.1f} years of data ({len(df)} records)")
            print(f"   Date range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error fetching {symbol} data: {e}")
            return None
    
    def calculate_arb_btc_ratio(self, arb_data, btc_data):
        """Calculate ARB/BTC ratio from price data"""
        print("🔄 Calculating ARB/BTC ratio...")
        
        # Align timestamps and calculate ratio
        combined = pd.merge(
            arb_data[['close']].rename(columns={'close': 'arb_price'}),
            btc_data[['close']].rename(columns={'close': 'btc_price'}),
            left_index=True,
            right_index=True,
            how='inner'
        )
        
        combined['arb_btc_ratio'] = combined['arb_price'] / combined['btc_price']
        
        print(f"✅ Calculated ratio for {len(combined)} data points")
        print(f"   Current ARB/BTC ratio: {combined['arb_btc_ratio'].iloc[-1]:.8f}")
        print(f"   All-time high: {combined['arb_btc_ratio'].max():.8f} on {combined['arb_btc_ratio'].idxmax().strftime('%Y-%m-%d')}")
        print(f"   All-time low: {combined['arb_btc_ratio'].min():.8f} on {combined['arb_btc_ratio'].idxmin().strftime('%Y-%m-%d')}")
        
        return combined
    
    def create_arb_btc_chart(self, ratio_data, save_path=None):
        """Create comprehensive ARB/BTC ratio chart"""
        print("📈 Creating ARB/BTC ratio chart...")
        
        # Set up the plot style with higher quality
        plt.style.use('default')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 14))  # Increased size for better readability
        fig.suptitle('', fontsize=24, fontweight='bold', y=0.95)
        
        # Chart 1: ARB/BTC Ratio Over Time
        ax1.plot(ratio_data.index, ratio_data['arb_btc_ratio'], 
                color='#28A0F0', linewidth=1.5, alpha=0.8, label='ARB/BTC Ratio')  # Arbitrum blue
        
        # Find yearly ATH and ATL points
        ratio_data['year'] = ratio_data.index.year
        yearly_ath = ratio_data.groupby('year')['arb_btc_ratio'].idxmax()
        yearly_atl = ratio_data.groupby('year')['arb_btc_ratio'].idxmin()
        
        # Get the actual data for yearly highs and lows
        yearly_ath_data = ratio_data.loc[yearly_ath]
        yearly_atl_data = ratio_data.loc[yearly_atl]
        
        # Plot yearly ATH points
        ax1.scatter(yearly_ath_data.index, yearly_ath_data['arb_btc_ratio'], 
                   color='green', s=120, marker='^', alpha=0.9, 
                   label='Yearly ATH', zorder=5, edgecolors='darkgreen', linewidth=1)
        
        # Plot yearly ATL points  
        ax1.scatter(yearly_atl_data.index, yearly_atl_data['arb_btc_ratio'], 
                   color='red', s=120, marker='v', alpha=0.9, 
                   label='Yearly ATL', zorder=5, edgecolors='darkred', linewidth=1)
        
        # Highlight overall ATH and ATL
        ath_date = ratio_data['arb_btc_ratio'].idxmax()
        ath_value = ratio_data['arb_btc_ratio'].max()
        atl_date = ratio_data['arb_btc_ratio'].idxmin()
        atl_value = ratio_data['arb_btc_ratio'].min()
        
        ax1.scatter(ath_date, ath_value, color='darkgreen', s=300, marker='^', 
                   label=f'Overall ATH: {ath_value:.8f}', zorder=6, edgecolors='white', linewidth=2)
        ax1.scatter(atl_date, atl_value, color='darkred', s=300, marker='v', 
                   label=f'Overall ATL: {atl_value:.8f}', zorder=6, edgecolors='white', linewidth=2)
        
        ax1.set_title('ARB/BTC Ratio with Yearly ATH/ATL Points', fontsize=18, fontweight='bold', pad=20)
        ax1.set_ylabel('ARB/BTC Ratio', fontsize=16)
        ax1.legend(loc='best', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(ratio_data.index[0], ratio_data.index[-1])
        
        # Format x-axis
        ax1.xaxis.set_major_locator(mdates.YearLocator())
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax1.xaxis.set_minor_locator(mdates.MonthLocator([1, 7]))
        
        # Chart 2: Individual Price Charts (Secondary Y-axis)
        ax2_right = ax2.twinx()
        
        # ARB price (left axis)
        line1 = ax2.plot(ratio_data.index, ratio_data['arb_price'], 
                        color='#28A0F0', linewidth=2, label='ARB Price')
        ax2.set_ylabel('ARB Price (USDT)', fontsize=14, color='#28A0F0')
        ax2.tick_params(axis='y', labelcolor='#28A0F0')
        
        # BTC price (right axis)  
        line2 = ax2_right.plot(ratio_data.index, ratio_data['btc_price'], 
                              color='#F7931A', linewidth=2, label='BTC Price')
        ax2_right.set_ylabel('BTC Price (USDT)', fontsize=14, color='#F7931A')
        ax2_right.tick_params(axis='y', labelcolor='#F7931A')
        
        ax2.set_title('ARB vs BTC Price Comparison', fontsize=16, fontweight='bold', pad=20)
        ax2.set_xlabel('Year', fontsize=14)
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(ratio_data.index[0], ratio_data.index[-1])
        
        # Format x-axis for second chart
        ax2.xaxis.set_major_locator(mdates.YearLocator())
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax2.xaxis.set_minor_locator(mdates.MonthLocator([1, 7]))
        
        # Combined legend for second chart
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_right.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=11)
        
        # Get current values for info boxes
        current_arb = ratio_data['arb_price'].iloc[-1]
        current_btc = ratio_data['btc_price'].iloc[-1]
        current_ratio = ratio_data['arb_btc_ratio'].iloc[-1]
        
        # Calculate changes
        ratio_change_30d = ((current_ratio / ratio_data['arb_btc_ratio'].iloc[-30]) - 1) * 100
        ratio_change_1y = ((current_ratio / ratio_data['arb_btc_ratio'].iloc[-365]) - 1) * 100 if len(ratio_data) > 365 else 0
        
        # Create info boxes on the chart
        # Current prices info box (top right)
        current_info = f"""ARB: ${current_arb:.3f}
BTC: ${current_btc:,.0f}
ARB/BTC: {current_ratio:.8f}"""
        
        ax1.text(0.98, 0.98, current_info, transform=ax1.transAxes, 
                fontsize=14, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.95),
                verticalalignment='top', horizontalalignment='right')
        
        # Add callout boxes for yearly ATH points with simple left-right alternating
        for i, (date, row) in enumerate(yearly_ath_data.iterrows()):
            year = date.year
            info_text = f"{year} ATH\nARB: ${row['arb_price']:.3f}\nBTC: ${row['btc_price']:.0f}\nARB/BTC: {row['arb_btc_ratio']:.8f}"
            
            # Simple alternating: odd index (0,2,4...) = left, even index (1,3,5...) = right
            if i % 2 == 0:  # 1st, 3rd, 5th... go LEFT
                offset_x = -180
                offset_y = 60 + (i * 15)  # Spread vertically
                connection_style = 'arc3,rad=-0.3'
            else:  # 2nd, 4th, 6th... go RIGHT
                offset_x = 180
                offset_y = 60 + (i * 15)  # Spread vertically
                connection_style = 'arc3,rad=0.3'
            
            ax1.annotate(info_text, xy=(date, row['arb_btc_ratio']), 
                        xytext=(offset_x, offset_y), textcoords='offset points',
                        bbox=dict(boxstyle="round,pad=0.4", facecolor="lightgreen", alpha=0.95, edgecolor='darkgreen'),
                        fontsize=9, fontweight='bold',
                        arrowprops=dict(arrowstyle='->', connectionstyle=connection_style, color='darkgreen', lw=1.5))
        
        # Add callout boxes for yearly ATL points with simple left-right alternating
        for i, (date, row) in enumerate(yearly_atl_data.iterrows()):
            year = date.year
            info_text = f"{year} ATL\nARB: ${row['arb_price']:.3f}\nBTC: ${row['btc_price']:.0f}\nARB/BTC: {row['arb_btc_ratio']:.8f}"
            
            # Simple alternating: odd index (0,2,4...) = left, even index (1,3,5...) = right
            if i % 2 == 0:  # 1st, 3rd, 5th... go LEFT
                offset_x = -180
                offset_y = -60 - (i * 15)  # Spread vertically downward
                connection_style = 'arc3,rad=0.3'
            else:  # 2nd, 4th, 6th... go RIGHT
                offset_x = 180
                offset_y = -60 - (i * 15)  # Spread vertically downward
                connection_style = 'arc3,rad=-0.3'
            
            ax1.annotate(info_text, xy=(date, row['arb_btc_ratio']), 
                        xytext=(offset_x, offset_y), textcoords='offset points',
                        bbox=dict(boxstyle="round,pad=0.4", facecolor="lightcoral", alpha=0.95, edgecolor='darkred'),
                        fontsize=9, fontweight='bold',
                        arrowprops=dict(arrowstyle='->', connectionstyle=connection_style, color='darkred', lw=1.5))
        
        # Summary statistics (bottom left)
        stats_text = f"""30-Day Change: {ratio_change_30d:+.2f}%
1-Year Change: {ratio_change_1y:+.2f}%
Data Points: {len(ratio_data):,}
Date Range: {ratio_data.index[0].strftime('%Y-%m-%d')} to {ratio_data.index[-1].strftime('%Y-%m-%d')}"""
        
        fig.text(0.02, 0.02, stats_text, fontsize=10, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8))
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.92, bottom=0.15)
        
        # Save chart if path provided with high quality settings
        if save_path:
            plt.savefig(save_path, dpi=600, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', 
                       format='png', transparent=False)
            print(f"💾 High-quality chart saved to: {save_path}")
        
        plt.show()
        
        return fig
    
    def generate_comprehensive_analysis(self, timeframe='1d', years_back=3):
        """Generate complete ARB/BTC analysis with charts"""
        print("=" * 60)
        print("🚀 ARB/BTC ALL-TIME CHART GENERATOR")
        print("=" * 60)
        
        # Fetch ARB data
        arb_data = self.fetch_historical_data('ARB/USDT', timeframe, years_back)
        if arb_data is None:
            print("❌ Failed to fetch ARB data")
            return None
        
        # Fetch BTC data
        btc_data = self.fetch_historical_data('BTC/USDT', timeframe, years_back)
        if btc_data is None:
            print("❌ Failed to fetch BTC data")
            return None
        
        # Calculate ratio
        ratio_data = self.calculate_arb_btc_ratio(arb_data, btc_data)
        
        # Create charts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = f"arb_btc_chart_{timestamp}.png"
        
        self.create_arb_btc_chart(ratio_data, save_path)
        
        print("\n" + "=" * 60)
        print("✅ ARB/BTC Analysis Complete!")
        print(f"📊 Chart saved as: {save_path}")
        print("=" * 60)
        
        return ratio_data

def main():
    """Main function to generate ARB/BTC chart"""
    try:
        # Create chart generator
        chart_gen = ARBBTCChartGenerator()
        
        # Generate analysis
        # ARB launched in 2023, so 3 years should cover its entire history
        ratio_data = chart_gen.generate_comprehensive_analysis(
            timeframe='1d',
            years_back=3  # ARB is very new, launched in 2023
        )
        
        if ratio_data is not None:
            print("\n📈 Additional Analysis Available:")
            print("   - ARB/BTC ratio trends")
            print("   - Yearly high/low identification") 
            print("   - All-time high/low tracking")
            print("   - Recent performance metrics")
            
    except KeyboardInterrupt:
        print("\n⏹️ Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 