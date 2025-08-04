#!/usr/bin/env python3
"""
Multi-Timeframe AI Trend Navigator Optimizer
Tests the strategy across different timeframes (4H, 8H, 1D, 1W, 1M) with optimized parameters
"""

import pandas as pd
import numpy as np
import requests
import os
import csv
from datetime import datetime, timedelta
from dotenv import load_dotenv
from ai_trend_navigator import AITrendNavigator
from concurrent.futures import ThreadPoolExecutor, as_completed
import itertools
import warnings
warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

class MultiTimeframeOptimizer:
    def __init__(self):
        self.api_key = os.getenv('FMP_API_KEY')
        self.timeframes = {
            '4H': {'interval': '4hour', 'days': 365 * 2},      # 2 years for 4H
            '8H': {'interval': '8hour', 'days': 365 * 2},      # 2 years for 8H  
            '1D': {'interval': '1day', 'days': 365 * 5},       # 5 years for 1D
            '1W': {'interval': '1week', 'days': 365 * 5},      # 5 years for 1W
            '1M': {'interval': '1month', 'days': 365 * 10}     # 10 years for 1M
        }
        
        # Default parameters for comparison
        self.default_parameters = {
            'numberOfClosestValues': 3,
            'smoothingPeriod': 50,
            'windowSize': 30,
            'maLen': 5
        }
        
        # Comprehensive parameter ranges for extensive testing
        self.parameter_ranges = {
            '4H': {
                'numberOfClosestValues': list(range(2, 26)),  # 2-25 (24 values)
                'smoothingPeriod': list(range(10, 201, 10)),  # 10-200 step 10 (20 values)
                'windowSize': list(range(10, 101, 5)),        # 10-100 step 5 (19 values)
                'maLen': list(range(2, 31))                   # 2-30 (29 values)
            },
            '8H': {
                'numberOfClosestValues': list(range(2, 26)),  # 2-25 (24 values)
                'smoothingPeriod': list(range(10, 181, 10)),  # 10-180 step 10 (18 values)
                'windowSize': list(range(8, 91, 4)),          # 8-90 step 4 (21 values)
                'maLen': list(range(2, 26))                   # 2-25 (24 values)
            },
            '1D': {
                'numberOfClosestValues': list(range(2, 21)),  # 2-20 (19 values)
                'smoothingPeriod': list(range(20, 151, 10)),  # 20-150 step 10 (14 values)
                'windowSize': list(range(15, 81, 5)),         # 15-80 step 5 (14 values)
                'maLen': list(range(3, 21))                   # 3-20 (18 values)
            },
            '1W': {
                'numberOfClosestValues': list(range(2, 21)),  # 2-20 (19 values)
                'smoothingPeriod': list(range(5, 101, 5)),    # 5-100 step 5 (20 values)
                'windowSize': list(range(5, 76, 3)),          # 5-75 step 3 (24 values)
                'maLen': list(range(2, 21))                   # 2-20 (19 values)
            },
            '1M': {
                'numberOfClosestValues': list(range(2, 16)),  # 2-15 (14 values)
                'smoothingPeriod': list(range(3, 61, 3)),     # 3-60 step 3 (20 values)
                'windowSize': list(range(3, 51, 2)),          # 3-50 step 2 (24 values)
                'maLen': list(range(2, 16))                   # 2-15 (14 values)
            }
        }
    
    def fetch_data_for_timeframe(self, timeframe):
        """Fetch data for specific timeframe"""
        if not self.api_key:
            print(f"❌ FMP API key not found for {timeframe}!")
            return None
            
        config = self.timeframes[timeframe]
        symbol = "BTCUSD"
        
        print(f"📊 Fetching {timeframe} data from FMP API...")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=config['days'])
        
        # FMP API uses different endpoints for different intervals
        if timeframe in ['4H', '8H']:
            # Use historical chart endpoint for intraday
            url = f"https://financialmodelingprep.com/api/v3/historical-chart/{config['interval']}/{symbol}"
        else:
            # Use historical price endpoint for daily and above
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
        
        params = {
            'apikey': self.api_key
        }
        
        if timeframe not in ['4H', '8H']:
            params['from'] = start_date.strftime('%Y-%m-%d')
            params['to'] = end_date.strftime('%Y-%m-%d')
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if timeframe in ['4H', '8H']:
                # For intraday data
                if not data:
                    print(f"❌ No data found for {timeframe}")
                    return None
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)
                
                # Filter by date range
                df = df[df['date'] >= start_date]
                
            else:
                # For daily+ data
                if 'historical' not in data:
                    print(f"❌ No historical data found for {timeframe}")
                    return None
                df = pd.DataFrame(data['historical'])
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)
            
            # Rename columns to match AITrendNavigator format
            df = df.rename(columns={
                'date': 'timestamp',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            })
            
            # Keep only required columns
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            print(f"✅ Fetched {len(df)} {timeframe} candles")
            print(f"📊 Date range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error fetching {timeframe} data: {e}")
            return None
    
    def optimize_parameters_for_timeframe(self, timeframe, max_workers=8):
        """Optimize parameters for specific timeframe"""
        print(f"\n🔍 OPTIMIZING PARAMETERS FOR {timeframe}")
        print("="*60)
        
        # Fetch data
        data = self.fetch_data_for_timeframe(timeframe)
        if data is None:
            return None
        
        # Get parameter ranges for this timeframe
        params = self.parameter_ranges[timeframe]
        
        # Generate all parameter combinations
        param_combinations = list(itertools.product(
            params['numberOfClosestValues'],
            params['smoothingPeriod'],
            params['windowSize'],
            params['maLen']
        ))
        
        print(f"🧮 Testing {len(param_combinations):,} parameter combinations for {timeframe}...")
        print(f"   📊 Parameter ranges:")
        print(f"      K: {min(params['numberOfClosestValues'])}-{max(params['numberOfClosestValues'])} ({len(params['numberOfClosestValues'])} values)")
        print(f"      Smoothing: {min(params['smoothingPeriod'])}-{max(params['smoothingPeriod'])} ({len(params['smoothingPeriod'])} values)")  
        print(f"      Window: {min(params['windowSize'])}-{max(params['windowSize'])} ({len(params['windowSize'])} values)")
        print(f"      MA Length: {min(params['maLen'])}-{max(params['maLen'])} ({len(params['maLen'])} values)")
        print(f"   ⚡ Using {max_workers} threads")
        
        # Estimate time (rough calculation: ~0.5 seconds per combination per thread - realistic estimate)
        estimated_seconds = (len(param_combinations) * 0.5) / max_workers
        estimated_minutes = estimated_seconds / 60
        estimated_hours = estimated_minutes / 60
        
        if estimated_hours > 1:
            print(f"   ⏱️  Estimated time: ~{estimated_hours:.1f} hours")
        elif estimated_minutes > 1:
            print(f"   ⏱️  Estimated time: ~{estimated_minutes:.0f} minutes")
        else:
            print(f"   ⏱️  Estimated time: ~{estimated_seconds:.0f} seconds")
        
        # Test parameters
        results = []
        
        def test_parameters(param_combo):
            k, smoothing, window, ma_len = param_combo
            
            try:
                # Skip invalid combinations
                if window < k or smoothing < 5 or ma_len < 2:
                    return None
                
                # Initialize navigator
                navigator = AITrendNavigator(
                    numberOfClosestValues=k,
                    smoothingPeriod=smoothing,
                    windowSize=window,
                    maLen=ma_len
                )
                
                # Calculate signals
                signals = navigator.calculate_trend_signals(data)
                
                # Skip if no signals generated
                if signals is None or len(signals) == 0:
                    return None
                
                # Calculate performance
                performance = self.calculate_performance(signals)
                
                # Skip if performance calculation failed
                if performance is None:
                    return None
                
                return {
                    'timeframe': timeframe,
                    'K': k,
                    'smoothing': smoothing,
                    'window': window,
                    'maLen': ma_len,
                    'total_return': performance['total_return'],
                    'annual_return': performance['annual_return'],
                    'win_rate': performance['win_rate'],
                    'max_drawdown': performance['max_drawdown'],
                    'sortino_ratio': performance['sortino_ratio'],
                    'trades': performance['trades'],
                    'profit_factor': performance['profit_factor']
                }
                
            except Exception as e:
                # print(f"Error with params K={k}, S={smoothing}, W={window}, MA={ma_len}: {e}")
                return None
        
        # Use multithreading with progress tracking
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_params = {executor.submit(test_parameters, params): params 
                              for params in param_combinations}
            
            completed = 0
            total = len(param_combinations)
            print(f"Progress: 0/{total} (0.00%)")
            
            for future in as_completed(future_to_params):
                result = future.result()
                if result:
                    results.append(result)
                
                completed += 1
                if completed % 100 == 0 or completed == total:
                    progress = (completed / total) * 100
                    print(f"Progress: {completed:,}/{total:,} ({progress:.1f}%)")
                    
                    # Show current best if we have results
                    if results:
                        current_best = max(results, key=lambda x: x['total_return'])
                        print(f"   Current best: {current_best['total_return']:.2f}% "
                              f"(K={current_best['K']}, smoothing={current_best['smoothing']}, "
                              f"window={current_best['window']}, maLen={current_best['maLen']})")
            
            print(f"✅ Completed testing {total} parameter combinations")
        
        if not results:
            print(f"❌ No valid results for {timeframe}")
            return None
        
        # Sort by total return
        results.sort(key=lambda x: x['total_return'], reverse=True)
        
        # Display top 10 results
        print(f"\n🏆 TOP 10 RESULTS FOR {timeframe}:")
        print("-" * 100)
        print(f"{'Rank':<5} {'K':<3} {'Smooth':<7} {'Window':<7} {'MA':<4} {'Total%':<8} {'Annual%':<8} {'Win%':<6} {'MaxDD%':<8} {'Sortino':<8} {'Trades':<7}")
        print("-" * 100)
        
        for i, result in enumerate(results[:10]):
            print(f"{i+1:<5} {result['K']:<3} {result['smoothing']:<7} {result['window']:<7} {result['maLen']:<4} "
                  f"{result['total_return']:<8.2f} {result['annual_return']:<8.2f} {result['win_rate']:<6.2f} "
                  f"{result['max_drawdown']:<8.2f} {result['sortino_ratio']:<8.4f} {result['trades']:<7}")
        
        # Test default parameters for comparison
        default_result = self.test_default_parameters(timeframe, data)
        
        # Show comparison
        if results and default_result:
            self.show_default_vs_optimized_comparison(timeframe, default_result, results[0])
        
        return results
    
    def test_default_parameters(self, timeframe, data):
        """Test default parameters for comparison"""
        print(f"\n📊 Testing DEFAULT parameters for {timeframe}...")
        
        try:
            # Initialize navigator with default parameters
            navigator = AITrendNavigator(**self.default_parameters)
            
            # Calculate signals
            signals = navigator.calculate_trend_signals(data)
            
            # Calculate performance
            performance = self.calculate_performance(signals)
            
            result = {
                'timeframe': timeframe,
                'K': self.default_parameters['numberOfClosestValues'],
                'smoothing': self.default_parameters['smoothingPeriod'],
                'window': self.default_parameters['windowSize'],
                'maLen': self.default_parameters['maLen'],
                'total_return': performance['total_return'],
                'annual_return': performance['annual_return'],
                'win_rate': performance['win_rate'],
                'max_drawdown': performance['max_drawdown'],
                'sortino_ratio': performance['sortino_ratio'],
                'trades': performance['trades'],
                'profit_factor': performance['profit_factor']
            }
            
            print(f"✅ Default parameters result: {result['total_return']:.2f}% return")
            return result
            
        except Exception as e:
            print(f"❌ Error testing default parameters: {e}")
            return None
    
    def show_default_vs_optimized_comparison(self, timeframe, default_result, best_result):
        """Show detailed comparison between default and optimized parameters"""
        print(f"\n🔥 DEFAULT vs OPTIMIZED COMPARISON FOR {timeframe}")
        print("="*80)
        
        # Parameters comparison
        print("📋 PARAMETERS:")
        print(f"{'Metric':<15} {'Default':<15} {'Optimized':<15} {'Improvement':<15}")
        print("-"*65)
        print(f"{'K':<15} {default_result['K']:<15} {best_result['K']:<15} {'+' if best_result['K'] > default_result['K'] else ''}{best_result['K'] - default_result['K']}")
        print(f"{'Smoothing':<15} {default_result['smoothing']:<15} {best_result['smoothing']:<15} {'+' if best_result['smoothing'] > default_result['smoothing'] else ''}{best_result['smoothing'] - default_result['smoothing']}")
        print(f"{'Window':<15} {default_result['window']:<15} {best_result['window']:<15} {'+' if best_result['window'] > default_result['window'] else ''}{best_result['window'] - default_result['window']}")
        print(f"{'MA Length':<15} {default_result['maLen']:<15} {best_result['maLen']:<15} {'+' if best_result['maLen'] > default_result['maLen'] else ''}{best_result['maLen'] - default_result['maLen']}")
        
        # Performance comparison
        print(f"\n📈 PERFORMANCE:")
        print(f"{'Metric':<15} {'Default':<15} {'Optimized':<15} {'Improvement':<15}")
        print("-"*65)
        
        return_improvement = best_result['total_return'] - default_result['total_return']
        annual_improvement = best_result['annual_return'] - default_result['annual_return']
        winrate_improvement = best_result['win_rate'] - default_result['win_rate']
        drawdown_improvement = best_result['max_drawdown'] - default_result['max_drawdown']  # negative is better
        sortino_improvement = best_result['sortino_ratio'] - default_result['sortino_ratio']
        
        print(f"{'Total Return':<15} {default_result['total_return']:>10.2f}% {best_result['total_return']:>10.2f}% {return_improvement:>+10.2f}%")
        print(f"{'Annual Return':<15} {default_result['annual_return']:>10.2f}% {best_result['annual_return']:>10.2f}% {annual_improvement:>+10.2f}%")
        print(f"{'Win Rate':<15} {default_result['win_rate']:>10.2f}% {best_result['win_rate']:>10.2f}% {winrate_improvement:>+10.2f}%")
        print(f"{'Max Drawdown':<15} {default_result['max_drawdown']:>10.2f}% {best_result['max_drawdown']:>10.2f}% {drawdown_improvement:>+10.2f}%")
        print(f"{'Sortino Ratio':<15} {default_result['sortino_ratio']:>10.4f} {best_result['sortino_ratio']:>10.4f} {sortino_improvement:>+10.4f}")
        print(f"{'Trades':<15} {default_result['trades']:>10} {best_result['trades']:>10} {best_result['trades'] - default_result['trades']:>+10}")
        
        # Summary
        print(f"\n🏆 SUMMARY:")
        improvement_factor = best_result['total_return'] / default_result['total_return'] if default_result['total_return'] > 0 else float('inf')
        print(f"   • Optimized parameters are {improvement_factor:.1f}x better than default")
        print(f"   • Extra return: {return_improvement:+.2f}% total ({annual_improvement:+.2f}% annually)")
        
        if drawdown_improvement < 0:
            print(f"   • Better risk control: {abs(drawdown_improvement):.2f}% less drawdown")
        else:
            print(f"   • Higher risk: {drawdown_improvement:.2f}% more drawdown")
            
        if sortino_improvement > 0:
            print(f"   • Better risk-adjusted returns: +{sortino_improvement:.4f} Sortino ratio")
    
    def calculate_performance(self, signals):
        """Calculate performance metrics"""
        # Generate entry/exit points
        entries = []
        exits = []
        current_position = 'cash'
        
        for idx, (date, signal) in enumerate(signals.iterrows()):
            current_signal = signal['signal']
            
            if current_signal == 'buy' and current_position == 'cash':
                entries.append({'date': date, 'price': signal['price']})
                current_position = 'long'
            elif current_signal == 'sell' and current_position == 'long':
                exits.append({'date': date, 'price': signal['price']})
                current_position = 'cash'
        
        if not entries:
            return {
                'total_return': 0, 'annual_return': 0, 'win_rate': 0,
                'max_drawdown': 0, 'sortino_ratio': 0, 'trades': 0, 'profit_factor': 0
            }
        
        # Calculate portfolio performance
        portfolio_value = []
        cash = 10000
        btc_holdings = 0
        position = 'cash'
        
        for idx, (date, signal) in enumerate(signals.iterrows()):
            current_signal = signal['signal']
            current_price = signal['price']
            
            if current_signal == 'buy' and position == 'cash':
                btc_holdings = cash / current_price
                cash = 0
                position = 'long'
            elif current_signal == 'sell' and position == 'long':
                cash = btc_holdings * current_price
                btc_holdings = 0
                position = 'cash'
            
            current_value = btc_holdings * current_price if position == 'long' else cash
            portfolio_value.append(current_value)
        
        if not portfolio_value:
            return {
                'total_return': 0, 'annual_return': 0, 'win_rate': 0,
                'max_drawdown': 0, 'sortino_ratio': 0, 'trades': 0, 'profit_factor': 0
            }
        
        # Calculate metrics
        portfolio_value = np.array(portfolio_value)
        total_return = ((portfolio_value[-1] / portfolio_value[0]) - 1) * 100
        
        # Calculate annualized return
        days = len(signals)
        if days > 0:
            years = days / 365.25
            annual_return = ((portfolio_value[-1] / portfolio_value[0]) ** (1/years) - 1) * 100
        else:
            annual_return = 0
        
        # Win rate
        wins = sum(1 for i in range(min(len(entries), len(exits))) 
                  if exits[i]['price'] > entries[i]['price'])
        win_rate = (wins / len(exits)) * 100 if exits else 0
        
        # Max drawdown
        running_max = np.maximum.accumulate(portfolio_value)
        drawdown = (portfolio_value - running_max) / running_max * 100
        max_drawdown = np.min(drawdown)
        
        # Sortino ratio
        portfolio_returns = np.diff(portfolio_value) / portfolio_value[:-1]
        avg_return = np.mean(portfolio_returns)
        negative_returns = portfolio_returns[portfolio_returns < 0]
        downside_deviation = np.std(negative_returns) if len(negative_returns) > 0 else 0.01
        sortino_ratio = avg_return / downside_deviation * np.sqrt(252) if downside_deviation > 0 else 0
        
        # Profit factor
        winning_trades = [exits[i]['price'] - entries[i]['price'] for i in range(min(len(entries), len(exits))) 
                         if exits[i]['price'] > entries[i]['price']]
        losing_trades = [entries[i]['price'] - exits[i]['price'] for i in range(min(len(entries), len(exits))) 
                        if exits[i]['price'] <= entries[i]['price']]
        
        gross_profit = sum(winning_trades) if winning_trades else 0
        gross_loss = sum(losing_trades) if losing_trades else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'sortino_ratio': sortino_ratio,
            'trades': len(entries),
            'profit_factor': profit_factor
        }
    
    def run_all_timeframes(self):
        """Run optimization for all timeframes"""
        print("🚀 MULTI-TIMEFRAME AI TREND NAVIGATOR OPTIMIZATION")
        print("="*70)
        
        # Show total combinations for each timeframe
        print("📊 COMPREHENSIVE PARAMETER TESTING:")
        total_combinations = 0
        for timeframe in self.timeframes.keys():
            params = self.parameter_ranges[timeframe]
            combinations = (len(params['numberOfClosestValues']) * 
                          len(params['smoothingPeriod']) * 
                          len(params['windowSize']) * 
                          len(params['maLen']))
            total_combinations += combinations
            print(f"   {timeframe}: {combinations:,} combinations")
        
        print(f"   TOTAL: {total_combinations:,} combinations across all timeframes")
        print()
        
        all_results = {}
        
        for timeframe in self.timeframes.keys():
            results = self.optimize_parameters_for_timeframe(timeframe)
            if results:
                all_results[timeframe] = results
        
        # Show comparison
        self.show_timeframe_comparison(all_results)
        
        return all_results
    def show_timeframe_comparison(self, all_results):
        """Show comparison across timeframes"""
        print("\n🏆 BEST PARAMETERS BY TIMEFRAME")
        print("="*100)
        print(f"{'Timeframe':<10} {'K':<3} {'Smooth':<7} {'Window':<7} {'MA':<4} {'Total%':<8} {'Annual%':<8} {'Win%':<6} {'MaxDD%':<8} {'Sortino':<8} {'Trades':<7}")
        print("-"*100)
        
        for timeframe, results in all_results.items():
            if results:
                best = results[0]
                print(f"{timeframe:<10} {best['K']:<3} {best['smoothing']:<7} {best['window']:<7} {best['maLen']:<4} "
                      f"{best['total_return']:<8.2f} {best['annual_return']:<8.2f} {best['win_rate']:<6.2f} "
                      f"{best['max_drawdown']:<8.2f} {best['sortino_ratio']:<8.4f} {best['trades']:<7}")
        
        print("\n📊 TIMEFRAME ANALYSIS:")
        
        # Find best performing timeframe
        best_timeframe = None
        best_return = -float('inf')
        
        for timeframe, results in all_results.items():
            if results and results[0]['total_return'] > best_return:
                best_return = results[0]['total_return']
                best_timeframe = timeframe
        
        if best_timeframe:
            print(f"🥇 Best Overall Performance: {best_timeframe} with {best_return:.2f}% return")
        
        # Find most consistent timeframe (best risk-adjusted)
        best_risk_adjusted = None
        best_sortino = -float('inf')
        
        for timeframe, results in all_results.items():
            if results and results[0]['sortino_ratio'] > best_sortino:
                best_sortino = results[0]['sortino_ratio']
                best_risk_adjusted = timeframe
        
        if best_risk_adjusted:
            print(f"🛡️  Best Risk-Adjusted: {best_risk_adjusted} with {best_sortino:.4f} Sortino ratio")

def main():
    optimizer = MultiTimeframeOptimizer()
    results = optimizer.run_all_timeframes()
    
    if results:
        print("\n✅ Multi-timeframe optimization completed!")
        print("📁 Check the CSV files for detailed results")
    else:
        print("❌ Optimization failed")

if __name__ == "__main__":
    main() 