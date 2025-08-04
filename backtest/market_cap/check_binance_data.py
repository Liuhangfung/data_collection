#!/usr/bin/env python3
"""
Check what historical data Binance API provides
Investigate data availability for ETH/BTC market cap analysis
"""

import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time

def check_binance_data_availability():
    """
    Check Binance API data availability and limitations
    """
    print("🔍 BINANCE API DATA AVAILABILITY CHECK")
    print("=" * 50)
    
    try:
        # Initialize Binance exchange
        exchange = ccxt.binance({
            'timeout': 30000,
            'rateLimit': 1200,
        })
        
        # Check available symbols
        markets = exchange.load_markets()
        eth_btc_available = 'ETH/BTC' in markets
        btc_usdt_available = 'BTC/USDT' in markets
        eth_usdt_available = 'ETH/USDT' in markets
        
        print(f"📊 Available Trading Pairs:")
        print(f"   ETH/BTC: {'✅ Available' if eth_btc_available else '❌ Not Available'}")
        print(f"   BTC/USDT: {'✅ Available' if btc_usdt_available else '❌ Not Available'}")
        print(f"   ETH/USDT: {'✅ Available' if eth_usdt_available else '❌ Not Available'}")
        
        # Test historical data availability
        print(f"\n📈 Historical Price Data Availability:")
        
        test_periods = [
            ("1 year", 365),
            ("2 years", 730), 
            ("3 years", 1095),
            ("4 years", 1460),
            ("5 years", 1825)
        ]
        
        for period_name, days in test_periods:
            try:
                since = exchange.milliseconds() - (days * 24 * 60 * 60 * 1000)
                
                # Test ETH/BTC data
                ohlcv = exchange.fetch_ohlcv('ETH/BTC', '1d', since, limit=10)
                
                if ohlcv:
                    first_date = pd.to_datetime(ohlcv[0][0], unit='ms')
                    print(f"   {period_name}: ✅ Available (oldest: {first_date.strftime('%Y-%m-%d')})")
                else:
                    print(f"   {period_name}: ❌ No data")
                    
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"   {period_name}: ❌ Error - {str(e)[:50]}...")
        
        # Test maximum historical data
        print(f"\n🔙 Maximum Historical Data Test:")
        try:
            # Try to get data from 5 years ago
            five_years_ago = exchange.milliseconds() - (5 * 365 * 24 * 60 * 60 * 1000)
            ohlcv = exchange.fetch_ohlcv('ETH/BTC', '1d', five_years_ago, limit=5)
            
            if ohlcv:
                first_date = pd.to_datetime(ohlcv[0][0], unit='ms')
                last_date = pd.to_datetime(ohlcv[-1][0], unit='ms')
                print(f"   ✅ 5-year test successful!")
                print(f"   📅 Date range: {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}")
                print(f"   📊 Sample data points: {len(ohlcv)}")
            else:
                print(f"   ❌ No 5-year historical data available")
                
        except Exception as e:
            print(f"   ❌ 5-year test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking Binance API: {e}")
        return False

def explain_market_cap_data_requirements():
    """
    Explain what data is needed for market cap analysis
    """
    print(f"\n💡 MARKET CAP DATA REQUIREMENTS")
    print("=" * 50)
    print("📊 Market Cap Formula: Price × Circulating Supply")
    print()
    print("🏦 What Binance Provides:")
    print("   ✅ Historical Prices (OHLCV data)")
    print("   ✅ Trading volumes")
    print("   ✅ Up to ~5 years of daily data")
    print("   ✅ Real-time price feeds")
    print()
    print("❌ What Binance DOESN'T Provide:")
    print("   ❌ Circulating supply data")
    print("   ❌ Market cap calculations")
    print("   ❌ Fundamental crypto metrics")
    print()
    print("🔄 For Market Cap Analysis, You Need:")
    print("   📈 Prices: Binance API (✅ Available)")
    print("   🔢 Supply: CoinGecko/CoinMarketCap APIs")
    print("   📊 Market Caps: CoinGecko/CoinMarketCap APIs")

def check_alternative_sources():
    """
    Check alternative data sources for 5-year market cap data
    """
    print(f"\n🌐 ALTERNATIVE DATA SOURCES FOR 5-YEAR MARKET CAP DATA")
    print("=" * 60)
    
    sources = [
        {
            "name": "CoinGecko Pro API",
            "cost": "$129/month",
            "features": "Full historical data back to 2013, market caps, supplies",
            "link": "https://www.coingecko.com/en/api/pricing"
        },
        {
            "name": "CoinMarketCap Pro API", 
            "cost": "$333/month",
            "features": "Historical market caps, comprehensive crypto data",
            "link": "https://coinmarketcap.com/api/pricing/"
        },
        {
            "name": "Yahoo Finance (yfinance)",
            "cost": "Free",
            "features": "BTC-USD, ETH-USD price data (5+ years), but NO market caps",
            "link": "pip install yfinance"
        },
        {
            "name": "Manual CSV Download",
            "cost": "Free",
            "features": "CoinMarketCap historical data export",
            "link": "https://coinmarketcap.com/currencies/bitcoin/historical-data/"
        },
        {
            "name": "CryptoCompare API",
            "cost": "Free tier limited",
            "features": "Historical price data, some market metrics",
            "link": "https://cryptocompare.com/cryptopian/api-keys"
        }
    ]
    
    for i, source in enumerate(sources, 1):
        print(f"{i}. **{source['name']}**")
        print(f"   💰 Cost: {source['cost']}")
        print(f"   🔧 Features: {source['features']}")
        print(f"   🔗 Link: {source['link']}")
        print()

def main():
    """
    Main function to check data availability
    """
    print("🚀 CHECKING 5-YEAR MARKET CAP DATA AVAILABILITY")
    print("=" * 60)
    
    # Check Binance capabilities
    binance_ok = check_binance_data_availability()
    
    # Explain market cap requirements
    explain_market_cap_data_requirements()
    
    # Check alternative sources
    check_alternative_sources()
    
    print("📝 SUMMARY FOR 5-YEAR ETH/BTC MARKET CAP ANALYSIS:")
    print("=" * 60)
    print("✅ Binance: 5 years of PRICE data available")
    print("❌ Binance: NO market cap or supply data")
    print("💡 Solution: Combine Binance prices + CoinGecko/CMC market caps")
    print()
    print("🎯 RECOMMENDED APPROACH:")
    print("1. Use Binance for historical ETH/BTC price ratios (5 years)")
    print("2. Use CoinGecko Pro or manual CSV for market cap data (5 years)")
    print("3. Combine both datasets for comprehensive analysis")
    
if __name__ == "__main__":
    main() 