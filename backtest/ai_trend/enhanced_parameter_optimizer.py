#!/usr/bin/env python3
"""
Enhanced Parameter Optimization System for AI Trend Navigator
Expanded parameter ranges for more comprehensive optimization
"""

import pandas as pd
import numpy as np
from itertools import product
import matplotlib.pyplot as plt
import seaborn as sns
from ai_trend_navigator import AITrendNavigator
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import warnings
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

def fetch_btc_data_fmp(api_key, days=1825):
    """
    Fetch BTC data from FMP API (same as entry_exit_visualization.py)
    """
    symbol = "BTCUSD"
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Format dates for FMP API
    from_date = start_date.strftime('%Y-%m-%d')
    to_date = end_date.strftime('%Y-%m-%d')
    
    # FMP API endpoint for historical data
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
    params = {
        'from': from_date,
        'to': to_date,
        'apikey': api_key
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if 'historical' not in data:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(data['historical'])
        
        # Convert date and sort
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
        
        # Keep only required columns and set timestamp as index
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df.set_index('timestamp', inplace=True)
        
        return df
        
    except Exception as e:
        print(f"❌ Error fetching FMP data: {e}")
        return None

def test_single_parameter_combination(args):
    """
    Test a single parameter combination - standalone function for parallel processing
    """
    params, api_key, days = args
    try:
        # Ensure parameters are integers (convert from float if needed)
        clean_params = {
            'numberOfClosestValues': int(params['numberOfClosestValues']),
            'smoothingPeriod': int(params['smoothingPeriod']),
            'windowSize': int(params['windowSize']),
            'maLen': int(params['maLen'])
        }
        
        # Create navigator with specific parameters
        navigator = AITrendNavigator(**clean_params)
        
        # Get data using FMP API (same as entry_exit_visualization)
        df = fetch_btc_data_fmp(api_key, days)
        if df is None:
            return None
        
        # Calculate signals
        signals = navigator.calculate_trend_signals(df)
        
        # Calculate performance
        optimizer = EnhancedParameterOptimizer(api_key=api_key, days=days)  # Create temporary instance for metrics
        metrics = optimizer.calculate_performance_metrics(df, signals)
        
        # Add parameters to results
        result = {**params, **metrics}
        return result
        
    except Exception as e:
        print(f"Error testing parameters {params}: {e}")
        return None

class EnhancedParameterOptimizer:
    """
    Enhanced Parameter Optimizer with comprehensive parameter ranges
    """
    
    def __init__(self, api_key=None, days=1825):
        self.api_key = api_key or os.getenv('FMP_API_KEY')
        self.days = days
        self.results = []
        self.results_df = None
        self.default_params = {
            'numberOfClosestValues': 3,
            'smoothingPeriod': 50,
            'windowSize': 30,
            'maLen': 5
        }
        print(f"🔧 Enhanced Parameter Optimizer initialized")
        print(f"📊 Data: BTCUSD via FMP API, {days} days")
    
    def define_comprehensive_parameter_ranges(self):
        """
        Define comprehensive parameter ranges for extensive testing
        """
        return {
            # K in KNN - test from 2 to 20 for thorough coverage
            'numberOfClosestValues': list(range(2, 21)),  # [2, 3, 4, ..., 20]
            
            # Smoothing period - test from 10 to 200 with finer granularity
            'smoothingPeriod': list(range(10, 201, 10)),  # [10, 20, 30, ..., 200]
            
            # Window size - test from 10 to 100 with good coverage
            'windowSize': list(range(10, 101, 5)),  # [10, 15, 20, ..., 100]
            
            # MA length - test from 2 to 25 for comprehensive coverage
            'maLen': list(range(2, 26))  # [2, 3, 4, ..., 25]
        }
    
    def define_focused_parameter_ranges(self):
        """
        Define focused parameter ranges around promising areas
        Based on your result: K=10, smoothing=100, window=40, maLen=15
        """
        return {
            # Focus around K=10 with wider range
            'numberOfClosestValues': [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
            
            # Focus around smoothing=100 with wider range
            'smoothingPeriod': [60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200],
            
            # Focus around window=40 with wider range
            'windowSize': [25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80],
            
            # Focus around maLen=15 with wider range
            'maLen': [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
        }
    
    def calculate_performance_metrics(self, df, signals, transaction_cost=0.001):
        """
        Calculate comprehensive performance metrics using strategy simulation
        """
        # Get buy/sell signals
        buy_signals = signals[signals['signal'] == 'buy'].copy()
        sell_signals = signals[signals['signal'] == 'sell'].copy()
        
        if len(buy_signals) == 0 or len(sell_signals) == 0:
            return self._empty_metrics()
        
        # Strategy simulation approach
        portfolio_value = []
        cash = 10000  # Starting with $10,000
        btc_holdings = 0
        position = None
        
        for i, (idx, row) in enumerate(signals.iterrows()):
            current_signal = row['signal']
            current_price = row['price']
            
            if current_signal == 'buy' and position != 'long':
                # Buy signal - convert cash to BTC
                if cash > 0:
                    # Apply transaction cost
                    effective_cash = cash * (1 - transaction_cost)
                    btc_holdings = effective_cash / current_price
                    cash = 0
                    position = 'long'
                    
            elif current_signal == 'sell' and position == 'long':
                # Sell signal - convert BTC to cash
                if btc_holdings > 0:
                    # Apply transaction cost
                    cash = btc_holdings * current_price * (1 - transaction_cost)
                    btc_holdings = 0
                    position = 'cash'
            
            # Calculate current portfolio value
            if position == 'long' and btc_holdings > 0:
                current_value = btc_holdings * current_price
            else:
                current_value = cash
                
            portfolio_value.append(current_value)
        
        if len(portfolio_value) == 0:
            return self._empty_metrics()
        
        # Convert to numpy array for calculations
        portfolio_value = np.array(portfolio_value)
        
        # Calculate strategy metrics
        total_return = ((portfolio_value[-1] / portfolio_value[0]) - 1) * 100
        
        # Portfolio returns for further calculations
        portfolio_returns = np.diff(portfolio_value) / portfolio_value[:-1]
        
        # Calculate win rate based on completed long trades only
        winning_trades = 0
        total_trades = 0
        entry_price = None
        in_trade = False
        
        for i, signal in enumerate(signals['signal']):
            current_price = signals.iloc[i]['price']
            
            if signal == 'buy' and not in_trade:
                # Enter long position
                entry_price = current_price
                in_trade = True
                
            elif signal == 'sell' and in_trade:
                # Exit long position
                if entry_price is not None:
                    trade_return = (current_price - entry_price) / entry_price
                    total_trades += 1
                    if trade_return > 0:
                        winning_trades += 1
                
                in_trade = False
                entry_price = None
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate drawdown
        running_max = np.maximum.accumulate(portfolio_value)
        drawdown = (portfolio_value - running_max) / running_max
        max_drawdown = np.min(drawdown) * 100
        
        # Sortino ratio based on portfolio returns
        avg_return = np.mean(portfolio_returns)
        negative_returns = portfolio_returns[portfolio_returns < 0]
        downside_deviation = np.std(negative_returns) if len(negative_returns) > 0 else 0.01
        sortino_ratio = avg_return / downside_deviation * np.sqrt(252) if downside_deviation > 0 else 0
        
        # Additional metrics
        avg_return_pct = avg_return * 100
        returns_std = np.std(portfolio_returns) * 100
        
        # Profit factor calculation
        positive_returns = portfolio_returns[portfolio_returns > 0]
        negative_returns = portfolio_returns[portfolio_returns < 0]
        total_gains = np.sum(positive_returns) if len(positive_returns) > 0 else 0
        total_losses = abs(np.sum(negative_returns)) if len(negative_returns) > 0 else 0.01
        profit_factor = total_gains / total_losses if total_losses > 0 else 0
        
        return {
            'total_return': total_return,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_return': avg_return_pct,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'profit_factor': profit_factor,
            'returns_std': returns_std
        }
    
    def _empty_metrics(self):
        """Return empty metrics for failed calculations"""
        return {
            'total_return': 0,
            'total_trades': 0,
            'win_rate': 0,
            'avg_return': 0,
            'sortino_ratio': 0,
            'max_drawdown': 0,
            'profit_factor': 0,
            'returns_std': 0
        }
    
    def optimize_parameters(self, max_combinations=500, use_parallel=True, optimization_mode='comprehensive'):
        """
        Run comprehensive parameter optimization
        
        Parameters:
        - max_combinations: Maximum number of combinations to test
        - use_parallel: Whether to use parallel processing
        - optimization_mode: 'comprehensive' or 'focused'
        """
        print(f"🔍 Starting {optimization_mode} parameter optimization...")
        
        # Choose parameter ranges based on mode
        if optimization_mode == 'comprehensive':
            parameter_ranges = self.define_comprehensive_parameter_ranges()
        else:
            parameter_ranges = self.define_focused_parameter_ranges()
        
        # Generate all combinations
        keys = list(parameter_ranges.keys())
        values = list(parameter_ranges.values())
        all_combinations = list(product(*values))
        
        print(f"📊 Total possible combinations: {len(all_combinations)}")
        
        # Limit combinations if needed
        if len(all_combinations) > max_combinations:
            import random
            random.seed(42)  # For reproducibility
            all_combinations = random.sample(all_combinations, max_combinations)
            print(f"📉 Reduced to {len(all_combinations)} combinations for testing")
        
        # Create parameter dictionaries
        param_dicts = []
        for combo in all_combinations:
            param_dict = dict(zip(keys, combo))
            param_dicts.append((param_dict, self.api_key, self.days))
        
        # Run optimization
        if use_parallel:
            # Use parallel processing
            max_workers = min(mp.cpu_count(), len(param_dicts))
            print(f"🔄 Using {max_workers} parallel workers")
            
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(test_single_parameter_combination, param_dict) 
                          for param_dict in param_dicts]
                
                # Collect results with progress
                completed = 0
                for future in as_completed(futures):
                    result = future.result()
                    if result is not None:
                        self.results.append(result)
                    completed += 1
                    if completed % 50 == 0:
                        print(f"⏳ Completed {completed}/{len(param_dicts)} combinations...")
        else:
            # Sequential processing
            for i, param_dict in enumerate(param_dicts):
                result = test_single_parameter_combination(param_dict)
                if result is not None:
                    self.results.append(result)
                if (i + 1) % 10 == 0:
                    print(f"⏳ Completed {i+1}/{len(param_dicts)} combinations...")
        
        # Convert to DataFrame
        if self.results:
            self.results_df = pd.DataFrame(self.results)
            print(f"✅ Optimization complete! Tested {len(self.results)} valid combinations")
        else:
            print("❌ No valid results found")
            
        return len(self.results)
    
    def get_best_parameters(self, metric='total_return', top_n=10):
        """
        Get best parameters based on specified metric
        """
        if len(self.results) == 0:
            print("❌ No results available. Run optimize_parameters() first.")
            return None
        
        # Sort by metric
        sorted_results = self.results_df.sort_values(metric, ascending=False)
        
        print(f"🏆 Top {top_n} Parameter Combinations (sorted by {metric}):")
        print("=" * 80)
        
        for i, (_, row) in enumerate(sorted_results.head(top_n).iterrows()):
            print(f"\n🥇 Rank {i+1}:")
            print(f"   Parameters: K={row['numberOfClosestValues']}, "
                  f"smoothing={row['smoothingPeriod']}, "
                  f"window={row['windowSize']}, "
                  f"maLen={row['maLen']}")
            print(f"   Performance: {metric}={row[metric]:.4f}, "
                  f"return={row['total_return']:.2f}%, "
                  f"win_rate={row['win_rate']:.2f}%, "
                  f"trades={row['total_trades']}")
        
        return sorted_results.head(top_n)
    
    def generate_report(self, output_file="enhanced_optimization_report.txt"):
        """
        Generate comprehensive optimization report
        """
        if len(self.results) == 0:
            print("❌ No results to report")
            return
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("ENHANCED AI TREND NAVIGATOR OPTIMIZATION REPORT\n")
            f.write("=" * 60 + "\n\n")
            
            # Summary statistics
            f.write("OPTIMIZATION SUMMARY\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total combinations tested: {len(self.results)}\n")
            f.write(f"Symbol: BTCUSD (FMP API)\n")
            f.write(f"Data source: FMP API\n")
            f.write(f"Data points: {self.days} days\n\n")
            
            # Best performers by each metric
            metrics = ['total_return', 'win_rate', 'sortino_ratio', 'profit_factor']
            for metric in metrics:
                best = self.results_df.nlargest(1, metric).iloc[0]
                f.write(f"BEST {metric.upper().replace('_', ' ')}\n")
                f.write(f"   Parameters: K={best['numberOfClosestValues']}, "
                       f"smoothing={best['smoothingPeriod']}, "
                       f"window={best['windowSize']}, "
                       f"maLen={best['maLen']}\n")
                f.write(f"   {metric}: {best[metric]:.4f}\n")
                f.write(f"   Total Return: {best['total_return']:.2f}%\n")
                f.write(f"   Win Rate: {best['win_rate']:.2f}%\n")
                f.write(f"   Sortino Ratio: {best['sortino_ratio']:.4f}\n")
                f.write(f"   Profit Factor: {best['profit_factor']:.4f}\n")
                f.write(f"   Max Drawdown: {best['max_drawdown']:.2f}%\n\n")
        
        print(f"📄 Report saved to {output_file}") 