-- Create tables for AI Trend Navigator trading data
-- Execute these commands in your Supabase SQL editor

-- Create ai_trend_analysis schema
CREATE SCHEMA IF NOT EXISTS ai_trend_analysis;

-- 1. Performance Summary Table
CREATE TABLE ai_trend_analysis.performance_summary (
    id SERIAL PRIMARY KEY,
    timeframe VARCHAR(10) NOT NULL,
    strategy_return DECIMAL(10,2) NOT NULL,
    buyhold_return DECIMAL(10,2) NOT NULL,
    outperformance DECIMAL(10,2) NOT NULL,
    total_trades INTEGER NOT NULL,
    win_rate DECIMAL(5,2) NOT NULL,
    average_gain DECIMAL(10,2) NOT NULL,
    average_loss DECIMAL(10,2) NOT NULL,
    max_gain DECIMAL(10,2) NOT NULL,
    max_loss DECIMAL(10,2) NOT NULL,
    max_drawdown DECIMAL(10,2) NOT NULL,
    sharpe_ratio DECIMAL(10,4) NOT NULL,
    sortino_ratio DECIMAL(10,4) NOT NULL,
    profit_factor DECIMAL(10,4) NOT NULL,
    best_params JSONB NOT NULL,
    date_analyzed DATE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create unique index to prevent duplicates
CREATE UNIQUE INDEX idx_performance_summary_timeframe_date 
ON ai_trend_analysis.performance_summary(timeframe, date_analyzed);

-- Create index for faster queries
CREATE INDEX idx_performance_summary_date_analyzed 
ON ai_trend_analysis.performance_summary(date_analyzed DESC);

-- 2. Transaction Records Table
CREATE TABLE ai_trend_analysis.transaction_records (
    id SERIAL PRIMARY KEY,
    timeframe VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('BUY', 'SELL')),
    price DECIMAL(15,8) NOT NULL,
    quantity DECIMAL(20,8) NOT NULL,
    portfolio_value DECIMAL(15,2) NOT NULL,
    signal_strength DECIMAL(10,6) NOT NULL,
    k_value INTEGER NOT NULL,
    smoothing_factor INTEGER NOT NULL,
    window_size INTEGER NOT NULL,
    ma_period INTEGER NOT NULL,
    date_analyzed DATE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create unique index to prevent duplicates
CREATE UNIQUE INDEX idx_transaction_records_unique 
ON ai_trend_analysis.transaction_records(timeframe, timestamp, date_analyzed);

-- Create indexes for faster queries
CREATE INDEX idx_transaction_records_timeframe 
ON ai_trend_analysis.transaction_records(timeframe);

CREATE INDEX idx_transaction_records_timestamp 
ON ai_trend_analysis.transaction_records(timestamp DESC);

CREATE INDEX idx_transaction_records_date_analyzed 
ON ai_trend_analysis.transaction_records(date_analyzed DESC);

CREATE INDEX idx_transaction_records_action 
ON ai_trend_analysis.transaction_records(action);

-- 3. AI Trend Data Table (Enhanced for UI Charting)
CREATE TABLE ai_trend_analysis.ai_trend_data (
    id SERIAL PRIMARY KEY,
    timeframe VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    close_price DECIMAL(15,8) NOT NULL,
    open_price DECIMAL(15,8) NOT NULL,
    high_price DECIMAL(15,8) NOT NULL,
    low_price DECIMAL(15,8) NOT NULL,
    volume DECIMAL(20,8) NOT NULL,
    signal DECIMAL(10,6) NOT NULL,
    smoothed_signal DECIMAL(10,6) NOT NULL,
    ma_signal DECIMAL(10,6) NOT NULL,
    trend_direction VARCHAR(20) NOT NULL CHECK (trend_direction IN ('BULLISH', 'BEARISH', 'NEUTRAL')),
    signal_strength DECIMAL(10,6) NOT NULL,
    buy_signal BOOLEAN NOT NULL DEFAULT FALSE,
    sell_signal BOOLEAN NOT NULL DEFAULT FALSE,
    k_value INTEGER NOT NULL,
    smoothing_factor INTEGER NOT NULL,
    window_size INTEGER NOT NULL,
    ma_period INTEGER NOT NULL,
    date_analyzed DATE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create unique index to prevent duplicates
CREATE UNIQUE INDEX idx_ai_trend_data_unique 
ON ai_trend_analysis.ai_trend_data(timeframe, timestamp, date_analyzed);

-- Create indexes for faster queries
CREATE INDEX idx_ai_trend_data_timeframe 
ON ai_trend_analysis.ai_trend_data(timeframe);

CREATE INDEX idx_ai_trend_data_timestamp 
ON ai_trend_analysis.ai_trend_data(timestamp DESC);

CREATE INDEX idx_ai_trend_data_date_analyzed 
ON ai_trend_analysis.ai_trend_data(date_analyzed DESC);

CREATE INDEX idx_ai_trend_data_trend_direction 
ON ai_trend_analysis.ai_trend_data(trend_direction);

CREATE INDEX idx_ai_trend_data_signal_strength 
ON ai_trend_analysis.ai_trend_data(signal_strength DESC);

-- Additional indexes for UI charting
CREATE INDEX idx_ai_trend_data_buy_signal 
ON ai_trend_analysis.ai_trend_data(buy_signal);

CREATE INDEX idx_ai_trend_data_sell_signal 
ON ai_trend_analysis.ai_trend_data(sell_signal);

-- 4. Equity Curve Table (For Portfolio Value Comparison Over Time)
CREATE TABLE ai_trend_analysis.equity_curve (
    id SERIAL PRIMARY KEY,
    timeframe VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    strategy_portfolio_value DECIMAL(15,2) NOT NULL,
    buyhold_portfolio_value DECIMAL(15,2) NOT NULL,
    strategy_cumulative_return DECIMAL(10,4) NOT NULL,
    buyhold_cumulative_return DECIMAL(10,4) NOT NULL,
    strategy_drawdown DECIMAL(10,4) NOT NULL,
    position_status VARCHAR(10) NOT NULL CHECK (position_status IN ('BUY', 'SELL', 'HOLD')),
    btc_price DECIMAL(15,8) NOT NULL,
    k_value INTEGER NOT NULL,
    smoothing_factor INTEGER NOT NULL,
    window_size INTEGER NOT NULL,
    ma_period INTEGER NOT NULL,
    date_analyzed DATE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create unique index to prevent duplicates
CREATE UNIQUE INDEX idx_equity_curve_unique 
ON ai_trend_analysis.equity_curve(timeframe, timestamp, date_analyzed);

-- Create indexes for faster queries
CREATE INDEX idx_equity_curve_timeframe 
ON ai_trend_analysis.equity_curve(timeframe);

CREATE INDEX idx_equity_curve_timestamp 
ON ai_trend_analysis.equity_curve(timestamp DESC);

CREATE INDEX idx_equity_curve_date_analyzed 
ON ai_trend_analysis.equity_curve(date_analyzed DESC);

CREATE INDEX idx_equity_curve_performance 
ON ai_trend_analysis.equity_curve(strategy_cumulative_return DESC);

-- Create view for latest equity curves across all timeframes
CREATE VIEW ai_trend_analysis.latest_equity_curves AS
SELECT 
    timeframe,
    timestamp,
    strategy_portfolio_value,
    buyhold_portfolio_value,
    strategy_cumulative_return,
    buyhold_cumulative_return,
    strategy_drawdown,
    position_status,
    btc_price,
    date_analyzed
FROM ai_trend_analysis.equity_curve 
WHERE date_analyzed = (SELECT MAX(date_analyzed) FROM ai_trend_analysis.equity_curve)
ORDER BY timeframe, timestamp;

-- Create view for equity curve comparison summary
CREATE VIEW ai_trend_analysis.equity_curve_summary AS
SELECT 
    timeframe,
    date_analyzed,
    COUNT(*) as data_points,
    MIN(timestamp) as start_date,
    MAX(timestamp) as end_date,
    FIRST_VALUE(strategy_portfolio_value) OVER (PARTITION BY timeframe, date_analyzed ORDER BY timestamp) as initial_value,
    LAST_VALUE(strategy_portfolio_value) OVER (PARTITION BY timeframe, date_analyzed ORDER BY timestamp ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as final_strategy_value,
    LAST_VALUE(buyhold_portfolio_value) OVER (PARTITION BY timeframe, date_analyzed ORDER BY timestamp ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as final_buyhold_value,
    MAX(strategy_cumulative_return) as max_strategy_return,
    MAX(buyhold_cumulative_return) as max_buyhold_return,
    MIN(strategy_drawdown) as max_drawdown
FROM ai_trend_analysis.equity_curve
GROUP BY timeframe, date_analyzed, strategy_portfolio_value, buyhold_portfolio_value, timestamp
ORDER BY timeframe, date_analyzed;

-- Enable Row Level Security (RLS) for better security
ALTER TABLE ai_trend_analysis.performance_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_trend_analysis.transaction_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_trend_analysis.ai_trend_data ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users (adjust as needed)
CREATE POLICY "Allow authenticated users to read performance_summary" 
ON ai_trend_analysis.performance_summary FOR SELECT 
TO authenticated 
USING (true);

CREATE POLICY "Allow authenticated users to insert/update performance_summary" 
ON ai_trend_analysis.performance_summary FOR ALL 
TO authenticated 
USING (true);

CREATE POLICY "Allow authenticated users to read transaction_records" 
ON ai_trend_analysis.transaction_records FOR SELECT 
TO authenticated 
USING (true);

CREATE POLICY "Allow authenticated users to insert/update transaction_records" 
ON ai_trend_analysis.transaction_records FOR ALL 
TO authenticated 
USING (true);

CREATE POLICY "Allow authenticated users to read ai_trend_data" 
ON ai_trend_analysis.ai_trend_data FOR SELECT 
TO authenticated 
USING (true);

CREATE POLICY "Allow authenticated users to insert/update ai_trend_data" 
ON ai_trend_analysis.ai_trend_data FOR ALL 
TO authenticated 
USING (true);

-- Create a view for latest performance summary
CREATE VIEW ai_trend_analysis.latest_performance_summary AS
SELECT DISTINCT ON (timeframe) *
FROM ai_trend_analysis.performance_summary
ORDER BY timeframe, date_analyzed DESC;

-- Create a view for recent signals
CREATE VIEW ai_trend_analysis.recent_signals AS
SELECT *
FROM ai_trend_analysis.ai_trend_data
WHERE date_analyzed >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY timeframe, timestamp DESC;

-- Create a view for chart data (optimized for UI)
CREATE VIEW ai_trend_analysis.chart_data AS
SELECT 
    timeframe,
    timestamp,
    close_price,
    open_price,
    high_price,
    low_price,
    volume,
    signal,
    smoothed_signal,
    ma_signal,
    trend_direction,
    signal_strength,
    buy_signal,
    sell_signal,
    date_analyzed
FROM ai_trend_analysis.ai_trend_data
ORDER BY timeframe, timestamp DESC;

-- Grant permissions to authenticated users
GRANT SELECT ON ai_trend_analysis.latest_performance_summary TO authenticated;
GRANT SELECT ON ai_trend_analysis.recent_signals TO authenticated;
GRANT SELECT ON ai_trend_analysis.chart_data TO authenticated; 