#!/usr/bin/env python3
"""
Debug AI Signals - Test calculation
"""

import pandas as pd
import numpy as np
import ccxt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

class OptimizedAITrendNavigator:
    """AI Trend Navigator - copied from best_params_comparison.py"""
    
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

def fetch_test_data():
    """Fetch small amount of test data"""
    print("📊 Fetching test data...")
    
    exchange = ccxt.binance({
        'rateLimit': 1200,
        'enableRateLimit': True,
    })
    
    symbol = 'BTC/USDT'
    
    try:
        # Fetch just 100 recent 4H candles for testing
        ohlcv = exchange.fetch_ohlcv(symbol, '4h', None, 100)
        
        if not ohlcv:
            print("❌ No data received")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        print(f"✅ Fetched {len(df)} 4H candles")
        return df
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None

def main():
    """Test AI signal calculation"""
    print("🔍 Testing AI Signal Calculation...")
    
    # Fetch test data
    df = fetch_test_data()
    if df is None:
        return
    
    # Test with optimized 4H parameters
    params = {'K': 23, 'smoothing': 10, 'window': 30, 'maLen': 5}
    
    navigator = OptimizedAITrendNavigator(
        numberOfClosestValues=params['K'],
        smoothingPeriod=params['smoothing'],
        windowSize=params['window'],
        maLen=params['maLen']
    )
    
    # Calculate signals
    print("🔮 Calculating AI signals...")
    signals = navigator.calculate_trend_signals(df)
    
    # Show sample of calculated values
    print("\n📊 Sample AI Signal Values:")
    print("="*80)
    
    # Get last 10 rows where signals are calculated
    sample_data = signals.tail(10)
    
    for i, (timestamp, row) in enumerate(sample_data.iterrows()):
        print(f"Row {i}:")
        print(f"  Timestamp: {timestamp}")
        print(f"  Price: ${row['price']:,.2f}")
        print(f"  knnMA: {row['knnMA']:.2f}")
        print(f"  knnMA_smoothed: {row['knnMA_smoothed']:.2f}")  # This is the blue line!
        print(f"  MA_knnMA: {row['MA_knnMA']:.2f}")
        print(f"  Signal: {row['signal']}")
        print(f"  Trend: {row['trend_direction']}")
        print("-" * 40)
    
    # Check for NaN/invalid values
    nan_count = signals['knnMA_smoothed'].isna().sum()
    inf_count = np.isinf(signals['knnMA_smoothed']).sum()
    zero_count = (signals['knnMA_smoothed'] == 0).sum()
    
    print(f"\n🔍 Data Quality Check:")
    print(f"  Total rows: {len(signals)}")
    print(f"  NaN values: {nan_count}")
    print(f"  Infinite values: {inf_count}")
    print(f"  Zero values: {zero_count}")
    print(f"  Valid values: {len(signals) - nan_count - inf_count}")
    
    # Show value ranges
    valid_smoothed = signals['knnMA_smoothed'][signals['knnMA_smoothed'] > 0]
    if len(valid_smoothed) > 0:
        print(f"\n📈 knnMA_smoothed (Blue Line) Range:")
        print(f"  Min: ${valid_smoothed.min():,.2f}")
        print(f"  Max: ${valid_smoothed.max():,.2f}")
        print(f"  Mean: ${valid_smoothed.mean():,.2f}")
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    main() 