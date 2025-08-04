# MACD Signal Analysis Database Schema

## Overview
This database contains analyzed MACD trading signals for Bitcoin across different timeframes (4h, 8h, 1d, 1w). The analysis tracks two types of signals:
- **BUY signals**: Track performance during holding periods (BUY → SELL)
- **SELL signals**: Track performance during waiting periods (SELL → next BUY)

## Database Structure

### Schema: `macd_analysis`
All tables are in the `macd_analysis` schema.

---

## 📊 Main Tables

### 1. `signal_analysis` - Core Signal Data
**Purpose**: Contains individual BUY and SELL signal records with their performance metrics.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Primary key |
| `timeframe` | VARCHAR(10) | Trading timeframe ('4h', '8h', '1d', '1w') |
| `signal_type` | VARCHAR(10) | Signal type ('BUY' or 'SELL') |
| `entry_time` | TIMESTAMP | When the signal occurred |
| `exit_time` | TIMESTAMP | When the next opposite signal occurred |
| `entry_price` | DECIMAL | Bitcoin price at signal time |
| `exit_price` | DECIMAL | Bitcoin price at next opposite signal |
| `extreme_price` | DECIMAL | Price at maximum gain/drop point |
| `max_gain_pct` | DECIMAL | **BUY only**: Maximum gain % during holding period |
| `max_drop_pct` | DECIMAL | **SELL only**: Maximum drop % during waiting period |
| `final_return_pct` | DECIMAL | **BUY**: Actual return %, **SELL**: Opportunity saved % |
| `duration_to_extreme` | INTEGER | Periods to reach max gain/drop |
| `holding_period_duration` | INTEGER | **BUY only**: Actual holding period length |
| `waiting_period_duration` | INTEGER | **SELL only**: Actual waiting period length |
| `macd_value` | DECIMAL | MACD value at signal time |
| `signal_value` | DECIMAL | Signal line value at signal time |
| `histogram_value` | DECIMAL | MACD histogram value at signal time |

**Key Points for UI**:
- BUY signals have `max_gain_pct` and `holding_period_duration` filled
- SELL signals have `max_drop_pct` and `waiting_period_duration` filled
- `final_return_pct` means different things for BUY vs SELL signals

### 2. `macd_transactions` - Historical Transactions
**Purpose**: Processed trading transactions from MACD signals.

| Column | Type | Description |
|--------|------|-------------|
| `timeframe` | VARCHAR(10) | Trading timeframe |
| `timestamp` | TIMESTAMP | Transaction time |
| `type` | VARCHAR(10) | Transaction type ('BUY' or 'SELL') |
| `price` | DECIMAL | Transaction price |
| `quantity` | DECIMAL | Transaction quantity |
| `profit` | DECIMAL | Profit/loss from transaction |
| `return_pct` | DECIMAL | Return percentage |

### 3. `macd_timeframe_comparison` - Timeframe Summary
**Purpose**: Overall performance comparison across timeframes.

| Column | Type | Description |
|--------|------|-------------|
| `timeframe` | VARCHAR(10) | Trading timeframe |
| `data_points` | INTEGER | Number of data points analyzed |
| `actual_days` | INTEGER | Actual days of data coverage |
| `fast_period` | INTEGER | MACD fast period parameter |
| `slow_period` | INTEGER | MACD slow period parameter |
| `signal_period` | INTEGER | MACD signal period parameter |
| `total_return` | DECIMAL | Total return % for this timeframe |
| `buy_hold_return` | DECIMAL | Buy-and-hold return % for comparison |
| `total_trades` | INTEGER | Total number of trades |
| `win_rate` | DECIMAL | Win rate percentage |
| `final_capital` | DECIMAL | Final capital after all trades |

---

## 📈 Views (Pre-calculated Data)

### 1. `buy_signal_performance` - BUY Signal Summary
**Purpose**: Aggregated statistics for BUY signals by timeframe.

**Key Columns**:
- `total_buy_signals`: Number of BUY signals
- `profitable_trades`: Number of profitable BUY signals
- `win_rate_pct`: Win rate percentage
- `avg_final_return_pct`: Average actual return
- `avg_max_gain_pct`: Average maximum gain potential
- `best_max_gain_pct`: Best maximum gain achieved
- `avg_holding_periods`: Average holding duration

### 2. `sell_signal_performance` - SELL Signal Summary
**Purpose**: Aggregated statistics for SELL signals by timeframe.

**Key Columns**:
- `total_sell_signals`: Number of SELL signals
- `good_sell_decisions`: Number of good SELL decisions
- `good_decision_rate_pct`: Good decision rate percentage
- `avg_opportunity_saved_pct`: Average opportunity saved
- `avg_max_drop_pct`: Average maximum drop after selling
- `biggest_drop_avoided_pct`: Biggest drop avoided by selling
- `avg_waiting_periods`: Average waiting duration

### 3. `signal_performance_summary` - Combined Summary
**Purpose**: Combined BUY and SELL performance in one view.

**Key Columns**:
- `buy_win_rate_pct`: BUY signal win rate
- `sell_accuracy_pct`: SELL signal accuracy rate
- `avg_max_gain_pct`: Average BUY max gain
- `avg_max_drop_pct`: Average SELL max drop
- `avg_holding_periods`: Average holding duration
- `avg_waiting_periods`: Average waiting duration

### 4. `best_performing_timeframes` - Ranked Performance
**Purpose**: Timeframes ranked by combined performance.

**Key Columns**:
- `combined_accuracy_pct`: Combined BUY/SELL accuracy
- `buy_win_rate_pct`: BUY signal win rate
- `sell_accuracy_pct`: SELL signal accuracy
- `total_buy_signals`: Total BUY signals
- `total_sell_signals`: Total SELL signals

