#!/usr/bin/env python3
"""
Daily Supabase Update Script
- Uses optimized parameters from best_params_comparison.py
- Fetches data, runs AI Trend Navigator analysis
- Stores results in Supabase database
"""

import pandas as pd
import numpy as np
import requests
import ccxt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

# Import our Supabase integration
from supabase_integration import SupabaseTradeDataManager, PerformanceMetrics, TransactionRecord, AITrendData, EquityCurve

class OptimizedAITrendNavigator:
    """Optimized AI Trend Navigator - Exact copy from best_params_comparison.py"""
    
    def __init__(self, numberOfClosestValues=3, smoothingPeriod=50, windowSize=30, maLen=5):
        self.numberOfClosestValues = numberOfClosestValues
        self.smoothingPeriod = smoothingPeriod
        self.windowSize = max(numberOfClosestValues, windowSize)
        self.maLen = maLen
        
    def _calculate_sma_vectorized(self, data, period):
        """Vectorized SMA calculation"""
        if len(data) < period:
            return np.zeros(len(data))
        return pd.Series(data).rolling(window=period, min_periods=1).mean().values
    
    def _calculate_ema_vectorized(self, data, period):
        """Vectorized EMA calculation"""
        return pd.Series(data).ewm(span=period, adjust=False).mean().values
    
    def _optimized_mean_of_k_closest(self, value_series, target_value, current_idx):
        """Optimized KNN function"""
        if current_idx < self.windowSize:
            return np.nan
        
        start_idx = max(0, current_idx - self.windowSize)
        window_values = value_series[start_idx:current_idx]
        
        if len(window_values) == 0:
            return np.nan
        
        distances = np.abs(window_values - target_value)
        k = min(self.numberOfClosestValues, len(distances))
        if k == 0:
            return np.nan
        
        indices = np.argpartition(distances, k-1)[:k]
        return np.mean(window_values[indices])
    
    def calculate_trend_signals(self, df):
        """Calculate trend signals"""
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        # Calculate value_in (HL2 with MA smoothing)
        hl2 = (high + low) / 2.0
        value_in = self._calculate_sma_vectorized(hl2, self.maLen)
        
        # Calculate target_in (EMA of close)
        target_in = self._calculate_ema_vectorized(close, self.maLen)
        
        # Calculate KNN MA
        data_len = len(df)
        knn_ma = np.zeros(data_len)
        
        for i in range(data_len):
            if i >= self.windowSize:
                knn_ma[i] = self._optimized_mean_of_k_closest(value_in, target_in[i], i)
        
        # Apply WMA smoothing
        knn_ma_smoothed = np.zeros(data_len)
        weights = np.arange(1, 6)
        weights = weights / weights.sum()
        
        for i in range(4, data_len):
            knn_ma_smoothed[i] = np.sum(knn_ma[i-4:i+1] * weights)
        
        # Calculate trend direction
        trend_direction = np.full(data_len, 'neutral', dtype=object)
        
        mask_up = (knn_ma_smoothed[1:] > knn_ma_smoothed[:-1]) & (knn_ma_smoothed[1:] > 0)
        mask_down = (knn_ma_smoothed[1:] < knn_ma_smoothed[:-1]) & (knn_ma_smoothed[1:] > 0)
        
        trend_direction[1:][mask_up] = 'up'
        trend_direction[1:][mask_down] = 'down'
        
        # Generate signals
        signals = np.full(data_len, 'hold', dtype=object)
        
        buy_mask = (trend_direction[:-1] == 'down') & (trend_direction[1:] == 'up')
        signals[1:][buy_mask] = 'buy'
        
        sell_mask = (trend_direction[:-1] == 'up') & (trend_direction[1:] == 'down')
        signals[1:][sell_mask] = 'sell'
        
        result = pd.DataFrame({
            'knnMA': knn_ma,
            'knnMA_smoothed': knn_ma_smoothed,
            'MA_knnMA': self._calculate_sma_vectorized(knn_ma, self.smoothingPeriod),
            'trend_direction': trend_direction,
            'price': close,
            'signal': signals
        }, index=df.index)
        
        return result

