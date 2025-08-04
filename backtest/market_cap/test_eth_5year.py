#!/usr/bin/env python3
"""
Test Enhanced Volume Strategy on ETH/USDT over 5 years
"""

from enhanced_volume_analysis import EnhancedVolumeProfileAnalyzer
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def test_eth_5year_strategy():
    """Test the enhanced strategy on ETH/USDT over 5 years"""
    print("🔮 ETH/USDT 5-Year Strategy Backtest")
    print("=" * 60)
    
    try:
        # Initialize analyzer
        analyzer = EnhancedVolumeProfileAnalyzer()
        
        # Fetch 5 years of daily data (roughly 1825 days)
        print("📡 Fetching 5 years of ETH/USDT data...")
        
        # Try different exchanges to get maximum historical data
        exchanges_to_try = ['binance', 'coinbase', 'kraken', 'okx']
        data = None
        
        for exchange in exchanges_to_try:
            try:
                print(f"   Trying {exchange}...")
                data = analyzer.fetch_data_ccxt(
                    symbol='ETH/USDT', 
                    timeframe='1d', 
                    limit=1825,  # 5 years of daily data
                    exchange=exchange
                )
                print(f"✅ Successfully fetched from {exchange}")
                break
            except Exception as e:
                print(f"   ❌ {exchange} failed: {e}")
                continue
        
        if data is None:
            raise Exception("Could not fetch data from any exchange")
        
        # Data info
        print(f"\n📊 Data Summary:")
        print(f"   Period: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
        print(f"   Duration: {(data.index[-1] - data.index[0]).days} days")
        print(f"   Candles: {len(data)}")
        print(f"   Price Range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
        print(f"   Total Price Change: {((data['close'].iloc[-1] / data['close'].iloc[0]) - 1) * 100:.1f}%")
        
        # Calculate buy & hold benchmark
        buy_hold_return = (data['close'].iloc[-1] / data['close'].iloc[0]) - 1
        print(f"   Buy & Hold Return: {buy_hold_return:.2%}")
        
        # Test different strategy configurations for longer timeframe
        strategies = [
            {
                "name": "Conservative 5Y", 
                "max_pos": 0.05, 
                "stop_loss": 0.08, 
                "take_profit": 0.20,
                "description": "Low risk, steady gains"
            },
            {
                "name": "Moderate 5Y", 
                "max_pos": 0.10, 
                "stop_loss": 0.12, 
                "take_profit": 0.25,
                "description": "Balanced risk/reward"
            },
            {
                "name": "Aggressive 5Y", 
                "max_pos": 0.15, 
                "stop_loss": 0.15, 
                "take_profit": 0.35,
                "description": "Higher risk, higher potential"
            },
            {
                "name": "Long-term 5Y", 
                "max_pos": 0.08, 
                "stop_loss": 0.20, 
                "take_profit": 0.50,
                "description": "Swing trading approach"
            }
        ]
        
        results = []
        portfolios = {}
        
        for strategy in strategies:
            print(f"\n🚀 Testing {strategy['name']} Strategy")
            print(f"   {strategy['description']}")
            print("-" * 40)
            
            # Calculate enhanced volume metrics
            volume_features = analyzer.calculate_enhanced_volume_metrics()
            
            # Build volume profile with longer lookback for 5-year data
            profile = analyzer.build_volume_profile(
                lookback=min(500, len(data)-1),  # Longer lookback for 5-year data
                rows=30
            )
            
            # Run backtest
            portfolio, performance = analyzer.backtest_volume_strategy(
                initial_capital=100000,
                max_position_size=strategy['max_pos'],
                stop_loss=strategy['stop_loss'],
                take_profit=strategy['take_profit']
            )
            
            portfolios[strategy['name']] = portfolio
            
            # Calculate additional metrics for 5-year analysis
            annual_return = (1 + performance['total_return']) ** (365.25 / (data.index[-1] - data.index[0]).days) - 1
            
            # Store results
            strategy_result = {
                'name': strategy['name'],
                'total_return': performance['total_return'],
                'annual_return': annual_return,
                'sharpe_ratio': performance['sharpe_ratio'],
                'max_drawdown': performance['max_drawdown'],
                'win_rate': performance['win_rate'],
                'total_trades': performance['total_trades'],
                'profit_factor': performance['profit_factor'],
                'vs_buy_hold': performance['total_return'] - buy_hold_return
            }
            results.append(strategy_result)
            
            # Print detailed results
            print(f"📈 Total Return: {performance['total_return']:.2%}")
            print(f"📊 Annualized Return: {annual_return:.2%}")
            print(f"⚖️  Sharpe Ratio: {performance['sharpe_ratio']:.2f}")
            print(f"📉 Max Drawdown: {performance['max_drawdown']:.2%}")
            print(f"🎯 Win Rate: {performance['win_rate']:.1%}")
            print(f"🔄 Total Trades: {performance['total_trades']}")
            print(f"💰 Profit Factor: {performance['profit_factor']:.2f}")
            print(f"🆚 vs Buy & Hold: {strategy_result['vs_buy_hold']:+.2%}")
            
            if performance['avg_win'] > 0 and performance['avg_loss'] < 0:
                print(f"✅ Avg Win: {performance['avg_win']:.2%}")
                print(f"❌ Avg Loss: {performance['avg_loss']:.2%}")
                print(f"⚖️  Risk/Reward: {abs(performance['avg_win']/performance['avg_loss']):.2f}")
        
        # Analysis and comparison
        print("\n" + "=" * 60)
        print("📊 5-YEAR ETH/USDT STRATEGY ANALYSIS")
        print("=" * 60)
        
        # Find best strategies
        best_return = max(results, key=lambda x: x['total_return'])
        best_annual = max(results, key=lambda x: x['annual_return'])
        best_sharpe = max(results, key=lambda x: x['sharpe_ratio'])
        best_dd = min(results, key=lambda x: x['max_drawdown'])
        best_vs_bh = max(results, key=lambda x: x['vs_buy_hold'])
        
        print(f"🏆 Best Total Return: {best_return['name']} ({best_return['total_return']:.2%})")
        print(f"📈 Best Annual Return: {best_annual['name']} ({best_annual['annual_return']:.2%})")
        print(f"📊 Best Sharpe Ratio: {best_sharpe['name']} ({best_sharpe['sharpe_ratio']:.2f})")
        print(f"🛡️  Lowest Drawdown: {best_dd['name']} ({best_dd['max_drawdown']:.2%})")
        print(f"🆚 Best vs Buy&Hold: {best_vs_bh['name']} ({best_vs_bh['vs_buy_hold']:+.2%})")
        
        # Summary table
        df_results = pd.DataFrame(results)
        print(f"\n📋 DETAILED COMPARISON:")
        print(df_results[['name', 'total_return', 'annual_return', 'sharpe_ratio', 
                         'max_drawdown', 'win_rate', 'total_trades', 'vs_buy_hold']].to_string(
                         index=False, float_format='%.3f'))
        
        # Strategy recommendations
        profitable_strategies = [r for r in results if r['total_return'] > 0]
        beat_market = [r for r in results if r['vs_buy_hold'] > 0]
        
        print(f"\n🎯 STRATEGY PERFORMANCE SUMMARY:")
        print(f"✅ Profitable Strategies: {len(profitable_strategies)}/{len(results)}")
        print(f"🏆 Beat Buy & Hold: {len(beat_market)}/{len(results)}")
        print(f"📊 Buy & Hold Benchmark: {buy_hold_return:.2%}")
        
        if beat_market:
            best_strategy = max(beat_market, key=lambda x: x['total_return'])
            print(f"\n💎 RECOMMENDED STRATEGY: {best_strategy['name']}")
            print(f"   📈 Total Return: {best_strategy['total_return']:.2%}")
            print(f"   📊 Annual Return: {best_strategy['annual_return']:.2%}")
            print(f"   ⚖️  Sharpe Ratio: {best_strategy['sharpe_ratio']:.2f}")
            print(f"   🎯 Win Rate: {best_strategy['win_rate']:.1%}")
            print(f"   🆚 Alpha vs Market: {best_strategy['vs_buy_hold']:+.2%}")
        
        # Risk analysis
        print(f"\n📊 RISK ANALYSIS:")
        avg_drawdown = np.mean([r['max_drawdown'] for r in results])
        avg_sharpe = np.mean([r['sharpe_ratio'] for r in results])
        avg_win_rate = np.mean([r['win_rate'] for r in results])
        
        print(f"   Average Max Drawdown: {avg_drawdown:.2%}")
        print(f"   Average Sharpe Ratio: {avg_sharpe:.2f}")
        print(f"   Average Win Rate: {avg_win_rate:.1%}")
        
        # Create visualization
        create_performance_chart(portfolios, data, buy_hold_return)
        
        return results, portfolios
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def create_performance_chart(portfolios, price_data, buy_hold_return):
    """Create performance comparison chart"""
    print(f"\n📈 Creating performance visualization...")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
    
    # Price chart
    ax1.plot(price_data.index, price_data['close'], label='ETH/USDT Price', color='orange', linewidth=2)
    ax1.set_title('ETH/USDT Price Over 5 Years', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Price (USD)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Strategy performance comparison
    colors = ['blue', 'green', 'red', 'purple']
    
    for i, (strategy_name, portfolio) in enumerate(portfolios.items()):
        if 'cumulative_returns' in portfolio.columns:
            ax2.plot(portfolio.index, (portfolio['cumulative_returns'] - 1) * 100, 
                    label=strategy_name, color=colors[i % len(colors)], linewidth=2)
    
    # Add buy & hold line
    buy_hold_line = price_data['close'] / price_data['close'].iloc[0] - 1
    ax2.plot(price_data.index, buy_hold_line * 100, 
            label=f'Buy & Hold ({buy_hold_return:.1%})', 
            color='black', linestyle='--', linewidth=2)
    
    ax2.set_title('Strategy Performance Comparison (5 Years)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Returns (%)')
    ax2.set_xlabel('Date')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig('eth_5year_strategy_performance.png', dpi=300, bbox_inches='tight')
    print("✅ Chart saved as 'eth_5year_strategy_performance.png'")
    
    return fig

if __name__ == "__main__":
    results, portfolios = test_eth_5year_strategy()
    
    if results:
        print("\n🎯 KEY TAKEAWAYS:")
        print("1. Long-term performance validation")
        print("2. Strategy consistency over market cycles")
        print("3. Risk-adjusted returns vs buy & hold")
        print("4. Trade frequency and efficiency")
        print("5. Drawdown periods and recovery")
        
        print("\n📋 NEXT STEPS:")
        print("• Analyze strategy performance in different market conditions")
        print("• Test on other timeframes (4h, 1h) for more opportunities")
        print("• Implement portfolio diversification across multiple assets")
        print("• Add transaction costs for realistic performance")
        print("• Set up real-time monitoring and alerts")
    
    plt.show() 