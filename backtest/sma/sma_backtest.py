import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import time
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

class SMABacktester:
    def __init__(self, exchange_name='binance'):
        """Initialize the SMA backtester with exchange connection."""
        self.exchange = getattr(ccxt, exchange_name)({
            'apiKey': '',  # Add your API key if needed for higher rate limits
            'secret': '',  # Add your secret if needed
            'timeout': 30000,
            'enableRateLimit': True,
        })
        self.data = {}
        
    def fetch_ohlcv_data(self, symbol, timeframe='8h', limit=1000):
        """Fetch OHLCV data from exchange with pagination for large datasets."""
        print(f"Fetching {symbol} data on {timeframe} timeframe (requesting {limit} candles)...")
        
        try:
            if limit <= 1000:
                # Single request for small datasets
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            else:
                # Pagination for large datasets
                print(f"Large dataset requested ({limit} candles), using pagination...")
                all_ohlcv = []
                current_limit = min(1000, limit)
                total_fetched = 0
                
                # Start from current time and go backwards
                since = None
                
                while total_fetched < limit:
                    try:
                        # Fetch batch
                        batch = self.exchange.fetch_ohlcv(symbol, timeframe, since, current_limit)
                        if not batch:
                            break
                            
                        all_ohlcv.extend(batch)
                        total_fetched += len(batch)
                        
                        # Set 'since' to the earliest timestamp from this batch minus 1ms to avoid duplicates
                        since = batch[0][0] - 1
                        
                        print(f"Fetched {len(batch)} candles (total: {total_fetched}/{limit})")
                        
                        # Break if we've fetched enough or if the batch was smaller than expected
                        if len(batch) < current_limit or total_fetched >= limit:
                            break
                            
                        # Rate limiting
                        time.sleep(1)
                        
                    except Exception as batch_error:
                        print(f"Error in batch fetch: {batch_error}")
                        break
                
                # Remove duplicates and sort by timestamp
                seen_timestamps = set()
                ohlcv = []
                for candle in all_ohlcv:
                    if candle[0] not in seen_timestamps:
                        seen_timestamps.add(candle[0])
                        ohlcv.append(candle)
                
                # Sort by timestamp (oldest first)
                ohlcv.sort(key=lambda x: x[0])
                
                # Limit to requested amount
                ohlcv = ohlcv[-limit:] if len(ohlcv) > limit else ohlcv
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Remove any duplicate timestamps
            df = df[~df.index.duplicated(keep='last')]
            df = df.sort_index()
            
            print(f"Final dataset: {len(df)} candles for {symbol}")
            print(f"Date range: {df.index[0]} to {df.index[-1]}")
            
            return df
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None
    
    def calculate_start_timestamp(self, years_ago):
        """Calculate the start timestamp for historical data."""
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years_ago)
        
        # Convert to milliseconds (CCXT format)
        start_timestamp = int(start_date.timestamp() * 1000)
        return start_timestamp
    
    def fetch_historical_data(self, symbol, timeframe='8h', years=2):
        """Fetch historical data for a specific number of years."""
        print(f"Fetching {years} years of {symbol} data...")
        
        try:
            # Calculate start timestamp
            start_timestamp = self.calculate_start_timestamp(years)
            
            all_ohlcv = []
            since = start_timestamp
            
            while True:
                try:
                    # Fetch batch
                    batch = self.exchange.fetch_ohlcv(symbol, timeframe, since, 1000)
                    if not batch:
                        break
                    
                    all_ohlcv.extend(batch)
                    
                    # Update since to the last timestamp + 1ms
                    since = batch[-1][0] + 1
                    
                    print(f"Fetched {len(batch)} candles (total: {len(all_ohlcv)})")
                    
                    # Break if we've reached current time or batch is smaller than expected
                    current_time = int(datetime.now().timestamp() * 1000)
                    if since >= current_time or len(batch) < 1000:
                        break
                    
                    # Rate limiting
                    time.sleep(1)
                    
                except Exception as batch_error:
                    print(f"Error in batch fetch: {batch_error}")
                    break
            
            if not all_ohlcv:
                print(f"No data fetched for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Remove duplicates and sort
            df = df[~df.index.duplicated(keep='last')]
            df = df.sort_index()
            
            print(f"Final dataset: {len(df)} candles for {symbol} ({years} years)")
            print(f"Date range: {df.index[0]} to {df.index[-1]}")
            
            return df
            
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    def calculate_sma(self, data, period):
        """Calculate Simple Moving Average."""
        return data['close'].rolling(window=period).mean()
    
    def backtest_sma_strategy(self, data, sma_period, initial_capital=10000):
        """
        Backtest SMA strategy using crossover signals.
        Buy when price crosses above SMA, sell when price crosses below SMA.
        """
        df = data.copy()
        df[f'SMA_{sma_period}'] = self.calculate_sma(df, sma_period)
        
        # Generate signals
        df['signal'] = 0
        df['position'] = 0
        
        # Buy signal: price crosses above SMA
        # Sell signal: price crosses below SMA
        for i in range(1, len(df)):
            if (df['close'].iloc[i] > df[f'SMA_{sma_period}'].iloc[i] and 
                df['close'].iloc[i-1] <= df[f'SMA_{sma_period}'].iloc[i-1]):
                df['signal'].iloc[i] = 1  # Buy signal
            elif (df['close'].iloc[i] < df[f'SMA_{sma_period}'].iloc[i] and 
                  df['close'].iloc[i-1] >= df[f'SMA_{sma_period}'].iloc[i-1]):
                df['signal'].iloc[i] = -1  # Sell signal
        
        # Calculate positions
        position = 0
        positions = []
        for signal in df['signal']:
            if signal == 1:
                position = 1
            elif signal == -1:
                position = 0
            positions.append(position)
        
        df['position'] = positions
        
        # Calculate returns
        df['market_return'] = df['close'].pct_change()
        df['strategy_return'] = df['position'].shift(1) * df['market_return']
        
        # Calculate cumulative returns
        df['cumulative_market_return'] = (1 + df['market_return']).cumprod()
        df['cumulative_strategy_return'] = (1 + df['strategy_return']).cumprod()
        
        # Calculate portfolio value
        df['portfolio_value'] = initial_capital * df['cumulative_strategy_return']
        
        return df
    
    def calculate_performance_metrics(self, backtest_data):
        """Calculate comprehensive performance metrics."""
        strategy_returns = backtest_data['strategy_return'].dropna()
        market_returns = backtest_data['market_return'].dropna()
        
        # Basic metrics
        total_return = backtest_data['cumulative_strategy_return'].iloc[-1] - 1
        market_total_return = backtest_data['cumulative_market_return'].iloc[-1] - 1
        
        # Annualized returns (assuming 8h timeframe, ~1095 periods per year)
        periods_per_year = 365 * 24 / 8  # ~1095
        n_periods = len(strategy_returns)
        annualized_return = (1 + total_return) ** (periods_per_year / n_periods) - 1
        market_annualized_return = (1 + market_total_return) ** (periods_per_year / n_periods) - 1
        
        # Volatility
        volatility = strategy_returns.std() * np.sqrt(periods_per_year)
        market_volatility = market_returns.std() * np.sqrt(periods_per_year)
        
        # Sharpe ratio (assuming 0% risk-free rate)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Maximum drawdown
        cumulative = backtest_data['cumulative_strategy_return']
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # Win rate
        winning_trades = strategy_returns[strategy_returns > 0]
        win_rate = len(winning_trades) / len(strategy_returns[strategy_returns != 0]) if len(strategy_returns[strategy_returns != 0]) > 0 else 0
        
        # Number of trades
        trades = backtest_data['signal'][backtest_data['signal'] != 0]
        num_trades = len(trades)
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'market_total_return': market_total_return,
            'market_annualized_return': market_annualized_return,
            'volatility': volatility,
            'market_volatility': market_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'num_trades': num_trades,
            'final_portfolio_value': backtest_data['portfolio_value'].iloc[-1]
        }
    
    def run_sma_optimization_multi_timeframe(self, symbols, time_periods, sma_range=(100, 200), initial_capital=10000):
        """Run SMA optimization across different parameters and time periods."""
        
        all_results = {}
        
        for symbol in symbols:
            symbol_results = {}
            
            for years in time_periods:
                print(f"\n=== Fetching {years} years of data for {symbol} ===")
                
                # Fetch historical data for this time period
                data = self.fetch_historical_data(symbol, timeframe='8h', years=years)
                if data is None or data.empty:
                    print(f"Failed to fetch data for {symbol} - {years} years")
                    continue
                
                # Run backtests for all SMA periods
                results = []
                total_combinations = sma_range[1] - sma_range[0] + 1
                
                print(f"Running backtests for SMA periods {sma_range[0]}-{sma_range[1]} on {years} years of {symbol} data")
                
                with tqdm(total=total_combinations, desc=f"{symbol} {years}Y") as pbar:
                    for sma_period in range(sma_range[0], sma_range[1] + 1):
                        # Skip if we don't have enough data
                        if len(data) < sma_period + 50:
                            pbar.update(1)
                            continue
                        
                        # Run backtest
                        backtest_data = self.backtest_sma_strategy(data, sma_period, initial_capital)
                        
                        # Calculate metrics
                        metrics = self.calculate_performance_metrics(backtest_data)
                        
                        # Store results
                        result = {
                            'symbol': symbol,
                            'time_period_years': years,
                            'sma_period': sma_period,
                            'data_points': len(data),
                            **metrics
                        }
                        results.append(result)
                        pbar.update(1)
                
                symbol_results[f"{years}Y"] = pd.DataFrame(results)
                time.sleep(2)  # Rate limiting between different time period requests
                
            all_results[symbol] = symbol_results
        
        return all_results
    
    def display_results(self, all_results):
        """Display and visualize the backtest results."""
        if all_results is None or not all_results:
            print("No results to display.")
            return
        
        print("\n" + "="*100)
        print("COMPREHENSIVE SMA BACKTEST RESULTS SUMMARY")
        print("="*100)
        
        # Combine all results into a single DataFrame for overall analysis
        combined_results = []
        for symbol, time_periods in all_results.items():
            for period, df in time_periods.items():
                if not df.empty:
                    combined_results.append(df)
        
        if not combined_results:
            print("No valid results to display.")
            return
            
        all_data = pd.concat(combined_results, ignore_index=True)
        
        # Display results for each symbol and time period
        for symbol in all_results.keys():
            print(f"\n{'='*60}")
            print(f"RESULTS FOR {symbol}")
            print(f"{'='*60}")
            
            for time_period, df in all_results[symbol].items():
                if df.empty:
                    continue
                    
                years = time_period.replace('Y', '')
                print(f"\n--- {years} Years Backtest ---")
                
                # Best strategy for this time period
                best = df.loc[df['total_return'].idxmax()]
                best_sharpe = df.loc[df['sharpe_ratio'].idxmax()]
                
                print(f"Best Total Return: SMA-{best['sma_period']} | "
                      f"Return: {best['total_return']:.2%} | "
                      f"Sharpe: {best['sharpe_ratio']:.3f} | "
                      f"Max DD: {best['max_drawdown']:.2%} | "
                      f"Trades: {best['num_trades']}")
                
                print(f"Best Sharpe Ratio: SMA-{best_sharpe['sma_period']} | "
                      f"Return: {best_sharpe['total_return']:.2%} | "
                      f"Sharpe: {best_sharpe['sharpe_ratio']:.3f} | "
                      f"Max DD: {best_sharpe['max_drawdown']:.2%} | "
                      f"Trades: {best_sharpe['num_trades']}")
                
                # Top 5 for this period
                print("\nTop 5 strategies by Total Return:")
                top_5 = df.nlargest(5, 'total_return')
                for idx, row in top_5.iterrows():
                    print(f"  SMA-{row['sma_period']}: {row['total_return']:.2%} return, "
                          f"{row['sharpe_ratio']:.3f} Sharpe, {row['max_drawdown']:.2%} max DD")
        
        # Overall best across all periods
        print(f"\n{'='*60}")
        print("OVERALL BEST STRATEGIES ACROSS ALL PERIODS")
        print(f"{'='*60}")
        
        print("\nTOP 10 STRATEGIES BY TOTAL RETURN:")
        top_overall = all_data.nlargest(10, 'total_return')
        print(top_overall[['symbol', 'time_period_years', 'sma_period', 'total_return', 
                          'annualized_return', 'sharpe_ratio', 'max_drawdown', 'num_trades']].round(4))
        
        print("\nTOP 10 STRATEGIES BY SHARPE RATIO:")
        top_sharpe_overall = all_data.nlargest(10, 'sharpe_ratio')
        print(top_sharpe_overall[['symbol', 'time_period_years', 'sma_period', 'total_return', 
                                 'annualized_return', 'sharpe_ratio', 'max_drawdown', 'num_trades']].round(4))
        
        # Create visualizations
        self.create_comprehensive_visualizations(all_results, all_data)
    
    def create_comprehensive_visualizations(self, all_results, combined_data):
        """Create comprehensive performance visualization charts for all time periods."""
        plt.style.use('default')
        
        # Create multiple figure sets
        # Figure 1: Overview comparison
        fig1, axes1 = plt.subplots(2, 2, figsize=(16, 12))
        fig1.suptitle('SMA Strategy Performance Analysis - All Time Periods', fontsize=16, fontweight='bold')
        
        # 1. Best return by time period for each symbol
        best_by_period = {}
        for symbol in all_results.keys():
            best_by_period[symbol] = {}
            for period, df in all_results[symbol].items():
                if not df.empty:
                    best = df.loc[df['total_return'].idxmax()]
                    years = int(period.replace('Y', ''))
                    best_by_period[symbol][years] = {
                        'return': best['total_return'],
                        'sma_period': best['sma_period'],
                        'sharpe': best['sharpe_ratio']
                    }
        
        # Plot best returns by time period
        for symbol in best_by_period.keys():
            periods = sorted(best_by_period[symbol].keys())
            returns = [best_by_period[symbol][p]['return'] for p in periods]
            axes1[0,0].plot(periods, returns, marker='o', label=symbol, linewidth=2, markersize=8)
        
        axes1[0,0].set_title('Best Total Return by Time Period')
        axes1[0,0].set_xlabel('Time Period (Years)')
        axes1[0,0].set_ylabel('Best Total Return')
        axes1[0,0].legend()
        axes1[0,0].grid(True, alpha=0.3)
        
        # 2. Best SMA period by time period
        for symbol in best_by_period.keys():
            periods = sorted(best_by_period[symbol].keys())
            sma_periods = [best_by_period[symbol][p]['sma_period'] for p in periods]
            axes1[0,1].plot(periods, sma_periods, marker='s', label=symbol, linewidth=2, markersize=8)
        
        axes1[0,1].set_title('Optimal SMA Period by Time Period')
        axes1[0,1].set_xlabel('Time Period (Years)')
        axes1[0,1].set_ylabel('Best SMA Period')
        axes1[0,1].legend()
        axes1[0,1].grid(True, alpha=0.3)
        
        # 3. Sharpe ratio comparison
        symbols = combined_data['symbol'].unique()
        time_periods = sorted(combined_data['time_period_years'].unique())
        
        # Create heatmap data for Sharpe ratios
        sharpe_matrix = []
        for symbol in symbols:
            sharpe_row = []
            for years in time_periods:
                symbol_year_data = combined_data[(combined_data['symbol'] == symbol) & 
                                                (combined_data['time_period_years'] == years)]
                if not symbol_year_data.empty:
                    best_sharpe = symbol_year_data['sharpe_ratio'].max()
                    sharpe_row.append(best_sharpe)
                else:
                    sharpe_row.append(0)
            sharpe_matrix.append(sharpe_row)
        
        sharpe_df = pd.DataFrame(sharpe_matrix, index=symbols, columns=[f"{y}Y" for y in time_periods])
        sns.heatmap(sharpe_df, annot=True, fmt='.3f', cmap='RdYlGn', 
                   ax=axes1[1,0], cbar_kws={'label': 'Best Sharpe Ratio'})
        axes1[1,0].set_title('Best Sharpe Ratio by Symbol and Time Period')
        
        # 4. Risk-Return scatter for all periods
        colors = ['red', 'blue', 'green', 'orange']
        for i, years in enumerate(time_periods):
            year_data = combined_data[combined_data['time_period_years'] == years]
            axes1[1,1].scatter(year_data['volatility'], year_data['annualized_return'], 
                             label=f"{years} Years", alpha=0.6, s=30, c=colors[i % len(colors)])
        
        axes1[1,1].set_title('Risk-Return Profile Across All Periods')
        axes1[1,1].set_xlabel('Volatility (Annualized)')
        axes1[1,1].set_ylabel('Annualized Return')
        axes1[1,1].legend()
        axes1[1,1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('sma_comprehensive_analysis.png', dpi=300, bbox_inches='tight')
        
        # Figure 2: Individual symbol detailed analysis
        for symbol in all_results.keys():
            fig2, axes2 = plt.subplots(2, 2, figsize=(16, 12))
            symbol_clean = symbol.replace('/', '_')
            fig2.suptitle(f'{symbol} - Detailed SMA Analysis Across Time Periods', fontsize=16, fontweight='bold')
            
            # Performance by SMA period for each time period
            for period, df in all_results[symbol].items():
                if not df.empty:
                    years = period.replace('Y', '')
                    axes2[0,0].plot(df['sma_period'], df['total_return'], 
                                  marker='o', label=f"{years} Years", linewidth=2)
            
            axes2[0,0].set_title(f'{symbol} - Total Return by SMA Period')
            axes2[0,0].set_xlabel('SMA Period')
            axes2[0,0].set_ylabel('Total Return')
            axes2[0,0].legend()
            axes2[0,0].grid(True, alpha=0.3)
            
            # Sharpe ratio by SMA period
            for period, df in all_results[symbol].items():
                if not df.empty:
                    years = period.replace('Y', '')
                    axes2[0,1].plot(df['sma_period'], df['sharpe_ratio'], 
                                  marker='s', label=f"{years} Years", linewidth=2)
            
            axes2[0,1].set_title(f'{symbol} - Sharpe Ratio by SMA Period')
            axes2[0,1].set_xlabel('SMA Period')
            axes2[0,1].set_ylabel('Sharpe Ratio')
            axes2[0,1].legend()
            axes2[0,1].grid(True, alpha=0.3)
            
            # Max drawdown comparison
            for period, df in all_results[symbol].items():
                if not df.empty:
                    years = period.replace('Y', '')
                    axes2[1,0].plot(df['sma_period'], df['max_drawdown'], 
                                  marker='^', label=f"{years} Years", linewidth=2)
            
            axes2[1,0].set_title(f'{symbol} - Maximum Drawdown by SMA Period')
            axes2[1,0].set_xlabel('SMA Period')
            axes2[1,0].set_ylabel('Maximum Drawdown')
            axes2[1,0].legend()
            axes2[1,0].grid(True, alpha=0.3)
            
            # Number of trades
            for period, df in all_results[symbol].items():
                if not df.empty:
                    years = period.replace('Y', '')
                    axes2[1,1].plot(df['sma_period'], df['num_trades'], 
                                  marker='d', label=f"{years} Years", linewidth=2)
            
            axes2[1,1].set_title(f'{symbol} - Number of Trades by SMA Period')
            axes2[1,1].set_xlabel('SMA Period')
            axes2[1,1].set_ylabel('Number of Trades')
            axes2[1,1].legend()
            axes2[1,1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(f'sma_{symbol_clean}_detailed_analysis.png', dpi=300, bbox_inches='tight')
        
        plt.show()
        
        print(f"\nVisualizations saved:")
        print(f"- sma_comprehensive_analysis.png (Overview)")
        for symbol in all_results.keys():
            symbol_clean = symbol.replace('/', '_')
            print(f"- sma_{symbol_clean}_detailed_analysis.png (Detailed {symbol} analysis)")

def main():
    """Main execution function."""
    print("COMPREHENSIVE SMA Strategy Backtesting System")
    print("="*60)
    
    # Initialize backtester
    backtester = SMABacktester(exchange_name='binance')
    
    # Define symbols and parameters
    symbols = ['BTC/USDT', 'ETH/USDT']
    time_periods = [2, 4, 6, 8]  # Years of historical data
    sma_range = (100, 200)
    initial_capital = 10000
    
    print(f"Symbols: {symbols}")
    print(f"Time Periods: {time_periods} years each")
    print(f"SMA Range: {sma_range[0]}-{sma_range[1]}")
    print(f"Timeframe: 8h")
    print(f"Initial Capital: ${initial_capital:,}")
    print(f"Total Backtests: {len(symbols)} × {len(time_periods)} = {len(symbols) * len(time_periods)}")
    
    # Run comprehensive optimization
    all_results = backtester.run_sma_optimization_multi_timeframe(
        symbols=symbols,
        time_periods=time_periods,
        sma_range=sma_range,
        initial_capital=initial_capital
    )
    
    if all_results is not None and all_results:
        # Save individual results to CSV files
        for symbol in all_results.keys():
            symbol_clean = symbol.replace('/', '_')
            for period, df in all_results[symbol].items():
                if not df.empty:
                    filename = f'sma_results_{symbol_clean}_{period}.csv'
                    df.to_csv(filename, index=False)
                    print(f"Results saved to '{filename}'")
        
        # Combine all results and save comprehensive CSV
        combined_results = []
        for symbol, time_periods_dict in all_results.items():
            for period, df in time_periods_dict.items():
                if not df.empty:
                    combined_results.append(df)
        
        if combined_results:
            all_data = pd.concat(combined_results, ignore_index=True)
            all_data.to_csv('sma_comprehensive_results.csv', index=False)
            print(f"Comprehensive results saved to 'sma_comprehensive_results.csv'")
        
        # Display results
        backtester.display_results(all_results)
    else:
        print("No results generated. Please check your internet connection and try again.")

if __name__ == "__main__":
    main() 