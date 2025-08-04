#!/usr/bin/env python3
"""
4H & 8H Parameter Optimization Script
Tests different parameter combinations to find optimal settings for each timeframe
"""

import pandas as pd
import numpy as np
import ccxt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import itertools
import warnings
import time
warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

class OptimizedAITrendNavigator:
    """AI Trend Navigator with configurable parameters"""
    
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

class CCXTDataFetcher:
    """CCXT data fetcher for 4H and 8H timeframes"""
    
    def __init__(self):
        self.exchange = ccxt.binance({
            'rateLimit': 1200,
            'enableRateLimit': True,
        })
    
    def fetch_data(self, timeframe):
        """Fetch 4H or 8H data using CCXT"""
        print(f"📊 Fetching {timeframe} data from Binance...")
        
        symbol = 'BTC/USDT'
        end_time = datetime.now()
        start_time = end_time - timedelta(days=365 * 5)  # 5 years
        
        try:
            all_ohlcv = []
            target_time = int(start_time.timestamp() * 1000)
            
            current_since = target_time
            chunk_count = 0
            
            while current_since < int(end_time.timestamp() * 1000):
                try:
                    ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe.lower(), current_since, 1000)
                    
                    if not ohlcv or len(ohlcv) == 0:
                        break
                    
                    all_ohlcv.extend(ohlcv)
                    chunk_count += 1
                    
                    last_timestamp = max(candle[0] for candle in ohlcv)
                    period_ms = 4 * 60 * 60 * 1000 if timeframe == '4H' else 8 * 60 * 60 * 1000
                    current_since = last_timestamp + period_ms
                    
                    time.sleep(0.1)  # Rate limiting
                    
                    if chunk_count > 100:  # Safety limit
                        break
                    
                except Exception as e:
                    print(f"❌ Error in chunk {chunk_count + 1}: {e}")
                    break
            
            if not all_ohlcv:
                return None
            
            # Process data
            unique_ohlcv = []
            seen_timestamps = set()
            for candle in all_ohlcv:
                if candle[0] not in seen_timestamps:
                    unique_ohlcv.append(candle)
                    seen_timestamps.add(candle[0])
            
            unique_ohlcv.sort(key=lambda x: x[0])
            
            end_timestamp = int(end_time.timestamp() * 1000)
            filtered_ohlcv = [candle for candle in unique_ohlcv if target_time <= candle[0] <= end_timestamp]
            
            df = pd.DataFrame(filtered_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            print(f"✅ Fetched {len(df)} {timeframe} candles")
            return df
            
        except Exception as e:
            print(f"❌ Error fetching {timeframe} data: {e}")
            return None

def calculate_performance_metrics(signals):
    """Calculate comprehensive performance metrics"""
    signal_array = signals['signal'].values
    price_array = signals['price'].values
    
    # Portfolio simulation
    portfolio_value = []
    position = False
    btc_holdings = 0
    cash = 10000
    
    trades = []
    entry_price = None
    
    for i in range(len(signals)):
        current_signal = signal_array[i]
        current_price = price_array[i]
        
        if current_signal == 'buy' and not position:
            btc_holdings = cash / current_price
            cash = 0
            position = True
            entry_price = current_price
            
        elif current_signal == 'sell' and position:
            cash = btc_holdings * current_price
            btc_holdings = 0
            position = False
            
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
    if len(portfolio_value) == 0:
        return None
    
    total_return = ((portfolio_value[-1] / portfolio_value[0]) - 1) * 100
    
    # Calculate annual return
    days = len(signals)
    years = days / 365.25
    annual_return = ((portfolio_value[-1] / portfolio_value[0]) ** (1/years) - 1) * 100 if years > 0 else 0
    
    # Trade metrics
    total_trades = len(trades)
    profitable_trades = len([t for t in trades if t['profitable']])
    win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
    
    # Max drawdown
    portfolio_series = pd.Series(portfolio_value)
    running_max = portfolio_series.expanding().max()
    drawdown = (portfolio_series - running_max) / running_max * 100
    max_drawdown = drawdown.min()
    
    # Buy & hold comparison
    start_price = price_array[0]
    end_price = price_array[-1]
    buy_hold_return = ((end_price / start_price) - 1) * 100
    
    # Sharpe ratio approximation
    if len(trades) > 1:
        trade_returns = [t['return'] for t in trades]
        sharpe_ratio = np.mean(trade_returns) / np.std(trade_returns) if np.std(trade_returns) > 0 else 0
    else:
        sharpe_ratio = 0
    
    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'max_drawdown': max_drawdown,
        'buy_hold_return': buy_hold_return,
        'outperformance': total_return - buy_hold_return,
        'sharpe_ratio': sharpe_ratio,
        'final_portfolio_value': portfolio_value[-1],
        'years_of_data': years
    }

