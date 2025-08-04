# MACD Bitcoin Backtesting System

A comprehensive MACD (Moving Average Convergence Divergence) backtesting system for Bitcoin using CCXT to fetch real-time data from cryptocurrency exchanges.

## Features

- ✅ **Real-time Data Fetching**: Uses CCXT to fetch Bitcoin price data from major exchanges
- ✅ **MACD Calculation**: Implements full MACD indicator with customizable parameters
- ✅ **Parameter Optimization**: Automatically finds the best MACD parameters for Bitcoin
- ✅ **Backtesting Engine**: Complete backtesting system with profit/loss analysis
- ✅ **Visual Charts**: Generates beautiful charts showing price, MACD, and trading signals
- ✅ **Performance Metrics**: Calculates win rate, total return, and comparison with buy-and-hold
- ✅ **Multiple Timeframes**: Supports 1h, 4h, 1d, and other timeframes
- ✅ **Multiprocessing**: Uses 8 CPU cores for 2.3x faster optimization

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Run Full Optimization (Recommended)
```bash
python macd.py
```

This will:
- Fetch 5 years of Bitcoin data
- Test hundreds of parameter combinations
- Find the best MACD parameters for Bitcoin
- Show comprehensive results and charts
- Save optimization results to CSV

### 2. Run Quick Examples
```bash
python example_usage.py
```

This will run various examples showing different ways to use the system.

## MACD Explanation

**MACD** consists of three components:

1. **MACD Line**: Fast EMA - Slow EMA (e.g., 12-period EMA - 26-period EMA)
2. **Signal Line**: EMA of MACD line (e.g., 9-period EMA of MACD)
3. **Histogram**: MACD Line - Signal Line

**Trading Signals:**
- **Buy**: MACD line crosses above Signal line (bullish crossover)
- **Sell**: MACD line crosses below Signal line (bearish crossover)

## Usage Examples

### Basic Usage
```python
from macd import MACDBacktester

# Initialize backtester
backtester = MACDBacktester(exchange_name='binance', symbol='BTC/USDT', timeframe='1h')

# Fetch data
data = backtester.fetch_bitcoin_data(days=1825)  # 5 years

# Calculate MACD with default parameters (12, 26, 9)
macd_data = backtester.calculate_macd(data)

# Generate trading signals
signals_data = backtester.generate_signals(macd_data)

# Run backtest
results = backtester.backtest_strategy(signals_data)

# Print results
backtester.print_summary(results)
```

### Custom Parameters
```python
# Test with custom MACD parameters
macd_data = backtester.calculate_macd(data, fast_period=8, slow_period=21, signal_period=5)
signals_data = backtester.generate_signals(macd_data)
results = backtester.backtest_strategy(signals_data)
```

### Parameter Optimization
```python
# Find best parameters automatically
optimization_results = backtester.optimize_parameters(
    data, 
    fast_range=(8, 15), 
    slow_range=(21, 30), 
    signal_range=(7, 12)
)

# Get best parameters
best_params = optimization_results.iloc[0]
print(f"Best parameters: Fast={best_params['fast_period']}, Slow={best_params['slow_period']}, Signal={best_params['signal_period']}")
```

## Configuration Options

### Exchange and Symbol
```python
# Different exchanges
backtester = MACDBacktester(exchange_name='coinbase', symbol='BTC/USD')
backtester = MACDBacktester(exchange_name='kraken', symbol='BTC/EUR')

# Different cryptocurrencies
backtester = MACDBacktester(symbol='ETH/USDT')
backtester = MACDBacktester(symbol='ADA/USDT')
```

### Timeframes
```python
# Different timeframes
backtester = MACDBacktester(timeframe='1h')   # 1 hour
backtester = MACDBacktester(timeframe='4h')   # 4 hours
backtester = MACDBacktester(timeframe='1d')   # 1 day
backtester = MACDBacktester(timeframe='1w')   # 1 week
```

## Output Files

- `macd_optimization_results.csv`: Complete optimization results with all tested parameter combinations
- Charts: Visual representation of price, MACD, and trading signals

## Performance Metrics

The system calculates:
- **Total Return**: Overall profit/loss percentage
- **Buy & Hold Return**: Comparison with simply holding Bitcoin
- **Win Rate**: Percentage of profitable trades
- **Total Trades**: Number of completed trades
- **Average Profit**: Average profit per winning trade

## Tips for Best Results

1. **Use sufficient data**: At least 2-5 years for reliable results
2. **Test different timeframes**: Higher timeframes (4h, 1d) often give better results
3. **Consider transaction costs**: Real trading involves fees that reduce profits
4. **Combine with other indicators**: MACD works best when combined with other technical indicators
5. **Regular re-optimization**: Market conditions change, so re-run optimization periodically

## Troubleshooting

**Common Issues:**
- **No data fetched**: Check your internet connection and exchange availability
- **Rate limiting**: Some exchanges have rate limits; add delays if needed
- **Memory issues**: Reduce the parameter optimization ranges for large datasets

## Next Steps

- Implement stop-loss and take-profit levels
- Add more technical indicators (RSI, Bollinger Bands, etc.)
- Implement portfolio management features
- Add paper trading functionality
- Create a web interface for easier use

## Disclaimer

This is for educational purposes only. Cryptocurrency trading involves significant risk. Always do your own research and never invest more than you can afford to lose. 