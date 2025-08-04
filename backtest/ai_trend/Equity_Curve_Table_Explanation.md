# 📈 Equity Curve Table - Technical Documentation

## Overview

The **equity curve table** is a critical component of our AI Trend Navigator system that tracks portfolio performance over time, enabling comprehensive comparison between our AI trading strategy and a simple buy-and-hold approach.

## 🎯 What is an Equity Curve?

An **equity curve** is a line chart that visualizes how portfolio value changes over time. It's one of the most important performance analysis tools in trading because it reveals:

- **Portfolio growth** (or decline) patterns over time
- **Drawdown periods** (when the strategy is losing money)
- **Recovery patterns** (how quickly the strategy bounces back from losses)
- **Performance comparison** vs benchmark strategies
- **Risk assessment** through volatility and drawdown analysis

## 🗄️ Database Table Structure

### Core Table: `ai_trend_analysis.equity_curve`

```sql
CREATE TABLE ai_trend_analysis.equity_curve (
    id SERIAL PRIMARY KEY,
    
    -- Core Performance Metrics
    timeframe VARCHAR(10) NOT NULL,                    -- 4H, 8H, 1D, 1W, 1M
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,       -- Point in time
    strategy_portfolio_value DECIMAL(15,2) NOT NULL,   -- AI strategy portfolio value
    buyhold_portfolio_value DECIMAL(15,2) NOT NULL,    -- Buy & hold portfolio value
    strategy_cumulative_return DECIMAL(10,4) NOT NULL, -- % return since start
    buyhold_cumulative_return DECIMAL(10,4) NOT NULL,  -- % return for buy & hold
    strategy_drawdown DECIMAL(10,4) NOT NULL,          -- Current drawdown %
    
    -- Market Context
    position_status VARCHAR(10) NOT NULL,              -- BUY, SELL, HOLD
    btc_price DECIMAL(15,8) NOT NULL,                  -- Bitcoin price at timestamp
    
    -- Strategy Parameters
    k_value INTEGER NOT NULL,                          -- K-nearest neighbors parameter
    smoothing_factor INTEGER NOT NULL,                 -- Signal smoothing parameter
    window_size INTEGER NOT NULL,                      -- Analysis window size
    ma_period INTEGER NOT NULL,                        -- Moving average period
    
    -- Metadata
    date_analyzed DATE NOT NULL,                       -- When analysis was run
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Supporting Database Views

#### 1. `latest_equity_curves`
Shows the most recent equity curve data across all timeframes:
```sql
SELECT timeframe, strategy_portfolio_value, buyhold_portfolio_value, 
       strategy_cumulative_return, buyhold_cumulative_return
FROM ai_trend_analysis.latest_equity_curves 
WHERE timeframe = '4H'
ORDER BY timestamp;
```

#### 2. `equity_curve_summary`
Provides aggregated performance statistics:
```sql
SELECT timeframe, max_strategy_return, max_buyhold_return, max_drawdown
FROM ai_trend_analysis.equity_curve_summary;
```

## 💡 Key Features & Capabilities

### 1. **Real-Time Portfolio Tracking**
Instead of only final results, we track **every moment**:
- **Initial Capital**: $10,000 for both strategies
- **AI Strategy**: Executes buy/sell based on AI trend signals
- **Buy & Hold**: Purchases Bitcoin on day 1, holds indefinitely

### 2. **Comprehensive Performance Comparison**
At every timestamp, simultaneous tracking of:
```
Example Data Points:
2023-03-15: AI Strategy = $25,430 | Buy & Hold = $22,100 | AI Advantage = +15.1%
2023-06-20: AI Strategy = $18,200 | Buy & Hold = $31,500 | AI Disadvantage = -42.2%
2023-12-01: AI Strategy = $45,600 | Buy & Hold = $28,900 | AI Advantage = +57.8%
```

### 3. **Advanced Drawdown Analysis**
Tracks portfolio decline periods:
- **Maximum Drawdown**: Peak-to-trough decline percentage
- **Recovery Time**: Duration to return to previous highs
- **Drawdown Frequency**: How often significant declines occur
- **Risk Assessment**: Comparative risk vs buy-and-hold

## 📊 Sample Data Structure

| Timestamp | Timeframe | Strategy Value | Buy&Hold Value | Strategy Return | Buy&Hold Return | Drawdown | Position | BTC Price |
|-----------|-----------|---------------|----------------|-----------------|-----------------|----------|----------|-----------|
| 2023-01-01T00:00:00Z | 4H | $10,000.00 | $10,000.00 | 0.0000% | 0.0000% | 0.0000% | HOLD | $16,625.00 |
| 2023-01-01T04:00:00Z | 4H | $10,000.00 | $10,120.00 | 0.0000% | 1.2000% | 0.0000% | HOLD | $16,825.00 |
| 2023-01-01T08:00:00Z | 4H | $10,850.00 | $10,340.00 | 8.5000% | 3.4000% | 0.0000% | BUY | $17,125.00 |
| 2023-01-01T12:00:00Z | 4H | $12,200.00 | $11,500.00 | 22.0000% | 15.0000% | 0.0000% | BUY | $18,900.00 |
| 2023-01-02T00:00:00Z | 4H | $9,800.00 | $11,200.00 | -2.0000% | 12.0000% | -19.67% | SELL | $18,400.00 |

## 🎯 Business Value & Applications

### **Strategy Evaluation**
- **Visual Performance Proof**: Clear graphical evidence of strategy effectiveness
- **Risk Assessment**: Quantified drawdown and volatility metrics
- **Entry/Exit Validation**: Timing effectiveness analysis
- **Parameter Optimization**: Performance across different AI parameters

### **Decision Making Support**
- **Position Sizing**: "Should we increase allocation during profitable periods?"
- **Risk Management**: "How long do typical drawdowns last?"
- **Timeframe Selection**: "Which timeframe performs best in different market conditions?"
- **Strategy Switching**: "When should we pause the AI strategy?"

### **Reporting & Communication**
- **Professional Charts**: Investor-grade performance visualizations
- **Risk Metrics**: Compliance and risk management reporting
- **Performance Attribution**: Understanding return sources
- **Comparative Analysis**: Strategy vs benchmark performance

## 🚀 Current Performance Metrics

Based on the latest analysis (2025-07-16):

| Timeframe | Strategy Return | Buy&Hold Return | Outperformance | Total Trades | Win Rate |
|-----------|----------------|-----------------|----------------|--------------|----------|
| **4H** | 855.39% | ~1,189% | -333.61% | 407 | ~37% |
| **8H** | 1,895.59% | ~1,189% | +706.59% | 145 | ~45% |
| **1D** | 1,903.03% | ~1,189% | +714.03% | 35 | ~57% |
| **1W** | 1,773.72% | ~1,189% | +584.72% | 37 | ~54% |
| **1M** | 1,474.58% | ~1,189% | +285.58% | 48 | ~52% |

## 🔧 Technical Implementation

### **Data Collection Process**
1. **Real-time Calculation**: Portfolio values computed at every timestamp
2. **Dual Tracking**: Simultaneous AI strategy and buy-hold simulation
3. **Batch Storage**: Efficient database insertion with duplicate prevention
4. **Parameter Tracking**: Complete audit trail of AI parameters used

### **Performance Optimization**
- **Indexed Queries**: Fast retrieval by timeframe, date, and timestamp
- **Batch Operations**: Efficient bulk data insertion
- **Duplicate Prevention**: Avoids redundant data storage
- **View Optimization**: Pre-computed aggregations for common queries

## 📈 Chart Implementation Examples

### **JavaScript/Chart.js Example**
```javascript
// Fetch equity curve data
const equityData = await supabase
  .schema('ai_trend_analysis')
  .from('latest_equity_curves')
  .select('timestamp, strategy_portfolio_value, buyhold_portfolio_value')
  .eq('timeframe', '4H')
  .order('timestamp');

