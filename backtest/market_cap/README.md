# ETH/BTC Market Cap Analysis Tool

This tool provides comprehensive analysis of ETH vs BTC using both **price ratios** and **market capitalization ratios** using the CCXT Binance API and CoinGecko market data.

## 📊 What This Tool Does

- **Real-time ETH/BTC price data** from Binance via CCXT
- **Market capitalization comparison** between ETH and BTC
- **Historical analysis** with comprehensive charting
- **Live data streaming** capabilities
- **Comparison between price ratios vs market cap ratios**

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Quick Test

Run the simple example to see current ETH/BTC market data:

```bash
python quick_eth_btc_example.py
```

### 3. Comprehensive Analysis

Run the full analysis with charting:

```bash
python eth_btc_market_cap_analysis.py
```

## 📈 Features

### Price vs Market Cap Analysis

The tool compares:
- **ETH/BTC Price Ratio**: Direct price comparison
- **ETH/BTC Market Cap Ratio**: Market capitalization comparison (Price × Circulating Supply)

### Key Insights

1. **Market Cap Ratio vs Price Ratio Divergence**:
   - When market cap ratio > price ratio → ETH has higher relative supply
   - When price ratio > market cap ratio → BTC has higher relative supply

2. **Historical Context**:
   - Market cap ratio > 0.15: ETH relatively strong
   - Market cap ratio < 0.10: ETH relatively weak
   - Market cap ratio 0.10-0.15: Normal range

### Data Sources

- **Price Data**: Binance API via CCXT
- **Market Cap Data**: CoinGecko API (free tier)
- **Historical Data**: From 2021 to present (~4 years of daily data)

## 🛠 Usage Examples

### Basic Market Data

```python
from eth_btc_market_cap_analysis import ETHBTCMarketCapAnalyzer

analyzer = ETHBTCMarketCapAnalyzer()
current_data = analyzer.get_current_market_data()
print(f"ETH/BTC Market Cap Ratio: {current_data['eth_btc_market_cap_ratio']:.4f}")
```

### Generate Charts

```python
# Create comprehensive analysis chart
analyzer.create_comprehensive_chart(days=365, save_chart=True)
```

### Real-time Streaming

```python
# Stream data for 30 minutes
analyzer.get_real_time_data_stream(duration_minutes=30)
```

## 📊 Chart Outputs

The comprehensive analysis generates a 4-panel chart:

1. **ETH/BTC Price Ratio**: Historical price ratio trend
2. **Market Cap Ratios**: Both ETH/BTC and BTC/ETH market cap ratios on dual y-axes
3. **BTC and ETH USD Prices**: Individual price movements
4. **Market Cap Values**: Absolute market capitalizations

## 🔧 Configuration

### API Keys (Optional)

For higher rate limits, you can add Binance API keys:

```python
analyzer = ETHBTCMarketCapAnalyzer()
analyzer.exchange.apiKey = 'your_api_key'
analyzer.exchange.secret = 'your_secret'
```

### Timeframes

Supported timeframes for historical data:
- `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, `1w`

### Data Limits

- **CoinGecko Free Tier**: Maximum historical data (from 2021 to present)
- **Binance**: Extensive historical data available
- **Real-time Updates**: 1-minute intervals recommended

## 📱 Sample Output

```
ETH/BTC MARKET ANALYSIS
============================================================
Timestamp: 2025-01-25 18:45:30

CURRENT PRICES:
  BTC: $108,786.00
  ETH: $2,568.24
  ETH/BTC Price Ratio: 0.023595

MARKET CAPITALIZATIONS:
  BTC Market Cap: $2,163,184,563,088 ($2.163T)
  ETH Market Cap: $310,039,926,898 ($0.310T)
  ETH/BTC Market Cap Ratio: 0.1433
  BTC/ETH Market Cap Ratio: 6.98

24H CHANGES:
  BTC 24h Change: +2.52%
  ETH 24h Change: +5.80%

ANALYSIS:
  📊 ETH market cap ratio is 507.5% HIGHER than price ratio
     This suggests ETH has higher circulating supply relative to BTC
  ⚖️  ETH market cap ratio (0.1433) is in normal range
============================================================
```

## 🔍 Understanding the Data

### Market Cap Formula
```
Market Cap = Current Price × Circulating Supply
ETH/BTC Market Cap Ratio = ETH Market Cap / BTC Market Cap
```

### Why Market Cap Matters
- Market cap reflects total value of all coins in circulation
- More meaningful for comparing different cryptocurrencies
- Accounts for supply differences between ETH and BTC

### Key Metrics Tracked
- Current prices from Binance
- Market capitalizations from CoinGecko
- 24-hour price changes
- Historical trends and patterns
- Real-time ratio monitoring

## 🚨 Error Handling

The tool includes robust error handling for:
- Network connectivity issues
- API rate limiting
- Data validation
- Missing historical data

## 📝 Requirements

- Python 3.7+
- Internet connection for API access
- No API keys required (but recommended for higher limits)

## 🤝 Contributing

Feel free to submit issues or pull requests to improve the analysis capabilities!

## 📜 License

This tool is for educational and analysis purposes. Please respect API terms of service for Binance and CoinGecko. 