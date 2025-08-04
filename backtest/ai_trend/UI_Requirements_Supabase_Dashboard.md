# AI Trend Navigator - Supabase Dashboard UI Requirements

## 📋 Project Overview

The AI Trend Navigator is a cryptocurrency trading strategy analyzer that processes Bitcoin (BTC) data across multiple timeframes (4H, 8H, 1D, 1W, 1M) using machine learning algorithms to generate buy/sell signals and track performance metrics.

## 🗄️ Database Schema: `ai_trend_analysis`

### Tables Structure

#### 1. **performance_summary** 
*Stores aggregated performance metrics for each timeframe*

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | SERIAL PRIMARY KEY | Auto-incrementing ID | 1 |
| `timeframe` | VARCHAR(5) | Trading timeframe | "4H", "8H", "1D", "1W", "1M" |
| `total_return` | DECIMAL(10,2) | Strategy total return % | 865.79 |
| `annual_return` | DECIMAL(10,2) | Annualized return % | 7.86 |
| `total_trades` | INTEGER | Number of trades executed | 335 |
| `win_rate` | DECIMAL(5,2) | Percentage of winning trades | 36.9 |
| `max_drawdown` | DECIMAL(10,2) | Maximum drawdown % | -25.43 |
| `buy_hold_return` | DECIMAL(10,2) | Buy & hold return % | 1189.37 |
| `outperformance` | DECIMAL(10,2) | Strategy vs buy & hold | -323.58 |
| `sharpe_ratio` | DECIMAL(8,4) | Risk-adjusted return | 0.2156 |
| `final_portfolio_value` | DECIMAL(15,2) | Final portfolio value $ | 96579.00 |
| `start_date` | TIMESTAMP | Analysis start date | 2020-07-16 |
| `end_date` | TIMESTAMP | Analysis end date | 2025-07-15 |
| `years_analyzed` | DECIMAL(4,2) | Years of data analyzed | 5.00 |
| `date_analyzed` | DATE | When analysis was run | 2025-07-15 |
| `created_at` | TIMESTAMP | Record creation time | 2025-07-15 10:30:00 |
| `updated_at` | TIMESTAMP | Last update time | 2025-07-15 10:30:00 |

#### 2. **transaction_records**
*Stores individual buy/sell transactions with signal details*

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | SERIAL PRIMARY KEY | Auto-incrementing ID | 1 |
| `timeframe` | VARCHAR(5) | Trading timeframe | "4H" |
| `timestamp` | TIMESTAMP | Transaction timestamp | 2023-03-15 08:00:00 |
| `action` | VARCHAR(10) | Buy or sell action | "buy", "sell" |
| `price` | DECIMAL(12,2) | Bitcoin price at transaction | 67500.00 |
| `quantity` | DECIMAL(18,8) | BTC quantity traded | 0.14814814 |
| `portfolio_value` | DECIMAL(15,2) | Portfolio value after trade | 25000.00 |
| `signal_strength` | DECIMAL(8,4) | AI signal strength | 0.7234 |
| `k_value` | INTEGER | K parameter used | 23 |
| `smoothing_factor` | INTEGER | Smoothing parameter | 10 |
| `window_size` | INTEGER | Window size parameter | 30 |
| `ma_period` | INTEGER | Moving average period | 5 |
| `date_analyzed` | DATE | Analysis run date | 2025-07-15 |
| `created_at` | TIMESTAMP | Record creation time | 2025-07-15 10:30:00 |
| `updated_at` | TIMESTAMP | Last update time | 2025-07-15 10:30:00 |

#### 3. **ai_trend_data**
*Stores detailed AI trend analysis data points*

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | SERIAL PRIMARY KEY | Auto-incrementing ID | 1 |
| `timeframe` | VARCHAR(5) | Trading timeframe | "4H" |
| `timestamp` | TIMESTAMP | Data point timestamp | 2023-03-15 08:00:00 |
| `open_price` | DECIMAL(12,2) | Opening price | 67000.00 |
| `high_price` | DECIMAL(12,2) | High price | 67800.00 |
| `low_price` | DECIMAL(12,2) | Low price | 66500.00 |
| `close_price` | DECIMAL(12,2) | Closing price | 67500.00 |
| `volume` | DECIMAL(20,8) | Trading volume | 1234567.89 |
| `signal` | VARCHAR(10) | Trading signal | "buy", "sell", "hold" |
| `trend_direction` | VARCHAR(10) | Trend direction | "up", "down", "neutral" |
| `buy_signal` | BOOLEAN | Buy signal flag | true |
| `sell_signal` | BOOLEAN | Sell signal flag | false |
| `signal_strength` | DECIMAL(8,4) | Signal strength | 0.7234 |
| `smoothed_signal` | DECIMAL(12,4) | Smoothed signal value | 67234.5678 |
| `ma_signal` | DECIMAL(12,4) | Moving average signal | 66800.1234 |
| `k_value` | INTEGER | K parameter | 23 |
| `smoothing_factor` | INTEGER | Smoothing parameter | 10 |
| `window_size` | INTEGER | Window size parameter | 30 |
| `ma_period` | INTEGER | MA period parameter | 5 |
| `date_analyzed` | DATE | Analysis run date | 2025-07-15 |
| `created_at` | TIMESTAMP | Record creation time | 2025-07-15 10:30:00 |
| `updated_at` | TIMESTAMP | Last update time | 2025-07-15 10:30:00 |

