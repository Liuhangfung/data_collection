import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
from functools import partial
warnings.filterwarnings('ignore')

def _test_parameter_combination_standalone(args):
    """
    Standalone function to test a single parameter combination (for multiprocessing)
    
    Args:
        args: Tuple of (data, fast, slow, signal)
    
    Returns:
        Dictionary with results or None if failed
    """
    data, fast, slow, signal = args
    
    # Skip invalid combinations
    if fast >= slow:
        return None
    
    try:
        # Calculate EMAs
        df = data.copy()
        df['ema_fast'] = df['close'].ewm(span=fast).mean()
        df['ema_slow'] = df['close'].ewm(span=slow).mean()
        
        # Calculate MACD line
        df['macd'] = df['ema_fast'] - df['ema_slow']
        
        # Calculate Signal line
        df['signal'] = df['macd'].ewm(span=signal).mean()
        
        # Calculate Histogram
        df['histogram'] = df['macd'] - df['signal']
        
        # Generate signals
        df['signal_type'] = 0
        df['position'] = 0
        
        for i in range(1, len(df)):
            # Buy signal: MACD crosses above Signal line
            if df['macd'].iloc[i] > df['signal'].iloc[i] and df['macd'].iloc[i-1] <= df['signal'].iloc[i-1]:
                df['signal_type'].iloc[i] = 1
                df['position'].iloc[i] = 1
            # Sell signal: MACD crosses below Signal line
            elif df['macd'].iloc[i] < df['signal'].iloc[i] and df['macd'].iloc[i-1] >= df['signal'].iloc[i-1]:
                df['signal_type'].iloc[i] = -1
                df['position'].iloc[i] = 0
            # Hold current position
            else:
                df['position'].iloc[i] = df['position'].iloc[i-1]
        
        # Backtest
        initial_capital = 10000
        capital = initial_capital
        position = 0
        entry_price = 0
        trades = []
        
        for i in range(len(df)):
            current_price = df['close'].iloc[i]
            signal_type = df['signal_type'].iloc[i]
            
            # Buy signal
            if signal_type == 1 and position == 0:
                position = capital / current_price
                entry_price = current_price
                capital = 0
                trades.append({'type': 'BUY', 'price': current_price})
            
            # Sell signal
            elif signal_type == -1 and position > 0:
                capital = position * current_price
                exit_price = current_price
                profit = (exit_price - entry_price) * position
                trades.append({'type': 'SELL', 'price': current_price, 'profit': profit})
                position = 0
                entry_price = 0
        
        # Handle open position at the end
        if position > 0:
            final_value = position * df['close'].iloc[-1]
            capital = final_value
        
        # Calculate metrics
        total_return = (capital - initial_capital) / initial_capital * 100
        profitable_trades = [t for t in trades if t.get('profit', 0) > 0]
        total_trades = len([t for t in trades if t['type'] == 'SELL'])
        win_rate = len(profitable_trades) / total_trades * 100 if total_trades > 0 else 0
        
        return {
            'fast_period': fast,
            'slow_period': slow,
            'signal_period': signal,
            'total_return': total_return,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'final_capital': capital
        }
        
    except Exception as e:
        return None

