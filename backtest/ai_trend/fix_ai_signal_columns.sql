-- Fix AI Signal Column Types
-- Run this in Supabase SQL Editor to fix the 9999 issue

-- Update ai_trend_data table columns to handle Bitcoin price-range values
ALTER TABLE ai_trend_analysis.ai_trend_data 
ALTER COLUMN signal TYPE DECIMAL(15,2);

ALTER TABLE ai_trend_analysis.ai_trend_data 
ALTER COLUMN smoothed_signal TYPE DECIMAL(15,2);

ALTER TABLE ai_trend_analysis.ai_trend_data 
ALTER COLUMN ma_signal TYPE DECIMAL(15,2);

-- Also update signal_strength to handle proper decimal values
ALTER TABLE ai_trend_analysis.ai_trend_data 
ALTER COLUMN signal_strength TYPE DECIMAL(8,4);

-- Verify the changes
SELECT 
    column_name, 
    data_type, 
    numeric_precision, 
    numeric_scale
FROM information_schema.columns 
WHERE table_name = 'ai_trend_data' 
  AND table_schema = 'ai_trend_analysis'
  AND column_name IN ('signal', 'smoothed_signal', 'ma_signal', 'signal_strength'); 