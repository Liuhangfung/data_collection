#!/usr/bin/env python3
"""
Complete MACD Signal Analysis
============================
BUY signals → Track max gain during holding period (BUY to SELL)
SELL signals → Track max drop during waiting period (SELL to next BUY)
Provides comprehensive signal performance analysis across all timeframes
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

def analyze_signal_max_gains_complete(data_with_macd, lookforward_periods=None):
    """
    Complete analysis: 
    BUY signals → track max gain during holding period (BUY to SELL)
    SELL signals → track max drop during waiting period (SELL to next BUY)
    Note: lookforward_periods is ignored - we use actual signal-to-signal periods
    """
    df = data_with_macd.copy()
    
    # Generate MACD signals
    df['signal_type'] = 0
    
    for i in range(1, len(df)):
        # Buy signal: MACD crosses above Signal line
        if df['macd'].iloc[i] > df['signal'].iloc[i] and df['macd'].iloc[i-1] <= df['signal'].iloc[i-1]:
            df['signal_type'].iloc[i] = 1  # Buy
        # Sell signal: MACD crosses below Signal line
        elif df['macd'].iloc[i] < df['signal'].iloc[i] and df['macd'].iloc[i-1] >= df['signal'].iloc[i-1]:
            df['signal_type'].iloc[i] = -1  # Sell
    
    # Extract signals
    signals = df[df['signal_type'] != 0].copy()
    
    print(f"   BUY signals found: {len(signals[signals['signal_type'] == 1])}")
    print(f"   SELL signals found: {len(signals[signals['signal_type'] == -1])}")
    print(f"   Total signals: {len(signals)}")
    
    signal_results = []
    
    # Convert signals to list for easier iteration
    signal_list = [(idx, row) for idx, row in signals.iterrows()]
    
    for i, (idx, signal) in enumerate(signal_list):
        signal_time = idx
        signal_price = signal['close']
        signal_type = signal['signal_type']
        
        # Find the next opposite signal
        next_signal_idx = None
        next_signal_time = None
        next_signal_price = None
        
        for j in range(i + 1, len(signal_list)):
            next_idx, next_signal = signal_list[j]
            if signal_type == 1 and next_signal['signal_type'] == -1:  # BUY looking for SELL
                next_signal_idx = j
                next_signal_time = next_idx
                next_signal_price = next_signal['close']
                break
            elif signal_type == -1 and next_signal['signal_type'] == 1:  # SELL looking for BUY
                next_signal_idx = j
                next_signal_time = next_idx
                next_signal_price = next_signal['close']
                break
        
        if next_signal_time is None:
            # No matching signal found, skip this signal
            continue
        
        # Get price data between the two signals
        start_idx = df.index.get_loc(signal_time)
        end_idx = df.index.get_loc(next_signal_time)
        
        period_data = df.iloc[start_idx:end_idx+1]
        
        if len(period_data) < 2:
            continue
        
        period_prices = period_data['close'].values
        period_duration = len(period_data) - 1  # Actual periods in this cycle
        
        if signal_type == 1:  # BUY signal - track max gain until SELL
            # Calculate gains relative to entry price
            price_changes = (period_prices - signal_price) / signal_price * 100
            
            max_gain_pct = np.max(price_changes)
            max_gain_idx = np.argmax(price_changes)
            max_gain_price = period_prices[max_gain_idx]
            
            # Final return at SELL
            final_return_pct = (next_signal_price - signal_price) / signal_price * 100
            
            signal_results.append({
                'signal_type': 'BUY',
                'entry_time': signal_time,
                'exit_time': next_signal_time,
                'entry_price': signal_price,
                'exit_price': next_signal_price,
                'extreme_price': max_gain_price,
                'max_gain_pct': max_gain_pct,
                'max_drop_pct': None,  # Not applicable for BUY signals
                'final_return_pct': final_return_pct,
                'duration_to_extreme': max_gain_idx,
                'holding_period_duration': period_duration,  # Actual holding period
                'waiting_period_duration': None,  # Not applicable for BUY signals
                'macd_value': signal['macd'],
                'signal_value': signal['signal'],
                'histogram_value': signal['histogram']
            })
            
        elif signal_type == -1:  # SELL signal - track max drop until next BUY
            # Calculate drops relative to exit price
            price_changes = (period_prices - signal_price) / signal_price * 100
            
            max_drop_pct = abs(np.min(price_changes))  # How much further it dropped
            max_drop_idx = np.argmin(price_changes)
            max_drop_price = period_prices[max_drop_idx]
            
            # Opportunity cost - how much you saved by selling
            opportunity_saved_pct = (signal_price - next_signal_price) / signal_price * 100
            
            signal_results.append({
                'signal_type': 'SELL',
                'entry_time': signal_time,
                'exit_time': next_signal_time,
                'entry_price': signal_price,
                'exit_price': next_signal_price,
                'extreme_price': max_drop_price,
                'max_gain_pct': None,  # Not applicable for SELL signals
                'max_drop_pct': max_drop_pct,
                'final_return_pct': opportunity_saved_pct,  # How much you saved by selling
                'duration_to_extreme': max_drop_idx,
                'holding_period_duration': None,  # Not applicable for SELL signals
                'waiting_period_duration': period_duration,  # Actual waiting period
                'macd_value': signal['macd'],
                'signal_value': signal['signal'],
                'histogram_value': signal['histogram']
            })
    
    print(f"   Valid BUY→SELL periods: {len([s for s in signal_results if s['signal_type'] == 'BUY'])}")
    print(f"   Valid SELL→BUY periods: {len([s for s in signal_results if s['signal_type'] == 'SELL'])}")
    print(f"   Total analysis periods: {len(signal_results)}")
    
    return signal_results

def calculate_macd_exact(data, fast_period=12, slow_period=26, signal_period=9):
    """Calculate MACD with exact same logic as original"""
    df = data.copy()
    
    df['ema_fast'] = df['close'].ewm(span=fast_period).mean()
    df['ema_slow'] = df['close'].ewm(span=slow_period).mean()
    df['macd'] = df['ema_fast'] - df['ema_slow']
    df['signal'] = df['macd'].ewm(span=signal_period).mean()
    df['histogram'] = df['macd'] - df['signal']
    
    return df

def fetch_bitcoin_data_exact(timeframe='1d', days=1825):
    """Fetch Bitcoin data with improved error handling and retry logic"""
    max_retries = 3
    retry_delay = 1  # Start with 1 second delay
    
    for attempt in range(max_retries):
        try:
            # Create fresh exchange instance for each attempt
            exchange = ccxt.binance({
                'rateLimit': 1200,  # Respect rate limits
                'enableRateLimit': True,
            })
            
            print(f"   Fetching {days} days of BTC/USDT data for {timeframe}... (Attempt {attempt + 1}/{max_retries})")
            
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            since = int(start_time.timestamp() * 1000)
            
            all_ohlcv = []
            current_since = since
            
            # Use same chunking logic as original
            chunk_days = 30
            if timeframe == '1d':
                chunk_days = 365
            elif timeframe == '1w':
                chunk_days = 730
            
            # Add initial delay before starting requests
            if attempt > 0:
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
            
            while current_since < int(end_time.timestamp() * 1000):
                try:
                    ohlcv_chunk = exchange.fetch_ohlcv('BTC/USDT', timeframe, since=current_since, limit=1000)
                    if not ohlcv_chunk:
                        break
                    all_ohlcv.extend(ohlcv_chunk)
                    current_since = ohlcv_chunk[-1][0] + 1
                    time.sleep(0.1)  # Increased delay between chunks
                except Exception as chunk_error:
                    print(f"   Error fetching chunk: {chunk_error}")
                    if "rate limit" in str(chunk_error).lower():
                        print(f"   Rate limit hit, waiting {retry_delay * 2} seconds...")
                        time.sleep(retry_delay * 2)
                        continue
                    break
            
            if not all_ohlcv:
                if attempt < max_retries - 1:
                    print(f"   No data retrieved, retrying in {retry_delay * (2 ** attempt)} seconds...")
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                else:
                    print(f"   No data available after {max_retries} attempts")
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
            
            print(f"   Successfully fetched {len(df)} data points")
            return df
            
        except Exception as e:
            print(f"   Error fetching data (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                print(f"   Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                print(f"   Failed to fetch data after {max_retries} attempts")
                return None
    
    return None

def analyze_timeframe_complete(timeframe, fast, slow, signal):
    """Analyze a specific timeframe with given parameters"""
    
    print(f"\n📊 ANALYZING {timeframe.upper()} TIMEFRAME")
    print("="*60)
    print(f"   Parameters: Fast={fast}, Slow={slow}, Signal={signal}")
    print(f"   Analysis: Actual signal-to-signal periods (no lookforward limit)")
    
    # Add small delay before API call
    time.sleep(1)
    
    # Fetch data with retries
    try:
        data = fetch_bitcoin_data_exact(timeframe, days=1825)
        
        if data is None:
            print(f"   ❌ Failed to fetch data for {timeframe}")
            return None
            
        if len(data) < 100:
            print(f"   ❌ Insufficient data for {timeframe} (only {len(data)} points)")
            return None
            
        print(f"   ✅ Data: {len(data)} points covering {(data.index[-1] - data.index[0]).days} days")
        
        # Calculate MACD
        macd_data = calculate_macd_exact(data, fast, slow, signal)
        
        # Analyze signals
        print(f"   🔍 Analyzing signals...")
        signal_results = analyze_signal_max_gains_complete(macd_data)
        
        if not signal_results:
            print(f"   ❌ No valid signal periods found for {timeframe}")
            return None
        
        # Separate BUY and SELL signals
        buy_signals = [s for s in signal_results if s['signal_type'] == 'BUY']
        sell_signals = [s for s in signal_results if s['signal_type'] == 'SELL']
        
        results = {
            'timeframe': timeframe,
            'parameters': {'fast': fast, 'slow': slow, 'signal': signal},
            'analysis_method': 'actual_signal_periods',
            'total_signals': len(signal_results),
            'buy_signals_count': len(buy_signals),
            'sell_signals_count': len(sell_signals),
            'expected_trades': len(buy_signals),  # Number of BUY→SELL pairs
            'valid_buy_signals': len(buy_signals),
            'valid_sell_signals': len(sell_signals)
        }
        
        # BUY signal statistics (holding periods)
        if buy_signals:
            buy_gains = [s['max_gain_pct'] for s in buy_signals]
            buy_returns = [s['final_return_pct'] for s in buy_signals]
            buy_durations = [s['holding_period_duration'] for s in buy_signals if s['holding_period_duration'] is not None]
            
            results['buy_stats'] = {
                'avg_max_gain': np.mean(buy_gains),
                'median_max_gain': np.median(buy_gains),
                'best_max_gain': np.max(buy_gains),
                'worst_max_gain': np.min(buy_gains),
                'avg_final_return': np.mean(buy_returns),
                'best_final_return': np.max(buy_returns),
                'worst_final_return': np.min(buy_returns),
                'positive_signals': len([g for g in buy_returns if g > 0]),
                'positive_rate': (len([g for g in buy_returns if g > 0]) / len(buy_returns)) * 100,
                'avg_holding_duration': np.mean(buy_durations) if buy_durations else 0,
                'median_holding_duration': np.median(buy_durations) if buy_durations else 0
            }
        
        # SELL signal statistics (waiting periods)
        if sell_signals:
            sell_drops = [s['max_drop_pct'] for s in sell_signals]
            sell_savings = [s['final_return_pct'] for s in sell_signals]  # Opportunity saved
            sell_durations = [s['waiting_period_duration'] for s in sell_signals if s['waiting_period_duration'] is not None]
            
            results['sell_stats'] = {
                'avg_max_drop': np.mean(sell_drops),
                'median_max_drop': np.median(sell_drops),
                'best_max_drop': np.max(sell_drops),
                'worst_max_drop': np.min(sell_drops),
                'avg_opportunity_saved': np.mean(sell_savings),
                'best_opportunity_saved': np.max(sell_savings),
                'worst_opportunity_saved': np.min(sell_savings),
                'positive_signals': len([d for d in sell_savings if d > 0]),  # Good sell decisions
                'positive_rate': (len([d for d in sell_savings if d > 0]) / len(sell_savings)) * 100,
                'avg_waiting_duration': np.mean(sell_durations) if sell_durations else 0,
                'median_waiting_duration': np.median(sell_durations) if sell_durations else 0
            }
        
        # Save detailed results
        try:
            df_signals = pd.DataFrame(signal_results)
            df_signals.to_csv(f'complete_max_analysis_{timeframe}.csv', index=False)
        except Exception as save_error:
            print(f"   ⚠️  Warning: Could not save CSV file: {save_error}")
        
        return results
        
    except Exception as e:
        print(f"   ❌ Error in timeframe analysis: {e}")
        return None

def print_timeframe_results(results):
    """Print formatted results for a timeframe"""
    if not results:
        return
    
    print(f"\n   📈 SIGNAL ANALYSIS RESULTS:")
    
    if 'buy_stats' in results:
        bs = results['buy_stats']
        print(f"   🟢 BUY SIGNALS ({results['valid_buy_signals']} analyzed) - Holding Periods:")
        print(f"      Max gain potential: {bs['avg_max_gain']:.2f}% avg, {bs['best_max_gain']:.2f}% best")
        print(f"      Actual returns: {bs['avg_final_return']:.2f}% avg, {bs['best_final_return']:.2f}% best")
        print(f"      Profitable trades: {bs['positive_signals']}/{results['valid_buy_signals']} ({bs['positive_rate']:.1f}%)")
        print(f"      Average holding time: {bs['avg_holding_duration']:.1f} periods")
    
    if 'sell_stats' in results:
        ss = results['sell_stats']
        print(f"   🔴 SELL SIGNALS ({results['valid_sell_signals']} analyzed) - Waiting Periods:")
        print(f"      Price drops after sell: {ss['avg_max_drop']:.2f}% avg, {ss['best_max_drop']:.2f}% max")
        print(f"      Opportunity saved: {ss['avg_opportunity_saved']:.2f}% avg, {ss['best_opportunity_saved']:.2f}% best")
        print(f"      Good sell decisions: {ss['positive_signals']}/{results['valid_sell_signals']} ({ss['positive_rate']:.1f}%)")
        print(f"      Average waiting time: {ss['avg_waiting_duration']:.1f} periods")

def run_complete_analysis():
    """Run complete analysis for all timeframes"""
    print("🚀 COMPLETE MACD SIGNAL ANALYSIS")
    print("="*70)
    print("BUY signals → Track max gain during holding period (BUY to SELL)")
    print("SELL signals → Track max drop during waiting period (SELL to next BUY)")
    print("Shows both potential and actual performance of each signal type")
    print()
    
    # Timeframe configurations based on your optimization results
    timeframe_configs = {
        '4h': {'fast': 6, 'slow': 27, 'signal': 13},   # No lookforward - use actual periods
        '8h': {'fast': 13, 'slow': 23, 'signal': 14},  # No lookforward - use actual periods
        '1d': {'fast': 19, 'slow': 22, 'signal': 9},   # No lookforward - use actual periods
        '1w': {'fast': 6, 'slow': 20, 'signal': 6}     # No lookforward - use actual periods
    }
    
    all_results = []
    total_timeframes = len(timeframe_configs)
    current_timeframe = 0
    
    for timeframe, config in timeframe_configs.items():
        current_timeframe += 1
        
        try:
            results = analyze_timeframe_complete(
                timeframe, 
                config['fast'], 
                config['slow'], 
                config['signal']
            )
            
            if results:
                all_results.append(results)
                print_timeframe_results(results)
                print(f"   💾 Saved to 'complete_max_analysis_{timeframe}.csv'")
            
            # Add delay between timeframe analyses (except for the last one)
            if current_timeframe < total_timeframes:
                print(f"   ⏳ Waiting 5 seconds before next timeframe analysis...")
                time.sleep(5)
        
        except Exception as e:
            print(f"   ❌ Error analyzing {timeframe}: {e}")
            # Still add delay even on error to prevent overwhelming API
            if current_timeframe < total_timeframes:
                print(f"   ⏳ Waiting 3 seconds before next timeframe analysis...")
                time.sleep(3)
            continue
    
    # Create summary comparison
    if all_results:
        print(f"\n📊 SIGNAL ANALYSIS SUMMARY COMPARISON")
        print("="*120)
        print(f"{'Timeframe':<10} {'BuySignals':<11} {'BuyWinRate':<11} {'AvgBuyGain':<12} {'SellSignals':<12} {'SellWinRate':<12} {'AvgSellDrop':<12}")
        print("-"*120)
        
        for result in all_results:
            buy_win_rate = result.get('buy_stats', {}).get('positive_rate', 0)
            buy_avg_gain = result.get('buy_stats', {}).get('avg_max_gain', 0)
            sell_win_rate = result.get('sell_stats', {}).get('positive_rate', 0)
            sell_avg_drop = result.get('sell_stats', {}).get('avg_max_drop', 0)
            
            print(f"{result['timeframe']:<10} {result['valid_buy_signals']:<11} {buy_win_rate:<11.1f} "
                  f"{buy_avg_gain:<12.2f} {result['valid_sell_signals']:<12} {sell_win_rate:<12.1f} "
                  f"{sell_avg_drop:<12.2f}")
        
        print("\n✅ Signal analysis complete!")
        print("\nFiles created:")
        for result in all_results:
            print(f"📋 complete_max_analysis_{result['timeframe']}.csv")
    else:
        print("\n❌ No successful analyses completed. Please check your network connection and try again.")
        print("\nTroubleshooting tips:")
        print("- Check your internet connection")
        print("- Ensure you're not behind a firewall blocking API requests")
        print("- Try running the script again after a few minutes")
        print("- Consider using a VPN if you're in a restricted region")

if __name__ == "__main__":
    run_complete_analysis() 