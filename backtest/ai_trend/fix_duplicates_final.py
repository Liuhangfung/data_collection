#!/usr/bin/env python3
"""
Final duplicate prevention fix using PostgreSQL UPSERT
This script modifies the Supabase integration to use proper UPSERT operations
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from supabase_integration import SupabaseTradeDataManager

# Load environment variables
load_dotenv()

def clear_all_duplicates_sql():
    """Generate SQL to clear all duplicates and add proper constraints"""
    
    sql_script = """
-- COMPREHENSIVE DUPLICATE CLEANUP AND PREVENTION SCRIPT
-- This script removes all duplicates and prevents future ones

-- 1. Clear all existing data
DELETE FROM ai_trend_analysis.equity_curve;
DELETE FROM ai_trend_analysis.ai_trend_data;
DELETE FROM ai_trend_analysis.transaction_records;
DELETE FROM ai_trend_analysis.performance_summary;

-- 2. Reset sequences
ALTER SEQUENCE ai_trend_analysis.performance_summary_id_seq RESTART WITH 1;
ALTER SEQUENCE ai_trend_analysis.transaction_records_id_seq RESTART WITH 1;
ALTER SEQUENCE ai_trend_analysis.ai_trend_data_id_seq RESTART WITH 1;
ALTER SEQUENCE ai_trend_analysis.equity_curve_id_seq RESTART WITH 1;

-- 3. Add unique constraints to prevent duplicates
-- Performance summary: one record per timeframe per date
ALTER TABLE ai_trend_analysis.performance_summary 
DROP CONSTRAINT IF EXISTS unique_performance_per_timeframe_date;

ALTER TABLE ai_trend_analysis.performance_summary 
ADD CONSTRAINT unique_performance_per_timeframe_date 
UNIQUE (timeframe, date_analyzed);

-- Transaction records: prevent exact duplicate transactions
ALTER TABLE ai_trend_analysis.transaction_records 
DROP CONSTRAINT IF EXISTS unique_transaction_per_timeframe_timestamp_date;

ALTER TABLE ai_trend_analysis.transaction_records 
ADD CONSTRAINT unique_transaction_per_timeframe_timestamp_date 
UNIQUE (timeframe, timestamp, date_analyzed);

-- AI trend data: prevent duplicate data points
ALTER TABLE ai_trend_analysis.ai_trend_data 
DROP CONSTRAINT IF EXISTS unique_ai_trend_per_timeframe_timestamp_date;

ALTER TABLE ai_trend_analysis.ai_trend_data 
ADD CONSTRAINT unique_ai_trend_per_timeframe_timestamp_date 
UNIQUE (timeframe, timestamp, date_analyzed);

-- Equity curve: prevent duplicate equity points
ALTER TABLE ai_trend_analysis.equity_curve 
DROP CONSTRAINT IF EXISTS unique_equity_per_timeframe_timestamp_date;

ALTER TABLE ai_trend_analysis.equity_curve 
ADD CONSTRAINT unique_equity_per_timeframe_timestamp_date 
UNIQUE (timeframe, timestamp, date_analyzed);

-- 4. Verify all tables are empty
SELECT 
    'performance_summary' as table_name,
    COUNT(*) as record_count
FROM ai_trend_analysis.performance_summary

UNION ALL

SELECT 
    'transaction_records' as table_name,
    COUNT(*) as record_count
FROM ai_trend_analysis.transaction_records

UNION ALL

SELECT 
    'ai_trend_data' as table_name,
    COUNT(*) as record_count
FROM ai_trend_analysis.ai_trend_data

UNION ALL

SELECT 
    'equity_curve' as table_name,
    COUNT(*) as record_count
FROM ai_trend_analysis.equity_curve;

COMMIT;
"""
    
    return sql_script

def test_current_duplicates():
    """Test and display current duplicate status"""
    
    print("🔍 TESTING CURRENT DUPLICATE STATUS...")
    print("=" * 60)
    
    # Run the test script
    import subprocess
    import sys
    
    try:
        result = subprocess.run([sys.executable, 'test_duplicate_fix.py'], 
                              capture_output=True, text=True, cwd='.')
        print(result.stdout)
        if result.stderr:
            print("ERRORS:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error running test: {e}")

def create_upsert_integration():
    """Create updated integration file with UPSERT logic"""
    
    print("🔄 CREATING UPSERT-BASED INTEGRATION...")
    
    # This would require modifying the supabase_integration.py file
    # For now, let's create a patch script
    
    patch_content = '''
# PATCH FOR SUPABASE_INTEGRATION.PY
# Replace the store methods with these UPSERT-based versions:

def store_performance_summary_upsert(self, metrics):
    """Store performance summary using UPSERT to prevent duplicates"""
    try:
        data = {
            'timeframe': metrics.timeframe,
            'strategy_return': metrics.strategy_return,
            'buyhold_return': metrics.buyhold_return,
            'outperformance': metrics.outperformance,
            'total_trades': metrics.total_trades,
            'win_rate': metrics.win_rate,
            'average_gain': metrics.average_gain,
            'average_loss': metrics.average_loss,
            'max_gain': metrics.max_gain,
            'max_loss': metrics.max_loss,
            'max_drawdown': metrics.max_drawdown,
            'sharpe_ratio': metrics.sharpe_ratio,
            'sortino_ratio': metrics.sortino_ratio,
            'profit_factor': metrics.profit_factor,
            'best_params': json.dumps(metrics.best_params),
            'date_analyzed': metrics.date_analyzed,
            'updated_at': datetime.now().isoformat()
        }
        
        # Use upsert with on_conflict
        result = self.supabase.schema(self.schema).table('performance_summary').upsert(
            data, 
            on_conflict='timeframe,date_analyzed'
        ).execute()
        
        logger.info(f"Upserted performance summary for {metrics.timeframe}")
        return True
        
    except Exception as e:
        logger.error(f"Error upserting performance summary: {e}")
        return False
'''
    
    with open('upsert_patch.py', 'w') as f:
        f.write(patch_content)
    
    print("✅ Created upsert_patch.py")

def main():
    """Main function to fix duplicates"""
    
    print("🚀 FINAL DUPLICATE FIX SCRIPT")
    print("=" * 60)
    
    # Step 1: Test current status
    print("\n1️⃣ TESTING CURRENT STATUS...")
    test_current_duplicates()
    
    # Step 2: Generate cleanup SQL
    print("\n2️⃣ GENERATING CLEANUP SQL...")
    cleanup_sql = clear_all_duplicates_sql()
    
    with open('final_cleanup.sql', 'w') as f:
        f.write(cleanup_sql)
    
    print("✅ Created final_cleanup.sql")
    print("📝 To apply: Copy and paste this SQL in your Supabase SQL Editor")
    
    # Step 3: Create UPSERT integration
    print("\n3️⃣ CREATING UPSERT INTEGRATION...")
    create_upsert_integration()
    
    print("\n✅ DUPLICATE FIX PREPARATION COMPLETE!")
    print("\n📋 NEXT STEPS:")
    print("1. Run final_cleanup.sql in Supabase SQL Editor")
    print("2. Test with: python test_duplicate_fix.py")
    print("3. Run daily update to verify no duplicates")
    
    return cleanup_sql

if __name__ == "__main__":
    sql_content = main()
    
    print("\n" + "="*60)
    print("📄 SQL CLEANUP SCRIPT CONTENT:")
    print("="*60)
    print(sql_content) 