### 5. `monthly_performance` - Time-based Performance
**Purpose**: Performance breakdown by month and signal type.

**Key Columns**:
- `month`: Month of analysis
- `signal_type`: BUY or SELL
- `signals_in_month`: Number of signals in that month
- `avg_return_per_signal`: Average return per signal
- `positive_signals`: Number of positive signals

---

## 🔧 Functions

### 1. `get_buy_signal_stats(timeframe)`
**Purpose**: Get detailed BUY signal statistics for a specific timeframe.

**Usage**: `SELECT * FROM macd_analysis.get_buy_signal_stats('4h')`

### 2. `get_sell_signal_stats(timeframe)`
**Purpose**: Get detailed SELL signal statistics for a specific timeframe.

**Usage**: `SELECT * FROM macd_analysis.get_sell_signal_stats('4h')`

### 3. `calculate_buy_sharpe_ratio(timeframe)`
**Purpose**: Calculate Sharpe ratio for BUY signals.

**Usage**: `SELECT macd_analysis.calculate_buy_sharpe_ratio('4h')`

---

## 🎨 UI Display Recommendations

### Dashboard Overview
```sql
-- Get overall performance summary
SELECT * FROM macd_analysis.best_performing_timeframes
ORDER BY combined_accuracy_pct DESC;
```

### BUY Signal Performance Chart
```sql
-- Get BUY signal performance by timeframe
SELECT 
    timeframe,
    total_buy_signals,
    win_rate_pct,
    avg_max_gain_pct,
    avg_final_return_pct,
    avg_holding_periods
FROM macd_analysis.buy_signal_performance
ORDER BY win_rate_pct DESC;
```

### SELL Signal Performance Chart
```sql
-- Get SELL signal performance by timeframe
SELECT 
    timeframe,
    total_sell_signals,
    good_decision_rate_pct,
    avg_max_drop_pct,
    avg_opportunity_saved_pct,
    avg_waiting_periods
FROM macd_analysis.sell_signal_performance
ORDER BY good_decision_rate_pct DESC;
```

### Recent Signals Table
```sql
-- Get recent signals
SELECT 
    timeframe,
    signal_type,
    entry_time,
    exit_time,
    entry_price,
    exit_price,
    final_return_pct,
    CASE 
        WHEN signal_type = 'BUY' THEN max_gain_pct
        WHEN signal_type = 'SELL' THEN max_drop_pct
    END as extreme_pct
FROM macd_analysis.signal_analysis
ORDER BY entry_time DESC
LIMIT 50;
```

### Monthly Performance Trend
```sql
-- Get monthly performance trend
SELECT 
    month,
    signal_type,
    signals_in_month,
    avg_return_per_signal,
    positive_signals
FROM macd_analysis.monthly_performance
ORDER BY month DESC, signal_type;
```

---

## 📊 Key Metrics Explained

### For BUY Signals:
- **Max Gain %**: Highest gain achieved during holding period
- **Final Return %**: Actual return when sold
- **Win Rate**: Percentage of profitable BUY signals
- **Holding Period**: Duration from BUY to SELL signal

### For SELL Signals:
- **Max Drop %**: How much further price dropped after selling
- **Opportunity Saved %**: How much loss was avoided by selling
- **Good Decision Rate**: Percentage of SELL signals that saved money
- **Waiting Period**: Duration from SELL to next BUY signal

### Performance Interpretation:
- **Higher Max Gain %**: Better potential upside
- **Higher Final Return %**: Better actual performance
- **Higher Win Rate**: More reliable signals
- **Lower Max Drop %**: Better timing of exits

---

## 🚀 Getting Started

### Connect to Database
```python
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
```

### Basic Query
```python
# Get all timeframe performance
result = supabase.table('best_performing_timeframes').select('*').execute()
```

### Filter by Timeframe
```python
# Get 4h BUY signals
result = supabase.table('signal_analysis').select('*').eq('timeframe', '4h').eq('signal_type', 'BUY').execute()
```

---

## 📝 Notes for UI Development

1. **Signal Types**: Always distinguish between BUY and SELL signals in the UI
2. **Timeframes**: '4h', '8h', '1d', '1w' are the available timeframes
3. **Null Values**: BUY signals have null `max_drop_pct`, SELL signals have null `max_gain_pct`
4. **Performance Metrics**: Use the views for aggregated data, raw table for detailed analysis
5. **Time Zones**: All timestamps are in UTC
6. **Decimal Precision**: Financial values are stored as DECIMAL for precision

---

## 🔍 Sample Queries for Common UI Components

### Performance Cards
```sql
-- BUY Performance Card
SELECT 
    COUNT(*) as total_signals,
    ROUND(AVG(final_return_pct), 2) as avg_return,
    ROUND(AVG(max_gain_pct), 2) as avg_max_gain,
    COUNT(*) FILTER (WHERE final_return_pct > 0) as profitable_signals
FROM macd_analysis.signal_analysis 
WHERE signal_type = 'BUY' AND timeframe = '4h';
```

### Signal History Table
```sql
-- Recent signals with formatted data
SELECT 
    timeframe,
    signal_type,
    TO_CHAR(entry_time, 'YYYY-MM-DD HH24:MI') as signal_time,
    ROUND(entry_price, 2) as price,
    ROUND(final_return_pct, 2) as return_pct,
    CASE 
        WHEN signal_type = 'BUY' THEN ROUND(max_gain_pct, 2)
        ELSE ROUND(max_drop_pct, 2)
    END as extreme_pct
FROM macd_analysis.signal_analysis
ORDER BY entry_time DESC
LIMIT 20;
```

This database provides comprehensive MACD signal analysis data that can power a full trading dashboard with performance metrics, signal history, and comparative analysis across different timeframes. 