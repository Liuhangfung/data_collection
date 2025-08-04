# Comprehensive SMA Strategy Backtesting System

A comprehensive Python-based backtesting system for Simple Moving Average (SMA) strategies on cryptocurrency markets using CCXT. This system runs 8 separate backtests across different time periods to identify optimal parameters.

## Features

- **Multi-Asset Support**: Test strategies on BTC/USDT and ETH/USDT
- **Multi-Timeframe Analysis**: Tests 2, 4, 6, and 8 years of historical data
- **Flexible SMA Range**: Test SMA periods from 100-200 (configurable)
- **8-Hour Timeframe**: Uses 8h candles for medium-term analysis
- **Comprehensive Metrics**: Calculates returns, Sharpe ratio, max drawdown, win rate, and more
- **Advanced Visualizations**: Generates comprehensive analysis charts
- **Detailed Export**: Saves results to multiple CSV files for thorough analysis

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Simply run the main script:
```bash
python sma_backtest.py
```

The system will:
1. Fetch 2, 4, 6, and 8 years of 8h OHLCV data for BTC/USDT and ETH/USDT
2. Test SMA crossover strategies for periods 100-200 on each time period
3. Calculate comprehensive performance metrics for each combination
4. Display best strategies for each time period and symbol
5. Generate detailed visualizations and save all results

This results in **8 separate backtests**:
- BTC/USDT: 2, 4, 6, 8 years
- ETH/USDT: 2, 4, 6, 8 years

## Strategy Logic

The SMA strategy uses simple crossover logic:
- **Buy Signal**: Price crosses above SMA
- **Sell Signal**: Price crosses below SMA
- **Position**: Long when price is above SMA, flat when below

## Output Files

**Individual Results:**
- `sma_results_BTC_USDT_2Y.csv` - BTC 2-year results
- `sma_results_BTC_USDT_4Y.csv` - BTC 4-year results
- `sma_results_BTC_USDT_6Y.csv` - BTC 6-year results
- `sma_results_BTC_USDT_8Y.csv` - BTC 8-year results
- `sma_results_ETH_USDT_2Y.csv` - ETH 2-year results
- `sma_results_ETH_USDT_4Y.csv` - ETH 4-year results
- `sma_results_ETH_USDT_6Y.csv` - ETH 6-year results
- `sma_results_ETH_USDT_8Y.csv` - ETH 8-year results

**Comprehensive Analysis:**
- `sma_comprehensive_results.csv` - All results combined
- `sma_comprehensive_analysis.png` - Overview charts
- `sma_BTC_USDT_detailed_analysis.png` - Detailed BTC analysis
- `sma_ETH_USDT_detailed_analysis.png` - Detailed ETH analysis

## Performance Metrics

- **Total Return**: Overall strategy return
- **Annualized Return**: Return adjusted for time period
- **Sharpe Ratio**: Risk-adjusted return metric
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Number of Trades**: Total trading signals generated

## Configuration

You can modify the following parameters in the `main()` function:

```python
symbols = ['BTC/USDT', 'ETH/USDT']  # Add more symbols
time_periods = [2, 4, 6, 8]         # Years of historical data
sma_range = (100, 200)              # Change SMA range  
initial_capital = 10000             # Starting capital
```

## Requirements

- Python 3.7+
- Internet connection for fetching market data
- No API keys required (uses public Binance data)

## Limitations

- Uses public API (rate limited, includes delays between requests)
- Assumes no trading fees or slippage
- Single SMA strategy only (can be extended)
- Maximum historical data depends on exchange limits
- Longer backtests (8 years) may take significant time to complete

## Example Results

The system will display comprehensive results like:

```
============================================================
RESULTS FOR BTC/USDT
============================================================

--- 2 Years Backtest ---
Best Total Return: SMA-145 | Return: 45.67% | Sharpe: 1.234 | Max DD: -15.23% | Trades: 23
Best Sharpe Ratio: SMA-160 | Return: 42.34% | Sharpe: 1.456 | Max DD: -12.45% | Trades: 19

--- 4 Years Backtest ---
Best Total Return: SMA-130 | Return: 78.91% | Sharpe: 1.123 | Max DD: -18.67% | Trades: 41
Best Sharpe Ratio: SMA-155 | Return: 71.23% | Sharpe: 1.345 | Max DD: -16.78% | Trades: 35

============================================================
OVERALL BEST STRATEGIES ACROSS ALL PERIODS
============================================================

TOP 10 STRATEGIES BY TOTAL RETURN:
    symbol  time_period_years  sma_period  total_return  annualized_return  sharpe_ratio
0  BTC/USDT                8         130        1.2456             0.1234        0.8765
1  ETH/USDT                6         145        1.1234             0.1123        0.7654
...
```

## Future Enhancements

- Multi-timeframe analysis
- More strategy types (dual SMA, EMA, etc.)
- Risk management features
- Portfolio optimization
- Real-time trading integration 