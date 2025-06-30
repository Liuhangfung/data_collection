import requests
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase = create_client(supabase_url, supabase_key)

def get_altcoin_season_index():
    # CoinGecko API endpoint
    base_url = "https://api.coingecko.com/api/v3"
    
    # Get top 100 coins by market cap
    try:
        response = requests.get(f"{base_url}/coins/markets", params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 100,
            "page": 1,
            "sparkline": False
        })
        response.raise_for_status()
        coins_data = response.json()
        
        # Calculate total market cap of all coins
        total_market_cap = sum(coin['market_cap'] for coin in coins_data)
        
        # Get Bitcoin's market cap
        btc_market_cap = next(coin['market_cap'] for coin in coins_data if coin['id'] == 'bitcoin')
        
        # Calculate altcoin market cap (total - BTC)
        altcoin_market_cap = total_market_cap - btc_market_cap
        
        # Calculate Altcoin Season Index
        altcoin_index = (altcoin_market_cap / total_market_cap) * 100
        
        # Determine season
        if altcoin_index > 75:
            season = "Altcoin Season"
        elif altcoin_index < 25:
            season = "Bitcoin Season"
        else:
            season = "Neutral"
            
        result = {
            "season_index": round(altcoin_index, 2),
            "season": season,
            "btc_dominance": round((btc_market_cap / total_market_cap) * 100, 2),
            "alt_dominance": round((altcoin_market_cap / total_market_cap) * 100, 2),
            "total_market_cap": total_market_cap,
            "btc_market_cap": btc_market_cap,
            "created_at": datetime.now().isoformat()
        }
        
        # Check if data for today already exists
        today = datetime.now().date().isoformat()
        data = supabase.table('coin_season').select('*').gte('created_at', today).lt('created_at', (datetime.now().date() + timedelta(days=1)).isoformat()).execute()
        
        # Save to Supabase
        try:
            if data.data and len(data.data) > 0:
                # Update existing record
                record_id = data.data[0]['id']
                supabase.table('coin_season').update(result).eq('id', record_id).execute()
                print(f"Data for today updated in Supabase (ID: {record_id})")
            else:
                # Insert new record
                supabase.table('coin_season').insert(result).execute()
                print("New data saved to Supabase")
        except Exception as e:
            print(f"Error saving to Supabase: {e}")
            
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

if __name__ == "__main__":
    result = get_altcoin_season_index()
    if result:
        print("\nAltcoin Season Index Analysis:")
        print("-" * 30)
        print(f"Altcoin Season Index: {result['season_index']}%")
        print(f"Current Season: {result['season']}")
        print(f"Bitcoin Dominance: {result['btc_dominance']}%")
        print(f"Altcoin Dominance: {result['alt_dominance']}%")
        print(f"Last Updated: {result['created_at']}")
