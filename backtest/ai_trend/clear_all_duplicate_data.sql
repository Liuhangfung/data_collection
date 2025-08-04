-- COMPREHENSIVE DATA CLEANUP SCRIPT
-- This script clears ALL data from AI Trend Analysis tables to start fresh
-- Run this to remove all duplicates and corrupted data

-- Show current data counts before cleanup
SELECT 'BEFORE CLEANUP - Data Counts:' as status;

SELECT 
    'performance_summary' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT CONCAT(timeframe, date_analyzed)) as unique_combinations
FROM ai_trend_analysis.performance_summary

UNION ALL

SELECT 
    'transaction_records' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT CONCAT(timeframe, timestamp, date_analyzed)) as unique_combinations
FROM ai_trend_analysis.transaction_records

UNION ALL

SELECT 
    'ai_trend_data' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT CONCAT(timeframe, timestamp, date_analyzed)) as unique_combinations
FROM ai_trend_analysis.ai_trend_data

UNION ALL

SELECT 
    'equity_curve' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT CONCAT(timeframe, timestamp, date_analyzed)) as unique_combinations
FROM ai_trend_analysis.equity_curve;

-- CLEAR ALL DATA (in correct order to avoid foreign key issues)
SELECT '🗑️ CLEARING ALL DATA...' as status;

-- 1. Clear equity curve data
DELETE FROM ai_trend_analysis.equity_curve;
SELECT 'Cleared equity_curve table' as status;

-- 2. Clear AI trend data
DELETE FROM ai_trend_analysis.ai_trend_data;
SELECT 'Cleared ai_trend_data table' as status;

-- 3. Clear transaction records
DELETE FROM ai_trend_analysis.transaction_records;
SELECT 'Cleared transaction_records table' as status;

-- 4. Clear performance summary
DELETE FROM ai_trend_analysis.performance_summary;
SELECT 'Cleared performance_summary table' as status;

-- Reset auto-increment sequences to start from 1
ALTER SEQUENCE ai_trend_analysis.performance_summary_id_seq RESTART WITH 1;
ALTER SEQUENCE ai_trend_analysis.transaction_records_id_seq RESTART WITH 1;
ALTER SEQUENCE ai_trend_analysis.ai_trend_data_id_seq RESTART WITH 1;
ALTER SEQUENCE ai_trend_analysis.equity_curve_id_seq RESTART WITH 1;

SELECT 'Reset all sequences to start from 1' as status;

-- Verify all tables are empty
SELECT 'AFTER CLEANUP - Verification:' as status;

SELECT 
    'performance_summary' as table_name,
    COUNT(*) as remaining_records
FROM ai_trend_analysis.performance_summary

UNION ALL

SELECT 
    'transaction_records' as table_name,
    COUNT(*) as remaining_records
FROM ai_trend_analysis.transaction_records

UNION ALL

SELECT 
    'ai_trend_data' as table_name,
    COUNT(*) as remaining_records
FROM ai_trend_analysis.ai_trend_data

UNION ALL

SELECT 
    'equity_curve' as table_name,
    COUNT(*) as remaining_records
FROM ai_trend_analysis.equity_curve;

SELECT '✅ CLEANUP COMPLETE - All tables cleared and ready for fresh data' as status;

COMMIT; 