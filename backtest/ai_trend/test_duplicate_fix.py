#!/usr/bin/env python3
"""
Test script to check duplicate data and verify delete operations
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from supabase_integration import SupabaseTradeDataManager

# Load environment variables
load_dotenv()

def check_current_data_state():
    """Check current state of data in all tables"""
    
    # Initialize database manager
    db_manager = SupabaseTradeDataManager(
        supabase_url=os.getenv('SUPABASE_URL'),
        supabase_key=os.getenv('SUPABASE_SERVICE_ROLE_KEY'),
        use_service_role=True
    )
    
    print("🔍 CHECKING CURRENT DATA STATE...")
    print("=" * 50)
    
    # Check each table
    tables = [
        'performance_summary',
        'transaction_records', 
        'ai_trend_data',
        'equity_curve'
    ]
    
    for table in tables:
        try:
            # Get total count
            result = db_manager.supabase.schema('ai_trend_analysis').table(table).select('*', count='exact').execute()
            total_count = result.count
            
            # Get unique combinations count
            if table == 'performance_summary':
                unique_result = db_manager.supabase.schema('ai_trend_analysis').table(table).select('timeframe, date_analyzed').execute()
                unique_combinations = len(set((r['timeframe'], r['date_analyzed']) for r in unique_result.data))
            else:
                unique_result = db_manager.supabase.schema('ai_trend_analysis').table(table).select('timeframe, timestamp, date_analyzed').execute()
                unique_combinations = len(set((r['timeframe'], r['timestamp'], r['date_analyzed']) for r in unique_result.data))
            
            duplicates = total_count - unique_combinations
            
            print(f"📊 {table}:")
            print(f"   Total records: {total_count}")
            print(f"   Unique combinations: {unique_combinations}")
            print(f"   Duplicates: {duplicates}")
            print()
            
        except Exception as e:
            print(f"❌ Error checking {table}: {e}")
            print()

def test_delete_operation():
    """Test if delete operations work properly"""
    
    db_manager = SupabaseTradeDataManager(
        supabase_url=os.getenv('SUPABASE_URL'),
        supabase_key=os.getenv('SUPABASE_SERVICE_ROLE_KEY'),
        use_service_role=True
    )
    
    print("🧪 TESTING DELETE OPERATIONS...")
    print("=" * 50)
    
    # Test delete on performance_summary
    today = datetime.now().date().isoformat()
    
    try:
        # Check what exists for today
        existing = db_manager.supabase.schema('ai_trend_analysis').table('performance_summary').select('*').eq(
            'date_analyzed', today
        ).execute()
        
        print(f"📅 Records for today ({today}): {len(existing.data)}")
        
        if existing.data:
            print("🗑️ Testing delete operation...")
            delete_result = db_manager.supabase.schema('ai_trend_analysis').table('performance_summary').delete().eq(
                'date_analyzed', today
            ).execute()
            
            print(f"   Deleted: {len(delete_result.data) if delete_result.data else 0} records")
            
            # Check if delete worked
            after_delete = db_manager.supabase.schema('ai_trend_analysis').table('performance_summary').select('*').eq(
                'date_analyzed', today
            ).execute()
            
            print(f"   Remaining: {len(after_delete.data)} records")
        else:
            print("✅ No records for today - delete test skipped")
            
    except Exception as e:
        print(f"❌ Error testing delete: {e}")

def clear_all_data():
    """Clear all data from all tables"""
    
    db_manager = SupabaseTradeDataManager(
        supabase_url=os.getenv('SUPABASE_URL'),
        supabase_key=os.getenv('SUPABASE_SERVICE_ROLE_KEY'),
        use_service_role=True
    )
    
    print("🗑️ CLEARING ALL DATA...")
    print("=" * 50)
    
    tables = ['equity_curve', 'ai_trend_data', 'transaction_records', 'performance_summary']
    
    for table in tables:
        try:
            result = db_manager.supabase.schema('ai_trend_analysis').table(table).delete().neq('id', 0).execute()
            print(f"✅ Cleared {table}: {len(result.data) if result.data else 'Unknown'} records deleted")
        except Exception as e:
            print(f"❌ Error clearing {table}: {e}")
    
    print("\n🔄 Resetting sequences...")
    try:
        # Reset sequences (this might require direct SQL)
        sequences = [
            'performance_summary_id_seq',
            'transaction_records_id_seq', 
            'ai_trend_data_id_seq',
            'equity_curve_id_seq'
        ]
        print("⚠️ Sequences need to be reset manually in SQL editor")
    except Exception as e:
        print(f"❌ Error resetting sequences: {e}")

if __name__ == "__main__":
    # Check current state
    check_current_data_state()
    
    # Test delete operation
    test_delete_operation()
    
    # Ask user if they want to clear all data
    response = input("\n❓ Do you want to clear ALL data? (yes/no): ").lower().strip()
    if response == 'yes':
        clear_all_data()
        print("\n✅ Data clearing completed!")
    else:
        print("\n⏭️ Data clearing skipped") 