#!/usr/bin/env python3
"""
Multi-Timeframe Optimized Python AI Trend Navigator Backtest
- Tests 4H, 8H, 1D, 1W, 1M timeframes
- 5 years of data for each timeframe
- Optimized KNN algorithm with NumPy vectorization
- Proper multi-threading with optimal thread count
"""

import pandas as pd
import numpy as np
import requests
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import itertools
import threading
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

class OptimizedAITrendNavigator:
    """Optimized AI Trend Navigator with vectorized operations"""
    
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
        """Optimized KNN function using NumPy operations"""
        if current_idx < self.windowSize:
            return np.nan
        
        # Get window data
        start_idx = max(0, current_idx - self.windowSize)
        window_values = value_series[start_idx:current_idx]
        
        if len(window_values) == 0:
            return np.nan
        
        # Vectorized distance calculation
        distances = np.abs(window_values - target_value)
        
        # Get k smallest distances using argpartition (O(n) average)
        k = min(self.numberOfClosestValues, len(distances))
        if k == 0:
            return np.nan
        
        # Use argpartition for efficient partial sorting
        indices = np.argpartition(distances, k-1)[:k]
        
        # Return mean of k closest values
        return np.mean(window_values[indices])
    
    def calculate_trend_signals(self, df):
        """Calculate trend signals with optimized algorithms"""
        # Convert to numpy arrays for speed
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        # Calculate value_in (HL2 with MA smoothing) - vectorized
        hl2 = (high + low) / 2.0
        value_in = self._calculate_sma_vectorized(hl2, self.maLen)
        
        # Calculate target_in (EMA of close) - vectorized  
        target_in = self._calculate_ema_vectorized(close, self.maLen)
        
        # Calculate KNN MA - optimized
        data_len = len(df)
        knn_ma = np.zeros(data_len)
        
        for i in range(data_len):
            if i >= self.windowSize:
                knn_ma[i] = self._optimized_mean_of_k_closest(value_in, target_in[i], i)
        
        # Apply WMA smoothing - vectorized
        knn_ma_smoothed = np.zeros(data_len)
        weights = np.arange(1, 6)  # WMA weights [1,2,3,4,5]
        weights = weights / weights.sum()
        
        for i in range(4, data_len):
            knn_ma_smoothed[i] = np.sum(knn_ma[i-4:i+1] * weights)
        
        # Calculate trend direction - vectorized
        trend_direction = np.full(data_len, 'neutral', dtype=object)
        
        # Vectorized comparison
        mask_up = (knn_ma_smoothed[1:] > knn_ma_smoothed[:-1]) & (knn_ma_smoothed[1:] > 0)
        mask_down = (knn_ma_smoothed[1:] < knn_ma_smoothed[:-1]) & (knn_ma_smoothed[1:] > 0)
        
        trend_direction[1:][mask_up] = 'up'
        trend_direction[1:][mask_down] = 'down'
        
        # Generate buy/sell signals - vectorized
        signals = np.full(data_len, 'hold', dtype=object)
        
        # Buy signals: down -> up
        buy_mask = (trend_direction[:-1] == 'down') & (trend_direction[1:] == 'up')
        signals[1:][buy_mask] = 'buy'
        
        # Sell signals: up -> down  
        sell_mask = (trend_direction[:-1] == 'up') & (trend_direction[1:] == 'down')
        signals[1:][sell_mask] = 'sell'
        
        # Create result DataFrame
        result = pd.DataFrame({
            'knnMA': knn_ma,
            'knnMA_smoothed': knn_ma_smoothed,
            'MA_knnMA': self._calculate_sma_vectorized(knn_ma, self.smoothingPeriod),
            'trend_direction': trend_direction,
            'price': close,
            'signal': signals
        }, index=df.index)
        
        return result