## 🎨 UI Dashboard Requirements

### 1. **Main Dashboard Overview**

#### Performance Summary Cards
Display key metrics for each timeframe in card format:

```
┌─────────────────────────────────────────────────────┐
│                    4H TIMEFRAME                     │
├─────────────────────────────────────────────────────┤
│ Total Return: 865.79%     │ Annual Return: 7.86%    │
│ Total Trades: 335         │ Win Rate: 36.9%         │
│ Max Drawdown: -25.43%     │ Sharpe Ratio: 0.22      │
│ Final Portfolio: $96,579  │ Outperformance: -323.58%│
└─────────────────────────────────────────────────────┘
```

#### Key Features:
- **Color coding**: Green for positive returns, red for negative
- **Comparison indicators**: Show best/worst performing timeframe
- **Trend arrows**: Up/down arrows for performance direction
- **Last updated**: Show when data was last refreshed

### 2. **Detailed Performance Table**

Interactive table showing all timeframes:

| Timeframe | Total Return | Annual Return | Trades | Win Rate | Max Drawdown | Sharpe Ratio | Status |
|-----------|--------------|---------------|--------|----------|--------------|--------------|--------|
| 4H        | 865.79%      | 7.86%        | 335    | 36.9%    | -25.43%     | 0.22        | ✅ Active |
| 8H        | 1887.57%     | 22.07%       | 145    | 33.8%    | -40.18%     | 0.20        | ✅ Active |
| 1D        | 1888.56%     | 15.23%       | 35     | 57.1%    | -15.21%     | 0.45        | ✅ Active |
| 1W        | 1760.18%     | 12.45%       | 37     | 54.1%    | -22.13%     | 0.38        | ✅ Active |
| 1M        | 1461.97%     | 9.87%        | 48     | 45.8%    | -18.76%     | 0.31        | ✅ Active |

#### Features:
- **Sortable columns**: Click to sort by any metric
- **Filtering**: Filter by timeframe, date range, performance
- **Export**: Download data as CSV/Excel
- **Tooltips**: Hover explanations for metrics

### 3. **Price Chart with Signals**

Interactive candlestick chart showing:
- **OHLC data**: Candlestick chart for selected timeframe
- **Buy/Sell signals**: Green triangles (buy), red triangles (sell)
- **Trend indicators**: AI trend direction overlay
- **Portfolio value**: Secondary Y-axis showing portfolio growth

#### Chart Controls:
- **Timeframe selector**: Dropdown to switch between 4H, 8H, 1D, 1W, 1M
- **Date range picker**: Select custom date ranges
- **Indicator toggles**: Show/hide various indicators
- **Zoom controls**: Pan and zoom functionality

### 4. **Transaction History**

Detailed transaction log table:

| Date | Time | Action | Price | Quantity | Portfolio Value | Signal Strength | P&L |
|------|------|--------|-------|----------|----------------|-----------------|-----|
| 2023-03-15 | 08:00 | BUY | $67,500 | 0.148148 | $25,000 | 0.72 | - |
| 2023-03-20 | 16:00 | SELL | $69,200 | 0.148148 | $25,252 | 0.68 | +$252 |

#### Features:
- **Pagination**: Handle large datasets
- **Search**: Find specific transactions
- **Filters**: By action, date range, timeframe
- **P&L calculation**: Profit/loss per trade

### 5. **Analytics Dashboard**

#### Monthly Performance Heatmap
```
        Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec
2023   +2.5% +1.2% +4.8% -0.5% +3.2% +1.8% +2.1% +0.9% +1.5% +2.3% +1.1% +0.8%
2024   +1.8% +2.9% +0.5% +3.7% +1.2% +2.4% +0.3% +1.9% +2.8% +1.6% +2.2% +1.0%
2025   +2.1% +1.7% +3.2% +0.9% +2.5% +1.3% +1.8% -     -     -     -     -
```

