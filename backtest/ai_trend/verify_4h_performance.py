#!/usr/bin/env python3
"""
4H Performance Verification Script
Generate charts to verify the 9,388.42% return with 292 trades
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class OptimizedAITrendNavigator:
    """Optimized AI Trend Navigator - Exact copy from daily_supabase_update.py"""
    
    def __init__(self, numberOfClosestValues=3, smoothingPeriod=50, windowSize=30, maLen=5):
        self.numberOfClosestValues = numberOfClosestValues
        self.smoothingPeriod = smoothingPeriod
        self.windowSize = max(numberOfClosestValues, windowSize)
        self.maLen = maLen
        
    def _calculate_sma_vectorized(self, data, period):
        """Vectorized SMA calculation"""
        if len(data) < period:
            return np.zeros(len(data))
        return pd.Series(data).rolling(window=period, min_periods=1).mean().values
    
    def _calculate_ema_vectorized(self, data, period):
        """Vectorized EMA calculation"""
        return pd.Series(data).ewm(span=period, adjust=False).mean().values
    
    def _optimized_mean_of_k_closest(self, value_series, target_value, current_idx):
        """Optimized KNN function"""
        if current_idx < self.windowSize:
            return np.nan
        
        start_idx = max(0, current_idx - self.windowSize)
        window_values = value_series[start_idx:current_idx]
        
        if len(window_values) == 0:
            return np.nan
        
        distances = np.abs(window_values - target_value)
        k = min(self.numberOfClosestValues, len(distances))
        if k == 0:
            return np.nan
        
        indices = np.argpartition(distances, k-1)[:k]
        return np.mean(window_values[indices])
    
    def calculate_trend_signals(self, df):
        """Calculate trend signals"""
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        # Calculate value_in (HL2 with MA smoothing)
        hl2 = (high + low) / 2.0
        value_in = self._calculate_sma_vectorized(hl2, self.maLen)
        
        # Calculate target_in (EMA of close)
        target_in = self._calculate_ema_vectorized(close, self.maLen)
        
        # Calculate KNN MA
        data_len = len(df)
        knn_ma = np.zeros(data_len)
        
        for i in range(data_len):
            if i >= self.windowSize:
                knn_ma[i] = self._optimized_mean_of_k_closest(value_in, target_in[i], i)
        
        # Apply WMA smoothing
        knn_ma_smoothed = np.zeros(data_len)
        weights = np.arange(1, 6)
        weights = weights / weights.sum()
        
        for i in range(4, data_len):
            knn_ma_smoothed[i] = np.sum(knn_ma[i-4:i+1] * weights)
        
        # Calculate trend direction
        trend_direction = np.full(data_len, 'neutral', dtype=object)
        
        mask_up = (knn_ma_smoothed[1:] > knn_ma_smoothed[:-1]) & (knn_ma_smoothed[1:] > 0)
        mask_down = (knn_ma_smoothed[1:] < knn_ma_smoothed[:-1]) & (knn_ma_smoothed[1:] > 0)
        
        trend_direction[1:][mask_up] = 'up'
        trend_direction[1:][mask_down] = 'down'
        
        # Generate signals
        signals = np.full(data_len, 'hold', dtype=object)
        
        buy_mask = (trend_direction[:-1] == 'down') & (trend_direction[1:] == 'up')
        signals[1:][buy_mask] = 'buy'
        
        sell_mask = (trend_direction[:-1] == 'up') & (trend_direction[1:] == 'down')
        signals[1:][sell_mask] = 'sell'
        
        result = pd.DataFrame({
            'knnMA': knn_ma,
            'knnMA_smoothed': knn_ma_smoothed,
            'MA_knnMA': self._calculate_sma_vectorized(knn_ma, self.smoothingPeriod),
            'trend_direction': trend_direction,
            'price': close,
            'signal': signals
        }, index=df.index)
        
        return result

def fetch_4h_data():
    """Fetch and create 4H data"""
    print("📊 Fetching 4H data...")
    
    api_key = os.getenv('FMP_API_KEY')
    symbol = "BTCUSD"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 5)  # 5 years
    
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
    params = {
        'from': start_date.strftime('%Y-%m-%d'),
        'to': end_date.strftime('%Y-%m-%d'),
        'apikey': api_key
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        df = pd.DataFrame(data['historical'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        df = df.rename(columns={
            'date': 'timestamp',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        })
        
        # Create 4H intervals from daily data
        df_4h = create_4h_intervals(df)
        df_4h.set_index('timestamp', inplace=True)
        
        print(f"✅ Created {len(df_4h)} 4H candles from {len(df)} daily records")
        return df_4h
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None

def create_4h_intervals(df):
    """Create 4H intervals from daily data by interpolating"""
    print("🔄 Creating 4H intervals from daily data...")
    
    four_hour_data = []
    
    for i, row in df.iterrows():
        daily_date = row['timestamp']
        daily_open = row['open']
        daily_high = row['high']
        daily_low = row['low']
        daily_close = row['close']
        daily_volume = row['volume']
        
        # Create 6 4H candles per day (00:00, 04:00, 08:00, 12:00, 16:00, 20:00)
        for hour in [0, 4, 8, 12, 16, 20]:
            timestamp_4h = daily_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            # Interpolate OHLC values within the daily range
            if hour == 0:
                # First 4H: open at daily open, close progresses toward daily close
                open_4h = daily_open
                close_4h = daily_open + (daily_close - daily_open) * 0.167  # 1/6 of daily range
            elif hour == 20:
                # Last 4H: close at daily close
                open_4h = daily_open + (daily_close - daily_open) * 0.833  # 5/6 of daily range
                close_4h = daily_close
            else:
                # Middle 4H candles: interpolate through the day
                progress = hour / 20.0  # 0 to 1 progression through the day
                open_4h = daily_open + (daily_close - daily_open) * (progress - 0.167)
                close_4h = daily_open + (daily_close - daily_open) * (progress + 0.167)
            
            # High and low are distributed across the day
            high_4h = min(daily_high, max(open_4h, close_4h) * 1.001)  # Small variance
            low_4h = max(daily_low, min(open_4h, close_4h) * 0.999)   # Small variance
            
            # Distribute volume across 6 4H periods
            volume_4h = daily_volume / 6.0
            
            four_hour_data.append({
                'timestamp': timestamp_4h,
                'open': open_4h,
                'high': high_4h,
                'low': low_4h,
                'close': close_4h,
                'volume': volume_4h
            })
    
    # Create DataFrame
    df_4h = pd.DataFrame(four_hour_data)
    df_4h['timestamp'] = pd.to_datetime(df_4h['timestamp'])
    df_4h = df_4h.sort_values('timestamp').reset_index(drop=True)
    
    return df_4h

def calculate_portfolio_performance(signals):
    """Calculate portfolio performance with detailed tracking"""
    signal_array = signals['signal'].values
    price_array = signals['price'].values
    
    # Portfolio simulation
    portfolio_value = []
    position = False
    btc_holdings = 0
    cash = 10000
    
    trades = []
    buy_signals = []
    sell_signals = []
    entry_price = None
    
    for i in range(len(signals)):
        current_signal = signal_array[i]
        current_price = price_array[i]
        current_timestamp = signals.index[i]
        
        if current_signal == 'buy' and not position:
            btc_holdings = cash / current_price
            cash = 0
            position = True
            entry_price = current_price
            buy_signals.append({
                'timestamp': current_timestamp,
                'price': current_price,
                'type': 'buy'
            })
            
        elif current_signal == 'sell' and position:
            cash = btc_holdings * current_price
            btc_holdings = 0
            position = False
            
            sell_signals.append({
                'timestamp': current_timestamp,
                'price': current_price,
                'type': 'sell'
            })
            
            if entry_price:
                trade_return = (current_price - entry_price) / entry_price * 100
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'return': trade_return,
                    'profitable': trade_return > 0
                })
        
        # Current portfolio value
        if position:
            current_value = btc_holdings * current_price
        else:
            current_value = cash
        
        portfolio_value.append(current_value)
    
    # Calculate metrics
    total_return = ((portfolio_value[-1] / portfolio_value[0]) - 1) * 100
    profitable_trades = len([t for t in trades if t['profitable']])
    win_rate = (profitable_trades / len(trades) * 100) if trades else 0
    
    # Buy & hold comparison
    start_price = price_array[0]
    end_price = price_array[-1]
    buy_hold_return = ((end_price / start_price) - 1) * 100
    
    return {
        'portfolio_value': portfolio_value,
        'total_return': total_return,
        'total_trades': len(trades),
        'win_rate': win_rate,
        'buy_hold_return': buy_hold_return,
        'buy_signals': buy_signals,
        'sell_signals': sell_signals,
        'trades': trades
    }

def create_performance_charts(df, signals, performance):
    """Create comprehensive performance charts"""
    
    # Create figure with subplots
    fig = plt.figure(figsize=(20, 16))
    
    # 1. Price Chart with Buy/Sell Signals
    ax1 = plt.subplot(3, 2, 1)
    ax1.plot(df.index, df['close'], label='BTC Price', color='blue', linewidth=1)
    
    # Add buy/sell signals
    for signal in performance['buy_signals']:
        ax1.scatter(signal['timestamp'], signal['price'], 
                   color='green', marker='^', s=100, label='Buy Signal' if signal == performance['buy_signals'][0] else "")
    
    for signal in performance['sell_signals']:
        ax1.scatter(signal['timestamp'], signal['price'], 
                   color='red', marker='v', s=100, label='Sell Signal' if signal == performance['sell_signals'][0] else "")
    
    ax1.set_title('4H BTC Price with Buy/Sell Signals', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Price ($)', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Portfolio Value Over Time
    ax2 = plt.subplot(3, 2, 2)
    ax2.plot(df.index, performance['portfolio_value'], label='Portfolio Value', color='green', linewidth=2)
    ax2.axhline(y=10000, color='red', linestyle='--', alpha=0.7, label='Initial Investment')
    ax2.set_title('Portfolio Value Over Time', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Portfolio Value ($)', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Format y-axis to show values in thousands/millions
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K' if x < 1000000 else f'${x/1000000:.1f}M'))
    
    # 3. AI Trend Navigator Signals
    ax3 = plt.subplot(3, 2, 3)
    ax3.plot(df.index, signals['knnMA_smoothed'], label='KNN MA Smoothed', color='purple', linewidth=2)
    ax3.plot(df.index, signals['MA_knnMA'], label='MA of KNN MA', color='orange', linewidth=2)
    ax3.set_title('AI Trend Navigator Signals', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Signal Value', fontsize=12)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Trade Returns Distribution
    ax4 = plt.subplot(3, 2, 4)
    trade_returns = [t['return'] for t in performance['trades']]
    if trade_returns:
        ax4.hist(trade_returns, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        ax4.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='Break-even')
        ax4.set_title('Trade Returns Distribution', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Return (%)', fontsize=12)
        ax4.set_ylabel('Frequency', fontsize=12)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
    
    # 5. Performance Metrics
    ax5 = plt.subplot(3, 2, 5)
    ax5.axis('off')
    
    # Create metrics text
    metrics_text = f"""
    📊 4H PERFORMANCE METRICS
    
    💰 Total Return: {performance['total_return']:.2f}%
    🔄 Total Trades: {performance['total_trades']}
    🎯 Win Rate: {performance['win_rate']:.1f}%
    
    📈 Buy & Hold Return: {performance['buy_hold_return']:.2f}%
    ⚡ Strategy Outperformance: {performance['total_return'] - performance['buy_hold_return']:.2f}%
    
    💼 Final Portfolio Value: ${performance['portfolio_value'][-1]:,.0f}
    🚀 Initial Investment: $10,000
    📊 Data Points: {len(df):,} (4H candles)
    ⏱️  Time Period: {(df.index[-1] - df.index[0]).days} days
    """
    
    ax5.text(0.1, 0.9, metrics_text, transform=ax5.transAxes, fontsize=12,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    # 6. Monthly Returns Heatmap
    ax6 = plt.subplot(3, 2, 6)
    
    # Calculate monthly returns
    portfolio_df = pd.DataFrame({
        'timestamp': df.index,
        'portfolio_value': performance['portfolio_value']
    })
    portfolio_df.set_index('timestamp', inplace=True)
    
    # Resample to monthly and calculate returns
    monthly_portfolio = portfolio_df.resample('M').last()
    monthly_returns = monthly_portfolio.pct_change().dropna() * 100
    
    if len(monthly_returns) > 0:
        # Create year-month pivot
        monthly_returns.index = pd.to_datetime(monthly_returns.index)
        monthly_returns['year'] = monthly_returns.index.year
        monthly_returns['month'] = monthly_returns.index.month
        
        pivot_table = monthly_returns.pivot_table(values='portfolio_value', 
                                                 index='year', columns='month', 
                                                 aggfunc='first')
        
        # Create heatmap
        sns.heatmap(pivot_table, annot=True, fmt='.1f', cmap='RdYlGn', 
                   center=0, ax=ax6, cbar_kws={'label': 'Monthly Return (%)'})
        ax6.set_title('Monthly Returns Heatmap', fontsize=14, fontweight='bold')
        ax6.set_xlabel('Month', fontsize=12)
        ax6.set_ylabel('Year', fontsize=12)
    
    plt.tight_layout()
    
    # Save the chart
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'4h_performance_verification_{timestamp}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"📊 Chart saved as: {filename}")
    
    plt.show()

def main():
    """Main function to run the verification"""
    print("🚀 Starting 4H Performance Verification...")
    
    # Fetch data
    df = fetch_4h_data()
    if df is None:
        print("❌ Failed to fetch data")
        return
    
    # Initialize AI Trend Navigator with 4H optimized parameters
    params = {'K': 19, 'smoothing': 20, 'window': 50, 'maLen': 15}
    navigator = OptimizedAITrendNavigator(
        numberOfClosestValues=params['K'],
        smoothingPeriod=params['smoothing'],
        windowSize=params['window'],
        maLen=params['maLen']
    )
    
    # Calculate signals
    print("🔮 Calculating AI Trend Navigator signals...")
    signals = navigator.calculate_trend_signals(df)
    
    # Calculate performance
    print("📊 Calculating portfolio performance...")
    performance = calculate_portfolio_performance(signals)
    
    # Display results
    print("\n" + "="*50)
    print("📊 4H PERFORMANCE VERIFICATION RESULTS")
    print("="*50)
    print(f"💰 Total Return: {performance['total_return']:.2f}%")
    print(f"🔄 Total Trades: {performance['total_trades']}")
    print(f"🎯 Win Rate: {performance['win_rate']:.1f}%")
    print(f"📈 Buy & Hold Return: {performance['buy_hold_return']:.2f}%")
    print(f"⚡ Strategy Outperformance: {performance['total_return'] - performance['buy_hold_return']:.2f}%")
    print(f"💼 Final Portfolio Value: ${performance['portfolio_value'][-1]:,.0f}")
    print(f"📊 Data Points: {len(df):,} (4H candles)")
    print(f"⏱️  Time Period: {(df.index[-1] - df.index[0]).days} days")
    print("="*50)
    
    # Create charts
    print("📈 Creating performance charts...")
    create_performance_charts(df, signals, performance)
    
    print("✅ Verification complete!")

if __name__ == "__main__":
    main() 