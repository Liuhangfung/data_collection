#!/usr/bin/env python3
"""
Quick test of the improved volume strategy
"""

from enhanced_volume_analysis import EnhancedVolumeProfileAnalyzer, run_complete_analysis
import matplotlib.pyplot as plt
import pandas as pd

def test_improved_strategy():
    """Test the improved strategy with better parameters"""
    print("🚀 Testing Improved Volume Strategy")
    print("=" * 50)
    
    try:
        # Initialize analyzer
        analyzer = EnhancedVolumeProfileAnalyzer()
        
        # Try to get live data first
        try:
            print("📡 Fetching live BTC data...")
            data = analyzer.fetch_data_ccxt('BTC/USDT', '1d', 300, 'binance')
            data_source = "Live CCXT Data"
        except:
            print("📁 Loading CSV data...")
            data = analyzer.load_csv("BTC.csv")
            data_source = "CSV Data"
        
        print(f"✅ Using {data_source}: {len(data)} candles")
        
        # Test different strategy parameters
        strategies = [
            {"name": "Conservative", "max_pos": 0.05, "stop_loss": 0.03, "take_profit": 0.10},
            {"name": "Moderate", "max_pos": 0.10, "stop_loss": 0.05, "take_profit": 0.15},
            {"name": "Aggressive", "max_pos": 0.15, "stop_loss": 0.07, "take_profit": 0.20},
        ]
        
        results = []
        
        for strategy in strategies:
            print(f"\n📊 Testing {strategy['name']} Strategy...")
            print("-" * 30)
            
            # Calculate enhanced volume metrics
            volume_features = analyzer.calculate_enhanced_volume_metrics()
            
            # Build volume profile
            profile = analyzer.build_volume_profile(lookback=min(200, len(data)-1), rows=25)
            
            # Run backtest with current parameters
            portfolio, performance = analyzer.backtest_volume_strategy(
                initial_capital=100000,
                max_position_size=strategy['max_pos'],
                stop_loss=strategy['stop_loss'],
                take_profit=strategy['take_profit']
            )
            
            # Store results
            strategy_result = {
                'name': strategy['name'],
                'total_return': performance['total_return'],
                'sharpe_ratio': performance['sharpe_ratio'],
                'max_drawdown': performance['max_drawdown'],
                'win_rate': performance['win_rate'],
                'total_trades': performance['total_trades'],
                'profit_factor': performance['profit_factor']
            }
            results.append(strategy_result)
            
            # Print results
            print(f"✅ Total Return: {performance['total_return']:.2%}")
            print(f"📈 Sharpe Ratio: {performance['sharpe_ratio']:.2f}")
            print(f"📉 Max Drawdown: {performance['max_drawdown']:.2%}")
            print(f"🎯 Win Rate: {performance['win_rate']:.1%}")
            print(f"📊 Total Trades: {performance['total_trades']}")
            print(f"💰 Profit Factor: {performance['profit_factor']:.2f}")
        
        # Summary comparison
        print("\n" + "=" * 50)
        print("📈 STRATEGY COMPARISON SUMMARY")
        print("=" * 50)
        
        best_return = max(results, key=lambda x: x['total_return'])
        best_sharpe = max(results, key=lambda x: x['sharpe_ratio'])
        best_dd = min(results, key=lambda x: x['max_drawdown'])
        
        print(f"🏆 Best Return: {best_return['name']} ({best_return['total_return']:.2%})")
        print(f"📊 Best Sharpe: {best_sharpe['name']} ({best_sharpe['sharpe_ratio']:.2f})")
        print(f"🛡️  Best Risk: {best_dd['name']} ({best_dd['max_drawdown']:.2%} DD)")
        
        # Create summary table
        df_results = pd.DataFrame(results)
        print(f"\n{df_results.to_string(index=False, float_format='%.3f')}")
        
        # Check if any strategy is profitable
        profitable_strategies = [r for r in results if r['total_return'] > 0]
        
        if profitable_strategies:
            print(f"\n🎉 SUCCESS: {len(profitable_strategies)}/{len(results)} strategies are profitable!")
            best_strategy = max(profitable_strategies, key=lambda x: x['total_return'])
            print(f"💎 Recommended: {best_strategy['name']} Strategy")
            print(f"   📈 Return: {best_strategy['total_return']:.2%}")
            print(f"   📊 Sharpe: {best_strategy['sharpe_ratio']:.2f}")
            print(f"   🎯 Win Rate: {best_strategy['win_rate']:.1%}")
        else:
            print("\n⚠️  All strategies still showing losses. This could be due to:")
            print("   • Market conditions during test period")
            print("   • Need for longer data history")
            print("   • Strategy parameters need further optimization")
        
        return results
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_old_vs_new():
    """Compare old simple strategy vs new enhanced strategy"""
    print("\n🔄 COMPARING OLD vs NEW STRATEGY")
    print("=" * 50)
    
    # This would require keeping the old strategy code for comparison
    # For now, just show the improvement framework
    print("Old Strategy Issues:")
    print("❌ No trend awareness")
    print("❌ No risk management") 
    print("❌ Poor signal filtering")
    print("❌ No position sizing")
    print("❌ No stop losses")
    
    print("\nNew Strategy Improvements:")
    print("✅ Trend-following + mean reversion")
    print("✅ Stop losses & take profits")
    print("✅ Volume profile integration")
    print("✅ Dynamic position sizing")
    print("✅ Market regime detection")
    print("✅ Multi-signal confirmation")

if __name__ == "__main__":
    results = test_improved_strategy()
    compare_old_vs_new()
    
    if results:
        print("\n🎯 Next Steps:")
        print("1. Fine-tune parameters based on results")
        print("2. Test on different time periods")
        print("3. Add transaction costs")
        print("4. Implement portfolio diversification")
        print("5. Add real-time monitoring") 