#### Trade Distribution Charts
- **Win/Loss ratio**: Pie chart showing winning vs losing trades
- **Return distribution**: Histogram of trade returns
- **Trade frequency**: Bar chart showing trades per month/week

### 6. **Real-time Monitoring**

#### Live Status Panel
```
┌─────────────────────────────────────────┐
│            SYSTEM STATUS                │
├─────────────────────────────────────────┤
│ Last Update: 2025-07-15 10:30:00        │
│ Data Status: ✅ Current                 │
│ Next Update: 2025-07-16 10:30:00        │
│ Active Timeframes: 5/5                  │
│ CCXT Connection: ✅ Connected           │
│ Database Status: ✅ Healthy             │
└─────────────────────────────────────────┘
```

#### Alert System
- **Performance alerts**: When strategy underperforms
- **Signal alerts**: Strong buy/sell signals
- **System alerts**: Data fetch failures, connection issues

## 🔧 Technical Implementation

### Supabase Configuration

#### RLS (Row Level Security) Policies
```sql
-- Enable RLS on all tables
ALTER TABLE performance_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE transaction_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_trend_data ENABLE ROW LEVEL SECURITY;

-- Create policies for read access
CREATE POLICY "Enable read access for all users" ON performance_summary
FOR SELECT USING (true);

CREATE POLICY "Enable read access for all users" ON transaction_records
FOR SELECT USING (true);

CREATE POLICY "Enable read access for all users" ON ai_trend_data
FOR SELECT USING (true);
```

#### Useful Views for UI

**1. Latest Performance Summary**
```sql
CREATE VIEW latest_performance AS
SELECT *
FROM performance_summary
WHERE date_analyzed = (SELECT MAX(date_analyzed) FROM performance_summary);
```

**2. Trade Summary by Timeframe**
```sql
CREATE VIEW trade_summary AS
SELECT 
    timeframe,
    COUNT(*) as total_trades,
    SUM(CASE WHEN action = 'buy' THEN 1 ELSE 0 END) as buy_trades,
    SUM(CASE WHEN action = 'sell' THEN 1 ELSE 0 END) as sell_trades,
    AVG(signal_strength) as avg_signal_strength,
    DATE(MAX(timestamp)) as last_trade_date
FROM transaction_records
GROUP BY timeframe;
```

**3. Daily Performance**
```sql
CREATE VIEW daily_performance AS
SELECT 
    timeframe,
    DATE(timestamp) as trade_date,
    COUNT(*) as trades_count,
    AVG(portfolio_value) as avg_portfolio_value,
    MIN(portfolio_value) as min_portfolio_value,
    MAX(portfolio_value) as max_portfolio_value
FROM transaction_records
GROUP BY timeframe, DATE(timestamp)
ORDER BY trade_date DESC;
```

### API Endpoints Suggestions

#### REST API Endpoints (using Supabase Auto-generated)
```
GET /rest/v1/performance_summary?select=*
GET /rest/v1/transaction_records?select=*&timeframe=eq.4H
GET /rest/v1/ai_trend_data?select=*&timeframe=eq.8H&order=timestamp.desc&limit=1000
```

#### Real-time Subscriptions
```javascript
// Listen for new performance data
const performanceChannel = supabase
  .channel('performance_updates')
  .on('postgres_changes', 
    { event: 'UPDATE', schema: 'public', table: 'performance_summary' },
    (payload) => {
      // Update UI with new performance data
      updatePerformanceCards(payload.new);
    }
  )
  .subscribe();
```

## 📱 Mobile Responsiveness

### Responsive Design Requirements
- **Mobile-first approach**: Design for mobile, enhance for desktop
- **Touch-friendly**: Large buttons, adequate spacing
- **Swipe gestures**: For chart navigation and table scrolling
- **Collapsible sections**: Accordion-style for mobile

### Mobile-Specific Features
- **Push notifications**: For important signals and alerts
- **Offline support**: Cache recent data for offline viewing
- **Quick actions**: Swipe gestures for common actions

## 🎯 Key Metrics to Highlight

### Primary KPIs
1. **Total Return %**: Most important metric
2. **Annual Return %**: Annualized performance
3. **Win Rate %**: Success rate of trades
4. **Sharpe Ratio**: Risk-adjusted returns
5. **Max Drawdown**: Worst performance period

