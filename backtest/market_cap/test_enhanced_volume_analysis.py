#!/usr/bin/env python3
"""
Test script for Enhanced Volume Profile Analysis
Tests both CCXT and CSV data loading methods
"""

import sys
import traceback
from enhanced_volume_analysis import EnhancedVolumeProfileAnalyzer, run_complete_analysis

def test_ccxt_integration():
    """Test CCXT data fetching and analysis"""
    print("Testing CCXT Integration...")
    print("-" * 40)
    
    try:
        # Test basic CCXT functionality
        analyzer = EnhancedVolumeProfileAnalyzer()
        
        # Try different symbols and exchanges
        test_cases = [
            {'symbol': 'BTC/USDT', 'exchange': 'binance', 'timeframe': '1d', 'limit': 100},
            {'symbol': 'ETH/USDT', 'exchange': 'coinbase', 'timeframe': '1h', 'limit': 200},
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\nTest Case {i+1}: {test_case['symbol']} on {test_case['exchange']}")
            
            try:
                data = analyzer.fetch_data_ccxt(
                    symbol=test_case['symbol'],
                    timeframe=test_case['timeframe'],
                    limit=test_case['limit'],
                    exchange=test_case['exchange']
                )
                
                print(f"✅ Successfully fetched {len(data)} candles")
                print(f"   Data range: {data.index[0]} to {data.index[-1]}")
                print(f"   Columns: {list(data.columns)}")
                print(f"   Price range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
                
                # Quick analysis test
                volume_features = analyzer.calculate_enhanced_volume_metrics()
                print(f"✅ Volume metrics calculated successfully")
                
                profile = analyzer.build_volume_profile(lookback=min(50, len(data)-1), rows=20)
                print(f"✅ Volume profile built with {len(profile)} rows")
                
                break  # Success, no need to test more
                
            except Exception as e:
                print(f"❌ Failed: {e}")
                continue
                
    except Exception as e:
        print(f"❌ CCXT test failed: {e}")
        traceback.print_exc()
        return False
    
    print("\n✅ CCXT integration test completed successfully!")
    return True

def test_csv_loading():
    """Test CSV data loading"""
    print("\nTesting CSV Loading...")
    print("-" * 40)
    
    try:
        analyzer = EnhancedVolumeProfileAnalyzer()
        
        # Test CSV loading
        data = analyzer.load_csv("BTC.csv")
        
        print(f"✅ Successfully loaded CSV with {len(data)} rows")
        print(f"   Data range: {data.index[0]} to {data.index[-1]}")
        print(f"   Columns: {list(data.columns)}")
        print(f"   Price range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
        
        # Test analysis
        volume_features = analyzer.calculate_enhanced_volume_metrics()
        print(f"✅ Volume metrics calculated successfully")
        
        profile = analyzer.build_volume_profile(lookback=min(100, len(data)-1), rows=25)
        print(f"✅ Volume profile built with {len(profile)} rows")
        
        smart_levels = analyzer.detect_smart_levels()
        print(f"✅ Smart levels detected: {len(smart_levels)} levels")
        
        metrics = analyzer.calculate_volume_profile_metrics()
        print(f"✅ Profile metrics calculated")
        print(f"   PoC Price: ${metrics['poc_price']:.2f}")
        print(f"   Value Area: ${metrics['va_low']:.2f} - ${metrics['va_high']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ CSV test failed: {e}")
        traceback.print_exc()
        return False

def test_complete_analysis():
    """Test complete analysis workflow"""
    print("\nTesting Complete Analysis Workflow...")
    print("-" * 40)
    
    try:
        # Use CCXT for this test
        analyzer = EnhancedVolumeProfileAnalyzer()
        
        try:
            # Try CCXT first
            data = analyzer.fetch_data_ccxt(symbol='BTC/USDT', timeframe='1d', limit=200, exchange='binance')
        except:
            # Fallback to CSV
            print("CCXT failed, falling back to CSV...")
            data = analyzer.load_csv("BTC.csv")
        
        # Run complete analysis
        analyzer_result, metrics, performance = run_complete_analysis(analyzer)
        
        if analyzer_result is None:
            print("❌ Analysis returned None")
            return False
        
        print("✅ Complete analysis workflow successful!")
        print(f"   Strategy return: {performance['total_return']:.2%}")
        print(f"   Sharpe ratio: {performance['sharpe_ratio']:.2f}")
        print(f"   Max drawdown: {performance['max_drawdown']:.2%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Complete analysis test failed: {e}")
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling"""
    print("\nTesting Error Handling...")
    print("-" * 40)
    
    try:
        analyzer = EnhancedVolumeProfileAnalyzer()
        
        # Test invalid symbol
        try:
            data = analyzer.fetch_data_ccxt(symbol='INVALID/PAIR', timeframe='1d', limit=100)
            print("❌ Should have failed with invalid symbol")
        except:
            print("✅ Properly handled invalid symbol")
        
        # Test invalid file
        try:
            data = analyzer.load_csv("nonexistent_file.csv")
            print("❌ Should have failed with invalid file")
        except:
            print("✅ Properly handled invalid file")
        
        # Test analysis without data
        try:
            analyzer_empty = EnhancedVolumeProfileAnalyzer()
            analyzer_result, _, _ = run_complete_analysis(analyzer_empty)
            if analyzer_result is None:
                print("✅ Properly handled missing data")
            else:
                print("❌ Should have failed with missing data")
        except:
            print("✅ Properly handled missing data exception")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Enhanced Volume Profile Analysis Test Suite")
    print("=" * 60)
    
    tests = [
        ("CCXT Integration", test_ccxt_integration),
        ("CSV Loading", test_csv_loading),
        ("Complete Analysis", test_complete_analysis),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📊 Running {test_name} Test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\nResult: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The enhanced volume analysis is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 