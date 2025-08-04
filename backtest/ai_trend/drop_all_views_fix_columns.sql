-- Comprehensive Fix: Drop ALL Views and Fix Columns
-- Run this in Supabase SQL Editor

-- Step 1: Drop ALL views in ai_trend_analysis schema
DROP VIEW IF EXISTS ai_trend_analysis.recent_signals CASCADE;
DROP VIEW IF EXISTS ai_trend_analysis.latest_signals CASCADE; 
DROP VIEW IF EXISTS ai_trend_analysis.trading_signals CASCADE;
DROP VIEW IF EXISTS ai_trend_analysis.chart_data CASCADE;
DROP VIEW IF EXISTS ai_trend_analysis.latest_performance CASCADE;
DROP VIEW IF EXISTS ai_trend_analysis.trade_summary CASCADE;
DROP VIEW IF EXISTS ai_trend_analysis.daily_performance CASCADE;

-- Step 2: Drop any other views that might exist (comprehensive approach)
DO $$ 
DECLARE 
    view_record RECORD;
BEGIN
    FOR view_record IN 
        SELECT schemaname, viewname 
        FROM pg_views 
        WHERE schemaname = 'ai_trend_analysis'
    LOOP
        EXECUTE 'DROP VIEW IF EXISTS ' || view_record.schemaname || '.' || view_record.viewname || ' CASCADE';
        RAISE NOTICE 'Dropped view: %.%', view_record.schemaname, view_record.viewname;
    END LOOP;
END $$;

-- Step 3: Now alter the column types (this should work now!)
ALTER TABLE ai_trend_analysis.ai_trend_data 
ALTER COLUMN signal TYPE DECIMAL(15,2);

ALTER TABLE ai_trend_analysis.ai_trend_data 
ALTER COLUMN smoothed_signal TYPE DECIMAL(15,2);

ALTER TABLE ai_trend_analysis.ai_trend_data 
ALTER COLUMN ma_signal TYPE DECIMAL(15,2);

ALTER TABLE ai_trend_analysis.ai_trend_data 
ALTER COLUMN signal_strength TYPE DECIMAL(8,4);

-- Step 4: Verify the changes worked
SELECT 
    column_name, 
    data_type, 
    numeric_precision, 
    numeric_scale
FROM information_schema.columns 
WHERE table_name = 'ai_trend_data' 
  AND table_schema = 'ai_trend_analysis'
  AND column_name IN ('signal', 'smoothed_signal', 'ma_signal', 'signal_strength');

-- Success message
SELECT 'SUCCESS: AI trend columns fixed! Can now store Bitcoin price range values.' as status; 