class MACDBacktester:
    def __init__(self, exchange_name='binance', symbol='BTC/USDT', timeframe='1h'):
        """
        Initialize the MACD Backtester
        
        Args:
            exchange_name: CCXT exchange name (default: 'binance')
            symbol: Trading pair symbol (default: 'BTC/USDT')
            timeframe: Timeframe for data (default: '1h')
        """
        self.exchange = getattr(ccxt, exchange_name)()
        self.symbol = symbol
        self.timeframe = timeframe
        self.data = None
        
    def fetch_bitcoin_data(self, days=365):
        """
        Fetch Bitcoin OHLCV data from exchange
        
        Args:
            days: Number of days of historical data to fetch
        """
        try:
            print(f"Fetching {days} days of {self.symbol} data from {self.exchange.id}...")
            
            # Calculate timestamp for historical data
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            since = int(start_time.timestamp() * 1000)
            
            # Fetch data in chunks to avoid API limits
            all_ohlcv = []
            current_since = since
            
            # Determine chunk size based on timeframe
            chunk_days = 30  # Fetch 30 days at a time
            if self.timeframe == '1d':
                chunk_days = 365  # For daily data, can fetch more
            elif self.timeframe == '1w':
                chunk_days = 730  # For weekly data, can fetch even more
            
            total_chunks = max(1, days // chunk_days)
            chunk_count = 0
            
            while current_since < int(end_time.timestamp() * 1000):
                try:
                    # Fetch chunk of data
                    chunk_end = min(current_since + (chunk_days * 24 * 60 * 60 * 1000), int(end_time.timestamp() * 1000))
                    
                    # Fetch OHLCV data for this chunk
                    ohlcv_chunk = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, since=current_since, limit=1000)
                    
                    if not ohlcv_chunk:
                        break
                    
                    all_ohlcv.extend(ohlcv_chunk)
                    
                    # Update progress
                    chunk_count += 1
                    progress = min(100, (chunk_count / total_chunks) * 100)
                    print(f"Progress: {progress:.1f}% - Fetched {len(all_ohlcv)} data points so far...")
                    
                    # Update since for next chunk
                    current_since = ohlcv_chunk[-1][0] + 1
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.05)  # Reduced delay for faster fetching
                    
                except Exception as chunk_error:
                    print(f"Error fetching chunk: {chunk_error}")
                    break
            
            if not all_ohlcv:
                print("No data fetched. Please check your internet connection and try again.")
                return None
            
            # Remove duplicates and sort
            unique_ohlcv = []
            seen_timestamps = set()
            for candle in all_ohlcv:
                if candle[0] not in seen_timestamps:
                    unique_ohlcv.append(candle)
                    seen_timestamps.add(candle[0])
            
            # Sort by timestamp
            unique_ohlcv.sort(key=lambda x: x[0])
            
            # Convert to DataFrame
            df = pd.DataFrame(unique_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            self.data = df
            print(f"Successfully fetched {len(df)} data points")
            print(f"Data range: {df.index[0]} to {df.index[-1]}")
            
            # Calculate actual days covered
            actual_days = (df.index[-1] - df.index[0]).days
            print(f"Actual period covered: {actual_days} days")
            
            return df
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            print("Trying to fetch maximum available data...")
            
            # Fallback: try to fetch without since parameter
            try:
                ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=1000)
                if ohlcv:
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    self.data = df
                    print(f"Fallback: fetched {len(df)} data points")
                    print(f"Data range: {df.index[0]} to {df.index[-1]}")
                    return df
            except Exception as fallback_error:
                print(f"Fallback also failed: {fallback_error}")
                return None
    
    def calculate_macd(self, data, fast_period=12, slow_period=26, signal_period=9):
        """
        Calculate MACD indicator
        
        Args:
            data: DataFrame with price data
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line EMA period (default: 9)
        
        Returns:
            DataFrame with MACD components
        """
        df = data.copy()
        
        # Calculate EMAs
        df['ema_fast'] = df['close'].ewm(span=fast_period).mean()
        df['ema_slow'] = df['close'].ewm(span=slow_period).mean()
        
        # Calculate MACD line
        df['macd'] = df['ema_fast'] - df['ema_slow']
        
        # Calculate Signal line
        df['signal'] = df['macd'].ewm(span=signal_period).mean()
        
        # Calculate Histogram
        df['histogram'] = df['macd'] - df['signal']
        
        return df
    
    def generate_signals(self, data_with_macd):
        """
        Generate buy/sell signals based on MACD crossovers
        
        Args:
            data_with_macd: DataFrame with MACD indicators
        
        Returns:
            DataFrame with trading signals
        """
        df = data_with_macd.copy()
        
        # Initialize signals
        df['signal_type'] = 0  # 0: Hold, 1: Buy, -1: Sell
        df['position'] = 0     # Track current position
        
        # Generate signals based on MACD crossovers
        for i in range(1, len(df)):
            # Buy signal: MACD crosses above Signal line
            if df['macd'].iloc[i] > df['signal'].iloc[i] and df['macd'].iloc[i-1] <= df['signal'].iloc[i-1]:
                df['signal_type'].iloc[i] = 1  # Buy
                df['position'].iloc[i] = 1
            
            # Sell signal: MACD crosses below Signal line
            elif df['macd'].iloc[i] < df['signal'].iloc[i] and df['macd'].iloc[i-1] >= df['signal'].iloc[i-1]:
                df['signal_type'].iloc[i] = -1  # Sell
                df['position'].iloc[i] = 0
            
            # Hold current position
            else:
                df['position'].iloc[i] = df['position'].iloc[i-1]
        
        return df
    
    def backtest_strategy(self, data_with_signals, initial_capital=10000):
        """
        Backtest the MACD strategy
        
        Args:
            data_with_signals: DataFrame with trading signals
            initial_capital: Starting capital (default: 10000)
        
        Returns:
            Dictionary with backtest results
        """
        df = data_with_signals.copy()
        
        # Initialize tracking variables
        capital = initial_capital
        position = 0
        entry_price = 0
        trades = []
        portfolio_value = []
        
        for i in range(len(df)):
            current_price = df['close'].iloc[i]
            signal = df['signal_type'].iloc[i]
            
            # Buy signal
            if signal == 1 and position == 0:
                position = capital / current_price
                entry_price = current_price
                capital = 0
                trades.append({
                    'type': 'BUY',
                    'timestamp': df.index[i],
                    'price': current_price,
                    'quantity': position
                })
            
            # Sell signal
            elif signal == -1 and position > 0:
                capital = position * current_price
                exit_price = current_price
                profit = (exit_price - entry_price) * position
                
                trades.append({
                    'type': 'SELL',
                    'timestamp': df.index[i],
                    'price': current_price,
                    'quantity': position,
                    'profit': profit,
                    'return_pct': (exit_price - entry_price) / entry_price * 100
                })
                
                position = 0
                entry_price = 0
            
            # Calculate current portfolio value
            if position > 0:
                portfolio_value.append(position * current_price)
            else:
                portfolio_value.append(capital)
        
        # Handle open position at the end
        if position > 0:
            final_value = position * df['close'].iloc[-1]
            capital = final_value
        
        # Calculate performance metrics
        total_return = (capital - initial_capital) / initial_capital * 100
        buy_and_hold_return = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100
        
        # Calculate win rate
        profitable_trades = [t for t in trades if t.get('profit', 0) > 0]
        total_trades = len([t for t in trades if t['type'] == 'SELL'])
        win_rate = len(profitable_trades) / total_trades * 100 if total_trades > 0 else 0
        
        return {
            'final_capital': capital,
            'total_return': total_return,
            'buy_and_hold_return': buy_and_hold_return,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'trades': trades,
            'portfolio_value': portfolio_value
        }
    
    def _test_single_parameter_combination(self, data, fast, slow, signal):
        """
        Test a single parameter combination (for multithreading)
        
        Args:
            data: Price data DataFrame
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal EMA period
        
        Returns:
            Dictionary with results or None if failed
        """
        # Skip invalid combinations
        if fast >= slow:
            return None
        
        try:
            # Calculate MACD with current parameters
            macd_data = self.calculate_macd(data, fast, slow, signal)
            
            # Generate signals
            signals_data = self.generate_signals(macd_data)
            
            # Backtest
            backtest_result = self.backtest_strategy(signals_data)
            
            # Return results
            return {
                'fast_period': fast,
                'slow_period': slow,
                'signal_period': signal,
                'total_return': backtest_result['total_return'],
                'win_rate': backtest_result['win_rate'],
                'total_trades': backtest_result['total_trades'],
                'final_capital': backtest_result['final_capital']
            }
            
        except Exception as e:
            return None

    def optimize_parameters(self, data, fast_range=(5, 20), slow_range=(20, 35), signal_range=(5, 15), max_workers=4):
        """
        Optimize MACD parameters by testing different combinations using multiprocessing
        
        Args:
            data: Price data DataFrame
            fast_range: Range for fast EMA period (min, max)
            slow_range: Range for slow EMA period (min, max)
            signal_range: Range for signal EMA period (min, max)
            max_workers: Number of processes to use (default: 4)
        
        Returns:
            DataFrame with optimization results
        """
        print("Optimizing MACD parameters with multiprocessing...")
        
        # Generate all parameter combinations
        parameter_combinations = []
        for fast in range(fast_range[0], fast_range[1]):
            for slow in range(slow_range[0], slow_range[1]):
                for signal in range(signal_range[0], signal_range[1]):
                    if fast < slow:  # Only include valid combinations
                        parameter_combinations.append((fast, slow, signal))
        
        total_combinations = len(parameter_combinations)
        print(f"Testing {total_combinations} parameter combinations using {max_workers} processes...")
        
        results = []
        completed = 0
        
        # Use ProcessPoolExecutor for parallel processing
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            task_args = [(data, fast, slow, signal) for fast, slow, signal in parameter_combinations]
            future_to_params = {
                executor.submit(_test_parameter_combination_standalone, args): args[1:4]
                for args in task_args
            }
            
            # Process completed tasks
            for future in as_completed(future_to_params):
                completed += 1
                result = future.result()
                
                if result is not None:
                    results.append(result)
                
                # Progress reporting
                if completed % 50 == 0 or completed == total_combinations:
                    progress = (completed / total_combinations) * 100
                    print(f"Progress: {progress:.1f}% ({completed}/{total_combinations}) - Found {len(results)} valid results")
        
        # Convert to DataFrame and sort by total return
        results_df = pd.DataFrame(results)
        if len(results_df) > 0:
            results_df = results_df.sort_values('total_return', ascending=False)
        
        print(f"\nOptimization complete! Tested {len(results_df)} valid combinations.")
        
        return results_df
    
    def plot_results(self, data_with_signals, backtest_results):
        """
        Plot MACD indicators and trading signals
        
        Args:
            data_with_signals: DataFrame with MACD and signals
            backtest_results: Backtest results dictionary
        """
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))
        
        # Plot 1: Price and Buy/Sell signals
        ax1.plot(data_with_signals.index, data_with_signals['close'], label='BTC Price', linewidth=1)
        
        # Mark buy/sell points
        buy_signals = data_with_signals[data_with_signals['signal_type'] == 1]
        sell_signals = data_with_signals[data_with_signals['signal_type'] == -1]
        
        ax1.scatter(buy_signals.index, buy_signals['close'], color='green', marker='^', s=100, label='Buy Signal')
        ax1.scatter(sell_signals.index, sell_signals['close'], color='red', marker='v', s=100, label='Sell Signal')
        
        ax1.set_title('Bitcoin Price with MACD Trading Signals')
        ax1.set_ylabel('Price (USDT)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: MACD and Signal lines
        ax2.plot(data_with_signals.index, data_with_signals['macd'], label='MACD', linewidth=1)
        ax2.plot(data_with_signals.index, data_with_signals['signal'], label='Signal', linewidth=1)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax2.set_title('MACD and Signal Lines')
        ax2.set_ylabel('MACD Value')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: MACD Histogram
        ax3.bar(data_with_signals.index, data_with_signals['histogram'], 
                color=np.where(data_with_signals['histogram'] >= 0, 'green', 'red'), alpha=0.7)
        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax3.set_title('MACD Histogram')
        ax3.set_ylabel('Histogram')
        ax3.set_xlabel('Date')
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def print_summary(self, results, best_params=None):
        """
        Print a summary of the backtest results
        
        Args:
            results: Backtest results dictionary
            best_params: Best parameters dictionary (optional)
        """
        print("\n" + "="*60)
        print("MACD BACKTEST SUMMARY")
        print("="*60)
        
        if best_params is not None:
            print(f"Best Parameters:")
            print(f"  Fast EMA: {best_params['fast_period']}")
            print(f"  Slow EMA: {best_params['slow_period']}")
            print(f"  Signal EMA: {best_params['signal_period']}")
            print()
        
        print(f"Initial Capital: ${10000:,.2f}")
        print(f"Final Capital: ${results['final_capital']:,.2f}")
        print(f"Total Return: {results['total_return']:.2f}%")
        print(f"Buy & Hold Return: {results['buy_and_hold_return']:.2f}%")
        print(f"Win Rate: {results['win_rate']:.2f}%")
        print(f"Total Trades: {results['total_trades']}")
        
        if results['total_trades'] > 0:
            profitable_trades = [t for t in results['trades'] if t.get('profit', 0) > 0]
            avg_profit = np.mean([t['profit'] for t in profitable_trades]) if profitable_trades else 0
            print(f"Average Profit per Winning Trade: ${avg_profit:.2f}")
        
        print("="*60)

# Main execution function
def main():
    """
    Main function to run MACD backtesting across multiple timeframes
    """
    print("🚀 MACD BACKTESTING ACROSS MULTIPLE TIMEFRAMES")
    print("="*70)
    
    # Test multiple timeframes - 5 timeframes as requested
    timeframes = ['4h', '8h', '1d', '1w', '1M']
    all_results = {}
    all_transaction_records = {}
    
    print(f"Will test timeframes: {timeframes}")
    print("Note: 4h = 4-hour, 8h = 8-hour, 1d = daily, 1w = weekly, 1M = monthly")
    
    for timeframe in timeframes:
        try:
            print(f"\n📊 TESTING TIMEFRAME: {timeframe}")
            print("="*50)
            
            # Initialize backtester for this timeframe
            backtester = MACDBacktester(exchange_name='binance', symbol='BTC/USDT', timeframe=timeframe)
            
            # Adjust days based on timeframe for comparable data
            if timeframe == '4h':
                days = 1825  # 5 years
                expected_points = 1825 * 6  # 6 data points per day (24h/4h)
            elif timeframe == '8h':
                days = 1825  # 5 years
                expected_points = 1825 * 3  # 3 data points per day (24h/8h)
            elif timeframe == '1d':
                days = 1825  # 5 years
                expected_points = 1825  # 1 data point per day
            elif timeframe == '1w':
                days = 1825  # 5 years
                expected_points = 1825 // 7  # 1 data point per week
            elif timeframe == '1M':
                days = 1825  # 5 years
                expected_points = 1825 // 30  # 1 data point per month
            
            print(f"Fetching {days} days of {timeframe} data...")
            print(f"Expected approximately {expected_points} data points...")
            
            # Fetch data
            data = backtester.fetch_bitcoin_data(days=days)
            
            if data is None:
                print(f"❌ Failed to fetch data for {timeframe}. Data is None. Skipping...")
                continue
            elif len(data) < 50:
                print(f"❌ Insufficient data for {timeframe}. Got {len(data)} data points, need at least 50. Skipping...")
                continue
            else:
                print(f"✅ Successfully fetched {len(data)} data points for {timeframe}")
            
            actual_days = (data.index[-1] - data.index[0]).days
            print(f"✅ Got {len(data)} data points covering {actual_days} days")
            
            # Comprehensive parameter optimization
            print(f"Optimizing parameters for {timeframe}...")
            
            # Calculate number of parameter combinations
            fast_range = (5, 20)
            slow_range = (20, 35)
            signal_range = (5, 15)
            
            # Count valid combinations where fast < slow
            valid_combinations = sum(1 for f in range(fast_range[0], fast_range[1]) 
                                   for s in range(slow_range[0], slow_range[1]) 
                                   for sig in range(signal_range[0], signal_range[1]) 
                                   if f < s)
            
            print(f"Testing {valid_combinations} parameter combinations...")
            print(f"  Fast EMA: {fast_range[0]}-{fast_range[1]-1} ({fast_range[1]-fast_range[0]} values)")
            print(f"  Slow EMA: {slow_range[0]}-{slow_range[1]-1} ({slow_range[1]-slow_range[0]} values)")
            print(f"  Signal EMA: {signal_range[0]}-{signal_range[1]-1} ({signal_range[1]-signal_range[0]} values)")
            print(f"  Estimated time: {valid_combinations/600:.1f}-{valid_combinations/300:.1f} minutes")
            
            # Use comprehensive parameter ranges for thorough testing
            optimization_results = backtester.optimize_parameters(
                data, 
                fast_range=fast_range,     # Comprehensive range: 15 values
                slow_range=slow_range,     # Comprehensive range: 15 values  
                signal_range=signal_range, # Comprehensive range: 10 values
                max_workers=6              # Use more workers for speed
            )
            
            if len(optimization_results) == 0:
                print(f"❌ No valid results for {timeframe}")
                continue
            
            # Get best parameters
            best_params = optimization_results.iloc[0]
            
            # Run backtest with best parameters
            best_macd_data = backtester.calculate_macd(
                data, 
                fast_period=best_params['fast_period'],
                slow_period=best_params['slow_period'],
                signal_period=best_params['signal_period']
            )
            
            best_signals_data = backtester.generate_signals(best_macd_data)
            best_backtest_results = backtester.backtest_strategy(best_signals_data)
            
            # Calculate buy and hold for comparison
            buy_hold_return = (data['close'].iloc[-1] - data['close'].iloc[0]) / data['close'].iloc[0] * 100
            
            # Store results
            all_results[timeframe] = {
                'timeframe': timeframe,
                'data_points': len(data),
                'actual_days': actual_days,
                'best_params': best_params,
                'backtest_results': best_backtest_results,
                'buy_hold_return': buy_hold_return,
                'total_return': best_backtest_results['total_return'],
                'win_rate': best_backtest_results['win_rate'],
                'total_trades': best_backtest_results['total_trades'],
                'final_capital': best_backtest_results['final_capital']
            }
            
            # Store detailed transaction records
            all_transaction_records[timeframe] = {
                'trades': best_backtest_results['trades'],
                'best_params': best_params,
                'performance': {
                    'total_return': best_backtest_results['total_return'],
                    'win_rate': best_backtest_results['win_rate'],
                    'total_trades': best_backtest_results['total_trades'],
                    'final_capital': best_backtest_results['final_capital']
                }
            }
            
            print(f"✅ {timeframe} analysis complete!")
            print(f"   Best Return: {best_backtest_results['total_return']:.2f}%")
            print(f"   Buy & Hold: {buy_hold_return:.2f}%")
            print(f"   Total Trades: {best_backtest_results['total_trades']}")
            print(f"   Win Rate: {best_backtest_results['win_rate']:.1f}%")
            
        except Exception as e:
            print(f"❌ Error processing {timeframe}: {str(e)}")
            print(f"   Skipping {timeframe} and continuing with next timeframe...")
            continue

    # Create comparison table
    print(f"\n📈 TIMEFRAME COMPARISON RESULTS")
    print("="*120)
    print(f"{'Timeframe':<10} {'Data Points':<12} {'Days':<8} {'Fast':<4} {'Slow':<4} {'Signal':<6} {'Return%':<8} {'B&H%':<8} {'Trades':<6} {'Win%':<6}")
    print("-"*120)
    
    for timeframe, results in all_results.items():
        bp = results['best_params']
        print(f"{timeframe:<10} {results['data_points']:<12} {results['actual_days']:<8} "
              f"{bp['fast_period']:<4.0f} {bp['slow_period']:<4.0f} {bp['signal_period']:<6.0f} "
              f"{results['total_return']:<8.2f} {results['buy_hold_return']:<8.2f} "
              f"{results['total_trades']:<6} {results['win_rate']:<6.1f}")
    
    print("-"*120)
    
    # Find best performing timeframe
    if all_results:
        best_timeframe = max(all_results.keys(), key=lambda x: all_results[x]['total_return'])
        print(f"\n🏆 BEST PERFORMING TIMEFRAME: {best_timeframe}")
        print(f"   Return: {all_results[best_timeframe]['total_return']:.2f}%")
        print(f"   Parameters: Fast={all_results[best_timeframe]['best_params']['fast_period']:.0f}, "
              f"Slow={all_results[best_timeframe]['best_params']['slow_period']:.0f}, "
              f"Signal={all_results[best_timeframe]['best_params']['signal_period']:.0f}")
        
        # Print detailed summary for best timeframe
        print(f"\n📊 DETAILED RESULTS FOR BEST TIMEFRAME ({best_timeframe}):")
        backtester.print_summary(
            all_results[best_timeframe]['backtest_results'], 
            all_results[best_timeframe]['best_params']
        )
        
        # Save results comparison
        comparison_df = pd.DataFrame([
            {
                'timeframe': tf,
                'data_points': results['data_points'],
                'actual_days': results['actual_days'],
                'fast_period': results['best_params']['fast_period'],
                'slow_period': results['best_params']['slow_period'],
                'signal_period': results['best_params']['signal_period'],
                'total_return': results['total_return'],
                'buy_hold_return': results['buy_hold_return'],
                'total_trades': results['total_trades'],
                'win_rate': results['win_rate'],
                'final_capital': results['final_capital']
            }
            for tf, results in all_results.items()
        ])
        
        comparison_df.to_csv('macd_timeframe_comparison.csv', index=False)
        print(f"\n💾 Results saved to 'macd_timeframe_comparison.csv'")
        
        # Save detailed transaction records for each timeframe
        print(f"\n💾 SAVING DETAILED TRANSACTION RECORDS...")
        for timeframe, transaction_data in all_transaction_records.items():
            if transaction_data['trades']:
                # Create detailed transaction DataFrame
                trades_list = []
                for trade in transaction_data['trades']:
                    trades_list.append({
                        'timestamp': trade['timestamp'],
                        'type': trade['type'],
                        'price': trade['price'],
                        'quantity': trade.get('quantity', 0),
                        'profit': trade.get('profit', 0),
                        'return_pct': trade.get('return_pct', 0)
                    })
                
                trades_df = pd.DataFrame(trades_list)
                filename = f'macd_transactions_{timeframe}.csv'
                trades_df.to_csv(filename, index=False)
                print(f"   📋 {timeframe} transactions saved to '{filename}' ({len(trades_df)} trades)")
        
        # Create summary report
        print(f"\n📄 CREATING SUMMARY REPORT...")
        with open('macd_summary_report.txt', 'w') as f:
            f.write("MACD BACKTESTING SUMMARY REPORT\n")
            f.write("="*50 + "\n\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Trading Pair: BTC/USDT\n")
            f.write(f"Exchange: Binance\n")
            f.write(f"Initial Capital: $10,000\n")
            f.write(f"Timeframes Tested: {', '.join(timeframes)}\n\n")
            
            f.write("BEST PARAMETERS FOR EACH TIMEFRAME:\n")
            f.write("-" * 50 + "\n")
            for timeframe, results in all_results.items():
                bp = results['best_params']
                f.write(f"{timeframe.upper()}: Fast={bp['fast_period']}, Slow={bp['slow_period']}, Signal={bp['signal_period']}\n")
                f.write(f"   Return: {results['total_return']:.2f}%\n")
                f.write(f"   Win Rate: {results['win_rate']:.1f}%\n")
                f.write(f"   Total Trades: {results['total_trades']}\n")
                f.write(f"   Final Capital: ${results['final_capital']:,.2f}\n\n")
            
            f.write(f"OVERALL BEST TIMEFRAME: {best_timeframe.upper()}\n")
            f.write(f"Best Return: {all_results[best_timeframe]['total_return']:.2f}%\n")
            f.write(f"Best Win Rate: {all_results[best_timeframe]['win_rate']:.1f}%\n")
        
        print(f"   📊 Summary report saved to 'macd_summary_report.txt'")
        
        # Optional: Plot best timeframe results
        try:
            print(f"\n📈 Generating chart for best timeframe ({best_timeframe})...")
            best_result = all_results[best_timeframe]
            
            # Recreate the backtester for best timeframe
            backtester = MACDBacktester(exchange_name='binance', symbol='BTC/USDT', timeframe=best_timeframe)
            data = backtester.fetch_bitcoin_data(days=1825)
            
            if data is not None:
                best_macd_data = backtester.calculate_macd(
                    data, 
                    fast_period=best_result['best_params']['fast_period'],
                    slow_period=best_result['best_params']['slow_period'],
                    signal_period=best_result['best_params']['signal_period']
                )
                
                best_signals_data = backtester.generate_signals(best_macd_data)
                best_backtest_results = backtester.backtest_strategy(best_signals_data)
                
                backtester.plot_results(best_signals_data, best_backtest_results)
                print("✅ Chart generated successfully!")
            
        except Exception as e:
            print(f"⚠️  Chart generation failed: {e}")
    
    else:
        print("❌ No valid results found for any timeframe")
    
    print("\n" + "="*70)
    print("MULTI-TIMEFRAME ANALYSIS COMPLETE")
    print("="*70)
    print("\nFILES CREATED:")
    print("📊 macd_timeframe_comparison.csv - Performance comparison")
    print("📋 macd_transactions_[timeframe].csv - Detailed trades for each timeframe")
    print("📄 macd_summary_report.txt - Complete analysis summary")
    print("="*70)

if __name__ == "__main__":
    main()
