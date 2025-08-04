"""
Enhanced Volume Profile Analysis with CCXT Integration
Advanced volume analysis toolkit for trading strategy development
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import ccxt
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def fetch_crypto_data_ccxt(symbol='BTC/USDT', timeframe='1d', limit=500, exchange='binance'):
    """
    Fetch cryptocurrency data using CCXT
    
    Parameters:
    symbol (str): Trading pair symbol (e.g., 'BTC/USDT', 'ETH/USDT')
    timeframe (str): Timeframe ('1m', '5m', '15m', '1h', '4h', '1d', '1w')
    limit (int): Number of candles to fetch
    exchange (str): Exchange name ('binance', 'coinbase', 'kraken', etc.)
    
    Returns:
    pd.DataFrame: OHLCV data
    """
    try:
        # Initialize exchange
        exchange_class = getattr(ccxt, exchange)
        exchange_instance = exchange_class({
            'apiKey': '',  # Add your API key if needed
            'secret': '',  # Add your secret if needed
            'timeout': 30000,
            'enableRateLimit': True,
        })
        
        # Fetch OHLCV data
        print(f"Fetching {symbol} data from {exchange}...")
        ohlcv = exchange_instance.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        # Create DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        print(f"Successfully fetched {len(df)} candles")
        return df
        
    except Exception as e:
        print(f"Error fetching data from {exchange}: {e}")
        print("Trying alternative exchange...")
        
        # Try alternative exchanges
        alternative_exchanges = ['coinbase', 'kraken', 'okx', 'huobi']
        
        for alt_exchange in alternative_exchanges:
            if alt_exchange != exchange:
                try:
                    alt_exchange_class = getattr(ccxt, alt_exchange)
                    alt_exchange_instance = alt_exchange_class({
                        'timeout': 30000,
                        'enableRateLimit': True,
                    })
                    
                    print(f"Trying {alt_exchange}...")
                    ohlcv = alt_exchange_instance.fetch_ohlcv(symbol, timeframe, limit=limit)
                    
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    
                    print(f"Successfully fetched {len(df)} candles from {alt_exchange}")
                    return df
                    
                except Exception as alt_e:
                    print(f"Failed with {alt_exchange}: {alt_e}")
                    continue
        
        raise Exception("Failed to fetch data from all attempted exchanges")

def load_csv_data(file_path, sep=','):
    """
    Load data from CSV file with flexible parsing
    
    Parameters:
    file_path (str): Path to CSV file
    sep (str): Separator character
    
    Returns:
    pd.DataFrame: OHLCV data
    """
    try:
        # Try different separators
        separators = [sep, ';', ',', '\t']
        
        for separator in separators:
            try:
                df = pd.read_csv(file_path, sep=separator)
                
                # Check if we have the required columns
                required_cols = ['open', 'high', 'low', 'close']
                if all(col in df.columns.str.lower() for col in required_cols):
                    print(f"Successfully loaded CSV with separator '{separator}'")
                    break
            except:
                continue
        else:
            raise ValueError("Could not parse CSV with any separator")
        
        # Standardize column names
        df.columns = df.columns.str.lower().str.strip()
        
        # Handle different timestamp column names
        timestamp_cols = ['timestamp', 'date', 'time', 'datetime', 'timeclose']
        timestamp_col = None
        
        for col in timestamp_cols:
            if col in df.columns:
                timestamp_col = col
                break
        
        if timestamp_col:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])
            df.set_index(timestamp_col, inplace=True)
        
        # Ensure we have volume column
        if 'volume' not in df.columns:
            print("Warning: No volume column found. Creating synthetic volume based on price range.")
            df['volume'] = (df['high'] - df['low']) * 1000000  # Synthetic volume
        
        # Select and clean the OHLCV columns
        ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
        df = df[ohlcv_cols].copy()
        
        # Convert to numeric
        for col in ohlcv_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove any rows with NaN values
        df.dropna(inplace=True)
        
        print(f"Loaded {len(df)} rows of data")
        return df
        
    except Exception as e:
        print(f"Error loading CSV: {e}")
        raise

class EnhancedVolumeProfileAnalyzer:
    def __init__(self, data=None):
        """
        Initialize the Enhanced Volume Profile Analyzer
        
        Parameters:
        data (DataFrame): OHLCV data with columns ['open', 'high', 'low', 'close', 'volume']
        """
        self.data = data
        self.profile_data = None
        self.smart_levels = None
        self.volume_features = None
        
    def load_data(self, data):
        """Load OHLCV data"""
        self.data = data.copy()
        if not isinstance(self.data.index, pd.DatetimeIndex):
            self.data.index = pd.to_datetime(self.data.index)
    
    def fetch_data_ccxt(self, symbol='BTC/USDT', timeframe='1d', limit=500, exchange='binance'):
        """
        Fetch data using CCXT and load it into the analyzer
        
        Parameters:
        symbol (str): Trading pair symbol
        timeframe (str): Timeframe
        limit (int): Number of candles
        exchange (str): Exchange name
        """
        self.data = fetch_crypto_data_ccxt(symbol, timeframe, limit, exchange)
        return self.data
    
    def load_csv(self, file_path, sep=','):
        """
        Load data from CSV file
        
        Parameters:
        file_path (str): Path to CSV file
        sep (str): Separator character
        """
        self.data = load_csv_data(file_path, sep)
        return self.data
        
    def calculate_enhanced_volume_metrics(self):
        """Calculate enhanced volume metrics"""
        df = self.data.copy()
        
        # Basic volume metrics
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        df['volume_rsi'] = self._calculate_rsi(df['volume'], 14)
        
        # Enhanced volume calculations
        df['money_flow'] = df['volume'] * (df['high'] + df['low'] + df['close']) / 3
        df['enhanced_money_flow'] = df['money_flow'] * (1 + abs(df['close'].pct_change()))
        
        # Volume pressure indicators
        df['buying_pressure'] = np.where(df['close'] > df['open'], df['volume'], 0)
        df['selling_pressure'] = np.where(df['close'] < df['open'], df['volume'], 0)
        df['volume_delta'] = df['buying_pressure'] - df['selling_pressure']
        df['cumulative_delta'] = df['volume_delta'].cumsum()
        
        # Institutional flow estimation
        df['institutional_threshold'] = df['volume_sma_20'] * 3
        df['institutional_flow'] = np.where(df['volume'] > df['institutional_threshold'], 
                                          df['volume'], 0)
        
        # Volume waves detection
        df['volume_wave'] = np.where(df['volume'] > df['volume_sma_20'] * 1.5, 1, 0)
        df['volume_anomaly'] = np.where(df['volume'] > df['volume_sma_20'] * 4, 1, 0)
        
        # Price-volume divergence
        df['price_momentum'] = df['close'].pct_change(5).rolling(5).mean()
        df['volume_momentum'] = df['volume'].pct_change(5).rolling(5).mean()
        df['pv_divergence'] = df['price_momentum'] - df['volume_momentum']
        
        self.volume_features = df
        return df
    
    def build_volume_profile(self, lookback=300, rows=30, profile_type='enhanced_money_flow'):
        """
        Build enhanced volume profile
        
        Parameters:
        lookback (int): Number of bars to analyze
        rows (int): Number of profile rows
        profile_type (str): Type of volume calculation
        """
        if self.volume_features is None:
            self.calculate_enhanced_volume_metrics()
            
        df = self.volume_features.tail(lookback).copy()
        
        # Calculate profile range
        profile_high = df['high'].max()
        profile_low = df['low'].min()
        row_height = (profile_high - profile_low) / rows
        
        # Initialize profile arrays
        profile_data = {
            'price_levels': [],
            'total_volume': [],
            'buy_volume': [],
            'sell_volume': [],
            'institutional_volume': [],
            'trade_count': [],
            'avg_trade_size': []
        }
        
        for row in range(rows):
            row_bottom = profile_low + row * row_height
            row_top = row_bottom + row_height
            row_center = (row_bottom + row_top) / 2
            
            # Find bars that intersect with this price level
            intersecting_bars = df[
                (df['low'] <= row_top) & (df['high'] >= row_bottom)
            ]
            
            if len(intersecting_bars) == 0:
                profile_data['price_levels'].append(row_center)
                for key in ['total_volume', 'buy_volume', 'sell_volume', 
                           'institutional_volume', 'trade_count', 'avg_trade_size']:
                    profile_data[key].append(0)
                continue
            
            # Calculate volume distribution
            total_vol = 0
            buy_vol = 0
            sell_vol = 0
            inst_vol = 0
            trade_count = 0
            
            for idx, bar in intersecting_bars.iterrows():
                bar_range = bar['high'] - bar['low']
                if bar_range == 0:
                    continue
                    
                # Calculate overlap
                overlap = min(bar['high'], row_top) - max(bar['low'], row_bottom)
                volume_portion = (overlap / bar_range) * bar[profile_type]
                
                total_vol += volume_portion
                trade_count += 1
                
                # Determine buy/sell pressure
                if bar['close'] > bar['open']:
                    buy_vol += volume_portion
                else:
                    sell_vol += volume_portion
                
                # Institutional volume
                if bar['volume'] > bar['institutional_threshold']:
                    inst_vol += volume_portion
            
            profile_data['price_levels'].append(row_center)
            profile_data['total_volume'].append(total_vol)
            profile_data['buy_volume'].append(buy_vol)
            profile_data['sell_volume'].append(sell_vol)
            profile_data['institutional_volume'].append(inst_vol)
            profile_data['trade_count'].append(trade_count)
            profile_data['avg_trade_size'].append(total_vol / trade_count if trade_count > 0 else 0)
        
        self.profile_data = pd.DataFrame(profile_data)
        return self.profile_data
    
    def detect_smart_levels(self, threshold_percentile=85, cluster_tolerance=0.002):
        """
        Detect smart support/resistance levels using volume clustering
        
        Parameters:
        threshold_percentile (float): Volume threshold percentile
        cluster_tolerance (float): Price clustering tolerance (as percentage)
        """
        if self.profile_data is None:
            self.build_volume_profile()
        
        # Find high-volume price levels
        volume_threshold = np.percentile(self.profile_data['total_volume'], threshold_percentile)
        high_volume_levels = self.profile_data[
            self.profile_data['total_volume'] > volume_threshold
        ].copy()
        
        if len(high_volume_levels) == 0:
            self.smart_levels = pd.DataFrame()
            return self.smart_levels
        
        # Cluster nearby price levels
        prices = high_volume_levels['price_levels'].values.reshape(-1, 1)
        volumes = high_volume_levels['total_volume'].values
        
        # Use price clustering to group nearby levels
        price_range = prices.max() - prices.min()
        eps = price_range * cluster_tolerance
        
        # Simple clustering based on price proximity
        clusters = []
        used_indices = set()
        
        for i, price in enumerate(prices.flatten()):
            if i in used_indices:
                continue
                
            cluster_prices = [price]
            cluster_volumes = [volumes[i]]
            cluster_indices = [i]
            
            for j, other_price in enumerate(prices.flatten()):
                if j != i and j not in used_indices:
                    if abs(price - other_price) / price < cluster_tolerance:
                        cluster_prices.append(other_price)
                        cluster_volumes.append(volumes[j])
                        cluster_indices.append(j)
                        used_indices.add(j)
            
            used_indices.add(i)
            
            # Calculate cluster statistics
            weighted_price = np.average(cluster_prices, weights=cluster_volumes)
            total_volume = sum(cluster_volumes)
            strength = len(cluster_prices)
            
            clusters.append({
                'price': weighted_price,
                'volume': total_volume,
                'strength': strength,
                'buy_volume': sum(high_volume_levels.iloc[cluster_indices]['buy_volume']),
                'sell_volume': sum(high_volume_levels.iloc[cluster_indices]['sell_volume']),
                'institutional_volume': sum(high_volume_levels.iloc[cluster_indices]['institutional_volume'])
            })
        
        self.smart_levels = pd.DataFrame(clusters).sort_values('volume', ascending=False)
        return self.smart_levels
    
    def calculate_volume_profile_metrics(self):
        """Calculate key volume profile metrics"""
        if self.profile_data is None:
            self.build_volume_profile()
        
        # Point of Control (PoC)
        poc_idx = self.profile_data['total_volume'].idxmax()
        poc_price = self.profile_data.loc[poc_idx, 'price_levels']
        poc_volume = self.profile_data.loc[poc_idx, 'total_volume']
        
        # Value Area (70% of volume)
        total_volume = self.profile_data['total_volume'].sum()
        target_va_volume = total_volume * 0.70
        
        # Sort by volume and find VA
        sorted_profile = self.profile_data.sort_values('total_volume', ascending=False)
        cumulative_volume = 0
        va_levels = []
        
        for idx, row in sorted_profile.iterrows():
            cumulative_volume += row['total_volume']
            va_levels.append(row['price_levels'])
            if cumulative_volume >= target_va_volume:
                break
        
        va_high = max(va_levels)
        va_low = min(va_levels)
        
        # Volume distribution analysis
        total_buy = self.profile_data['buy_volume'].sum()
        total_sell = self.profile_data['sell_volume'].sum()
        net_delta = total_buy - total_sell
        delta_ratio = net_delta / (total_buy + total_sell) if (total_buy + total_sell) > 0 else 0
        
        # Institutional participation
        total_institutional = self.profile_data['institutional_volume'].sum()
        institutional_ratio = total_institutional / total_volume if total_volume > 0 else 0
        
        metrics = {
            'poc_price': poc_price,
            'poc_volume': poc_volume,
            'va_high': va_high,
            'va_low': va_low,
            'va_range': va_high - va_low,
            'total_volume': total_volume,
            'net_delta': net_delta,
            'delta_ratio': delta_ratio,
            'institutional_ratio': institutional_ratio,
            'profile_balance': self._calculate_profile_balance()
        }
        
        return metrics
    
    def _calculate_profile_balance(self):
        """Calculate profile balance (above vs below PoC)"""
        if self.profile_data is None:
            return 0
        
        poc_idx = self.profile_data['total_volume'].idxmax()
        poc_price = self.profile_data.loc[poc_idx, 'price_levels']
        
        above_poc = self.profile_data[self.profile_data['price_levels'] > poc_price]['total_volume'].sum()
        below_poc = self.profile_data[self.profile_data['price_levels'] <= poc_price]['total_volume'].sum()
        
        total = above_poc + below_poc
        return (above_poc - below_poc) / total if total > 0 else 0
    
    def _calculate_rsi(self, series, period=14):
        """Calculate RSI"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def plot_enhanced_volume_profile(self, figsize=(15, 10)):
        """Create comprehensive volume profile visualization"""
        if self.profile_data is None:
            self.build_volume_profile()
        
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        fig.suptitle('Enhanced Volume Profile Analysis', fontsize=16, fontweight='bold')
        
        # Main volume profile
        ax1 = axes[0, 0]
        ax1.barh(self.profile_data['price_levels'], self.profile_data['total_volume'], 
                alpha=0.7, color='steelblue')
        ax1.set_title('Volume Profile')
        ax1.set_xlabel('Volume')
        ax1.set_ylabel('Price')
        
        # Mark PoC and VA
        metrics = self.calculate_volume_profile_metrics()
        ax1.axhline(y=metrics['poc_price'], color='red', linestyle='--', linewidth=2, label='PoC')
        ax1.axhspan(metrics['va_low'], metrics['va_high'], alpha=0.2, color='yellow', label='Value Area')
        ax1.legend()
        
        # Buy/Sell pressure
        ax2 = axes[0, 1]
        ax2.barh(self.profile_data['price_levels'], self.profile_data['buy_volume'], 
                alpha=0.7, color='green', label='Buy Volume')
        ax2.barh(self.profile_data['price_levels'], -self.profile_data['sell_volume'], 
                alpha=0.7, color='red', label='Sell Volume')
        ax2.set_title('Buy/Sell Pressure')
        ax2.set_xlabel('Volume')
        ax2.legend()
        
        # Institutional flow
        ax3 = axes[1, 0]
        inst_ratio = self.profile_data['institutional_volume'] / self.profile_data['total_volume']
        inst_ratio = inst_ratio.fillna(0)
        ax3.barh(self.profile_data['price_levels'], inst_ratio, 
                alpha=0.7, color='orange')
        ax3.set_title('Institutional Participation Ratio')
        ax3.set_xlabel('Institutional Volume Ratio')
        
        # Smart levels
        ax4 = axes[1, 1]
        if self.smart_levels is not None and len(self.smart_levels) > 0:
            ax4.scatter(self.smart_levels['volume'], self.smart_levels['price'], 
                       s=self.smart_levels['strength']*50, alpha=0.6, color='purple')
            ax4.set_title('Smart Support/Resistance Levels')
            ax4.set_xlabel('Volume')
            ax4.set_ylabel('Price')
        else:
            ax4.text(0.5, 0.5, 'No Smart Levels Detected', 
                    transform=ax4.transAxes, ha='center', va='center')
            ax4.set_title('Smart Support/Resistance Levels')
        
        plt.tight_layout()
        return fig
    
    def generate_trading_signals(self):
        """Generate enhanced trading signals with trend awareness and risk management"""
        if self.volume_features is None:
            self.calculate_enhanced_volume_metrics()
        
        df = self.volume_features.copy()
        signals = pd.DataFrame(index=df.index)
        
        # Add trend indicators
        df['sma_20'] = df['close'].rolling(20).mean()
        df['sma_50'] = df['close'].rolling(50).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['rsi'] = self._calculate_rsi(df['close'], 14)
        
        # Market regime detection
        df['trend_strength'] = (df['close'] - df['sma_50']) / df['sma_50']
        df['is_uptrend'] = (df['sma_20'] > df['sma_50']) & (df['close'] > df['sma_20'])
        df['is_downtrend'] = (df['sma_20'] < df['sma_50']) & (df['close'] < df['sma_20'])
        df['is_ranging'] = ~(df['is_uptrend'] | df['is_downtrend'])
        
        # Enhanced volume signals with trend filtering
        signals['volume_breakout'] = (df['volume_ratio'] > 2.5).astype(int)  # Higher threshold
        signals['volume_confirmation'] = (df['volume_ratio'] > 1.5) & (df['volume_ratio'] < 3.0)
        signals['institutional_flow'] = (df['institutional_flow'] > 0).astype(int)
        
        # Trend-following signals
        signals['bullish_trend'] = (
            df['is_uptrend'] & 
            (df['macd'] > df['macd_signal']) &
            (df['rsi'] > 45) & (df['rsi'] < 75) &
            (df['cumulative_delta'].diff() > 0)
        ).astype(int)
        
        signals['bearish_trend'] = (
            df['is_downtrend'] & 
            (df['macd'] < df['macd_signal']) &
            (df['rsi'] < 55) & (df['rsi'] > 25) &
            (df['cumulative_delta'].diff() < 0)
        ).astype(int)
        
        # Volume Profile specific signals
        if self.profile_data is not None:
            metrics = self.calculate_volume_profile_metrics()
            poc_price = metrics['poc_price']
            va_high = metrics['va_high']
            va_low = metrics['va_low']
            
            # Support/Resistance signals
            signals['poc_support'] = (
                (df['close'] <= poc_price * 1.02) & 
                (df['close'] >= poc_price * 0.98) &
                df['is_uptrend'] &
                (df['volume_ratio'] > 1.2)
            ).astype(int)
            
            signals['va_breakout'] = (
                ((df['close'] > va_high) & df['is_uptrend']) |
                ((df['close'] < va_low) & df['is_downtrend'])
            ).astype(int)
        else:
            signals['poc_support'] = 0
            signals['va_breakout'] = 0
        
        # Mean reversion signals for ranging markets
        signals['oversold_reversal'] = (
            df['is_ranging'] &
            (df['rsi'] < 30) &
            (df['volume_ratio'] > 1.5) &
            (df['cumulative_delta'].diff() > 0)
        ).astype(int)
        
        signals['overbought_reversal'] = (
            df['is_ranging'] &
            (df['rsi'] > 70) &
            (df['volume_ratio'] > 1.5) &
            (df['cumulative_delta'].diff() < 0)
        ).astype(int)
        
        # Volume divergence signals (early reversal detection)
        signals['bullish_divergence'] = (
            (df['price_momentum'] < -0.02) & 
            (df['volume_momentum'] > 0.1) &
            (df['rsi'] < 40)
        ).astype(int)
        
        signals['bearish_divergence'] = (
            (df['price_momentum'] > 0.02) & 
            (df['volume_momentum'] < -0.1) &
            (df['rsi'] > 60)
        ).astype(int)
        
        # Exit signals for risk management
        signals['profit_take'] = (
            (df['rsi'] > 80) | (df['rsi'] < 20) |
            (df['volume_ratio'] < 0.5)  # Very low volume
        ).astype(int)
        
        return signals
    
    def backtest_volume_strategy(self, initial_capital=100000, max_position_size=0.1, stop_loss=0.05, take_profit=0.15):
        """Enhanced backtest with proper risk management and position sizing"""
        signals = self.generate_trading_signals()
        df = self.volume_features.copy()
        
        portfolio = pd.DataFrame(index=df.index)
        portfolio['price'] = df['close']
        portfolio['returns'] = df['close'].pct_change()
        
        # Calculate position signals with proper weighting
        portfolio['long_signal'] = (
            signals['bullish_trend'] * 3 +           # Strong trend following
            signals['poc_support'] * 2 +             # Volume profile support
            signals['oversold_reversal'] * 2 +       # Mean reversion
            signals['bullish_divergence'] * 2 +      # Early reversal detection
            signals['volume_breakout'] * 1 +         # Volume confirmation
            signals['institutional_flow'] * 1        # Large player activity
        )
        
        portfolio['short_signal'] = (
            signals['bearish_trend'] * 3 +           # Strong trend following
            signals['va_breakout'] * 2 +             # Volume profile breakout
            signals['overbought_reversal'] * 2 +     # Mean reversion
            signals['bearish_divergence'] * 2        # Early reversal detection
        )
        
        # Normalize signals to position size (0 to max_position_size)
        max_long = portfolio['long_signal'].max() if portfolio['long_signal'].max() > 0 else 1
        max_short = portfolio['short_signal'].max() if portfolio['short_signal'].max() > 0 else 1
        
        portfolio['target_position'] = (
            (portfolio['long_signal'] / max_long * max_position_size) -
            (portfolio['short_signal'] / max_short * max_position_size)
        )
        
        # Apply risk management
        portfolio['position'] = 0.0
        portfolio['entry_price'] = 0.0
        portfolio['cash'] = initial_capital
        portfolio['holdings'] = 0.0
        portfolio['portfolio_value'] = initial_capital
        
        # Track trades
        trades = []
        current_position = 0.0
        entry_price = 0.0
        
        for i in range(1, len(portfolio)):
            current_price = portfolio['price'].iloc[i]
            target_pos = portfolio['target_position'].iloc[i]
            
            # Exit conditions (stop loss, take profit, or exit signal)
            if current_position != 0:
                price_change = (current_price - entry_price) / entry_price
                
                # Long position exits
                if current_position > 0:
                    if (price_change <= -stop_loss or  # Stop loss
                        price_change >= take_profit or   # Take profit
                        signals['profit_take'].iloc[i] or  # Signal exit
                        target_pos < 0):  # Signal reversal
                        
                        # Close long position
                        trade_return = current_position * price_change
                        trades.append({
                            'entry_price': entry_price,
                            'exit_price': current_price,
                            'position_size': current_position,
                            'return': trade_return,
                            'type': 'long_exit'
                        })
                        current_position = 0.0
                        entry_price = 0.0
                
                # Short position exits  
                elif current_position < 0:
                    if (price_change >= stop_loss or   # Stop loss (opposite for short)
                        price_change <= -take_profit or  # Take profit (opposite for short)
                        signals['profit_take'].iloc[i] or  # Signal exit
                        target_pos > 0):  # Signal reversal
                        
                        # Close short position
                        trade_return = -current_position * price_change  # Negative because short
                        trades.append({
                            'entry_price': entry_price,
                            'exit_price': current_price,
                            'position_size': current_position,
                            'return': trade_return,
                            'type': 'short_exit'
                        })
                        current_position = 0.0
                        entry_price = 0.0
            
            # Entry conditions (only if no current position)
            if current_position == 0 and abs(target_pos) > 0.01:  # Minimum threshold
                current_position = target_pos
                entry_price = current_price
                
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': None,
                    'position_size': current_position,
                    'return': None,
                    'type': 'long_entry' if current_position > 0 else 'short_entry'
                })
            
            # Update portfolio
            portfolio.iloc[i, portfolio.columns.get_loc('position')] = current_position
            portfolio.iloc[i, portfolio.columns.get_loc('entry_price')] = entry_price if current_position != 0 else 0
        
        # Calculate strategy returns
        portfolio['strategy_returns'] = 0.0
        for i in range(1, len(portfolio)):
            if portfolio['position'].iloc[i-1] != 0:
                position = portfolio['position'].iloc[i-1]
                price_return = portfolio['returns'].iloc[i]
                strategy_return = position * price_return  # Position * market return
                portfolio.iloc[i, portfolio.columns.get_loc('strategy_returns')] = strategy_return
        
        portfolio['cumulative_returns'] = (1 + portfolio['strategy_returns']).cumprod()
        portfolio['portfolio_value'] = initial_capital * portfolio['cumulative_returns']
        
        # Calculate enhanced performance metrics
        total_return = portfolio['cumulative_returns'].iloc[-1] - 1
        strategy_returns_clean = portfolio['strategy_returns'].dropna()
        
        if len(strategy_returns_clean) > 0 and strategy_returns_clean.std() > 0:
            volatility = strategy_returns_clean.std() * np.sqrt(252)
            sharpe_ratio = (strategy_returns_clean.mean() * 252) / volatility
        else:
            volatility = 0
            sharpe_ratio = 0
        
        # Calculate maximum drawdown
        rolling_max = portfolio['cumulative_returns'].expanding().max()
        drawdown = (portfolio['cumulative_returns'] / rolling_max - 1)
        max_drawdown = drawdown.min()
        
        # Calculate win rate and other trade statistics
        completed_trades = [t for t in trades if t['return'] is not None]
        if completed_trades:
            wins = len([t for t in completed_trades if t['return'] > 0])
            total_trades = len(completed_trades)
            win_rate = wins / total_trades
            avg_win = np.mean([t['return'] for t in completed_trades if t['return'] > 0]) if wins > 0 else 0
            avg_loss = np.mean([t['return'] for t in completed_trades if t['return'] < 0]) if (total_trades - wins) > 0 else 0
            profit_factor = abs(avg_win * wins / (avg_loss * (total_trades - wins))) if avg_loss != 0 else float('inf')
        else:
            win_rate = 0
            total_trades = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
        
        performance = {
            'total_return': total_return,
            'annualized_volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'final_portfolio_value': portfolio['portfolio_value'].iloc[-1],
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'trades': trades
        }
        
        return portfolio, performance

