#!/usr/bin/env python3
"""
Entry and Exit Points Visualization for AI Trend Navigator
Shows BTC/USDT price chart with clear entry/exit signals using optimized parameters
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv
from ai_trend_navigator import AITrendNavigator

# Load environment variables from .env file
load_dotenv()

def fetch_btc_data_fmp(api_key, days=1825):
    """
    Fetch BTC data from FMP API
    
    Parameters:
    - api_key: Your FMP API key
    - days: Number of days to fetch (default: 1825 = ~5 years)
    """
    symbol = "BTCUSD"
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Format dates for FMP API
    from_date = start_date.strftime('%Y-%m-%d')
    to_date = end_date.strftime('%Y-%m-%d')
    
    # FMP API endpoint for historical data
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
    params = {
        'from': from_date,
        'to': to_date,
        'apikey': api_key
    }
    
    print(f"📊 Fetching BTC data from FMP API...")
    print(f"   Symbol: {symbol}")
    print(f"   Date range: {from_date} to {to_date}")
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if 'historical' not in data:
            print("❌ No historical data found in FMP response")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(data['historical'])
        
        # Convert date and sort
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # Rename columns to match AITrendNavigator format
        df = df.rename(columns={
            'date': 'timestamp',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        })
        
        # Keep only required columns
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        # Set timestamp as index for easier date calculations
        df.set_index('timestamp', inplace=True)
        
        print(f"✅ Fetched {len(df)} days of BTC data")
        print(f"📊 Date range: {df.index[0]} to {df.index[-1]}")
        
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data from FMP API: {e}")
        return None
    except Exception as e:
        print(f"❌ Error processing FMP data: {e}")
        return None

def create_entry_exit_plot(api_key=None):
    """Create a detailed plot showing entry and exit points with price chart"""
    
    # Check if API key is provided as parameter, otherwise read from .env
    if api_key is None:
        api_key = os.getenv('FMP_API_KEY')
        
    if api_key is None:
        print("❌ FMP API key not found!")
        print("   Please either:")
        print("   1. Add FMP_API_KEY to your .env file, or")
        print("   2. Pass the API key as parameter: create_entry_exit_plot('your_api_key_here')")
        print("   3. Get your free API key from: https://financialmodelingprep.com/")
        return None, None, 0, 0
    
    # Use BEST optimized parameters from latest comprehensive optimization
    optimized_params = {
        'numberOfClosestValues': 19,
        'smoothingPeriod': 70,
        'windowSize': 65,
        'maLen': 12
    }
    
    print("🚀 Creating Entry/Exit Visualization with BEST Optimized Parameters...")
    print(f"   K={optimized_params['numberOfClosestValues']}, smoothing={optimized_params['smoothingPeriod']}, window={optimized_params['windowSize']}, maLen={optimized_params['maLen']}")
    print(f"   Expected Performance: 2088.13% return, 43.59% win rate, 39 trades")
    
    # Initialize navigator with optimized parameters
    navigator = AITrendNavigator(**optimized_params)
    
    # Fetch 5 years of BTC data using FMP API
    data = fetch_btc_data_fmp(api_key, days=1825)
    
    if data is None:
        print("❌ Failed to fetch data from FMP API")
        return None, None, 0, 0
    
    # Calculate signals using the AITrendNavigator
    print("🧮 Calculating trend signals...")
    # Reset index for navigator (it expects timestamp as column)
    data_for_navigator = data.reset_index()
    signals = navigator.calculate_trend_signals(data_for_navigator)
    
    # Ensure signals DataFrame has the same datetime index as data
    signals.index = data.index
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), height_ratios=[3, 1])
    
    # Plot 1: Price chart with entry/exit points
    ax1.plot(data.index, data['close'], color='black', linewidth=1, alpha=0.7, label='BTC/USDT Price')
    
    # Plot AI Trend Navigator line with trend-based coloring
    for i in range(1, len(signals)):
        start_idx = i - 1
        end_idx = i
        
        # Get trend direction for coloring
        trend = signals.iloc[i]['trend_direction']
        color = 'green' if trend == 'up' else 'red' if trend == 'down' else 'gray'
        
        # Plot line segment
        ax1.plot([signals.index[start_idx], signals.index[end_idx]], 
                [signals.iloc[start_idx]['knnMA_smoothed'], signals.iloc[end_idx]['knnMA_smoothed']], 
                color=color, linewidth=2, alpha=0.8)
    
    # Add legend entries for trend colors
    ax1.plot([], [], color='green', linewidth=2, label='AI Trend Navigator (Uptrend)')
    ax1.plot([], [], color='red', linewidth=2, label='AI Trend Navigator (Downtrend)')
    
    # Get entry and exit points
    entries = []
    exits = []
    current_position = None
    
    for i, (date, signal) in enumerate(signals.iterrows()):
        if signal['signal'] == 'buy' and current_position != 'long':
            entries.append({'date': date, 'price': signal['price'], 'type': 'buy'})
            current_position = 'long'
        elif signal['signal'] == 'sell' and current_position == 'long':
            exits.append({'date': date, 'price': signal['price'], 'type': 'sell'})
            current_position = 'cash'
    
    # Calculate price range for marker offset
    price_range = data['close'].max() - data['close'].min()
    offset = price_range * 0.04  # 4% of price range for better visual separation
    
    # Plot entry points (green triangles up) - above actual price
    if entries:
        entry_dates = [e['date'] for e in entries]
        entry_prices = [e['price'] + offset for e in entries]  # Offset upward
        ax1.scatter(entry_dates, entry_prices, color='darkgreen', marker='^', s=120, 
                   label=f'Entry Points ({len(entries)})', zorder=6, edgecolors='white', linewidth=1)
    
    # Plot exit points (red triangles down) - well below actual price
    if exits:
        exit_dates = [e['date'] for e in exits]
        exit_prices = [e['price'] - offset * 1.5 for e in exits]  # Larger offset downward
        ax1.scatter(exit_dates, exit_prices, color='darkred', marker='v', s=120, 
                   label=f'Exit Points ({len(exits)})', zorder=6, edgecolors='white', linewidth=1)
    
    # Calculate performance metrics first (needed for drawdown period)
    def calculate_basic_metrics(entries, exits, signals):
        """Calculate basic performance metrics"""
        if len(entries) == 0 or len(exits) == 0:
            return 0, 0, 0, 0, None, None
        
        # Strategy return calculation based on portfolio performance
        winning_trades = 0
        total_trades = 0
        
        # Count winning trades for win rate calculation
        for i in range(min(len(entries), len(exits))):
            if i < len(entries) and i < len(exits):
                entry_price = entries[i]['price']
                exit_price = exits[i]['price']
                trade_return = (exit_price - entry_price) / entry_price
                total_trades += 1
                if trade_return > 0:
                    winning_trades += 1
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Strategy drawdown calculation based on trading signals
        # Simulate following the buy/sell signals
        portfolio_value = []
        cash = 10000  # Starting with $10,000
        btc_holdings = 0
        position = None
        
        for i in range(len(signals)):
            current_signal = signals.iloc[i]['signal']
            current_price = signals.iloc[i]['price']
            
            if current_signal == 'buy' and position != 'long':
                # Buy signal - convert cash to BTC
                if cash > 0:
                    btc_holdings = cash / current_price
                    cash = 0
                    position = 'long'
                    
            elif current_signal == 'sell' and position == 'long':
                # Sell signal - convert BTC to cash
                if btc_holdings > 0:
                    cash = btc_holdings * current_price
                    btc_holdings = 0
                    position = 'short'
            
            # Calculate current portfolio value
            if position == 'long':
                current_value = btc_holdings * current_price
            else:
                current_value = cash
                
            portfolio_value.append(current_value)
        
        # Calculate strategy drawdown
        portfolio_value = np.array(portfolio_value)
        running_max = np.maximum.accumulate(portfolio_value)
        drawdown = (portfolio_value - running_max) / running_max * 100
        max_drawdown = np.min(drawdown)
        
        # Find max drawdown period
        max_dd_idx = np.argmin(drawdown)
        max_dd_date = signals.index[max_dd_idx]
        
        # Find the start of the drawdown period (when it was at the previous high)
        dd_start_idx = max_dd_idx
        for i in range(max_dd_idx, -1, -1):
            if drawdown[i] >= -0.5:  # Less than 0.5% drawdown
                dd_start_idx = i
                break
        dd_start_date = signals.index[dd_start_idx]
        
        # Calculate total strategy return
        total_return = ((portfolio_value[-1] / portfolio_value[0]) - 1) * 100
        
        # Sortino ratio calculation based on portfolio returns
        portfolio_returns = np.diff(portfolio_value) / portfolio_value[:-1]
        avg_return = np.mean(portfolio_returns)
        negative_returns = portfolio_returns[portfolio_returns < 0]
        downside_deviation = np.std(negative_returns) if len(negative_returns) > 0 else 0.01
        sortino_ratio = avg_return / downside_deviation * np.sqrt(252) if downside_deviation > 0 else 0
        
        return total_return, sortino_ratio, win_rate, max_drawdown, dd_start_date, max_dd_date
    
    total_return, sortino_ratio, win_rate, max_drawdown, dd_start_date, dd_end_date = calculate_basic_metrics(entries, exits, signals)
    
    # Color background based on trend direction (more transparent)
    for i in range(len(signals)):
        if i == 0:
            continue
            
        current_trend = signals.iloc[i]['trend_direction']
        start_date = signals.index[i-1]
        end_date = signals.index[i]
        
        if current_trend == 'up':
            ax1.axvspan(start_date, end_date, alpha=0.05, color='green', zorder=1)
        elif current_trend == 'down':
            ax1.axvspan(start_date, end_date, alpha=0.05, color='red', zorder=1)
    
    # Highlight maximum strategy drawdown period
    if dd_start_date and dd_end_date:
        ax1.axvspan(dd_start_date, dd_end_date, alpha=0.2, color='orange', zorder=2, 
                   label=f'Strategy Max Drawdown Period ({max_drawdown:.1f}%)')
        
        # Add text annotation for max drawdown
        ax1.annotate(f'Strategy Max Drawdown: {max_drawdown:.1f}%', 
                    xy=(dd_end_date, signals.loc[dd_end_date, 'price']), 
                    xytext=(10, 10), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='orange', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', color='orange'),
                    fontsize=9, fontweight='bold')
    
    ax1.set_title('BTC/USDT - Entry/Exit Points with AI Trend Navigator\n(Optimized Parameters)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Price (USD)', fontsize=12)
    ax1.legend(loc='upper left', bbox_to_anchor=(0, 0.95))
    ax1.grid(True, alpha=0.3)
    
    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    
    # Plot 2: Signal strength and trend direction
    signal_numeric = signals['signal'].map({'buy': 1, 'sell': -1, 'hold': 0})
    ax2.plot(signals.index, signal_numeric, color='purple', linewidth=2, label='Signal Strength')
    ax2.fill_between(signals.index, 0, signal_numeric, 
                     where=(signal_numeric > 0), color='green', alpha=0.3, label='Buy Signal')
    ax2.fill_between(signals.index, 0, signal_numeric, 
                     where=(signal_numeric < 0), color='red', alpha=0.3, label='Sell Signal')
    
    ax2.set_title('Signal Strength Over Time', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Signal', fontsize=10)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(-1.5, 1.5)
    
    # Format x-axis
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    
    plt.tight_layout()
    plt.xticks(rotation=45)
    
    # Add performance text box
    performance_text = f"""
