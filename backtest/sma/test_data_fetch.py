import ccxt
import pandas as pd
from datetime import datetime, timedelta

def test_historical_data_fetch():
    """Test script to verify different time periods return different data."""
    
    # Initialize exchange
    exchange = ccxt.binance({
        'apiKey': '',
        'secret': '',
        'timeout': 30000,
        'enableRateLimit': True,
    })
    
    symbol = 'BTC/USDT'
    timeframe = '8h'
    
    print("Testing Historical Data Fetching")
    print("="*50)
    
    # Test different time periods
    time_periods = [1, 2]  # Test with 1 and 2 years for quick verification
    
    for years in time_periods:
        print(f"\nFetching {years} year(s) of data for {symbol}...")
        
        try:
            # Calculate start timestamp
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 * years)
            start_timestamp = int(start_date.timestamp() * 1000)
            
            print(f"Start date: {start_date}")
            print(f"End date: {end_date}")
            
            # Fetch data from start timestamp
            all_ohlcv = []
            since = start_timestamp
            batch_count = 0
            
            while batch_count < 3:  # Limit to 3 batches for testing
                batch = exchange.fetch_ohlcv(symbol, timeframe, since, 1000)
                if not batch:
                    break
                
                all_ohlcv.extend(batch)
                since = batch[-1][0] + 1
                batch_count += 1
                
                print(f"Batch {batch_count}: Fetched {len(batch)} candles")
                
                # Check the date range of this batch
                first_date = pd.to_datetime(batch[0][0], unit='ms')
                last_date = pd.to_datetime(batch[-1][0], unit='ms')
                print(f"  Date range: {first_date} to {last_date}")
                
                # Break if batch is smaller than expected
                if len(batch) < 1000:
                    break
            
            if all_ohlcv:
                # Convert to DataFrame to check final range
                df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                print(f"Total candles fetched: {len(df)}")
                print(f"Final date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
                print(f"Duration: {df['timestamp'].max() - df['timestamp'].min()}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_historical_data_fetch() 