# Example usage functions
def analyze_crypto_data_ccxt(symbol='BTC/USDT', timeframe='1d', limit=500, exchange='binance'):
    """Example function to analyze cryptocurrency data using CCXT"""
    # Initialize analyzer
    analyzer = EnhancedVolumeProfileAnalyzer()
    
    # Fetch data using CCXT
    try:
        data = analyzer.fetch_data_ccxt(symbol, timeframe, limit, exchange)
        print(f"Data shape: {data.shape}")
        print(f"Columns: {data.columns.tolist()}")
        print(f"Date range: {data.index.min()} to {data.index.max()}")
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None, None, None

def analyze_crypto_data_csv(file_path):
    """Example function to analyze cryptocurrency data from CSV"""
    # Initialize analyzer
    analyzer = EnhancedVolumeProfileAnalyzer()
    
    # Load data from CSV
    try:
        data = analyzer.load_csv(file_path)
        print(f"Data shape: {data.shape}")
        print(f"Columns: {data.columns.tolist()}")
        print(f"Date range: {data.index.min()} to {data.index.max()}")
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None, None, None

def run_complete_analysis(analyzer):
    """Run complete analysis on loaded data"""
    if analyzer.data is None:
        print("No data loaded!")
        return None, None, None
    
    # Calculate enhanced metrics
    volume_features = analyzer.calculate_enhanced_volume_metrics()
    
    # Build volume profile
    profile = analyzer.build_volume_profile(lookback=200, rows=25)
    
    # Detect smart levels
    smart_levels = analyzer.detect_smart_levels()
    
    # Calculate metrics
    metrics = analyzer.calculate_volume_profile_metrics()
    
    # Generate signals
    signals = analyzer.generate_trading_signals()
    
    # Run backtest
    portfolio, performance = analyzer.backtest_volume_strategy()
    
    # Create visualization
    fig = analyzer.plot_enhanced_volume_profile()
    
    print("=== Enhanced Volume Profile Analysis ===")
    print(f"Point of Control: ${metrics['poc_price']:.2f}")
    print(f"Value Area: ${metrics['va_low']:.2f} - ${metrics['va_high']:.2f}")
    print(f"Delta Ratio: {metrics['delta_ratio']:.3f}")
    print(f"Institutional Participation: {metrics['institutional_ratio']:.3f}")
    print(f"Profile Balance: {metrics['profile_balance']:.3f}")
    
    print("\n=== Smart Levels ===")
    if len(smart_levels) > 0:
        for idx, level in smart_levels.head().iterrows():
            print(f"Level: ${level['price']:.2f}, Volume: {level['volume']:.0f}, Strength: {level['strength']}")
    else:
        print("No smart levels detected")
    
    print("\n=== Enhanced Strategy Performance ===")
    print(f"Total Return: {performance['total_return']:.2%}")
    print(f"Sharpe Ratio: {performance['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {performance['max_drawdown']:.2%}")
    print(f"Total Trades: {performance['total_trades']}")
    print(f"Win Rate: {performance['win_rate']:.1%}")
    print(f"Profit Factor: {performance['profit_factor']:.2f}")
    if performance['avg_win'] > 0 and performance['avg_loss'] < 0:
        print(f"Avg Win: {performance['avg_win']:.2%}")
        print(f"Avg Loss: {performance['avg_loss']:.2%}")
        print(f"Risk/Reward Ratio: {abs(performance['avg_win']/performance['avg_loss']):.2f}")
    
    return analyzer, metrics, performance

