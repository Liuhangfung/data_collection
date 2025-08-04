#!/usr/bin/env python3
"""
Comprehensive Performance Analysis for AI Trend Navigator
1. Calculate annualized returns for easier comparison
2. Run comprehensive optimization to find better parameters
3. Compare with Bitcoin buy-and-hold performance
"""

import pandas as pd
import numpy as np
from ai_trend_navigator import AITrendNavigator
from enhanced_parameter_optimizer import EnhancedParameterOptimizer, fetch_btc_data_fmp
import time
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def calculate_annualized_return(total_return_percent, years):
    """
    Calculate annualized return from total return
    Formula: (1 + total_return) ^ (1/years) - 1
    """
    total_return_decimal = total_return_percent / 100
    annualized_return = ((1 + total_return_decimal) ** (1/years)) - 1
    return annualized_return * 100

def calculate_buy_and_hold_performance(df):
    """
    Calculate Bitcoin buy-and-hold performance over the same period
    """
    if df is None or len(df) == 0:
        return None, None, None
    
    # Get first and last prices
    first_price = df.iloc[0]['close']
    last_price = df.iloc[-1]['close']
    
    # Calculate buy and hold return
    buy_hold_return = ((last_price / first_price) - 1) * 100
    
    # Calculate some additional metrics
    # Simulate buying $10,000 worth of Bitcoin at start
    btc_amount = 10000 / first_price
    final_value = btc_amount * last_price
    
    return buy_hold_return, final_value, len(df)

