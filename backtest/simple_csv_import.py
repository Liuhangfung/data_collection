#!/usr/bin/env python3
"""
Simple CSV to Supabase Importer
===============================
Uses Supabase client library - much simpler than direct PostgreSQL connection
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
import re
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://fogyzjunwiqxdqomyczz.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY', 'your_service_key_here')

def extract_timeframe_from_filename(filename: str) -> str:
    """Extract timeframe from filename (e.g., '4h' from 'complete_max_analysis_4h.csv')"""
    pattern = r'_(\d*[hdwM])\.csv$'
    match = re.search(pattern, filename)
    if match:
        return match.group(1)
    return '1d'

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and prepare dataframe for database insertion"""
    # Replace NaN values with None
    df = df.replace({np.nan: None})
    
    # Convert timestamp columns to ISO format strings
    timestamp_columns = ['entry_time', 'exit_time', 'timestamp']
    for col in timestamp_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Convert integer columns (handle float values like "1.0")
    integer_columns = ['duration_to_extreme', 'holding_period_duration', 'waiting_period_duration']
    for col in integer_columns:
        if col in df.columns:
            # Convert to numeric first, then to integer, handling NaN/None
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(0).astype(int)
            df[col] = df[col].replace(0, None)  # Convert back to None for NULL values
    
    return df

def import_signal_analysis(supabase: Client, csv_files: list):
    """Import signal analysis files (BUY and SELL signals)"""
    logger.info("📊 Importing signal analysis files...")
    
    # Clear existing data
    supabase.schema('macd_analysis').table('signal_analysis').delete().neq('id', 0).execute()
    
    total_imported = 0
    
    for file in csv_files:
        if not file.startswith('complete_max_analysis_'):
            continue
            
        logger.info(f"Processing {file}...")
        timeframe = extract_timeframe_from_filename(file)
        
        # Read and clean data
        df = pd.read_csv(file)
        df = clean_dataframe(df)
        df['timeframe'] = timeframe
        
        # Convert to list of dictionaries
        records = df.to_dict('records')
        
        # Insert in batches
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            supabase.schema('macd_analysis').table('signal_analysis').insert(batch).execute()
        
        total_imported += len(df)
        logger.info(f"✅ Imported {len(df)} records from {file}")
    
    logger.info(f"✅ Signal analysis import finished. Total records: {total_imported}")

def import_macd_transactions(supabase: Client, csv_files: list):
    """Import MACD transactions files"""
    logger.info("💰 Importing MACD transactions files...")
    
    # Clear existing data
    supabase.schema('macd_analysis').table('macd_transactions').delete().neq('id', 0).execute()
    
    total_imported = 0
    
    for file in csv_files:
        if not file.startswith('macd_transactions_'):
            continue
            
        logger.info(f"Processing {file}...")
        timeframe = extract_timeframe_from_filename(file)
        
        # Read and clean data
        df = pd.read_csv(file)
        df = clean_dataframe(df)
        df['timeframe'] = timeframe
        
        # Convert to list of dictionaries
        records = df.to_dict('records')
        
        # Insert in batches
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            supabase.schema('macd_analysis').table('macd_transactions').insert(batch).execute()
        
        total_imported += len(df)
        logger.info(f"✅ Imported {len(df)} records from {file}")
    
    logger.info(f"✅ MACD transactions import finished. Total records: {total_imported}")

def import_timeframe_comparison(supabase: Client, csv_files: list):
    """Import timeframe comparison file"""
    logger.info("📈 Importing timeframe comparison file...")
    
    # Clear existing data
    supabase.schema('macd_analysis').table('macd_timeframe_comparison').delete().neq('id', 0).execute()
    
    for file in csv_files:
        if 'timeframe_comparison' not in file:
            continue
            
        logger.info(f"Processing {file}...")
        
        # Read and clean data
        df = pd.read_csv(file)
        df = clean_dataframe(df)
        
        # Convert to list of dictionaries
        records = df.to_dict('records')
        
        # Insert data
        supabase.schema('macd_analysis').table('macd_timeframe_comparison').insert(records).execute()
        
        logger.info(f"✅ Imported {len(df)} records from {file}")

def main():
    """Main function"""
    print("🚀 Simple CSV to Supabase Importer")
    print("=" * 50)
    
    # Check if service key is configured
    if SUPABASE_KEY == 'your_service_key_here':
        print("❌ Please set your Supabase service key:")
        print("1. Create a .env file in this directory")
        print("2. Add the following lines:")
        print("   SUPABASE_URL=https://fogyzjunwiqxdqomyczz.supabase.co")
        print("   SUPABASE_SERVICE_KEY=your_actual_service_key")
        print("3. Get your service key from Supabase dashboard > Settings > API")
        return
    
    # Create Supabase client
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Connected to Supabase successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Supabase: {e}")
        return
    
    # Get CSV files
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    if not csv_files:
        logger.warning("⚠️ No CSV files found in the directory")
        return
    
    logger.info(f"Found {len(csv_files)} CSV files: {csv_files}")
    
    try:
        # Import each type of data
        import_signal_analysis(supabase, csv_files)
        import_macd_transactions(supabase, csv_files)
        import_timeframe_comparison(supabase, csv_files)
        
        logger.info("🎉 All CSV files imported successfully!")
        
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")

if __name__ == "__main__":
    main() 