if __name__ == "__main__":
    print("Enhanced Volume Profile Analysis with CCXT Integration")
    print("=" * 60)
    
    # Method 1: Using CCXT (recommended)
    print("\n1. Fetching live data using CCXT...")
    try:
        analyzer = EnhancedVolumeProfileAnalyzer()
        data = analyzer.fetch_data_ccxt(symbol='BTC/USDT', timeframe='1d', limit=300, exchange='binance')
        analyzer, metrics, performance = run_complete_analysis(analyzer)
        if analyzer:
            plt.show()
    except Exception as e:
        print(f"CCXT method failed: {e}")
        
        # Method 2: Fallback to CSV
        print("\n2. Trying CSV file...")
        try:
            analyzer = EnhancedVolumeProfileAnalyzer()
            data = analyzer.load_csv("BTC.csv")
            analyzer, metrics, performance = run_complete_analysis(analyzer)
            if analyzer:
                plt.show()
        except Exception as csv_e:
            print(f"CSV method also failed: {csv_e}")
            print("\nPlease ensure you have:")
            print("1. CCXT installed: pip install ccxt")
            print("2. Internet connection for live data")
            print("3. Valid CSV file with OHLCV data")

def demo_multiple_symbols():
    """Demo function to analyze multiple cryptocurrency symbols"""
    symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT']
    
    for symbol in symbols:
        print(f"\n{'='*20} {symbol} {'='*20}")
        try:
            analyzer = EnhancedVolumeProfileAnalyzer()
            data = analyzer.fetch_data_ccxt(symbol=symbol, timeframe='1d', limit=200)
            analyzer, metrics, performance = run_complete_analysis(analyzer)
            
            # Quick summary
            if metrics:
                print(f"PoC: ${metrics['poc_price']:.2f}")
                print(f"VA Range: ${metrics['va_range']:.2f}")
                print(f"Strategy Return: {performance['total_return']:.2%}")
                
        except Exception as e:
            print(f"Failed to analyze {symbol}: {e}")
            
        time.sleep(1)  # Rate limiting

# Uncomment to run multi-symbol demo
# demo_multiple_symbols() 