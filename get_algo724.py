import clickhouse_connect
import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime
import pytz
import sys
import uuid

# Load environment variables
load_dotenv()

# Check required environment variables
required_vars = ['SUPABASE_USER_EMAIL', 'SUPABASE_USER_PASSWORD']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print("Error: Missing required environment variables:")
    for var in missing_vars:
        print(f"- {var}")
    print("\nPlease add these to your .env file.")
    sys.exit(1)

# Initialize Clickhouse client
client = clickhouse_connect.get_client(
    host=os.getenv('CLICKHOUSE_HOST'),
    port=int(os.getenv('CLICKHOUSE_PORT')),
    username=os.getenv('CLICKHOUSE_USERNAME'),
    password=os.getenv('CLICKHOUSE_PASSWORD'),
    secure=True
)

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_ANON_KEY')
)

# Authenticate with Supabase
try:
    auth_response = supabase.auth.sign_in_with_password({
        'email': os.getenv('SUPABASE_USER_EMAIL'),
        'password': os.getenv('SUPABASE_USER_PASSWORD')
    })
    user_id = auth_response.user.id
    print(f"Successfully authenticated with Supabase as {os.getenv('SUPABASE_USER_EMAIL')}")
except Exception as e:
    print(f"Error authenticating with Supabase: {e}")
    print("\nPlease check your credentials in .env file or run reset_password.py to reset your password.")
    sys.exit(1)

def clear_supabase_table():
    """Delete all records from the whale_signals table"""
    try:
        # Only delete records owned by the current user
        supabase.table('whale_signals').delete().eq('user_id', user_id).execute()
        print("Successfully cleared all records from Supabase")
    except Exception as e:
        print(f"Error clearing Supabase table: {e}")

def safe_float(value, default=0.0):
    """Safely convert value to float, returning default if value is None"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Safely convert value to int, returning default if value is None"""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def generate_unique_id(row_id, symbol, timeframe, timestamp):
    """Generate a unique ID for each record"""
    unique_str = f"{row_id}-{symbol}-{timeframe}-{timestamp}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_str))

# Get data from Clickhouse
print("\nFetching data from Clickhouse...")
# Get the data with explicit column names
data_query = """
SELECT 
    id,
    prefix,
    symbol,
    timeframe,
    timestamp,
    open,
    high,
    low,
    close,
    observe_event,
    trade_event,
    LT_attr,
    ST_attr,
    delete_pivot,
    pivot_offset,
    pivot_attr,
    pivot_price,
    invalid_count,
    peak_price,
    weak_price,
    grow_price,
    valley_price,
    macd,
    rsi,
    label_attr,
    label_price,
    label_active,
    pivot_active,
    updated_at
FROM tv_whale_snapshot_latest 
WHERE label_price != 0 
    AND timeframe != '30m'
    AND toDate(timestamp) = yesterday()
ORDER BY timestamp DESC
"""
data_result = client.query(data_query)
rows = data_result.result_rows

# Convert to DataFrame for inspection
df = pd.DataFrame(rows, columns=[
    'id', 'prefix', 'symbol', 'timeframe', 'timestamp',
    'open', 'high', 'low', 'close', 'observe_event',
    'trade_event', 'lt_attr', 'st_attr', 'delete_pivot',
    'pivot_offset', 'pivot_attr', 'pivot_price', 'invalid_count',
    'peak_price', 'weak_price', 'grow_price', 'valley_price',
    'macd', 'rsi', 'label_attr', 'label_price', 'label_active',
    'pivot_active', 'updated_at'
])

print(f"\nFound {len(df)} records with non-zero label_price from yesterday")

# Show data summary
print("\nData Summary:")
print(f"Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
print("\nUnique symbols found:")
print(sorted(df['symbol'].unique()))
print("\nUnique timeframes found:")
print(sorted(df['timeframe'].unique()))

# Show sample of the data
print("\nSample of records:")
sample_df = df[['symbol', 'timeframe', 'timestamp', 'label_price']].head()
print(sample_df)

def convert_to_utc(timestamp_str):
    """Convert timestamp string to UTC timezone-aware datetime"""
    if not timestamp_str:
        return None
    try:
        # Parse the timestamp string
        dt = pd.to_datetime(timestamp_str)
        # If timestamp is naive (no timezone), assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        # If timestamp has timezone, convert to UTC
        else:
            dt = dt.astimezone(pytz.UTC)
        return dt
    except:
        return None

# Function to insert data to Supabase
def insert_to_supabase(rows):
    # Convert rows to list of dictionaries
    data_to_insert = []
    
    for row in rows:
        # Generate a unique ID for this record
        unique_id = generate_unique_id(row[0], row[2], row[3], row[4].isoformat() if row[4] else '')
        
        # Ensure timestamp is UTC
        timestamp = row[4].astimezone(pytz.UTC) if row[4] else None
        updated_at = row[28].astimezone(pytz.UTC) if row[28] else None
        
        data = {
            'id': unique_id,  # Use the generated unique ID
            'original_id': str(row[0]),  # Store the original ID in a new field
            'prefix': row[1],
            'symbol': row[2],
            'timeframe': row[3],
            'timestamp': timestamp.isoformat() if timestamp else None,
            'open': safe_float(row[5]),
            'high': safe_float(row[6]),
            'low': safe_float(row[7]),
            'close': safe_float(row[8]),
            'observe_event': safe_int(row[9]),
            'trade_event': safe_int(row[10]),
            'lt_attr': safe_int(row[11]),
            'st_attr': safe_int(row[12]),
            'delete_pivot': safe_int(row[13]),
            'pivot_offset': safe_int(row[14]),
            'pivot_attr': safe_int(row[15]),
            'pivot_price': safe_float(row[16]),
            'invalid_count': safe_int(row[17]),
            'peak_price': safe_float(row[18]),
            'weak_price': safe_float(row[19]),
            'grow_price': safe_float(row[20]),
            'valley_price': safe_float(row[21]),
            'macd': safe_float(row[22]),
            'rsi': safe_float(row[23]),
            'label_attr': safe_int(row[24]),
            'label_price': safe_float(row[25]),
            'label_active': safe_int(row[26]),
            'pivot_active': safe_int(row[27]),
            'updated_at': updated_at.isoformat() if updated_at else None,
            'user_id': user_id  # Set the authenticated user's ID
        }
        data_to_insert.append(data)
    
    if not data_to_insert:
        print("No data to insert")
        return None
    
    try:
        # Insert records in smaller batches to avoid timeouts
        batch_size = 50
        total_batches = (len(data_to_insert) - 1) // batch_size + 1
        
        print(f"\nInserting {len(data_to_insert)} records in {total_batches} batches...")
        
        for i in range(0, len(data_to_insert), batch_size):
            batch = data_to_insert[i:i + batch_size]
            result = supabase.table('whale_signals').insert(batch).execute()
            print(f"Successfully inserted batch {i//batch_size + 1} of {total_batches}")
        return True
    except Exception as e:
        print(f"Error inserting records: {e}")
        return None

# Clear existing data and insert new records
print("\nClearing existing data...")
clear_supabase_table()
print("\nInserting new records...")
insert_to_supabase(rows)