📊 STRATEGY PERFORMANCE (5 Years):
• Total Return: {total_return:.2f}%
• Sortino Ratio: {sortino_ratio:.4f}
• Win Rate: {win_rate:.2f}%
• Max Drawdown: {max_drawdown:.2f}%
• Total Entries: {len(entries)}
• Total Exits: {len(exits)}
• Starting Capital: $10,000
"""
    
    ax1.text(0.98, 0.02, performance_text, transform=ax1.transAxes, 
             verticalalignment='bottom', horizontalalignment='right', 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
             fontsize=10, fontfamily='monospace')
    
    plt.savefig('btc_entry_exit_signals.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print summary
    print("\n" + "="*60)
    print("📊 AI TREND NAVIGATOR STRATEGY RESULTS")
    print("="*60)
    print(f"Starting Capital: $10,000")
    print(f"Total Entry Points: {len(entries)}")
    print(f"Total Exit Points: {len(exits)}")
    print(f"Strategy Total Return: {total_return:.2f}%")
    print(f"Sortino Ratio: {sortino_ratio:.4f}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Strategy Max Drawdown: {max_drawdown:.2f}%")
    if dd_start_date and dd_end_date:
        try:
            print(f"Max Drawdown Period: {dd_start_date.strftime('%Y-%m-%d')} to {dd_end_date.strftime('%Y-%m-%d')}")
        except AttributeError:
            print(f"Max Drawdown Period: {dd_start_date} to {dd_end_date}")
    print("="*60)
    
    return entries, exits, total_return, sortino_ratio

def compare_strategies(api_key=None):
    """
    Compare three strategies: Default parameters, Buy & Hold, and Best Optimized parameters
    """
    print("🔍 COMPREHENSIVE STRATEGY COMPARISON")
    print("=" * 60)
    
    # Get API key from environment if not provided
    if api_key is None:
        api_key = os.getenv('FMP_API_KEY')
        if api_key is None:
            print("❌ FMP API key not found!")
            print("   Please add FMP_API_KEY to your .env file")
            return
    
    # Fetch data once for all strategies
    btc_data = fetch_btc_data_fmp(api_key)
    if btc_data is None:
        return
    
    # Define strategy parameters
    strategies = {
        'Default Parameters': {
            'numberOfClosestValues': 3,
            'smoothingPeriod': 50,
            'windowSize': 30,
            'maLen': 5
        },
        'Best Optimized': {
            'numberOfClosestValues': 19,
            'smoothingPeriod': 70,
            'windowSize': 65,
            'maLen': 12
        }
    }
    
    results = {}
    
    # Calculate Buy & Hold performance
    print("\n📈 Calculating Buy & Hold Performance...")
    start_price = btc_data['close'].iloc[0]
    end_price = btc_data['close'].iloc[-1]
    buy_hold_return = ((end_price / start_price) - 1) * 100
    
    # Calculate annualized return for buy & hold
    days = (btc_data.index[-1] - btc_data.index[0]).days
    years = days / 365.25
    buy_hold_annual = ((end_price / start_price) ** (1/years) - 1) * 100
    
    results['Buy & Hold'] = {
        'total_return': buy_hold_return,
        'annual_return': buy_hold_annual,
        'win_rate': 100.0,  # Always wins if held long enough
        'max_drawdown': 0,  # Simplified for comparison
        'sortino_ratio': 0,  # Not applicable
        'trades': 1,
        'description': 'Simple buy and hold strategy'
    }
    
    # Calculate performance for each AI strategy
    for strategy_name, params in strategies.items():
        print(f"\n🤖 Calculating {strategy_name} Performance...")
        print(f"   Parameters: K={params['numberOfClosestValues']}, smoothing={params['smoothingPeriod']}, window={params['windowSize']}, maLen={params['maLen']}")
        
        # Initialize navigator with specific parameters
        navigator = AITrendNavigator(**params)
        # Reset index for navigator (it expects timestamp as column)
        btc_data_for_navigator = btc_data.reset_index()
        signals = navigator.calculate_trend_signals(btc_data_for_navigator)
        
        # Ensure signals DataFrame has the same datetime index as btc_data
        signals.index = btc_data.index
        
        # Calculate metrics
        def calculate_strategy_metrics(signals):
            entries = []
            exits = []
            current_position = 'cash'
            
            for idx, (date, signal) in enumerate(signals.iterrows()):
                current_signal = signal['signal']
                
                if current_signal == 'buy' and current_position == 'cash':
                    entries.append({'date': date, 'price': signal['price']})
                    current_position = 'long'
                elif current_signal == 'sell' and current_position == 'long':
                    exits.append({'date': date, 'price': signal['price']})
                    current_position = 'cash'
            
            # Calculate portfolio performance
            portfolio_value = []
            cash = 10000  # Starting capital
            btc_holdings = 0
            position = 'short'
            
            for idx, (date, signal) in enumerate(signals.iterrows()):
                current_signal = signal['signal']
                current_price = signal['price']
                
                if current_signal == 'buy' and position == 'short':
                    btc_holdings = cash / current_price
                    cash = 0
                    position = 'long'
                elif current_signal == 'sell' and position == 'long':
                    cash = btc_holdings * current_price
                    btc_holdings = 0
                    position = 'short'
                
                current_value = btc_holdings * current_price if position == 'long' else cash
                portfolio_value.append(current_value)
            
            # Calculate metrics
            portfolio_value = np.array(portfolio_value)
            total_return = ((portfolio_value[-1] / portfolio_value[0]) - 1) * 100
            
            # Calculate annualized return
            annual_return = ((portfolio_value[-1] / portfolio_value[0]) ** (1/years) - 1) * 100
            
            # Calculate win rate
            wins = sum(1 for i in range(len(entries)) if i < len(exits) and exits[i]['price'] > entries[i]['price'])
            win_rate = (wins / len(exits)) * 100 if exits else 0
            
            # Calculate drawdown
            running_max = np.maximum.accumulate(portfolio_value)
            drawdown = (portfolio_value - running_max) / running_max * 100
            max_drawdown = np.min(drawdown)
            
            # Calculate Sortino ratio
            portfolio_returns = np.diff(portfolio_value) / portfolio_value[:-1]
            avg_return = np.mean(portfolio_returns)
            negative_returns = portfolio_returns[portfolio_returns < 0]
            downside_deviation = np.std(negative_returns) if len(negative_returns) > 0 else 0.01
            sortino_ratio = avg_return / downside_deviation * np.sqrt(252) if downside_deviation > 0 else 0
            
            return {
                'total_return': total_return,
                'annual_return': annual_return,
                'win_rate': win_rate,
                'max_drawdown': max_drawdown,
                'sortino_ratio': sortino_ratio,
                'trades': len(entries),
                'entries': entries,
                'exits': exits
            }
        
        strategy_results = calculate_strategy_metrics(signals)
        results[strategy_name] = strategy_results
    
    # Display comparison results
    print("\n" + "=" * 80)
    print("📊 STRATEGY COMPARISON RESULTS")
    print("=" * 80)
    
    # Create comparison table
    print(f"{'Strategy':<20} {'Total Return':<15} {'Annual Return':<15} {'Win Rate':<12} {'Max DD':<12} {'Sortino':<12} {'Trades':<8}")
    print("-" * 100)
    
    for strategy_name, result in results.items():
        print(f"{strategy_name:<20} {result['total_return']:>12.2f}% {result['annual_return']:>12.2f}% "
              f"{result['win_rate']:>9.2f}% {result['max_drawdown']:>9.2f}% "
              f"{result['sortino_ratio']:>9.4f} {result['trades']:>6}")
    
    # Determine winner
    best_strategy = max(results.keys(), key=lambda x: results[x]['total_return'])
    print(f"\n🏆 WINNER: {best_strategy} with {results[best_strategy]['total_return']:.2f}% total return")
    
    # Show detailed comparison
    print("\n📈 DETAILED COMPARISON:")
    for strategy_name, result in results.items():
        print(f"\n{strategy_name}:")
        print(f"  • Total Return: {result['total_return']:.2f}%")
        print(f"  • Annualized Return: {result['annual_return']:.2f}%")
        print(f"  • Win Rate: {result['win_rate']:.2f}%")
        print(f"  • Max Drawdown: {result['max_drawdown']:.2f}%")
        print(f"  • Sortino Ratio: {result['sortino_ratio']:.4f}")
        print(f"  • Number of Trades: {result['trades']}")
        
        if strategy_name != 'Buy & Hold':
            print(f"  • Risk-Adjusted Performance: {'Excellent' if result['sortino_ratio'] > 1 else 'Good' if result['sortino_ratio'] > 0.5 else 'Average'}")
    
    return results

if __name__ == "__main__":
    print("🚀 BTC Entry/Exit Visualization with AI Trend Navigator")
    print("="*60)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  No .env file found. Creating template...")
        with open('.env', 'w') as f:
            f.write("# Add your FMP API key here\n")
            f.write("# Get your free API key from: https://financialmodelingprep.com/\n")
            f.write("FMP_API_KEY=your_api_key_here\n")
        print("✅ Template .env file created. Please add your FMP API key and run again.")
        exit(1)
    
    # Ask user what they want to do
    print("\nChoose an option:")
    print("1. Show visualization with best parameters")
    print("2. Compare strategies (Default vs Buy & Hold vs Best Optimized)")
    choice = input("Enter your choice (1 or 2): ").strip()
    
    if choice == "2":
        # Run strategy comparison
        print("\n" + "="*60)
        print("🔍 RUNNING COMPREHENSIVE STRATEGY COMPARISON")
        print("="*60)
        results = compare_strategies()
        
        if results:
            print("\n✅ Strategy comparison completed!")
            print("📊 Check the detailed results above to make informed decisions")
    else:
        # Create visualization (default)
        entries, exits, total_return, sortino_ratio = create_entry_exit_plot()
        
        if entries is not None and exits is not None:
            print("✅ Entry/Exit visualization completed successfully!")
            print(f"📊 Chart saved as: btc_entry_exit_signals.png")
            plt.show()
        else:
            print("❌ Failed to create visualization. Please check your API key in .env file and try again.") 