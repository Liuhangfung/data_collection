#!/usr/bin/env python3
"""
Quick ETH/BTC Market Cap Ratio Example

This script demonstrates how to quickly get ETH/BTC market cap ratios
using CCXT Binance API and CoinGecko market cap data.
"""

import ccxt
import requests
from datetime import datetime

def get_quick_eth_btc_market_cap_ratio():
    """
    Quick function to get current ETH/BTC market cap ratio
    """
    try:
        # Initialize Binance exchange (no API keys needed for public data)
        exchange = ccxt.binance({
            'timeout': 30000,
            'rateLimit': 1200,
        })
        
        # Get current prices from Binance
        print("Fetching current prices from Binance...")
        eth_btc_ticker = exchange.fetch_ticker('ETH/BTC')
        btc_ticker = exchange.fetch_ticker('BTC/USDT')
        eth_ticker = exchange.fetch_ticker('ETH/USDT')
        
        # Get market cap data from CoinGecko (free API)
        print("Fetching market cap data from CoinGecko...")
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': 'bitcoin,ethereum',
            'vs_currencies': 'usd',
            'include_market_cap': 'true',
            'include_24hr_change': 'true'
        }
        
        response = requests.get(url, params=params)
        market_data = response.json()
        
        # Calculate ratios
        price_ratio = eth_btc_ticker['last']
        btc_market_cap = market_data['bitcoin']['usd_market_cap']
        eth_market_cap = market_data['ethereum']['usd_market_cap']
        market_cap_ratio = eth_market_cap / btc_market_cap
        
        # Display results
        print("\n" + "="*60)
        print("ETH/BTC MARKET ANALYSIS")
        print("="*60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        print("CURRENT PRICES:")
        print(f"  BTC: ${btc_ticker['last']:,.2f}")
        print(f"  ETH: ${eth_ticker['last']:,.2f}")
        print(f"  ETH/BTC Price Ratio: {price_ratio:.6f}")
        print()
        
        print("MARKET CAPITALIZATIONS:")
        print(f"  BTC Market Cap: ${btc_market_cap:,.0f} (${btc_market_cap/1e12:.3f}T)")
        print(f"  ETH Market Cap: ${eth_market_cap:,.0f} (${eth_market_cap/1e12:.3f}T)")
        print(f"  ETH/BTC Market Cap Ratio: {market_cap_ratio:.4f}")
        print(f"  BTC/ETH Market Cap Ratio: {1/market_cap_ratio:.2f}")
        print()
        
        print("24H CHANGES:")
        print(f"  BTC 24h Change: {market_data['bitcoin']['usd_24h_change']:+.2f}%")
        print(f"  ETH 24h Change: {market_data['ethereum']['usd_24h_change']:+.2f}%")
        print()
        
        print("ANALYSIS:")
        if market_cap_ratio > price_ratio:
            difference = ((market_cap_ratio / price_ratio) - 1) * 100
            print(f"  📊 ETH market cap ratio is {difference:.1f}% HIGHER than price ratio")
            print(f"     This suggests ETH has higher circulating supply relative to BTC")
        else:
            difference = ((price_ratio / market_cap_ratio) - 1) * 100
            print(f"  📊 ETH price ratio is {difference:.1f}% HIGHER than market cap ratio")
            print(f"     This suggests BTC has higher circulating supply relative to ETH")
        
        # Historical context
        if market_cap_ratio > 0.15:
            print(f"  🔥 ETH market cap ratio ({market_cap_ratio:.4f}) is relatively HIGH")
        elif market_cap_ratio < 0.10:
            print(f"  ❄️  ETH market cap ratio ({market_cap_ratio:.4f}) is relatively LOW")
        else:
            print(f"  ⚖️  ETH market cap ratio ({market_cap_ratio:.4f}) is in normal range")
        
        print("="*60)
        
        return {
            'timestamp': datetime.now(),
            'btc_price': btc_ticker['last'],
            'eth_price': eth_ticker['last'],
            'price_ratio': price_ratio,
            'btc_market_cap': btc_market_cap,
            'eth_market_cap': eth_market_cap,
            'market_cap_ratio': market_cap_ratio
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    result = get_quick_eth_btc_market_cap_ratio()
    
    if result:
        print("\n💡 TIP: Run 'python eth_btc_market_cap_analysis.py' for comprehensive charting!")
    else:
        print("❌ Failed to fetch data. Please check your internet connection.") 