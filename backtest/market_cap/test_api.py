#!/usr/bin/env python3
"""
Simple test script to debug CoinGecko API issues
"""

import requests
import json

def test_coingecko_simple_api():
    """Test the simple price API"""
    print("Testing CoinGecko Simple Price API...")
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': 'bitcoin,ethereum',
        'vs_currencies': 'usd',
        'include_market_cap': 'true',
        'include_24hr_change': 'true'
    }
    
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        print(f"URL: {response.url}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Keys: {list(data.keys())}")
            print(f"Full Response: {json.dumps(data, indent=2)}")
            
            # Test calculations
            if 'bitcoin' in data and 'ethereum' in data:
                btc_mc = data['bitcoin']['usd_market_cap']
                eth_mc = data['ethereum']['usd_market_cap']
                ratio = eth_mc / btc_mc
                print(f"\nCalculations:")
                print(f"BTC Market Cap: ${btc_mc:,.0f}")
                print(f"ETH Market Cap: ${eth_mc:,.0f}")
                print(f"ETH/BTC Ratio: {ratio:.4f}")
                print(f"BTC/ETH Ratio: {1/ratio:.2f}")
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

def test_coingecko_market_chart():
    """Test the market chart API"""
    print("\n" + "="*50)
    print("Testing CoinGecko Market Chart API...")
    
    # Test with different parameters
    test_params = [
        {'days': 30, 'interval': 'daily'},
        {'days': 365, 'interval': 'daily'},
        {'days': 'max', 'interval': 'daily'},
    ]
    
    for params in test_params:
        print(f"\nTesting with params: {params}")
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        params_full = {'vs_currency': 'usd', **params}
        
        try:
            response = requests.get(url, params=params_full)
            print(f"Status Code: {response.status_code}")
            print(f"URL: {response.url}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response Keys: {list(data.keys())}")
                
                if 'market_caps' in data:
                    print(f"Market Caps Data Points: {len(data['market_caps'])}")
                    print(f"First Entry: {data['market_caps'][0]}")
                    print(f"Last Entry: {data['market_caps'][-1]}")
                else:
                    print(f"No 'market_caps' key. Full response: {json.dumps(data, indent=2)[:500]}...")
                    
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")
        
        print("-" * 30)

if __name__ == "__main__":
    test_coingecko_simple_api()
    test_coingecko_market_chart() 