-- Cleanup Duplicate Performance Summary Records
-- This script removes duplicate entries, keeping only the most recent one for each timeframe

-- First, let's see what duplicates we have
SELECT 
    timeframe, 
    date_analyzed, 
    COUNT(*) as record_count,
    STRING_AGG(id::text, ', ' ORDER BY id) as ids
FROM ai_trend_analysis.performance_summary 
GROUP BY timeframe, date_analyzed 
HAVING COUNT(*) > 1
ORDER BY timeframe, date_analyzed;

-- Create a temporary table with the IDs to keep (highest ID for each timeframe/date combination)
CREATE TEMP TABLE records_to_keep AS
SELECT 
    timeframe,
    date_analyzed,
    MAX(id) as max_id
FROM ai_trend_analysis.performance_summary
GROUP BY timeframe, date_analyzed;

-- Delete all records except the ones we want to keep
DELETE FROM ai_trend_analysis.performance_summary 
WHERE id NOT IN (
    SELECT max_id 
    FROM records_to_keep
);

-- Show the final count per timeframe
SELECT 
    timeframe,
    COUNT(*) as remaining_records,
    MAX(date_analyzed) as latest_analysis_date
FROM ai_trend_analysis.performance_summary 
GROUP BY timeframe 
ORDER BY timeframe;

-- Verify no duplicates remain
SELECT 
    timeframe, 
    date_analyzed, 
    COUNT(*) as record_count
FROM ai_trend_analysis.performance_summary 
GROUP BY timeframe, date_analyzed 
HAVING COUNT(*) > 1;

-- If the above query returns no rows, cleanup was successful!

COMMIT; 