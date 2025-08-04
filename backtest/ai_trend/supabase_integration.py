import os
import pandas as pd
import numpy as np
from supabase import create_client, Client
from datetime import datetime, date
import json
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    timeframe: str
    strategy_return: float
    buyhold_return: float
    outperformance: float
    total_trades: int
    win_rate: float
    average_gain: float
    average_loss: float
    max_gain: float
    max_loss: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    profit_factor: float
    best_params: Dict[str, Any]
    date_analyzed: str

@dataclass
class TransactionRecord:
    timeframe: str
    timestamp: str
    action: str  # 'BUY' or 'SELL'
    price: float
    quantity: float
    portfolio_value: float
    signal_strength: float
    k_value: int
    smoothing_factor: int
    window_size: int
    ma_period: int
    date_analyzed: str

@dataclass
class AITrendData:
    timeframe: str
    timestamp: str
    close_price: float
    signal: float
    smoothed_signal: float
    trend_direction: str
    signal_strength: float
    k_value: int
    smoothing_factor: int
    window_size: int
    ma_period: int
    date_analyzed: str
    # Additional fields for UI charting
    open_price: float
    high_price: float
    low_price: float
    volume: float
    ma_signal: float  # Moving average of the signal
    buy_signal: bool
    sell_signal: bool

@dataclass
class EquityCurve:
    timeframe: str
    timestamp: str
    strategy_portfolio_value: float
    buyhold_portfolio_value: float
    strategy_cumulative_return: float
    buyhold_cumulative_return: float
    strategy_drawdown: float
    position_status: str  # 'BUY', 'SELL', 'HOLD'
    btc_price: float
    k_value: int
    smoothing_factor: int
    window_size: int
    ma_period: int
    date_analyzed: str

