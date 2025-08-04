#!/usr/bin/env python3
"""
Best Parameters vs Buy & Hold Comparison
- Uses optimized parameters from multi-timeframe backtest
- Compares strategy performance vs buy & hold for each timeframe
- Creates detailed charts and performance analysis
"""

import pandas as pd
import numpy as np
import requests
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

class OptimizedAITrendNavigator:
    """Optimized AI Trend Navigator"""
    
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

class BestParamsComparison:
    """Compare best parameters against buy & hold"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        
        # Best parameters from optimization
        self.best_params = {
            '4H': {'K': 19, 'smoothing': 20, 'window': 50, 'maLen': 15},
            '8H': {'K': 19, 'smoothing': 20, 'window': 50, 'maLen': 15},
            '1D': {'K': 19, 'smoothing': 30, 'window': 70, 'maLen': 12},
            '1W': {'K': 25, 'smoothing': 10, 'window': 50, 'maLen': 8},
            '1M': {'K': 19, 'smoothing': 6, 'window': 40, 'maLen': 12}
        }
    
    def fetch_data_for_timeframe(self, timeframe):
        """Fetch data for specific timeframe"""
        print(f"📊 Fetching {timeframe} data...")
        
        symbol = "BTCUSD"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * 5)  # 5 years
        
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
            
            # Resample for higher timeframes
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
        
        resample_rules = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        
        if timeframe == '4H':
            resampled = df.resample('4H').agg(resample_rules).dropna()
        elif timeframe == '8H':
            resampled = df.resample('8H').agg(resample_rules).dropna()
        
        resampled.reset_index(inplace=True)
        return resampled
    
    def calculate_strategy_performance(self, signals):
        """Calculate strategy performance with detailed metrics"""
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
        total_return = ((portfolio_value[-1] / portfolio_value[0]) - 1) * 100
        
        # Calculate annual return
        days = len(signals)
        years = days / 365.25
        annual_return = ((portfolio_value[-1] / portfolio_value[0]) ** (1/years) - 1) * 100
        
        # Win rate
        profitable_trades = len([t for t in trades if t['profitable']])
        win_rate = (profitable_trades / len(trades) * 100) if trades else 0
        
        # Max drawdown
        portfolio_series = pd.Series(portfolio_value)
        running_max = portfolio_series.expanding().max()
        drawdown = (portfolio_series - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'trades': len(trades),
            'portfolio_value': portfolio_value,
            'trade_details': trades
        }
    
    def calculate_buy_hold_performance(self, data):
        """Calculate buy & hold performance"""
        start_price = data['close'].iloc[0]
        end_price = data['close'].iloc[-1]
        
        total_return = ((end_price / start_price) - 1) * 100
        
        # Calculate annual return
        years = len(data) / 365.25
        annual_return = ((end_price / start_price) ** (1/years) - 1) * 100
        
        # Max drawdown for buy & hold
        prices = data['close'].values
        running_max = pd.Series(prices).expanding().max()
        drawdown = (prices - running_max) / running_max * 100
        max_drawdown = min(drawdown)
        
        # Portfolio value over time
        portfolio_value = [(price / start_price) * 10000 for price in prices]
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'portfolio_value': portfolio_value
        }
    
    def create_comparison_chart(self, timeframe, data, signals, strategy_perf, buyhold_perf):
        """Create comprehensive comparison chart"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 15))
        fig.suptitle(f'{timeframe} Timeframe - Strategy vs Buy & Hold Comparison', fontsize=16, fontweight='bold')
        
        # Chart 1: Price and Strategy Signals
        ax1.plot(data.index, data['close'], color='black', linewidth=1, alpha=0.7, label='BTC Price')
        ax1.plot(data.index, signals['knnMA_smoothed'], color='blue', linewidth=2, label='AI Trend Navigator')
        
        # Add buy/sell signals
        buy_signals = signals[signals['signal'] == 'buy']
        sell_signals = signals[signals['signal'] == 'sell']
        
        if not buy_signals.empty:
            ax1.scatter(buy_signals.index, data.loc[buy_signals.index, 'close'], 
                       color='green', marker='^', s=100, label='Buy Signal', zorder=5)
        
        if not sell_signals.empty:
            ax1.scatter(sell_signals.index, data.loc[sell_signals.index, 'close'], 
                       color='red', marker='v', s=100, label='Sell Signal', zorder=5)
        
        ax1.set_title(f'{timeframe} - Price Action & Strategy Signals')
        ax1.set_ylabel('Price (USD)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Chart 2: Portfolio Value Comparison
        ax2.plot(data.index, strategy_perf['portfolio_value'], color='blue', linewidth=2, label='Strategy Portfolio')
        ax2.plot(data.index, buyhold_perf['portfolio_value'], color='orange', linewidth=2, label='Buy & Hold Portfolio')
        
        ax2.set_title(f'{timeframe} - Portfolio Value Comparison')
        ax2.set_ylabel('Portfolio Value (USD)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Chart 3: Performance Metrics Bar Chart
        categories = ['Total Return (%)', 'Annual Return (%)', 'Max Drawdown (%)']
        strategy_values = [strategy_perf['total_return'], strategy_perf['annual_return'], abs(strategy_perf['max_drawdown'])]
        buyhold_values = [buyhold_perf['total_return'], buyhold_perf['annual_return'], abs(buyhold_perf['max_drawdown'])]
        
        x = np.arange(len(categories))
        width = 0.35
        
        bars1 = ax3.bar(x - width/2, strategy_values, width, label='Strategy', color='blue', alpha=0.7)
        bars2 = ax3.bar(x + width/2, buyhold_values, width, label='Buy & Hold', color='orange', alpha=0.7)
        
        ax3.set_title(f'{timeframe} - Performance Metrics Comparison')
        ax3.set_ylabel('Percentage (%)')
        ax3.set_xticks(x)
        ax3.set_xticklabels(categories)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax3.annotate(f'{height:.1f}%',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),  # 3 points vertical offset
                           textcoords="offset points",
                           ha='center', va='bottom')
        
        # Chart 4: Trade Analysis
        if strategy_perf['trade_details']:
            returns = [trade['return'] for trade in strategy_perf['trade_details']]
            ax4.hist(returns, bins=20, alpha=0.7, color='blue', edgecolor='black')
            ax4.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='Break-even')
            ax4.set_title(f'{timeframe} - Trade Returns Distribution')
            ax4.set_xlabel('Trade Return (%)')
            ax4.set_ylabel('Number of Trades')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
        else:
            ax4.text(0.5, 0.5, 'No trades executed', transform=ax4.transAxes, 
                    ha='center', va='center', fontsize=14)
            ax4.set_title(f'{timeframe} - No Trade Data')
        
        plt.tight_layout()
        plt.savefig(f'{timeframe}_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def run_comparison_for_timeframe(self, timeframe):
        """Run comparison for a specific timeframe"""
        print(f"\n🔍 ANALYZING {timeframe} TIMEFRAME")
        print("=" * 60)
        
        # Fetch data
        data = self.fetch_data_for_timeframe(timeframe)
        if data is None:
            return None
        
        # Get best parameters
        params = self.best_params[timeframe]
        print(f"📊 Using best parameters: K={params['K']}, smoothing={params['smoothing']}, "
              f"window={params['window']}, maLen={params['maLen']}")
        
        # Initialize navigator with best parameters
        navigator = OptimizedAITrendNavigator(
            numberOfClosestValues=params['K'],
            smoothingPeriod=params['smoothing'],
            windowSize=params['window'],
            maLen=params['maLen']
        )
        
        # Calculate signals
        signals = navigator.calculate_trend_signals(data)
        
        # Calculate strategy performance
        strategy_perf = self.calculate_strategy_performance(signals)
        
        # Calculate buy & hold performance
        buyhold_perf = self.calculate_buy_hold_performance(data)
        
        # Create comparison chart
        self.create_comparison_chart(timeframe, data, signals, strategy_perf, buyhold_perf)
        
        # Print results
        print(f"\n📈 PERFORMANCE COMPARISON - {timeframe}")
        print("-" * 50)
        print(f"{'Metric':<20} {'Strategy':<15} {'Buy & Hold':<15} {'Difference':<15}")
        print("-" * 50)
        
        total_diff = strategy_perf['total_return'] - buyhold_perf['total_return']
        annual_diff = strategy_perf['annual_return'] - buyhold_perf['annual_return']
        dd_diff = strategy_perf['max_drawdown'] - buyhold_perf['max_drawdown']
        
        print(f"{'Total Return (%)':<20} {strategy_perf['total_return']:<15.2f} {buyhold_perf['total_return']:<15.2f} {total_diff:+.2f}")
        print(f"{'Annual Return (%)':<20} {strategy_perf['annual_return']:<15.2f} {buyhold_perf['annual_return']:<15.2f} {annual_diff:+.2f}")
        print(f"{'Max Drawdown (%)':<20} {strategy_perf['max_drawdown']:<15.2f} {buyhold_perf['max_drawdown']:<15.2f} {dd_diff:+.2f}")
        print(f"{'Win Rate (%)':<20} {strategy_perf['win_rate']:<15.2f} {'N/A':<15} {'N/A':<15}")
        print(f"{'Total Trades':<20} {strategy_perf['trades']:<15} {'1':<15} {'N/A':<15}")
        
        return {
            'timeframe': timeframe,
            'strategy': strategy_perf,
            'buyhold': buyhold_perf,
            'data': data,
            'signals': signals
        }
    
    def run_all_comparisons(self):
        """Run comparisons for all timeframes"""
        print("🚀 Best Parameters vs Buy & Hold - Multi-Timeframe Analysis")
        print("=" * 80)
        
        results = {}
        
        for timeframe in ['4H', '8H', '1D', '1W', '1M']:
            result = self.run_comparison_for_timeframe(timeframe)
            if result:
                results[timeframe] = result
        
        # Summary table
        print(f"\n🎯 SUMMARY - ALL TIMEFRAMES")
        print("=" * 100)
        print(f"{'Timeframe':<10} {'Strategy Return':<15} {'Buy&Hold Return':<15} {'Outperformance':<15} {'Trades':<8} {'Win Rate':<10}")
        print("-" * 100)
        
        for timeframe, result in results.items():
            strategy = result['strategy']
            buyhold = result['buyhold']
            outperformance = strategy['total_return'] - buyhold['total_return']
            
            print(f"{timeframe:<10} {strategy['total_return']:<15.2f} {buyhold['total_return']:<15.2f} "
                  f"{outperformance:+<15.2f} {strategy['trades']:<8} {strategy['win_rate']:<10.1f}")
        
        print("\n✅ All comparisons completed!")
        print("📊 Charts saved as PNG files for each timeframe")
        
        return results

def main():
    """Main function"""
    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        print("❌ FMP_API_KEY not found in environment variables")
        return
    
    comparison = BestParamsComparison(api_key)
    results = comparison.run_all_comparisons()

if __name__ == "__main__":
    main() 