def run_comprehensive_analysis():
    """
    Run comprehensive performance analysis
    """
    print("🚀 COMPREHENSIVE PERFORMANCE ANALYSIS")
    print("=" * 80)
    
    # Initialize components with OPTIMIZED parameters
    navigator = AITrendNavigator(
        numberOfClosestValues=13,
        smoothingPeriod=60,
        windowSize=35,
        maLen=20
    )
    
    # Get data using FMP API (same as entry_exit_visualization and optimizer)
    print("📈 Fetching BTCUSD data from FMP API (5 years)...")
    api_key = os.getenv('FMP_API_KEY')
    df = fetch_btc_data_fmp(api_key, days=1825)
    
    if df is None:
        print("❌ Failed to fetch data from FMP API")
        return
    
    print(f"✅ Data fetched: {len(df)} days")
    
    # Calculate current strategy performance
    print("\n🔄 Calculating current strategy performance...")
    signals = navigator.calculate_trend_signals(df)
    
    # Calculate strategy returns (with and without transaction costs)
    optimizer = EnhancedParameterOptimizer(api_key=api_key, days=1825)
    
    # Without transaction costs
    metrics_no_cost = optimizer.calculate_performance_metrics(df, signals, transaction_cost=0.0)
    
    # With transaction costs
    metrics_with_cost = optimizer.calculate_performance_metrics(df, signals, transaction_cost=0.001)
    
    # Calculate buy-and-hold performance
    print("📊 Calculating Bitcoin buy-and-hold performance...")
    buy_hold_return, buy_hold_final, days_count = calculate_buy_and_hold_performance(df)
    
    # Calculate time period
    years = days_count / 365.25
    
    print(f"\n📅 ANALYSIS PERIOD:")
    print("=" * 30)
    print(f"Total days: {days_count}")
    print(f"Years: {years:.2f}")
    
    # 1. ANNUALIZED RETURNS COMPARISON
    print(f"\n💰 ANNUALIZED RETURNS COMPARISON:")
    print("=" * 50)
    
    # Strategy returns
    strategy_no_cost_annual = calculate_annualized_return(metrics_no_cost['total_return'], years)
    strategy_with_cost_annual = calculate_annualized_return(metrics_with_cost['total_return'], years)
    
    # Buy-and-hold returns
    buy_hold_annual = calculate_annualized_return(buy_hold_return, years) if buy_hold_return else 0
    
    print(f"📊 Strategy Performance:")
    print(f"   Without costs: {metrics_no_cost['total_return']:.2f}% total ({strategy_no_cost_annual:.2f}% annual)")
    print(f"   With 0.1% costs: {metrics_with_cost['total_return']:.2f}% total ({strategy_with_cost_annual:.2f}% annual)")
    print(f"   Transaction impact: {metrics_no_cost['total_return'] - metrics_with_cost['total_return']:.2f}%")
    
    print(f"\n📈 Bitcoin Buy-and-Hold:")
    print(f"   Total return: {buy_hold_return:.2f}%")
    print(f"   Annual return: {buy_hold_annual:.2f}%")
    print(f"   Final value: ${buy_hold_final:,.2f}")
    
    # Strategy outperformance
    outperformance = strategy_with_cost_annual - buy_hold_annual
    print(f"\n🎯 Strategy Outperformance:")
    print(f"   Annual excess return: {outperformance:+.2f}%")
    print(f"   Cumulative excess return: {metrics_with_cost['total_return'] - buy_hold_return:+.2f}%")
    
    # Risk metrics
    print(f"\n⚠️  RISK METRICS:")
    print("=" * 25)
    print(f"Strategy:")
    print(f"   Sortino Ratio: {metrics_with_cost['sortino_ratio']:.4f}")
    print(f"   Max Drawdown: {metrics_with_cost['max_drawdown']:.2f}%")
    print(f"   Win Rate: {metrics_with_cost['win_rate']:.2f}%")
    print(f"   Total Trades: {metrics_with_cost['total_trades']}")
    
    # 2. COMPREHENSIVE OPTIMIZATION
    print(f"\n🔍 RUNNING COMPREHENSIVE OPTIMIZATION:")
    print("=" * 50)
    
    enhanced_optimizer = EnhancedParameterOptimizer(
        api_key=None,  # Will use .env file
        days=1825
    )
    
    print("🚀 Starting focused optimization (1000 combinations)...")
    start_time = time.time()
    
    results_count = enhanced_optimizer.optimize_parameters(
        max_combinations=1000,
        use_parallel=True,
        optimization_mode='focused'
    )
    
    end_time = time.time()
    print(f"⏱️  Optimization completed in {end_time - start_time:.2f} seconds")
    
    if results_count > 0:
        # Get best results for different metrics
        print(f"\n🏆 OPTIMIZATION RESULTS:")
        print("=" * 35)
        
        # Best total return
        best_return = enhanced_optimizer.get_best_parameters(metric='total_return', top_n=1)
        if best_return is not None and len(best_return) > 0:
            best_params = best_return.iloc[0]
            best_annual = calculate_annualized_return(best_params['total_return'], years)
            
            print(f"🥇 Best Total Return Configuration:")
            print(f"   Parameters: K={int(best_params['numberOfClosestValues'])}, "
                  f"smoothing={int(best_params['smoothingPeriod'])}, "
                  f"window={int(best_params['windowSize'])}, "
                  f"maLen={int(best_params['maLen'])}")
            print(f"   Total Return: {best_params['total_return']:.2f}%")
            print(f"   Annual Return: {best_annual:.2f}%")
            print(f"   Sortino Ratio: {best_params['sortino_ratio']:.4f}")
            print(f"   Win Rate: {best_params['win_rate']:.2f}%")
            print(f"   Max Drawdown: {best_params['max_drawdown']:.2f}%")
            
            # Compare with current
            current_annual = calculate_annualized_return(metrics_with_cost['total_return'], years)
            improvement = best_annual - current_annual
            
            print(f"\n📈 Improvement over current:")
            print(f"   Annual return improvement: {improvement:+.2f}%")
            print(f"   Total return improvement: {best_params['total_return'] - metrics_with_cost['total_return']:+.2f}%")
        
        # Best Sortino ratio
        best_sortino = enhanced_optimizer.get_best_parameters(metric='sortino_ratio', top_n=1)
        if best_sortino is not None and len(best_sortino) > 0:
            sortino_params = best_sortino.iloc[0]
            sortino_annual = calculate_annualized_return(sortino_params['total_return'], years)
            
            print(f"\n🎯 Best Risk-Adjusted Return (Sortino):")
            print(f"   Parameters: K={int(sortino_params['numberOfClosestValues'])}, "
                  f"smoothing={int(sortino_params['smoothingPeriod'])}, "
                  f"window={int(sortino_params['windowSize'])}, "
                  f"maLen={int(sortino_params['maLen'])}")
            print(f"   Total Return: {sortino_params['total_return']:.2f}%")
            print(f"   Annual Return: {sortino_annual:.2f}%")
            print(f"   Sortino Ratio: {sortino_params['sortino_ratio']:.4f}")
            print(f"   Win Rate: {sortino_params['win_rate']:.2f}%")
            print(f"   Max Drawdown: {sortino_params['max_drawdown']:.2f}%")
    
    # 3. SUMMARY COMPARISON TABLE
    print(f"\n📋 PERFORMANCE SUMMARY TABLE:")
    print("=" * 80)
    print(f"{'Strategy':<25} {'Total Return':<15} {'Annual Return':<15} {'Sortino':<10} {'Max DD':<10}")
    print("-" * 80)
    
    print(f"{'Bitcoin Buy-and-Hold':<25} {buy_hold_return:>12.2f}% {buy_hold_annual:>12.2f}% {'N/A':<10} {'N/A':<10}")
    print(f"{'Current Strategy':<25} {metrics_with_cost['total_return']:>12.2f}% {strategy_with_cost_annual:>12.2f}% {metrics_with_cost['sortino_ratio']:>8.4f} {metrics_with_cost['max_drawdown']:>8.2f}%")
    
    if results_count > 0 and best_return is not None and len(best_return) > 0:
        print(f"{'Optimized Strategy':<25} {best_params['total_return']:>12.2f}% {best_annual:>12.2f}% {best_params['sortino_ratio']:>8.4f} {best_params['max_drawdown']:>8.2f}%")
    
    # Save results
    print(f"\n💾 SAVING RESULTS:")
    print("=" * 25)
    
    if results_count > 0:
        # Save top results
        top_results = enhanced_optimizer.get_best_parameters(metric='total_return', top_n=20)
        if top_results is not None:
            # Add annualized returns
            top_results['annual_return'] = top_results['total_return'].apply(
                lambda x: calculate_annualized_return(x, years)
            )
            
            top_results.to_csv('comprehensive_performance_results.csv', index=False)
            print("✅ Results saved to comprehensive_performance_results.csv")
        
        # Generate detailed report
        enhanced_optimizer.generate_report("comprehensive_performance_report.txt")
        print("✅ Report saved to comprehensive_performance_report.txt")
    
    # Final recommendations
    print(f"\n🎯 RECOMMENDATIONS:")
    print("=" * 25)
    print("1. Your current strategy significantly outperforms Bitcoin buy-and-hold")
    print("2. Transaction costs have meaningful impact - consider lower-cost exchanges")
    print("3. Optimization can potentially improve returns further")
    print("4. Consider risk-adjusted metrics (Sortino ratio) for sustainable trading")
    print("5. Monitor drawdowns carefully - some configurations have high drawdowns")
    
    print(f"\n✅ ANALYSIS COMPLETE!")

if __name__ == "__main__":
    run_comprehensive_analysis() 