class SupabaseTradeDataManager:
    def __init__(self, supabase_url: str, supabase_key: str, use_service_role: bool = False):
        """Initialize Supabase client"""
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.use_service_role = use_service_role
        
        # Use service role key if available and requested
        if use_service_role and SUPABASE_SERVICE_ROLE_KEY:
            self.supabase: Client = create_client(supabase_url, SUPABASE_SERVICE_ROLE_KEY)
            logger.info("Using service role key for backend operations")
        else:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("Using anon key for operations")
            
        self.schema = "ai_trend_analysis"
        self.setup_tables()
    
    def setup_tables(self):
        """Create tables if they don't exist"""
        try:
            # Test performance_summary table
            self.supabase.schema(self.schema).table('performance_summary').select('*').limit(1).execute()
            logger.info("Successfully connected to ai_trend_analysis schema")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error connecting to {self.schema} schema: {error_msg}")
            
            if 'permission denied' in error_msg or '403' in error_msg:
                logger.error("❌ Permission denied for ai_trend_analysis schema")
                logger.error("🔧 SOLUTIONS:")
                logger.error("   1. Go to Supabase Dashboard → Settings → API")
                logger.error("   2. Add 'ai_trend_analysis' to 'Exposed schemas' list")
                logger.error("   3. Or run fix_schema_permissions.sql in SQL editor")
                logger.error("   4. Make sure you're using the correct service role key")
            elif 'schema must be one of' in error_msg:
                logger.error("❌ Schema not exposed in API settings")
                logger.error("🔧 Go to Supabase Dashboard → Settings → API → Exposed schemas")
                logger.error("   Add 'ai_trend_analysis' to the list")
            else:
                logger.info("Tables will be created when first used")
        
        try:
            # Test transaction_records table
            self.supabase.schema(self.schema).table('transaction_records').select('*').limit(1).execute()
        except Exception as e:
            if 'permission denied' not in str(e):
                logger.info("Creating transaction_records table...")
            pass
        
        try:
            # Test ai_trend_data table
            self.supabase.schema(self.schema).table('ai_trend_data').select('*').limit(1).execute()
        except Exception as e:
            if 'permission denied' not in str(e):
                logger.info("Creating ai_trend_data table...")
            pass
    
    def clear_todays_data(self, date_analyzed: str) -> bool:
        """Clear ALL data for today's analysis date to prevent duplicates"""
        try:
            tables = ['equity_curve', 'ai_trend_data', 'transaction_records', 'performance_summary']
            
            for table in tables:
                delete_result = self.supabase.schema(self.schema).table(table).delete().eq(
                    'date_analyzed', date_analyzed
                ).execute()
                
                if delete_result.data:
                    logger.info(f"🗑️ Cleared {len(delete_result.data)} existing records from {table} for {date_analyzed}")
            
            logger.info(f"✅ Cleared all data for analysis date: {date_analyzed}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing today's data: {e}")
            return False

    def check_existing_data_coverage(self, timeframe: str, date_analyzed: str) -> Dict[str, Any]:
        """Check what data already exists for a specific timeframe and date"""
        try:
            coverage = {
                'performance_summary_exists': False,
                'ai_trend_data_count': 0,
                'transaction_records_count': 0,
                'equity_curve_count': 0,
                'latest_timestamp': None,
                'earliest_timestamp': None
            }
            
            # Check performance summary
            perf_result = self.supabase.schema(self.schema).table('performance_summary').select('*').eq(
                'timeframe', timeframe
            ).eq('date_analyzed', date_analyzed).execute()
            
            coverage['performance_summary_exists'] = len(perf_result.data) > 0
            
            # Check AI trend data
            ai_trend_result = self.supabase.schema(self.schema).table('ai_trend_data').select(
                'timestamp'
            ).eq('timeframe', timeframe).eq('date_analyzed', date_analyzed).order(
                'timestamp'
            ).execute()
            
            coverage['ai_trend_data_count'] = len(ai_trend_result.data)
            if ai_trend_result.data:
                coverage['earliest_timestamp'] = ai_trend_result.data[0]['timestamp']
                coverage['latest_timestamp'] = ai_trend_result.data[-1]['timestamp']
            
            # Check transaction records
            trans_result = self.supabase.schema(self.schema).table('transaction_records').select(
                'id'
            ).eq('timeframe', timeframe).eq('date_analyzed', date_analyzed).execute()
            
            coverage['transaction_records_count'] = len(trans_result.data)
            
            # Check equity curve
            equity_result = self.supabase.schema(self.schema).table('equity_curve').select(
                'id'
            ).eq('timeframe', timeframe).eq('date_analyzed', date_analyzed).execute()
            
            coverage['equity_curve_count'] = len(equity_result.data)
            
            return coverage
            
        except Exception as e:
            logger.error(f"Error checking existing data coverage: {e}")
            return {
                'performance_summary_exists': False,
                'ai_trend_data_count': 0,
                'transaction_records_count': 0,
                'equity_curve_count': 0,
                'latest_timestamp': None,
                'earliest_timestamp': None
            }
    
    def get_missing_timestamps(self, timeframe: str, date_analyzed: str, all_timestamps: List[str]) -> List[str]:
        """Get list of timestamps that are missing from the database for incremental updates"""
        try:
            # Get existing timestamps for this timeframe and date
            existing_result = self.supabase.schema(self.schema).table('ai_trend_data').select(
                'timestamp'
            ).eq('timeframe', timeframe).eq('date_analyzed', date_analyzed).execute()
            
            existing_timestamps = set(record['timestamp'] for record in existing_result.data)
            missing_timestamps = [ts for ts in all_timestamps if ts not in existing_timestamps]
            
            logger.info(f"Found {len(existing_timestamps)} existing timestamps, {len(missing_timestamps)} missing for {timeframe}")
            return missing_timestamps
            
        except Exception as e:
            logger.error(f"Error getting missing timestamps: {e}")
            # If there's an error, assume all timestamps are missing (safe fallback)
            return all_timestamps
    
    def has_complete_data_for_timeframe(self, timeframe: str, date_analyzed: str, expected_record_count: int) -> bool:
        """Check if we have complete data for a timeframe (within 5% tolerance)"""
        try:
            coverage = self.check_existing_data_coverage(timeframe, date_analyzed)
            
            # Consider data complete if we have:
            # 1. Performance summary exists
            # 2. AI trend data count is within 95% of expected (allows for small variations)
            # 3. Has some equity curve data (since it matches AI trend data count)
            
            min_expected = int(expected_record_count * 0.95)  # 95% threshold
            
            is_complete = (
                coverage['performance_summary_exists'] and
                coverage['ai_trend_data_count'] >= min_expected and
                coverage['equity_curve_count'] >= min_expected
            )
            
            if is_complete:
                logger.info(f"✅ {timeframe} data appears complete: {coverage['ai_trend_data_count']}/{expected_record_count} records")
            else:
                logger.info(f"📊 {timeframe} data incomplete: {coverage['ai_trend_data_count']}/{expected_record_count} records, performance_summary: {coverage['performance_summary_exists']}")
            
            return is_complete
            
        except Exception as e:
            logger.error(f"Error checking data completeness: {e}")
            return False
    
    def store_incremental_data(self, timeframe: str, date_analyzed: str, 
                              ai_trend_data: List[AITrendData] = None,
                              transaction_records: List[TransactionRecord] = None,
                              equity_curve_data: List[EquityCurve] = None,
                              performance_metrics: PerformanceMetrics = None) -> bool:
        """Store data incrementally, only adding what's missing"""
        try:
            success = True
            
            # Store performance summary (always update if provided)
            if performance_metrics:
                success &= self.store_performance_summary(performance_metrics)
            
            # Store AI trend data incrementally
            if ai_trend_data:
                # Check which timestamps are missing
                all_timestamps = [data.timestamp for data in ai_trend_data]
                missing_timestamps = self.get_missing_timestamps(timeframe, date_analyzed, all_timestamps)
                
                if missing_timestamps:
                    missing_data = [data for data in ai_trend_data if data.timestamp in missing_timestamps]
                    logger.info(f"📊 Adding {len(missing_data)} missing AI trend records for {timeframe}")
                    success &= self.store_ai_trend_data(missing_data)
                else:
                    logger.info(f"✅ All AI trend data already exists for {timeframe}")
            
            # Store transaction records (always replace for simplicity since they're typically few)
            if transaction_records:
                # Clear existing transaction records for this timeframe/date and re-insert
                self.supabase.schema(self.schema).table('transaction_records').delete().eq(
                    'timeframe', timeframe
                ).eq('date_analyzed', date_analyzed).execute()
                success &= self.store_transaction_records(transaction_records)
            
            # Store equity curve data incrementally (similar to AI trend data)
            if equity_curve_data:
                all_timestamps = [data.timestamp for data in equity_curve_data]
                # Use same missing timestamps as AI trend data since they should match
                missing_timestamps = self.get_missing_timestamps(timeframe, date_analyzed, all_timestamps)
                
                if missing_timestamps:
                    missing_equity_data = [data for data in equity_curve_data if data.timestamp in missing_timestamps]
                    logger.info(f"📈 Adding {len(missing_equity_data)} missing equity curve records for {timeframe}")
                    success &= self.store_equity_curve(missing_equity_data)
                else:
                    logger.info(f"✅ All equity curve data already exists for {timeframe}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error storing incremental data: {e}")
            return False
    
    def store_performance_summary(self, metrics: PerformanceMetrics) -> bool:
        """Store performance summary (data clearing done at start of daily update)"""
        try:
            data = {
                'timeframe': metrics.timeframe,
                'strategy_return': metrics.strategy_return,
                'buyhold_return': metrics.buyhold_return,
                'outperformance': metrics.outperformance,
                'total_trades': metrics.total_trades,
                'win_rate': metrics.win_rate,
                'average_gain': metrics.average_gain,
                'average_loss': metrics.average_loss,
                'max_gain': metrics.max_gain,
                'max_loss': metrics.max_loss,
                'max_drawdown': metrics.max_drawdown,
                'sharpe_ratio': metrics.sharpe_ratio,
                'sortino_ratio': metrics.sortino_ratio,
                'profit_factor': metrics.profit_factor,
                'best_params': json.dumps(metrics.best_params),
                'date_analyzed': metrics.date_analyzed,
                'updated_at': datetime.now().isoformat()
            }
            
            # Insert the new record
            result = self.supabase.schema(self.schema).table('performance_summary').insert(data).execute()
            logger.info(f"✅ Stored performance summary for {metrics.timeframe}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing performance summary: {e}")
            return False
    
    def store_transaction_records(self, transactions: List[TransactionRecord]) -> bool:
        """Store transaction records (data clearing done at start of daily update)"""
        try:
            if not transactions:
                return True
            
            # Prepare all records for insertion
            new_records = []
            for transaction in transactions:
                data = {
                    'timeframe': transaction.timeframe,
                    'timestamp': transaction.timestamp,
                    'action': transaction.action,
                    'price': transaction.price,
                    'quantity': transaction.quantity,
                    'portfolio_value': transaction.portfolio_value,
                    'signal_strength': transaction.signal_strength,
                    'k_value': transaction.k_value,
                    'smoothing_factor': transaction.smoothing_factor,
                    'window_size': transaction.window_size,
                    'ma_period': transaction.ma_period,
                    'date_analyzed': transaction.date_analyzed,
                    'updated_at': datetime.now().isoformat()
                }
                new_records.append(data)
            
            # Insert all records
            if new_records:
                self.supabase.schema(self.schema).table('transaction_records').insert(new_records).execute()
                logger.info(f"✅ Stored {len(new_records)} transaction records")
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing transaction records: {e}")
            return False
    
    def store_ai_trend_data(self, trend_data: List[AITrendData]) -> bool:
        """Store AI trend navigator data (data clearing done at start of daily update)"""
        try:
            if not trend_data:
                return True
            
            # Prepare all records for insertion
            new_records = []
            for data_point in trend_data:
                # Handle potential numeric overflow by clamping large values
                def safe_numeric(value, max_val=9999.0):
                    if pd.isna(value) or np.isnan(value):
                        return 0.0
                    # Don't clamp AI signal values - they should be in Bitcoin price range
                    return float(value)
                
                # Handle volume separately with higher limit
                volume_val = data_point.volume
                if pd.isna(volume_val) or np.isnan(volume_val):
                    volume_val = 0.0
                else:
                    volume_val = min(max(float(volume_val), 0.0), 99999999.0)  # 99M limit
                
                data = {
                    'timeframe': data_point.timeframe,
                    'timestamp': data_point.timestamp,
                    'close_price': safe_numeric(data_point.close_price, 999999.0),
                    'open_price': safe_numeric(data_point.open_price, 999999.0),
                    'high_price': safe_numeric(data_point.high_price, 999999.0),
                    'low_price': safe_numeric(data_point.low_price, 999999.0),
                    'volume': volume_val,
                    'signal': safe_numeric(data_point.signal, 999999.0),
                    'smoothed_signal': safe_numeric(data_point.smoothed_signal, 999999.0),
                    'ma_signal': safe_numeric(data_point.ma_signal, 999999.0),
                    'trend_direction': data_point.trend_direction,
                    'signal_strength': safe_numeric(data_point.signal_strength, 10.0),
                    'buy_signal': 1 if data_point.buy_signal else 0,
                    'sell_signal': 1 if data_point.sell_signal else 0,
                    'k_value': data_point.k_value,
                    'smoothing_factor': data_point.smoothing_factor,
                    'window_size': data_point.window_size,
                    'ma_period': data_point.ma_period,
                    'date_analyzed': data_point.date_analyzed,
                    'updated_at': datetime.now().isoformat()
                }
                new_records.append(data)
            
            # Insert all records
            if new_records:
                self.supabase.schema(self.schema).table('ai_trend_data').insert(new_records).execute()
                logger.info(f"✅ Stored {len(new_records)} AI trend data points")
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing AI trend data: {e}")
            return False
    
    def store_equity_curve(self, equity_data: List[EquityCurve]) -> bool:
        """Store equity curve data (data clearing done at start of daily update)"""
        try:
            if not equity_data:
                return True
            
            # Prepare all records for insertion
            new_records = []
            for equity_point in equity_data:
                data = {
                    'timeframe': equity_point.timeframe,
                    'timestamp': equity_point.timestamp,
                    'strategy_portfolio_value': equity_point.strategy_portfolio_value,
                    'buyhold_portfolio_value': equity_point.buyhold_portfolio_value,
                    'strategy_cumulative_return': equity_point.strategy_cumulative_return,
                    'buyhold_cumulative_return': equity_point.buyhold_cumulative_return,
                    'strategy_drawdown': equity_point.strategy_drawdown,
                    'position_status': equity_point.position_status,
                    'btc_price': equity_point.btc_price,
                    'k_value': equity_point.k_value,
                    'smoothing_factor': equity_point.smoothing_factor,
                    'window_size': equity_point.window_size,
                    'ma_period': equity_point.ma_period,
                    'date_analyzed': equity_point.date_analyzed,
                    'updated_at': datetime.now().isoformat()
                }
                new_records.append(data)
            
            # Insert all records
            if new_records:
                self.supabase.schema(self.schema).table('equity_curve').insert(new_records).execute()
                logger.info(f"✅ Stored {len(new_records)} equity curve data points")
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing equity curve data: {e}")
            return False
    
    def get_latest_performance_summary(self) -> List[Dict]:
        """Get the latest performance summary for all timeframes"""
        try:
            result = self.supabase.schema(self.schema).table('performance_summary').select('*').order(
                'date_analyzed', desc=True
            ).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching performance summary: {e}")
            return []
    
    def get_transaction_history(self, timeframe: str = None, limit: int = 100) -> List[Dict]:
        """Get transaction history, optionally filtered by timeframe"""
        try:
            query = self.supabase.schema(self.schema).table('transaction_records').select('*')
            if timeframe:
                query = query.eq('timeframe', timeframe)
            
            result = query.order('timestamp', desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching transaction history: {e}")
            return []
    
    def get_ai_trend_signals(self, timeframe: str = None, limit: int = 100) -> List[Dict]:
        """Get AI trend signals, optionally filtered by timeframe"""
        try:
            query = self.supabase.schema(self.schema).table('ai_trend_data').select('*')
            if timeframe:
                query = query.eq('timeframe', timeframe)
            
            result = query.order('timestamp', desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching AI trend signals: {e}")
            return []
    
    def get_chart_data(self, timeframe: str, days: int = 30) -> List[Dict]:
        """Get AI trend data optimized for UI charting"""
        try:
            cutoff_date = (datetime.now() - pd.Timedelta(days=days)).isoformat()
            
            result = self.supabase.schema(self.schema).table('ai_trend_data').select(
                'timestamp, close_price, open_price, high_price, low_price, volume, '
                'signal, smoothed_signal, ma_signal, trend_direction, signal_strength, '
                'buy_signal, sell_signal'
            ).eq('timeframe', timeframe).gte('timestamp', cutoff_date).order(
                'timestamp', desc=False
            ).execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Error fetching chart data: {e}")
            return []
    
    def get_equity_curve_data(self, timeframe: str = None, days: int = 30) -> List[Dict]:
        """Get equity curve data for portfolio comparison visualization"""
        try:
            cutoff_date = (datetime.now() - pd.Timedelta(days=days)).isoformat()
            
            query = self.supabase.schema(self.schema).table('equity_curve').select(
                'timestamp, timeframe, strategy_portfolio_value, buyhold_portfolio_value, '
                'strategy_cumulative_return, buyhold_cumulative_return, strategy_drawdown, '
                'position_status, btc_price, date_analyzed'
            ).gte('timestamp', cutoff_date)
            
            if timeframe:
                query = query.eq('timeframe', timeframe)
            
            result = query.order('timestamp', desc=False).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching equity curve data: {e}")
            return []
    
    def get_latest_equity_curves(self) -> List[Dict]:
        """Get the latest equity curves for all timeframes using the view"""
        try:
            result = self.supabase.schema(self.schema).table('latest_equity_curves').select('*').execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching latest equity curves: {e}")
            return []
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data beyond specified days"""
        try:
            cutoff_date = (datetime.now() - pd.Timedelta(days=days_to_keep)).isoformat()
            
            # Clean up old transaction records
            self.supabase.schema(self.schema).table('transaction_records').delete().lt(
                'date_analyzed', cutoff_date
            ).execute()
            
            # Clean up old AI trend data
            self.supabase.schema(self.schema).table('ai_trend_data').delete().lt(
                'date_analyzed', cutoff_date
            ).execute()
            
            logger.info(f"Cleaned up data older than {days_to_keep} days")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return False

# Environment variables for Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
FMP_API_KEY = os.getenv('FMP_API_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    logger.warning("Supabase credentials not found in environment variables")
    logger.warning("Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables")

if not FMP_API_KEY:
    logger.warning("FMP API key not found in environment variables")
    logger.warning("Please set FMP_API_KEY environment variable") 