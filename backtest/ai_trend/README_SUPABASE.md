# AI Trend Navigator - Supabase Integration

This integration allows you to store your AI Trend Navigator trading data in Supabase for persistent storage and analysis.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Supabase
1. Create a new project at [supabase.com](https://supabase.com)
2. Go to Settings → API to get your Project URL and anon key
3. Run the SQL commands in `create_supabase_tables.sql` in your Supabase SQL editor

### 3. Get FMP API Key
1. Sign up at [financialmodelingprep.com](https://financialmodelingprep.com)
2. Get your API key from the dashboard

### 4. Configure Environment
```bash
python setup_supabase.py
```
Choose option 4 for complete setup, then edit the `.env` file with your credentials.

### 5. Test Connection
```bash
python setup_supabase.py
```
Choose option 3 to test your connection.

### 6. Run Daily Update
```bash
python daily_supabase_update.py
```

## 📊 Data Structure

The integration stores data in the `ai_trend_analysis` schema with three tables:

### 1. Performance Summary (`ai_trend_analysis.performance_summary`)
- **Purpose**: Stores daily performance metrics for each timeframe
- **Key Metrics**: 
  - Strategy return, Buy & Hold return, Outperformance
  - Total trades, Win rate
  - Average gain/loss, Max gain/loss
  - Max drawdown, Sharpe ratio, Sortino ratio
  - Profit factor, Best parameters

### 2. Transaction Records (`ai_trend_analysis.transaction_records`)
- **Purpose**: Stores all buy/sell transactions
- **Key Data**:
  - Timestamp, Action (BUY/SELL), Price, Quantity
  - Portfolio value, Signal strength
  - Strategy parameters (K, smoothing, window, MA)

### 3. AI Trend Data (`ai_trend_analysis.ai_trend_data`)
- **Purpose**: Stores raw AI trend signals and analysis (Enhanced for UI Charting)
- **Key Data**:
  - OHLCV data (Open, High, Low, Close, Volume)
  - Close price, Raw signal, Smoothed signal, MA signal
  - Trend direction (BULLISH/BEARISH/NEUTRAL)
  - Signal strength, Buy/Sell signal flags
  - Strategy parameters

## 🔧 Configuration

### Environment Variables (.env)
```
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
FMP_API_KEY=your_fmp_api_key
```

### Current Best Parameters
The system uses these optimized parameters:
- **4H**: K=19, Smoothing=20, Window=50, MA=15
- **8H**: K=19, Smoothing=20, Window=50, MA=15
- **1D**: K=19, Smoothing=30, Window=70, MA=12
- **1W**: K=25, Smoothing=10, Window=50, MA=8
- **1M**: K=19, Smoothing=6, Window=40, MA=12

## 📈 UI Charting Features

The `ai_trend_data` table is enhanced for UI charting with:
- **OHLCV Data**: Full candlestick data for price charts
- **Signal Lines**: Raw signal, smoothed signal, and MA signal for overlay
- **Buy/Sell Flags**: Boolean flags for marking entry/exit points
- **Trend Direction**: Color-coded trend indicators
- **Signal Strength**: For dynamic line thickness or opacity

### Chart Data Access
```python
# Get chart data for specific timeframe
chart_data = db_manager.get_chart_data('1D', days=30)

# Access via SQL view
SELECT * FROM ai_trend_analysis.chart_data 
WHERE timeframe = '1D' 
AND timestamp >= NOW() - INTERVAL '30 days'
ORDER BY timestamp;
```

## 🔄 Daily Automation

### Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set to run daily at your preferred time
4. Set action to start program: `python`
5. Add arguments: `daily_supabase_update.py`
6. Set start in directory to your project folder

### Linux/Mac Cron Job
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 6 AM
0 6 * * * cd /path/to/ai_trend && python daily_supabase_update.py
```

## 🛡️ Duplicate Prevention

The system prevents duplicate data through:
- **Unique indexes** on timeframe + date_analyzed
- **Upsert operations** that update existing records
- **Automatic cleanup** of old data (30 days retention)

## 📈 Performance Metrics

### Added Metrics (as requested)
- **Average Gain**: Average return on winning trades
- **Average Loss**: Average return on losing trades  
- **Max Gain**: Best single trade return
- **Max Loss**: Worst single trade return
- **Max Drawdown**: Maximum portfolio decline from peak

### Existing Metrics
- **Strategy Return**: Total return of AI strategy
- **Buy & Hold Return**: Simple buy and hold return
- **Outperformance**: Strategy vs Buy & Hold
- **Win Rate**: Percentage of profitable trades
- **Sharpe Ratio**: Risk-adjusted return
- **Sortino Ratio**: Downside risk-adjusted return
- **Profit Factor**: Gross profit / Gross loss

## 🔍 Querying Data

### Python Examples
```python
from supabase_integration import SupabaseTradeDataManager

# Initialize
db = SupabaseTradeDataManager(supabase_url, supabase_key)

# Get latest performance
performance = db.get_latest_performance_summary()

# Get recent transactions
transactions = db.get_transaction_history(timeframe='1D', limit=50)

# Get AI trend signals
signals = db.get_ai_trend_signals(timeframe='1D', limit=100)

# Get chart data for UI
chart_data = db.get_chart_data('1D', days=30)
```

### SQL Examples
```sql
-- Get latest performance for all timeframes
SELECT * FROM ai_trend_analysis.latest_performance_summary;

-- Get recent bullish signals
SELECT * FROM ai_trend_analysis.ai_trend_data 
WHERE trend_direction = 'BULLISH' 
AND date_analyzed >= CURRENT_DATE - INTERVAL '7 days';

-- Get buy/sell signals for charting
SELECT timestamp, close_price, buy_signal, sell_signal 
FROM ai_trend_analysis.chart_data 
WHERE timeframe = '1D' 
AND (buy_signal = true OR sell_signal = true)
ORDER BY timestamp DESC;
```

## 🚨 Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check SUPABASE_URL and SUPABASE_ANON_KEY in .env
   - Verify Supabase project is active
   - Check RLS policies if using service role key

2. **FMP API Errors**
   - Verify FMP_API_KEY is correct
   - Check FMP API limits and usage
   - Ensure proper symbol format (BTCUSD not BTC-USD)

3. **Table Not Found**
   - Run SQL commands in `create_supabase_tables.sql`
   - Check schema name is ai_trend_analysis

4. **Permission Denied**
   - Verify RLS policies allow your operations
   - Check if using correct key (anon vs service role)

### Debug Mode
Add to your .env file:
```
DEBUG=True
```

## 📋 File Structure

```
ai_trend/
├── supabase_integration.py      # Core Supabase integration
├── daily_supabase_update.py     # Daily update script (uses FMP API)
├── setup_supabase.py           # Setup and configuration
├── create_supabase_tables.sql  # Database schema with ai_trend_analysis
├── requirements.txt            # Python dependencies
├── README_SUPABASE.md         # This file
└── .env                       # Environment variables (create this)
```

## 🔒 Security Best Practices

1. **Never commit .env files** to version control
2. **Use RLS policies** to restrict data access
3. **Regularly rotate keys** in production
4. **Monitor usage** through Supabase dashboard
5. **Use service role key** only for admin operations
6. **Protect FMP API key** - monitor usage limits

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review Supabase documentation
3. Test connection with `setup_supabase.py`
4. Check system logs for error details

## 🔄 Updates

To update the system:
1. Pull latest changes
2. Run `pip install -r requirements.txt`
3. Check for schema changes in SQL files
4. Test connection before running daily updates 