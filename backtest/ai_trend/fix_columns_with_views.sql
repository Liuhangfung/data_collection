-- Fix AI Signal Column Types (Handle View Dependencies)
-- Run this in Supabase SQL Editor

-- Step 1: Find all dependent views
SELECT 
    schemaname, 
    viewname, 
    definition
FROM pg_views 
WHERE schemaname = 'ai_trend_analysis';

-- Step 2: Drop dependent views temporarily
DROP VIEW IF EXISTS ai_trend_analysis.recent_signals CASCADE;
DROP VIEW IF EXISTS ai_trend_analysis.latest_signals CASCADE;
DROP VIEW IF EXISTS ai_trend_analysis.trading_signals CASCADE;

-- Step 3: Now alter the column types
ALTER TABLE ai_trend_analysis.ai_trend_data 
ALTER COLUMN signal TYPE DECIMAL(15,2);

ALTER TABLE ai_trend_analysis.ai_trend_data 
ALTER COLUMN smoothed_signal TYPE DECIMAL(15,2);

ALTER TABLE ai_trend_analysis.ai_trend_data 
ALTER COLUMN ma_signal TYPE DECIMAL(15,2);

ALTER TABLE ai_trend_analysis.ai_trend_data 
ALTER COLUMN signal_strength TYPE DECIMAL(8,4);

-- Step 4: Recreate the views with new column types (if needed)
-- You can recreate these views after the column changes are complete

-- Verify the changes worked
SELECT 
    column_name, 
    data_type, 
    numeric_precision, 
    numeric_scale
FROM information_schema.columns 
WHERE table_name = 'ai_trend_data' 
  AND table_schema = 'ai_trend_analysis'
  AND column_name IN ('signal', 'smoothed_signal', 'ma_signal', 'signal_strength');

-- Show success message
SELECT 'AI trend signal columns successfully updated to handle Bitcoin price range values!' as status; 