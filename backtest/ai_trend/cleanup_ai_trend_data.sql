-- Cleanup script for ai_trend_analysis schema
-- This will delete all data from all tables in the schema

-- Delete all data from AI trend data table
DELETE FROM ai_trend_analysis.ai_trend_data;

-- Delete all data from transaction records table
DELETE FROM ai_trend_analysis.transaction_records;

-- Delete all data from performance summary table
DELETE FROM ai_trend_analysis.performance_summary;

-- Optional: Reset sequences (auto-increment counters)
-- Uncomment these lines if you want to reset ID counters back to 1
-- ALTER SEQUENCE ai_trend_analysis.ai_trend_data_id_seq RESTART WITH 1;
-- ALTER SEQUENCE ai_trend_analysis.transaction_records_id_seq RESTART WITH 1;
-- ALTER SEQUENCE ai_trend_analysis.performance_summary_id_seq RESTART WITH 1;

-- Verify cleanup (should return 0 for all tables)
SELECT 
    'ai_trend_data' as table_name, 
    COUNT(*) as record_count 
FROM ai_trend_analysis.ai_trend_data
UNION ALL
SELECT 
    'transaction_records' as table_name, 
    COUNT(*) as record_count 
FROM ai_trend_analysis.transaction_records
UNION ALL
SELECT 
    'performance_summary' as table_name, 
    COUNT(*) as record_count 
FROM ai_trend_analysis.performance_summary; 