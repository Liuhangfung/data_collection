import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import ta
import warnings
warnings.filterwarnings('ignore')

class AITrendNavigator:
    def __init__(self, numberOfClosestValues=3, smoothingPeriod=50, windowSize=30, maLen=5):
        """
        Initialize AI Trend Navigator with KNN-based moving average
        
        Parameters:
        - numberOfClosestValues: K in KNN (default: 3)
        - smoothingPeriod: period for final smoothing (default: 50)
        - windowSize: lookback window for KNN search (default: 30)
        - maLen: smoothing period for input values (default: 5)
        """
        self.numberOfClosestValues = numberOfClosestValues
        self.smoothingPeriod = smoothingPeriod
        self.windowSize = max(numberOfClosestValues, windowSize)
        self.maLen = maLen
        
    def get_btc_data(self, symbol="BTCUSDT", interval="1h", limit=1000):
        """
        Fetch BTC/USDT data from Binance API
        """
        url = f"https://api.binance.com/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Convert to DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert to proper types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            df[numeric_cols] = df[numeric_cols].astype(float)
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
    def calculate_value_in(self, df, price_value="hl2"):
        """
        Calculate the value_in series based on price_value type
        """
        if price_value == "hl2":
            raw_value = (df['high'] + df['low']) / 2
            return raw_value.rolling(window=self.maLen).mean()
        elif price_value == "sma":
            return df['close'].rolling(window=self.maLen).mean()
        elif price_value == "ema":
            return df['close'].ewm(span=self.maLen).mean()
        elif price_value == "wma":
            return df['close'].rolling(window=self.maLen).apply(
                lambda x: np.average(x, weights=np.arange(1, len(x) + 1))
            )
        else:
            return df['close'].rolling(window=self.maLen).mean()
    
    def calculate_target_in(self, df, target_value="Price Action"):
        """
        Calculate the target_in series based on target_value type
        """
        if target_value == "Price Action":
            return df['close'].ewm(span=self.maLen).mean()  # RMA approximation
        elif target_value == "Volatility":
            return ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
        elif target_value == "sma":
            return df['close'].rolling(window=self.maLen).mean()
        elif target_value == "ema":
            return df['close'].ewm(span=self.maLen).mean()
        else:
            return df['close'].ewm(span=self.maLen).mean()
    
    def mean_of_k_closest(self, value_series, target_value, current_idx):
        """
        Core KNN function: find K closest values and return their average
        
        This is the Python equivalent of the Pine Script meanOfKClosest function
        """
        if current_idx < self.windowSize:
            return np.nan
        
        # Initialize arrays to store closest distances and values
        closest_distances = np.full(self.numberOfClosestValues, float('inf'))
        closest_values = np.zeros(self.numberOfClosestValues)
        
        # Look back through the window
        for i in range(1, self.windowSize + 1):
            if current_idx - i < 0:
                break
                
            value = value_series.iloc[current_idx - i]
            if np.isnan(value) or np.isnan(target_value):
                continue
                
            # Calculate distance (absolute difference)
            distance = abs(target_value - value)
            
            # Find the index with maximum distance among current closest
            max_dist_index = np.argmax(closest_distances)
            max_dist_value = closest_distances[max_dist_index]
            
            # If current distance is smaller, replace the maximum
            if distance < max_dist_value:
                closest_distances[max_dist_index] = distance
                closest_values[max_dist_index] = value
        
        # Return average of closest values
        valid_values = closest_values[closest_distances < float('inf')]
        return np.mean(valid_values) if len(valid_values) > 0 else np.nan
    
    def calculate_knnMA(self, df, price_value="hl2", target_value="Price Action"):
        """
        Calculate the KNN-based moving average
        """
        # Calculate input series
        value_in = self.calculate_value_in(df, price_value)
        target_in = self.calculate_target_in(df, target_value)
        
        # Calculate knnMA for each bar
        knnMA = []
        for i in range(len(df)):
            if i < self.windowSize or np.isnan(target_in.iloc[i]):
                knnMA.append(np.nan)
            else:
                knn_value = self.mean_of_k_closest(value_in, target_in.iloc[i], i)
                knnMA.append(knn_value)
        
        return pd.Series(knnMA, index=df.index)
    
    def calculate_trend_signals(self, df, price_value="hl2", target_value="Price Action"):
        """
        Calculate complete trend signals including knnMA, smoothed version, and trend direction
        """
        # Calculate raw knnMA
        knnMA = self.calculate_knnMA(df, price_value, target_value)
        
        # Apply WMA smoothing (knnMA_)
        knnMA_smoothed = knnMA.rolling(window=5).apply(
            lambda x: np.average(x.dropna(), weights=np.arange(1, len(x.dropna()) + 1))
        )
        
        # Calculate trend direction
        knnMA_prev = knnMA_smoothed.shift(1)
        trend_direction = pd.Series(index=df.index, dtype='object')
        
        for i in range(1, len(df)):
            if np.isnan(knnMA_smoothed.iloc[i]) or np.isnan(knnMA_prev.iloc[i]):
                trend_direction.iloc[i] = 'neutral'
            elif knnMA_smoothed.iloc[i] > knnMA_prev.iloc[i]:
                trend_direction.iloc[i] = 'up'
            elif knnMA_smoothed.iloc[i] < knnMA_prev.iloc[i]:
                trend_direction.iloc[i] = 'down'
            else:
                trend_direction.iloc[i] = 'neutral'
        
        # Calculate MA of knnMA for additional smoothing
        MA_knnMA = knnMA.rolling(window=self.smoothingPeriod).mean()
        
        # Generate signals
        signals = pd.DataFrame({
            'knnMA': knnMA,
            'knnMA_smoothed': knnMA_smoothed,
            'MA_knnMA': MA_knnMA,
            'trend_direction': trend_direction,
            'price': df['close']
        })
        
        # Add buy/sell signals
        signals['signal'] = 'hold'
        signals['signal'] = signals['signal'].astype('object')
        
        for i in range(1, len(signals)):
            if (signals['trend_direction'].iloc[i-1] == 'down' and 
                signals['trend_direction'].iloc[i] == 'up'):
                signals.loc[signals.index[i], 'signal'] = 'buy'
            elif (signals['trend_direction'].iloc[i-1] == 'up' and 
                  signals['trend_direction'].iloc[i] == 'down'):
                signals.loc[signals.index[i], 'signal'] = 'sell'
        
        return signals
    
    def plot_results(self, df, signals, title="AI Trend Navigator - BTC/USDT"):
        """
        Plot the results with trend direction integrated into the price chart
        """
        fig, ax = plt.subplots(1, 1, figsize=(15, 8))
        
        # Add background coloring for trend direction
        for i in range(1, len(signals)):
            start_time = df['timestamp'].iloc[i-1]
            end_time = df['timestamp'].iloc[i]
            trend = signals['trend_direction'].iloc[i]
            
            if trend == 'up':
                ax.axvspan(start_time, end_time, alpha=0.1, color='green', zorder=0)
            elif trend == 'down':
                ax.axvspan(start_time, end_time, alpha=0.1, color='red', zorder=0)
            else:  # neutral
                ax.axvspan(start_time, end_time, alpha=0.05, color='orange', zorder=0)
        
        # Plot price and knnMA (knnMA at the back)
        ax.plot(df['timestamp'], df['close'], label='BTC/USDT Price', color='black', linewidth=1.5, zorder=3)
        ax.plot(df['timestamp'], signals['knnMA_smoothed'], label='knnMA (smoothed)', color='blue', linewidth=2, zorder=1)
        ax.plot(df['timestamp'], signals['MA_knnMA'], label='MA knnMA', color='teal', linewidth=1.5, zorder=2)
        
        # Add trend direction as colored line segments (on top)
        for i in range(1, len(signals)):
            start_idx = i-1
            end_idx = i
            trend = signals['trend_direction'].iloc[i]
            
            if trend == 'up':
                ax.plot([df['timestamp'].iloc[start_idx], df['timestamp'].iloc[end_idx]], 
                       [signals['knnMA_smoothed'].iloc[start_idx], signals['knnMA_smoothed'].iloc[end_idx]], 
                       color='lime', linewidth=4, alpha=0.8, zorder=4)
            elif trend == 'down':
                ax.plot([df['timestamp'].iloc[start_idx], df['timestamp'].iloc[end_idx]], 
                       [signals['knnMA_smoothed'].iloc[start_idx], signals['knnMA_smoothed'].iloc[end_idx]], 
                       color='red', linewidth=4, alpha=0.8, zorder=4)
            else:  # neutral
                ax.plot([df['timestamp'].iloc[start_idx], df['timestamp'].iloc[end_idx]], 
                       [signals['knnMA_smoothed'].iloc[start_idx], signals['knnMA_smoothed'].iloc[end_idx]], 
                       color='orange', linewidth=4, alpha=0.8, zorder=4)
        
        # Add buy/sell signals
        buy_signals = signals[signals['signal'] == 'buy']
        sell_signals = signals[signals['signal'] == 'sell']
        
        if not buy_signals.empty:
            ax.scatter(df.loc[buy_signals.index, 'timestamp'], 
                       df.loc[buy_signals.index, 'close'], 
                       color='darkgreen', marker='^', s=150, label='Buy Signal', 
                       edgecolors='white', linewidth=1, zorder=6)
        
        if not sell_signals.empty:
            ax.scatter(df.loc[sell_signals.index, 'timestamp'], 
                       df.loc[sell_signals.index, 'close'], 
                       color='darkred', marker='v', s=150, label='Sell Signal', 
                       edgecolors='white', linewidth=1, zorder=6)
        
        # Create custom legend entries for trend direction
        from matplotlib.patches import Patch
        existing_handles, existing_labels = ax.get_legend_handles_labels()
        
        # Add trend direction patches to legend
        trend_patches = [
            Patch(facecolor='green', alpha=0.3, label='Up Trend'),
            Patch(facecolor='red', alpha=0.3, label='Down Trend'),
            Patch(facecolor='orange', alpha=0.3, label='Neutral Trend')
        ]
        
        all_handles = existing_handles + trend_patches
        all_labels = existing_labels + ['Up Trend', 'Down Trend', 'Neutral Trend']
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_ylabel('Price (USDT)', fontsize=12)
        ax.set_xlabel('Time', fontsize=12)
        ax.legend(handles=all_handles, labels=all_labels, loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        # Format y-axis to show price with proper formatting
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.show()
    
    def run_analysis(self, symbol="BTCUSDT", interval="1h", limit=500):
        """
        Run complete analysis
        """
        print(f"🔍 Fetching {symbol} data...")
        df = self.get_btc_data(symbol, interval, limit)
        
        if df is None:
            print("❌ Failed to fetch data")
            return None
        
        print(f"✅ Data fetched successfully: {len(df)} bars")
        print(f"📊 Time range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
        
        print("\n🧮 Calculating KNN-based trend signals...")
        signals = self.calculate_trend_signals(df)
        
        # Show latest signals
        latest_signals = signals.tail(10)
        print(f"\n📈 Latest 10 signals:")
        for i, (idx, row) in enumerate(latest_signals.iterrows()):
            print(f"{i+1:2d}. {df.loc[idx, 'timestamp'].strftime('%Y-%m-%d %H:%M')} | "
                  f"Price: ${row['price']:.2f} | "
                  f"knnMA: {row['knnMA_smoothed']:.2f} | "
                  f"Trend: {row['trend_direction']} | "
                  f"Signal: {row['signal']}")
        
        # Show recent buy/sell signals
        recent_signals = signals[signals['signal'].isin(['buy', 'sell'])].tail(5)
        if not recent_signals.empty:
            print(f"\n🎯 Recent Buy/Sell Signals:")
            for idx, row in recent_signals.iterrows():
                print(f"• {df.loc[idx, 'timestamp'].strftime('%Y-%m-%d %H:%M')} | "
                      f"Price: ${row['price']:.2f} | "
                      f"Action: {row['signal'].upper()}")
        
        # Plot results
        self.plot_results(df, signals, f"AI Trend Navigator - {symbol} ({interval})")
        
        return df, signals

# Example usage
if __name__ == "__main__":
    # Initialize the AI Trend Navigator
    navigator = AITrendNavigator(
        numberOfClosestValues=3,  # K in KNN
        smoothingPeriod=50,      # Final smoothing period
        windowSize=30,           # Lookback window
        maLen=5                  # Input smoothing
    )
    
    # Run analysis
    df, signals = navigator.run_analysis(
        symbol="BTCUSDT",
        interval="1d",          # 1h, 4h, 1d, etc.
        limit=500               # Number of bars to fetch
    )
    
    print("\n" + "="*50)
    print("🎯 ANALYSIS COMPLETE!")
    print("="*50) 