class HybridDataFetcher:
    """Hybrid data fetcher: CCXT for 4H/8H, FMP for daily/weekly/monthly"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        
        # Initialize Binance exchange for 4H and 8H data
        self.exchange = ccxt.binance({
            'rateLimit': 1200,
            'enableRateLimit': True,
        })
        
        # Best parameters from optimization (updated based on 4H/8H parameter optimization)
        self.best_params = {
            '4H': {'K': 23, 'smoothing': 10, 'window': 30, 'maLen': 5},   # Optimized: 865.79% return, 7.86% annual
            '8H': {'K': 31, 'smoothing': 10, 'window': 70, 'maLen': 10},  # Optimized: 1887.57% return, 22.07% annual
            '1D': {'K': 19, 'smoothing': 30, 'window': 70, 'maLen': 12},
            '1W': {'K': 25, 'smoothing': 10, 'window': 50, 'maLen': 8},
            '1M': {'K': 19, 'smoothing': 6, 'window': 40, 'maLen': 12}
        }
    
    def fetch_data_for_timeframe(self, timeframe):
        """Fetch data - use FMP for all timeframes, resample as needed"""
        return self._fetch_fmp_data(timeframe)
    

    
    def _fetch_fmp_data(self, timeframe):
        """Fetch data using hybrid approach: CCXT for 4H/8H, FMP for others"""
        print(f"📊 Fetching {timeframe} data...")
        
        # For 4H and 8H, use CCXT
        if timeframe in ['4H', '8H']:
            return self._fetch_ccxt_data(timeframe)
        else:
            return self._fetch_daily_data(timeframe)
    
    def _fetch_ccxt_data(self, timeframe):
        """Fetch 4H or 8H data using CCXT with chunking for 5 years"""
        print(f"   📡 Fetching {timeframe} data from Binance (CCXT)...")
        
        symbol = 'BTC/USDT'
        end_time = datetime.now()
        start_time = end_time - timedelta(days=365 * 5)  # 5 years
        
        print(f"   📅 Target range: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}")
        
        try:
            all_ohlcv = []
            target_time = int(start_time.timestamp() * 1000)
            
            chunk_count = 0
            total_fetched = 0
            
            # Start from the beginning and fetch forward
            current_since = target_time
            
            while current_since < int(end_time.timestamp() * 1000):
                try:
                    # Fetch data chunk starting from current_since
                    print(f"   🔄 Fetching chunk {chunk_count + 1} from {datetime.fromtimestamp(current_since/1000).strftime('%Y-%m-%d %H:%M')}...")
                    
                    ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe.lower(), current_since, 1000)
                    
                    if not ohlcv or len(ohlcv) == 0:
                        print(f"   ⚠️  No more data available")
                        break
                    
                    # Add to our collection
                    all_ohlcv.extend(ohlcv)
                    total_fetched += len(ohlcv)
                    chunk_count += 1
                    
                    print(f"   📦 Chunk {chunk_count}: {len(ohlcv)} records (Total: {total_fetched})")
                    
                    # Update current_since to the timestamp after the last candle
                    last_timestamp = max(candle[0] for candle in ohlcv)
                    
                    # Move to next chunk - add one period to avoid overlap
                    period_ms = 4 * 60 * 60 * 1000 if timeframe == '4H' else 8 * 60 * 60 * 1000
                    current_since = last_timestamp + period_ms
                    
                    # Rate limiting - small delay between requests
                    import time
                    time.sleep(0.1)
                    
                    # Safety check to avoid infinite loops
                    if chunk_count > 100:  # Reasonable limit
                        print(f"   ⚠️  Reached maximum chunk limit, stopping")
                        break
                    
                except Exception as chunk_error:
                    print(f"   ❌ Error fetching chunk {chunk_count + 1}: {chunk_error}")
                    break
            
            if not all_ohlcv:
                print(f"❌ No data received for {timeframe}")
                return None
            
            print(f"   📦 Total received: {len(all_ohlcv)} {timeframe} records from Binance")
            
            # Remove duplicates and sort by timestamp
            unique_ohlcv = []
            seen_timestamps = set()
            for candle in all_ohlcv:
                if candle[0] not in seen_timestamps:
                    unique_ohlcv.append(candle)
                    seen_timestamps.add(candle[0])
            
            # Sort by timestamp
            unique_ohlcv.sort(key=lambda x: x[0])
            
            # Filter to only include data within our target range
            end_timestamp = int(end_time.timestamp() * 1000)
            filtered_ohlcv = [candle for candle in unique_ohlcv if target_time <= candle[0] <= end_timestamp]
            
            print(f"   🔍 After deduplication and filtering: {len(filtered_ohlcv)} records")
            
            # Convert to DataFrame
            df = pd.DataFrame(filtered_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Set timestamp as index
            df.set_index('timestamp', inplace=True)
            
            # Show data range
            if len(df) > 0:
                print(f"   ⏰ Data range: {df.index[0].strftime('%Y-%m-%d %H:%M')} to {df.index[-1].strftime('%Y-%m-%d %H:%M')}")
                
                # Calculate years of data
                total_days = (df.index[-1] - df.index[0]).days
                years = total_days / 365.25
                print(f"📅 {timeframe}: {years:.1f} years of data ({len(df)} records)")
                
                print(f"✅ Fetched {len(df)} {timeframe} candles from CCXT")
                return df
            else:
                print(f"❌ No data after filtering for {timeframe}")
                return None
            
        except Exception as e:
            print(f"❌ Error fetching {timeframe} data from CCXT: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _fetch_daily_data(self, timeframe):
        """Fetch daily data for 1D, 1W, 1M timeframes"""
        symbol = "BTCUSD"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * 5)  # 5 years
        
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
        params = {
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            df = pd.DataFrame(data['historical'])
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            df = df.rename(columns={
                'date': 'timestamp',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            })
            
            df.set_index('timestamp', inplace=True)
            
            # Calculate years of data
            total_days = (df.index[-1] - df.index[0]).days
            years = total_days / 365.25
            print(f"📅 {timeframe}: {years:.1f} years of data ({len(df)} records)")
            
            print(f"✅ Fetched {len(df)} {timeframe} candles from FMP")
            return df
            
        except Exception as e:
            print(f"❌ Error fetching {timeframe} data from FMP: {e}")
            return None
    

    
    def calculate_strategy_performance(self, signals):
        """Calculate strategy performance with detailed metrics and equity curve data"""
        signal_array = signals['signal'].values
        price_array = signals['price'].values
        timestamps = signals.index
        
        # Portfolio simulation
        portfolio_value = []
        buyhold_value = []
        position_status = []
        position = False
        btc_holdings = 0
        cash = 10000
        initial_capital = 10000
        
        # Buy and hold simulation (buy at first price, hold throughout)
        initial_price = price_array[0]
        buyhold_btc = initial_capital / initial_price
        
        trades = []
        entry_price = None
        
        for i in range(len(signals)):
            current_signal = signal_array[i]
            current_price = price_array[i]
            
            if current_signal == 'buy' and not position:
                btc_holdings = cash / current_price
                cash = 0
                position = True
                entry_price = current_price
                position_status.append('BUY')
                
            elif current_signal == 'sell' and position:
                cash = btc_holdings * current_price
                btc_holdings = 0
                position = False
                position_status.append('SELL')
                
                if entry_price:
                    trade_return = (current_price - entry_price) / entry_price * 100
                    trades.append({
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'return': trade_return,
                        'profitable': trade_return > 0
                    })
            else:
                position_status.append('HOLD')
            
            # Current strategy portfolio value
            if position:
                current_value = btc_holdings * current_price
            else:
                current_value = cash
            
            # Current buy and hold value
            current_buyhold_value = buyhold_btc * current_price
            
            portfolio_value.append(current_value)
            buyhold_value.append(current_buyhold_value)
        
        # Calculate metrics
        total_return = ((portfolio_value[-1] / portfolio_value[0]) - 1) * 100
        
        # Calculate annual return
        days = len(signals)
        years = days / 365.25
        annual_return = ((portfolio_value[-1] / portfolio_value[0]) ** (1/years) - 1) * 100
        
        # Win rate
        profitable_trades = len([t for t in trades if t['profitable']])
        win_rate = (profitable_trades / len(trades) * 100) if trades else 0
        
        # Max drawdown calculation
        portfolio_series = pd.Series(portfolio_value)
        running_max = portfolio_series.expanding().max()
        drawdown = (portfolio_series - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        
        # Average and max gains/losses
        returns = [t['return'] for t in trades]
        avg_gain = np.mean([r for r in returns if r > 0]) if any(r > 0 for r in returns) else 0
        avg_loss = np.mean([r for r in returns if r < 0]) if any(r < 0 for r in returns) else 0
        max_gain = max(returns) if returns else 0
        max_loss = min(returns) if returns else 0
        
        # Calculate buy & hold performance
        buyhold_return = ((buyhold_value[-1] / buyhold_value[0]) - 1) * 100
        
        # Create equity curve data
        equity_curve_data = []
        for i in range(len(signals)):
            # Calculate cumulative returns
            strategy_cum_return = ((portfolio_value[i] / portfolio_value[0]) - 1) * 100
            buyhold_cum_return = ((buyhold_value[i] / buyhold_value[0]) - 1) * 100
            
            # Calculate drawdown at this point
            if i == 0:
                strategy_drawdown = 0.0
            else:
                running_max_val = max(portfolio_value[:i+1])
                strategy_drawdown = ((portfolio_value[i] - running_max_val) / running_max_val * 100) if running_max_val > 0 else 0.0
            
            equity_curve_data.append({
                'timestamp': timestamps[i],
                'strategy_portfolio_value': portfolio_value[i],
                'buyhold_portfolio_value': buyhold_value[i],
                'strategy_cumulative_return': strategy_cum_return,
                'buyhold_cumulative_return': buyhold_cum_return,
                'strategy_drawdown': strategy_drawdown,
                'position_status': position_status[i],
                'btc_price': price_array[i]
            })
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'buyhold_return': buyhold_return,
            'outperformance': total_return - buyhold_return,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'trades': len(trades),
            'avg_gain': avg_gain,
            'avg_loss': avg_loss,
            'max_gain': max_gain,
            'max_loss': max_loss,
            'portfolio_value': portfolio_value,
            'trade_details': trades,
            'equity_curve_data': equity_curve_data
        }

class DailySupabaseUpdater:
    """Daily Supabase update manager"""
    
    def __init__(self, force_refresh=False):
        # Check for FMP API key
        fmp_api_key = os.getenv('FMP_API_KEY')
        if not fmp_api_key:
            raise ValueError("FMP_API_KEY not found in environment variables")
        
        # Get Supabase credentials
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_anon_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
        
        self.fetcher = HybridDataFetcher(fmp_api_key)
        self.db_manager = SupabaseTradeDataManager(supabase_url, supabase_anon_key, use_service_role=True)
        self.force_refresh = force_refresh  # Option to force full data refresh
        

    
    def process_timeframe(self, timeframe):
        """Process a single timeframe with incremental updates"""
        print(f"\n📊 Processing {timeframe} timeframe...")
        
        analysis_date = datetime.now().date().isoformat()
        
        # Check if we already have complete data for this timeframe
        if not self.force_refresh:
            # First, do a quick check - fetch a small sample to estimate total records
            print(f"🔍 Checking existing data for {timeframe}...")
            
            # Get a small sample to estimate data size
            sample_data = self.fetcher.fetch_data_for_timeframe(timeframe)
            if sample_data is None:
                print(f"❌ Failed to fetch {timeframe} data")
                return None
            
            expected_record_count = len(sample_data)
            
            # Check if we have complete data
            is_complete = self.db_manager.has_complete_data_for_timeframe(
                timeframe, analysis_date, expected_record_count
            )
            
            if is_complete:
                print(f"✅ {timeframe} data is already complete, skipping...")
                # Still return the existing data summary for reporting
                coverage = self.db_manager.check_existing_data_coverage(timeframe, analysis_date)
                return {
                    'timeframe': timeframe,
                    'skipped': True,
                    'reason': 'Data already complete',
                    'existing_records': coverage['ai_trend_data_count']
                }
        
        # Fetch data (we already have it from the check above, but re-fetch for clarity)
        data = self.fetcher.fetch_data_for_timeframe(timeframe)
        if data is None:
            print(f"❌ Failed to fetch {timeframe} data")
            return None
        
        # Calculate data coverage
        if len(data) > 0:
            start_date = data.index[0]
            end_date = data.index[-1]
            time_span = end_date - start_date
            years = time_span.days / 365.25
            
            print(f"📅 {timeframe}: {years:.1f} years of data ({len(data)} records)")
        else:
            print(f"❌ No data records for {timeframe}")
            return None
        
        # Get best parameters
        params = self.fetcher.best_params[timeframe]
        
        # Initialize navigator with best parameters
        navigator = OptimizedAITrendNavigator(
            numberOfClosestValues=params['K'],
            smoothingPeriod=params['smoothing'],
            windowSize=params['window'],
            maLen=params['maLen']
        )
        
        # Calculate signals
        signals = navigator.calculate_trend_signals(data)
        
        # Calculate performance
        performance = self.fetcher.calculate_strategy_performance(signals)
        
        print(f"✅ {timeframe}: {performance['total_return']:.2f}% return, {performance['trades']} trades")
        
        # Store in database using incremental updates
        self.store_analysis_results_incremental(timeframe, data, signals, performance, params)
        
        return {
            'timeframe': timeframe,
            'data': data,
            'signals': signals,
            'performance': performance,
            'params': params,
            'skipped': False
        }
    
    def store_analysis_results_incremental(self, timeframe, data, signals, performance, params):
        """Store analysis results in Supabase using incremental updates"""
        analysis_date = datetime.now().date().isoformat()
        
        print(f"💾 Storing data for {timeframe} incrementally...")
        
        # Create performance metrics
        metrics = PerformanceMetrics(
            timeframe=timeframe,
            strategy_return=performance['total_return'],
            buyhold_return=performance['buyhold_return'],
            outperformance=performance['outperformance'],
            total_trades=performance['trades'],
            win_rate=performance['win_rate'],
            average_gain=performance['avg_gain'],
            average_loss=performance['avg_loss'],
            max_gain=performance['max_gain'],
            max_loss=performance['max_loss'],
            max_drawdown=performance['max_drawdown'],
            sharpe_ratio=0.0,  # Can be calculated if needed
            sortino_ratio=0.0,  # Can be calculated if needed
            profit_factor=0.0,  # Can be calculated if needed
            best_params={
                'K': params['K'],
                'smoothing': params['smoothing'],
                'window': params['window'],
                'maLen': params['maLen']
            },
            date_analyzed=analysis_date
        )
        
        # Create transaction records (batch operation)
        transaction_records = []
        for i, trade in enumerate(performance['trade_details']):
            # Find entry and exit timestamps
            entry_idx = None
            exit_idx = None
            
            for j, signal in enumerate(signals['signal']):
                if signal == 'buy' and signals['price'].iloc[j] == trade['entry_price']:
                    entry_idx = j
                elif signal == 'sell' and signals['price'].iloc[j] == trade['exit_price'] and entry_idx is not None:
                    exit_idx = j
                    break
            
            if entry_idx is not None and exit_idx is not None:
                entry_timestamp = data.index[entry_idx]
                exit_timestamp = data.index[exit_idx]
                
                # Buy transaction
                buy_record = TransactionRecord(
                    timeframe=timeframe,
                    timestamp=entry_timestamp.isoformat(),
                    action='BUY',
                    price=trade['entry_price'],
                    quantity=10000 / trade['entry_price'],  # $10k initial capital
                    portfolio_value=10000,
                    signal_strength=1.0,
                    k_value=params['K'],
                    smoothing_factor=params['smoothing'],
                    window_size=params['window'],
                    ma_period=params['maLen'],
                    date_analyzed=analysis_date
                )
                
                # Sell transaction
                sell_record = TransactionRecord(
                    timeframe=timeframe,
                    timestamp=exit_timestamp.isoformat(),
                    action='SELL',
                    price=trade['exit_price'],
                    quantity=10000 / trade['entry_price'],
                    portfolio_value=10000 * (1 + trade['return'] / 100),
                    signal_strength=1.0,
                    k_value=params['K'],
                    smoothing_factor=params['smoothing'],
                    window_size=params['window'],
                    ma_period=params['maLen'],
                    date_analyzed=analysis_date
                )
                
                transaction_records.extend([buy_record, sell_record])
        
        # Create AI trend data for charting (batch operation)
        print(f"🔄 Preparing {len(data)} AI trend data points...")
        
        # Clean signals data to handle NaN values
        signals_clean = signals.copy()
        signals_clean = signals_clean.fillna(0)  # Replace NaN with 0
        
        ai_trend_records = []
        for i, (timestamp, row) in enumerate(data.iterrows()):
            signal_row = signals_clean.iloc[i]
            
            # Convert boolean to integer for JSON serialization
            buy_signal = 1 if signal_row['signal'] == 'buy' else 0
            sell_signal = 1 if signal_row['signal'] == 'sell' else 0
            
            # Safe numeric conversion function - preserve AI signal values
            def safe_numeric(value, default=0.0):
                if pd.isna(value) or np.isnan(value) or np.isinf(value):
                    return default
                # Don't clamp values - AI signals should be in Bitcoin price range
                return float(value)
            
            # Map trend direction to database values
            trend_direction_raw = str(signal_row['trend_direction']).lower()
            if trend_direction_raw == 'up':
                trend_direction = 'BULLISH'
            elif trend_direction_raw == 'down':
                trend_direction = 'BEARISH'
            else:
                trend_direction = 'NEUTRAL'
            
            # Handle volume more carefully to prevent overflow
            volume = safe_numeric(row['volume'], 0.0)
            if volume > 999999999:
                volume = 999999999.0
            
            ai_record = AITrendData(
                timeframe=timeframe,
                timestamp=timestamp.isoformat(),
                open_price=safe_numeric(row['open']),
                high_price=safe_numeric(row['high']),
                low_price=safe_numeric(row['low']),
                close_price=safe_numeric(row['close']),
                volume=volume,
                signal=safe_numeric(signal_row['knnMA']),
                smoothed_signal=safe_numeric(signal_row['knnMA_smoothed']),
                ma_signal=safe_numeric(signal_row['MA_knnMA']),
                trend_direction=trend_direction,
                buy_signal=buy_signal,
                sell_signal=sell_signal,
                signal_strength=1.0 if signal_row['signal'] in ['buy', 'sell'] else 0.0,
                k_value=params['K'],
                smoothing_factor=params['smoothing'],
                window_size=params['window'],
                ma_period=params['maLen'],
                date_analyzed=analysis_date
            )
            ai_trend_records.append(ai_record)
        
        # Create equity curve data (batch operation)
        print(f"🔄 Preparing {len(performance['equity_curve_data'])} equity curve data points...")
        
        equity_curve_records = []
        for equity_point in performance['equity_curve_data']:
            equity_record = EquityCurve(
                timeframe=timeframe,
                timestamp=equity_point['timestamp'].isoformat(),
                strategy_portfolio_value=equity_point['strategy_portfolio_value'],
                buyhold_portfolio_value=equity_point['buyhold_portfolio_value'],
                strategy_cumulative_return=equity_point['strategy_cumulative_return'],
                buyhold_cumulative_return=equity_point['buyhold_cumulative_return'],
                strategy_drawdown=equity_point['strategy_drawdown'],
                position_status=equity_point['position_status'],
                btc_price=equity_point['btc_price'],
                k_value=params['K'],
                smoothing_factor=params['smoothing'],
                window_size=params['window'],
                ma_period=params['maLen'],
                date_analyzed=analysis_date
            )
            equity_curve_records.append(equity_record)
        
        # Store all data incrementally using the new method
        success = self.db_manager.store_incremental_data(
            timeframe=timeframe,
            date_analyzed=analysis_date,
            ai_trend_data=ai_trend_records,
            transaction_records=transaction_records,
            equity_curve_data=equity_curve_records,
            performance_metrics=metrics
        )
        
        if success:
            print(f"✅ Successfully stored data for {timeframe}")
        else:
            print(f"❌ Error storing data for {timeframe}")
    
    def run_daily_update(self):
        """Run the daily update for all timeframes with incremental updates"""
        print("🚀 Starting daily AI Trend Navigator analysis...")
        
        if self.force_refresh:
            # Clear all existing data for today if force refresh is requested
            analysis_date = datetime.now().date().isoformat()
            print(f"🗑️ Force refresh requested - clearing all existing data for {analysis_date}...")
            
            if self.db_manager.clear_todays_data(analysis_date):
                print("✅ Successfully cleared existing data")
            else:
                print("⚠️ Warning: Could not clear existing data")
        else:
            print("🔄 Using incremental update mode - checking for existing data...")
        
        timeframes = ['4H', '8H', '1D', '1W', '1M']
        results = {}
        
        for timeframe in timeframes:
            try:
                result = self.process_timeframe(timeframe)
                if result:
                    results[timeframe] = result
            except Exception as e:
                print(f"❌ Error processing {timeframe}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Summary
        processed = len([r for r in results.values() if not r.get('skipped', False)])
        skipped = len([r for r in results.values() if r.get('skipped', False)])
        
        print(f"\n✅ Daily update completed!")
        print(f"   📊 Processed: {processed} timeframes")
        print(f"   ⏭️  Skipped: {skipped} timeframes (already complete)")
        print(f"   🎯 Total: {len(results)} timeframes")
        
        return results

def main():
    """Main function"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Daily AI Trend Navigator Supabase Update')
    parser.add_argument('--force-refresh', action='store_true', 
                        help='Force full data refresh (clear existing data and re-insert all)')
    parser.add_argument('--timeframe', type=str, choices=['4H', '8H', '1D', '1W', '1M'],
                        help='Process only specific timeframe (default: all)')
    
    args = parser.parse_args()
    
    try:
        updater = DailySupabaseUpdater(force_refresh=args.force_refresh)
        
        if args.force_refresh:
            print("⚡ Running in FORCE REFRESH mode - will clear and re-insert all data")
        else:
            print("🔄 Running in INCREMENTAL mode - will only add missing data")
        
        if args.timeframe:
            print(f"🎯 Processing only {args.timeframe} timeframe")
            # Process single timeframe
            result = updater.process_timeframe(args.timeframe)
            if result:
                if result.get('skipped', False):
                    print(f"⏭️  {args.timeframe} was skipped: {result['reason']}")
                else:
                    print(f"✅ Successfully processed {args.timeframe}")
                return 0
            else:
                print(f"❌ Failed to process {args.timeframe}")
                return 1
        else:
            # Process all timeframes
            results = updater.run_daily_update()
            processed = len([r for r in results.values() if not r.get('skipped', False)])
            if processed > 0:
                print(f"\n🎉 Success! Updated {processed} timeframes in database")
                return 0
            else:
                print(f"\n⚠️  No timeframes were processed")
                return 1
        
    except Exception as e:
        print(f"❌ Error in daily update: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main()) 