// Create dual-line chart
const chartData = {
  labels: equityData.map(d => d.timestamp),
  datasets: [
    {
      label: 'AI Strategy',
      data: equityData.map(d => d.strategy_portfolio_value),
      borderColor: 'rgb(75, 192, 192)',
      backgroundColor: 'rgba(75, 192, 192, 0.2)',
    },
    {
      label: 'Buy & Hold',
      data: equityData.map(d => d.buyhold_portfolio_value),
      borderColor: 'rgb(255, 99, 132)',
      backgroundColor: 'rgba(255, 99, 132, 0.2)',
    }
  ]
};
```

### **SQL Analysis Queries**
```sql
-- Get drawdown periods longer than 30 days
SELECT timeframe, 
       MIN(timestamp) as drawdown_start,
       MAX(timestamp) as drawdown_end,
       MIN(strategy_drawdown) as max_drawdown_in_period
FROM ai_trend_analysis.equity_curve 
WHERE strategy_drawdown < -5.0
GROUP BY timeframe, 
         (timestamp::date - ROW_NUMBER() OVER (PARTITION BY timeframe ORDER BY timestamp)::int);

-- Compare final performance across timeframes
SELECT timeframe,
       LAST_VALUE(strategy_portfolio_value) OVER (PARTITION BY timeframe ORDER BY timestamp) as final_strategy_value,
       LAST_VALUE(buyhold_portfolio_value) OVER (PARTITION BY timeframe ORDER BY timestamp) as final_buyhold_value,
       MIN(strategy_drawdown) as max_drawdown
FROM ai_trend_analysis.equity_curve
WHERE date_analyzed = (SELECT MAX(date_analyzed) FROM ai_trend_analysis.equity_curve);
```

## 🛠️ Next Development Steps

### **Immediate Enhancements**
- **Interactive Dashboard**: Real-time equity curve visualization
- **Risk Metrics**: Sharpe ratio, Sortino ratio, Calmar ratio calculations
- **Correlation Analysis**: Strategy performance vs market conditions
- **Alert System**: Notification when drawdowns exceed thresholds

### **Advanced Features**
- **Rolling Performance**: 30-day, 90-day, 1-year rolling returns
- **Benchmark Comparison**: Performance vs multiple benchmarks (S&P 500, Gold, etc.)
- **Scenario Analysis**: Performance during different market regimes
- **Portfolio Optimization**: Multi-timeframe allocation strategies

## 📝 Summary

The equity curve table transforms raw trading signals into actionable performance intelligence. It provides a comprehensive foundation for:

- **Performance visualization** through detailed portfolio tracking
- **Risk assessment** via drawdown and volatility analysis  
- **Strategy optimization** through parameter and timeframe comparison
- **Investment decisions** based on quantified risk-return metrics

This system enables data-driven trading decisions by providing complete transparency into how our AI strategy performs against traditional buy-and-hold approaches across multiple timeframes and market conditions.

---

*Generated: 2025-07-16 | AI Trend Navigator v2.0* 