class MultiTimeframeOptimizer:
    """Multi-timeframe optimizer for different intervals"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.timeframes = {
            '4H': {'interval': '4hour', 'days': 365 * 5},      # 5 years
            '8H': {'interval': '8hour', 'days': 365 * 5},      # 5 years
            '1D': {'interval': '1day', 'days': 365 * 5},       # 5 years
            '1W': {'interval': '1week', 'days': 365 * 5},      # 5 years
            '1M': {'interval': '1month', 'days': 365 * 5}      # 5 years
        }
        
        # Optimized parameter ranges for each timeframe
        self.parameter_ranges = {
            '4H': {
                'numberOfClosestValues': [3, 5, 7, 10, 15, 19],        # 6 values
                'smoothingPeriod': [20, 30, 50, 70, 100],              # 5 values
                'windowSize': [20, 25, 30, 40, 50],                    # 5 values
                'maLen': [3, 5, 8, 10, 15]                             # 5 values
            },
            '8H': {
                'numberOfClosestValues': [3, 5, 7, 10, 15, 19],        # 6 values
                'smoothingPeriod': [20, 30, 50, 70, 100],              # 5 values
                'windowSize': [20, 25, 30, 40, 50],                    # 5 values
                'maLen': [3, 5, 8, 10, 15]                             # 5 values
            },
            '1D': {
                'numberOfClosestValues': [3, 5, 7, 10, 15, 19, 25],    # 7 values
                'smoothingPeriod': [30, 40, 50, 60, 70, 80, 100],      # 7 values  
                'windowSize': [25, 30, 35, 40, 50, 60, 70],             # 7 values
                'maLen': [5, 8, 10, 12, 15, 20]                        # 6 values
            },
            '1W': {
                'numberOfClosestValues': [3, 5, 7, 10, 15, 19, 25],    # 7 values
                'smoothingPeriod': [10, 20, 30, 40, 50, 60],           # 6 values
                'windowSize': [15, 20, 25, 30, 40, 50],                # 6 values
                'maLen': [3, 5, 8, 10, 12, 15]                         # 6 values
            },
            '1M': {
                'numberOfClosestValues': [3, 5, 7, 10, 15, 19],        # 6 values
                'smoothingPeriod': [6, 10, 15, 20, 30, 40],            # 6 values
                'windowSize': [10, 15, 20, 25, 30, 40],                # 6 values
                'maLen': [2, 3, 5, 8, 10, 12]                          # 6 values
            }
        }
    
    def fetch_data_for_timeframe(self, timeframe):
        """Fetch data for specific timeframe"""
        print(f"📊 Fetching {timeframe} data...")
        
        config = self.timeframes[timeframe]
        symbol = "BTCUSD"
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=config['days'])
        
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
        params = {
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'apikey': self.api_key
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
            
            # For higher timeframes, we need to resample the daily data
            if timeframe in ['4H', '8H']:
                df = self._resample_to_timeframe(df, timeframe)
            
            df.set_index('timestamp', inplace=True)
            
            print(f"✅ Fetched {len(df)} {timeframe} candles")
            return df
            
        except Exception as e:
            print(f"❌ Error fetching {timeframe} data: {e}")
            return None
    
    def _resample_to_timeframe(self, df, timeframe):
        """Resample daily data to higher timeframes"""
        df.set_index('timestamp', inplace=True)
        
        # Define resampling rules
        resample_rules = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        
        if timeframe == '4H':
            # Create 4H candles (6 per day)
            resampled = df.resample('4H').agg(resample_rules).dropna()
        elif timeframe == '8H':
            # Create 8H candles (3 per day)
            resampled = df.resample('8H').agg(resample_rules).dropna()
        
        resampled.reset_index(inplace=True)
        return resampled
    
    def calculate_performance_fast(self, signals):
        """Fast performance calculation using vectorized operations"""
        try:
            # Convert to numpy for speed
            signal_array = signals['signal'].values
            price_array = signals['price'].values
            
            # Find buy/sell indices
            buy_indices = np.where(signal_array == 'buy')[0]
            sell_indices = np.where(signal_array == 'sell')[0]
            
            if len(buy_indices) == 0:
                return {'total_return': 0, 'trades': 0, 'win_rate': 0}
            
            # Vectorized portfolio simulation
            portfolio_value = np.full(len(signals), 10000.0)
            position = np.zeros(len(signals), dtype=bool)
            btc_holdings = np.zeros(len(signals))
            cash = np.full(len(signals), 10000.0)
            
            for i in range(1, len(signals)):
                # Copy previous state
                position[i] = position[i-1]
                btc_holdings[i] = btc_holdings[i-1]
                cash[i] = cash[i-1]
                
                if signal_array[i] == 'buy' and not position[i-1]:
                    btc_holdings[i] = cash[i-1] / price_array[i]
                    cash[i] = 0
                    position[i] = True
                elif signal_array[i] == 'sell' and position[i-1]:
                    cash[i] = btc_holdings[i-1] * price_array[i]
                    btc_holdings[i] = 0
                    position[i] = False
                
                # Update portfolio value
                if position[i]:
                    portfolio_value[i] = btc_holdings[i] * price_array[i]
                else:
                    portfolio_value[i] = cash[i]
            
            # Calculate metrics
            total_return = ((portfolio_value[-1] / portfolio_value[0]) - 1) * 100
            
            # Calculate win rate
            trades = 0
            wins = 0
            entry_price = None
            
            for i in range(len(signals)):
                if signal_array[i] == 'buy' and not (i > 0 and position[i-1]):
                    entry_price = price_array[i]
                elif signal_array[i] == 'sell' and entry_price is not None:
                    trades += 1
                    if price_array[i] > entry_price:
                        wins += 1
                    entry_price = None
            
            win_rate = (wins / trades * 100) if trades > 0 else 0
            
            return {
                'total_return': total_return,
                'trades': trades,
                'win_rate': win_rate
            }
            
        except Exception as e:
            return {'total_return': 0, 'trades': 0, 'win_rate': 0}
    
    def test_single_combination(self, args):
        """Test a single parameter combination"""
        timeframe, data, params = args
        k, smoothing, window, ma_len = params
        
        try:
            # Skip invalid combinations
            if window < k or smoothing < 5 or ma_len < 2:
                return None
            
            # Create navigator
            navigator = OptimizedAITrendNavigator(
                numberOfClosestValues=k,
                smoothingPeriod=smoothing,
                windowSize=window,
                maLen=ma_len
            )
            
            # Calculate signals
            signals = navigator.calculate_trend_signals(data)
            
            # Calculate performance
            performance = self.calculate_performance_fast(signals)
            
            return {
                'timeframe': timeframe,
                'K': k,
                'smoothing': smoothing,
                'window': window,
                'maLen': ma_len,
                'total_return': performance['total_return'],
                'trades': performance['trades'],
                'win_rate': performance['win_rate']
            }
            
        except Exception as e:
            return None
    
    def optimize_timeframe(self, timeframe, max_workers=12):
        """Optimize parameters for a specific timeframe"""
        print(f"\n🔍 OPTIMIZING {timeframe} TIMEFRAME")
        print("=" * 60)
        
        # Fetch data
        data = self.fetch_data_for_timeframe(timeframe)
        if data is None:
            return []
        
        # Get parameter ranges
        params = self.parameter_ranges[timeframe]
        
        # Generate combinations
        combinations = list(itertools.product(
            params['numberOfClosestValues'],
            params['smoothingPeriod'],
            params['windowSize'],
            params['maLen']
        ))
        
        print(f"🧮 Testing {len(combinations)} combinations for {timeframe}")
        print(f"⚡ Using {max_workers} threads")
        print(f"📊 Data: {len(data)} candles")
        
        # Estimate time
        estimated_time = len(combinations) * 0.5 / max_workers
        print(f"⏱️ Estimated time: ~{estimated_time/60:.1f} minutes")
        
        results = []
        completed = 0
        start_time = time.time()
        
        # Prepare arguments for threading
        test_args = [(timeframe, data, params) for params in combinations]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_args = {
                executor.submit(self.test_single_combination, args): args 
                for args in test_args
            }
            
            for future in as_completed(future_to_args):
                result = future.result()
                if result and result['total_return'] > -999:
                    results.append(result)
                
                completed += 1
                elapsed = time.time() - start_time
                
                if completed % 50 == 0 or completed == len(combinations):
                    progress = (completed / len(combinations)) * 100
                    rate = completed / elapsed if elapsed > 0 else 0
                    eta = (len(combinations) - completed) / rate if rate > 0 else 0
                    
                    print(f"Progress: {completed:,}/{len(combinations):,} ({progress:.1f}%) | "
                          f"Rate: {rate:.1f}/s | ETA: {eta/60:.1f}min")
                    
                    if results:
                        current_best = max(results, key=lambda x: x['total_return'])
                        print(f"   Current best: {current_best['total_return']:.2f}% "
                              f"(K={current_best['K']}, S={current_best['smoothing']}, "
                              f"W={current_best['window']}, MA={current_best['maLen']})")
        
        total_time = time.time() - start_time
        print(f"\n⏱️ {timeframe} optimization completed in {total_time/60:.1f} minutes")
        
        if results:
            results.sort(key=lambda x: x['total_return'], reverse=True)
            
            # Test default parameters
            print(f"📊 Testing DEFAULT parameters for {timeframe}...")
            default_result = self.test_single_combination((timeframe, data, (3, 50, 30, 5)))
            
            if default_result:
                print(f"Default: {default_result['total_return']:.2f}% return")
                
                if results:
                    best = results[0]
                    improvement = best['total_return'] - default_result['total_return']
                    print(f"🔥 IMPROVEMENT: +{improvement:.2f}% over default!")
        
        return results
    
    def run_all_timeframes(self):
        """Run optimization for all timeframes"""
        print("🚀 Multi-Timeframe Optimized Python Backtest")
        print("=" * 80)
        print("📊 Timeframes: 4H, 8H, 1D, 1W, 1M")
        print("📅 Data period: 5 years for each timeframe")
        print("⚡ Optimized Python with multi-threading")
        
        all_results = {}
        
        for timeframe in ['4H', '8H', '1D', '1W', '1M']:
            results = self.optimize_timeframe(timeframe)
            all_results[timeframe] = results
            
            if results:
                print(f"\n🏆 TOP 5 RESULTS FOR {timeframe}:")
                print("-" * 80)
                print(f"{'Rank':<5} {'K':<3} {'Smooth':<7} {'Window':<7} {'MA':<4} {'Return%':<10} {'Trades':<7} {'Win%':<6}")
                print("-" * 80)
                
                for i, result in enumerate(results[:5]):
                    print(f"{i+1:<5} {result['K']:<3} {result['smoothing']:<7} {result['window']:<7} "
                          f"{result['maLen']:<4} {result['total_return']:<10.2f} {result['trades']:<7} "
                          f"{result['win_rate']:<6.1f}")
        
        # Summary of best results across all timeframes
        print(f"\n🎯 BEST RESULTS ACROSS ALL TIMEFRAMES:")
        print("=" * 80)
        print(f"{'Timeframe':<10} {'K':<3} {'Smooth':<7} {'Window':<7} {'MA':<4} {'Return%':<10} {'Trades':<7} {'Win%':<6}")
        print("-" * 80)
        
        for timeframe, results in all_results.items():
            if results:
                best = results[0]
                print(f"{timeframe:<10} {best['K']:<3} {best['smoothing']:<7} {best['window']:<7} "
                      f"{best['maLen']:<4} {best['total_return']:<10.2f} {best['trades']:<7} "
                      f"{best['win_rate']:<6.1f}")
        
        return all_results

def main():
    """Main function"""
    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        print("❌ FMP_API_KEY not found in environment variables")
        return
    
    optimizer = MultiTimeframeOptimizer(api_key)
    results = optimizer.run_all_timeframes()
    
    print("\n✅ Multi-timeframe optimization completed!")
    print("🎉 Check the results above for the best parameters for each timeframe!")

if __name__ == "__main__":
    main() 