### Secondary Metrics
- **Total Trades**: Activity level
- **Outperformance**: vs Buy & Hold
- **Portfolio Value**: Current value
- **Years of Data**: Analysis period

## 🔍 Filter and Search Features

### Date Range Filters
- **Preset ranges**: Last 30 days, 90 days, 1 year, All time
- **Custom range picker**: Calendar-based selection
- **Relative dates**: Last week, month, quarter

### Timeframe Filters
- **Multi-select**: Choose multiple timeframes
- **Comparison mode**: Side-by-side comparison
- **Performance ranking**: Best to worst

### Advanced Filters
- **Trade type**: Buy/sell only
- **Signal strength**: Strong signals only (>0.7)
- **Profitable trades**: Winning trades only
- **Date range**: Custom date selections

## 🚀 Performance Optimization

### Data Loading
- **Pagination**: Load data in chunks
- **Lazy loading**: Load charts on demand
- **Caching**: Cache frequently accessed data
- **Compression**: Minimize data transfer

### UI Performance
- **Virtual scrolling**: For large datasets
- **Debounced search**: Prevent excessive API calls
- **Optimistic updates**: Show changes immediately
- **Loading states**: Skeleton screens, spinners

## 📊 Dashboard Layout Suggestions

### Desktop Layout (Large Screens)
```
┌─────────────────────────────────────────────────────────────────┐
│                    HEADER & NAVIGATION                          │
├─────────────────────────────────────────────────────────────────┤
│  Performance Cards (4H, 8H, 1D, 1W, 1M)                       │
├─────────────────────────────────────────────────────────────────┤
│  Chart (70%)                    │  Transaction History (30%)    │
│                                 │                               │
│                                 │                               │
├─────────────────────────────────────────────────────────────────┤
│  Analytics Dashboard (Heatmap, Distribution Charts)            │
└─────────────────────────────────────────────────────────────────┘
```

### Mobile Layout (Small Screens)
```
┌─────────────────────┐
│   HEADER & MENU     │
├─────────────────────┤
│  Performance Cards  │
│  (Stack Vertically) │
├─────────────────────┤
│      Chart          │
│   (Full Width)      │
├─────────────────────┤
│   Transaction       │
│     History         │
├─────────────────────┤
│    Analytics        │
│   (Collapsed)       │
└─────────────────────┘
```

## 🎨 Color Scheme and Styling

### Color Palette
- **Primary**: #2563eb (Blue)
- **Success**: #10b981 (Green) - Positive returns
- **Danger**: #ef4444 (Red) - Negative returns
- **Warning**: #f59e0b (Yellow) - Neutral/alerts
- **Background**: #f8fafc (Light gray)
- **Text**: #1f2937 (Dark gray)

### Typography
- **Headers**: Inter, sans-serif, 24px, bold
- **Body**: Inter, sans-serif, 16px, regular
- **Numbers**: JetBrains Mono, monospace, 14px (for consistent alignment)

## 🔐 Security Considerations

### Data Protection
- **RLS policies**: Proper row-level security
- **API rate limiting**: Prevent abuse
- **Input validation**: Sanitize all inputs
- **HTTPS only**: Secure data transmission

### User Authentication
- **Role-based access**: Different permissions for different users
- **Session management**: Secure session handling
- **Password policies**: Strong password requirements

## 📝 Testing Requirements

### Unit Testing
- **Component testing**: Test individual UI components
- **API testing**: Test all API endpoints
- **Data validation**: Test data parsing and validation

### Integration Testing
- **Database connectivity**: Test Supabase connections
- **Real-time updates**: Test live data updates
- **Cross-browser**: Test on different browsers

### Performance Testing
- **Load testing**: Test with large datasets
- **Stress testing**: Test under high load
- **Mobile testing**: Test on various devices

## 🚀 Deployment Checklist

### Pre-deployment
- [ ] Database schema created
- [ ] RLS policies configured
- [ ] API endpoints tested
- [ ] Authentication setup
- [ ] Mobile responsiveness verified

### Post-deployment
- [ ] Performance monitoring setup
- [ ] Error tracking configured
- [ ] Analytics tracking enabled
- [ ] User feedback system
- [ ] Documentation updated

---

## 📞 Contact Information

For questions or clarifications about this UI requirements document, please contact:

**Project Lead**: [Your Name]  
**Email**: [Your Email]  
**Repository**: [GitHub Repository Link]  
**Supabase Project**: [Supabase Project URL]

---

*This document should be reviewed and updated as the project evolves. Last updated: 2025-07-15* 