def optimize_parameters(timeframe, data):
    """Optimize parameters for a specific timeframe"""
    print(f"\n🔍 Optimizing parameters for {timeframe} timeframe...")
    
    # Parameter ranges to test
    param_ranges = {
        'K': [15, 19, 23, 27, 31],  # numberOfClosestValues
        'smoothing': [10, 20, 30, 40, 50],  # smoothingPeriod
        'window': [30, 50, 70, 90, 110],  # windowSize
        'maLen': [5, 10, 15, 20, 25]  # maLen
    }
    
    # Generate all combinations
    param_combinations = list(itertools.product(
        param_ranges['K'],
        param_ranges['smoothing'],
        param_ranges['window'],
        param_ranges['maLen']
    ))
    
    print(f"📊 Testing {len(param_combinations)} parameter combinations...")
    
    best_performance = None
    best_params = None
    results = []
    
    for i, (k, smoothing, window, ma_len) in enumerate(param_combinations):
        try:
            # Test parameters
            navigator = OptimizedAITrendNavigator(
                numberOfClosestValues=k,
                smoothingPeriod=smoothing,
                windowSize=window,
                maLen=ma_len
            )
            
            signals = navigator.calculate_trend_signals(data)
            performance = calculate_performance_metrics(signals)
            
            if performance:
                results.append({
                    'K': k,
                    'smoothing': smoothing,
                    'window': window,
                    'maLen': ma_len,
                    'total_return': performance['total_return'],
                    'annual_return': performance['annual_return'],
                    'total_trades': performance['total_trades'],
                    'win_rate': performance['win_rate'],
                    'max_drawdown': performance['max_drawdown'],
                    'outperformance': performance['outperformance'],
                    'sharpe_ratio': performance['sharpe_ratio']
                })
                
                # Track best performance (optimize for total return)
                if best_performance is None or performance['total_return'] > best_performance['total_return']:
                    best_performance = performance
                    best_params = {
                        'K': k,
                        'smoothing': smoothing,
                        'window': window,
                        'maLen': ma_len
                    }
            
            # Progress indicator
            if (i + 1) % 50 == 0:
                print(f"   📈 Progress: {i + 1}/{len(param_combinations)} ({(i + 1)/len(param_combinations)*100:.1f}%)")
                
        except Exception as e:
            print(f"❌ Error testing params K={k}, smoothing={smoothing}, window={window}, maLen={ma_len}: {e}")
            continue
    
    # Sort results by total return
    results.sort(key=lambda x: x['total_return'], reverse=True)
    
    return results, best_params, best_performance

def main():
    """Main optimization function"""
    print("🚀 Starting 4H & 8H Parameter Optimization...")
    print("=" * 60)
    
    # Initialize data fetcher
    fetcher = CCXTDataFetcher()
    
    # Fetch data for both timeframes
    data_4h = fetcher.fetch_data('4H')
    data_8h = fetcher.fetch_data('8H')
    
    if data_4h is None or data_8h is None:
        print("❌ Failed to fetch data. Exiting.")
        return
    
    # Optimize parameters for each timeframe
    timeframes = {
        '4H': data_4h,
        '8H': data_8h
    }
    
    all_results = {}
    
    for timeframe, data in timeframes.items():
        print(f"\n{'='*20} {timeframe} OPTIMIZATION {'='*20}")
        results, best_params, best_performance = optimize_parameters(timeframe, data)
        
        if best_params and best_performance:
            print(f"\n🏆 BEST PARAMETERS FOR {timeframe}:")
            print(f"   K (numberOfClosestValues): {best_params['K']}")
            print(f"   Smoothing Period: {best_params['smoothing']}")
            print(f"   Window Size: {best_params['window']}")
            print(f"   MA Length: {best_params['maLen']}")
            
            print(f"\n📊 BEST PERFORMANCE FOR {timeframe}:")
            print(f"   Total Return: {best_performance['total_return']:.2f}%")
            print(f"   Annual Return: {best_performance['annual_return']:.2f}%")
            print(f"   Total Trades: {best_performance['total_trades']}")
            print(f"   Win Rate: {best_performance['win_rate']:.1f}%")
            print(f"   Max Drawdown: {best_performance['max_drawdown']:.2f}%")
            print(f"   Outperformance: {best_performance['outperformance']:.2f}%")
            print(f"   Sharpe Ratio: {best_performance['sharpe_ratio']:.2f}")
            print(f"   Final Portfolio: ${best_performance['final_portfolio_value']:,.0f}")
            
            # Show top 10 results
            print(f"\n🔝 TOP 10 PARAMETER COMBINATIONS FOR {timeframe}:")
            print("Rank | K  | Smooth | Window | MA | Total Return | Annual | Trades | Win% | Drawdown | Sharpe")
            print("-" * 90)
            
            for i, result in enumerate(results[:10]):
                print(f"{i+1:4d} | {result['K']:2d} | {result['smoothing']:6d} | {result['window']:6d} | {result['maLen']:2d} | "
                      f"{result['total_return']:10.2f}% | {result['annual_return']:6.2f}% | {result['total_trades']:6d} | "
                      f"{result['win_rate']:4.1f}% | {result['max_drawdown']:8.2f}% | {result['sharpe_ratio']:6.2f}")
            
            all_results[timeframe] = {
                'best_params': best_params,
                'best_performance': best_performance,
                'all_results': results
            }
    
    # Summary comparison
    print(f"\n{'='*25} SUMMARY {'='*25}")
    print("Timeframe | Best Total Return | Best Annual Return | Best Trades | Best Win Rate")
    print("-" * 78)
    
    for timeframe, data in all_results.items():
        perf = data['best_performance']
        print(f"{timeframe:9} | {perf['total_return']:15.2f}% | {perf['annual_return']:16.2f}% | "
              f"{perf['total_trades']:11d} | {perf['win_rate']:11.1f}%")
    
    # Save results to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'4h_8h_optimization_results_{timestamp}.txt'
    
    with open(filename, 'w') as f:
        f.write("4H & 8H Parameter Optimization Results\n")
        f.write("=" * 50 + "\n\n")
        
        for timeframe, data in all_results.items():
            f.write(f"{timeframe} TIMEFRAME RESULTS:\n")
            f.write(f"Best Parameters: {data['best_params']}\n")
            f.write(f"Best Performance: {data['best_performance']}\n")
            f.write("\nTop 10 Results:\n")
            
            for i, result in enumerate(data['all_results'][:10]):
                f.write(f"{i+1}. {result}\n")
            
            f.write("\n" + "="*50 + "\n\n")
    
    print(f"\n💾 Results saved to: {filename}")
    print("✅ Optimization complete!")

if __name__ == "__main__":
    main() 