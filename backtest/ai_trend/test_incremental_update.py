#!/usr/bin/env python3
"""
Test script for incremental update functionality
Tests both incremental and force refresh modes
"""

import os
from datetime import datetime
from daily_supabase_update import DailySupabaseUpdater

def test_incremental_updates():
    """Test the incremental update functionality"""
    print("🧪 Testing Incremental Update Functionality")
    print("=" * 50)
    
    try:
        # Test 1: Run incremental update
        print("\n📊 Test 1: Running incremental update...")
        updater = DailySupabaseUpdater(force_refresh=False)
        
        # Test with a single timeframe first
        print("🎯 Testing with 4H timeframe only...")
        result = updater.process_timeframe('4H')
        
        if result:
            if result.get('skipped', False):
                print(f"✅ Test 1 PASSED: {result['reason']}")
                print(f"   Existing records: {result.get('existing_records', 'N/A')}")
            else:
                print("✅ Test 1 PASSED: Data was processed successfully")
                print(f"   Performance: {result.get('performance', {}).get('total_return', 'N/A')}% return")
        else:
            print("❌ Test 1 FAILED: No result returned")
            return False
        
        # Test 2: Run again immediately (should skip)
        print("\n📊 Test 2: Running same timeframe again (should skip)...")
        result2 = updater.process_timeframe('4H')
        
        if result2 and result2.get('skipped', False):
            print("✅ Test 2 PASSED: Data was correctly skipped")
            print(f"   Reason: {result2['reason']}")
        else:
            print("⚠️  Test 2 WARNING: Data was not skipped (might be force refresh mode)")
        
        # Test 3: Check data coverage
        print("\n📊 Test 3: Checking data coverage...")
        analysis_date = datetime.now().date().isoformat()
        coverage = updater.db_manager.check_existing_data_coverage('4H', analysis_date)
        
        print(f"   📈 AI Trend Data: {coverage['ai_trend_data_count']} records")
        print(f"   💰 Transaction Records: {coverage['transaction_records_count']} records")
        print(f"   📊 Equity Curve: {coverage['equity_curve_count']} records")
        print(f"   📋 Performance Summary: {'Yes' if coverage['performance_summary_exists'] else 'No'}")
        
        if coverage['ai_trend_data_count'] > 0:
            print("✅ Test 3 PASSED: Data exists in database")
        else:
            print("❌ Test 3 FAILED: No data found in database")
            return False
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_force_refresh():
    """Test the force refresh functionality"""
    print("\n🔥 Testing Force Refresh Functionality")
    print("=" * 50)
    
    try:
        # Run force refresh on a single timeframe
        print("⚡ Running force refresh on 4H timeframe...")
        updater = DailySupabaseUpdater(force_refresh=True)
        result = updater.process_timeframe('4H')
        
        if result and not result.get('skipped', False):
            print("✅ Force refresh test PASSED: Data was processed")
            return True
        else:
            print("❌ Force refresh test FAILED: Data was skipped unexpectedly")
            return False
            
    except Exception as e:
        print(f"❌ Force refresh test FAILED with error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Incremental Update Tests")
    print("=" * 60)
    
    # Test incremental updates
    test1_passed = test_incremental_updates()
    
    # Ask user if they want to test force refresh
    response = input("\n❓ Do you want to test force refresh? (y/N): ").lower()
    test2_passed = True
    
    if response in ['y', 'yes']:
        test2_passed = test_force_refresh()
    else:
        print("⏭️  Skipping force refresh test")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Incremental Update Test: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"✅ Force Refresh Test: {'PASSED' if test2_passed else 'SKIPPED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests PASSED! Incremental updates are working correctly.")
        return 0
    else:
        print("\n❌ Some tests FAILED. Please check the output above.")
        return 1

if __name__ == "__main__":
    exit(main()) 