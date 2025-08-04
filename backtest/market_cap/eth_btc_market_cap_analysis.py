import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import requests
import json
import time
import warnings
from typing import Dict, List, Optional, Tuple

warnings.filterwarnings('ignore')

class ETHBTCMarketCapAnalyzer:
    def __init__(self, use_testnet: bool = False):
        """
        Initialize the ETH/BTC Market Cap Analyzer
        
        Args:
            use_testnet: Whether to use Binance testnet (default: False)
        """
        self.exchange = ccxt.binance({
            'apiKey': '',  # Add your API key if needed for higher rate limits
            'secret': '',  # Add your secret if needed
            'timeout': 30000,
            'rateLimit': 1200,
            'verbose': False,
            'sandbox': use_testnet,  # Use testnet if True
        })
        
        # CoinGecko API for market cap data (free tier)
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        
    def get_current_market_data(self) -> Dict:
        """
        Get current market data for ETH and BTC including market cap
        """
        try:
            # Get current prices from Binance
            eth_btc_ticker = self.exchange.fetch_ticker('ETH/BTC')
            btc_usdt_ticker = self.exchange.fetch_ticker('BTC/USDT') 
            eth_usdt_ticker = self.exchange.fetch_ticker('ETH/USDT')
            
            # Get market cap data from CoinGecko
            coins_url = f"{self.coingecko_base_url}/simple/price"
            params = {
                'ids': 'bitcoin,ethereum',
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true'
            }
            
            response = requests.get(coins_url, params=params)
            
            if response.status_code != 200:
                print(f"CoinGecko API Error: {response.status_code} - {response.text}")
                return None
                
            market_data = response.json()
            print(f"Market data keys: {list(market_data.keys())}")
            
            if 'bitcoin' not in market_data or 'ethereum' not in market_data:
                print(f"Missing expected data in response: {market_data}")
                return None
            
            current_data = {
                'timestamp': datetime.now(),
                'btc_price_usd': btc_usdt_ticker['last'],
                'eth_price_usd': eth_usdt_ticker['last'],
                'eth_btc_price_ratio': eth_btc_ticker['last'],
                'btc_market_cap': market_data['bitcoin']['usd_market_cap'],
                'eth_market_cap': market_data['ethereum']['usd_market_cap'],
                'eth_btc_market_cap_ratio': market_data['ethereum']['usd_market_cap'] / market_data['bitcoin']['usd_market_cap'],
                'btc_24h_change': market_data['bitcoin']['usd_24h_change'],
                'eth_24h_change': market_data['ethereum']['usd_24h_change'],
                'btc_volume': market_data['bitcoin']['usd_24h_vol'],
                'eth_volume': market_data['ethereum']['usd_24h_vol']
            }
            
            return current_data
            
        except Exception as e:
            print(f"Error fetching current market data: {e}")
            return None

    def get_historical_ohlcv(self, symbol: str, timeframe: str = '1d', days: int = 365) -> pd.DataFrame:
        """
        Get historical OHLCV data from Binance
        
        Args:
            symbol: Trading pair symbol (e.g., 'ETH/BTC', 'BTC/USDT')
            timeframe: Timeframe for data ('1m', '5m', '1h', '1d', etc.)
            days: Number of days of historical data
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            since = self.exchange.milliseconds() - (days * 24 * 60 * 60 * 1000)
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()

    def get_historical_market_cap_data(self, days: int = 365) -> pd.DataFrame:
        """
        Get historical market cap data for ETH and BTC from CoinGecko
        
        Args:
            days: Number of days of historical data (max 365 for free tier)
            
        Returns:
            DataFrame with historical market cap data
        """
        try:
            # CoinGecko free tier is limited to 365 days max
            days_param = min(days, 365)
            interval = 'daily'
            
            print(f"Fetching {days_param} days of historical market cap data...")
            if days > 365:
                print("⚠️  CoinGecko free tier limits historical data to 365 days max.")
                print("💡 For data from 2021, you would need:")
                print("   • CoinGecko Pro API ($129/month): https://www.coingecko.com/en/api/pricing")
                print("   • Alternative: Use historical CSV data from CoinMarketCap or other sources")
                print("   • Current analysis shows last 365 days trends")
            
            # Get BTC historical market cap
            btc_url = f"{self.coingecko_base_url}/coins/bitcoin/market_chart"
            btc_params = {'vs_currency': 'usd', 'days': days_param, 'interval': interval}
            print(f"Fetching BTC data with params: {btc_params}")
            btc_response = requests.get(btc_url, params=btc_params)
            
            if btc_response.status_code != 200:
                print(f"BTC API Error: {btc_response.status_code} - {btc_response.text}")
                return pd.DataFrame()
                
            btc_data = btc_response.json()
            print(f"BTC API Response keys: {list(btc_data.keys())}")
            
            # Get ETH historical market cap  
            eth_url = f"{self.coingecko_base_url}/coins/ethereum/market_chart"
            eth_params = {'vs_currency': 'usd', 'days': days_param, 'interval': interval}
            print(f"Fetching ETH data with params: {eth_params}")
            eth_response = requests.get(eth_url, params=eth_params)
            
            if eth_response.status_code != 200:
                print(f"ETH API Error: {eth_response.status_code} - {eth_response.text}")
                return pd.DataFrame()
                
            eth_data = eth_response.json()
            print(f"ETH API Response keys: {list(eth_data.keys())}")
            
            # Process data
            btc_df = pd.DataFrame(btc_data['market_caps'], columns=['timestamp', 'btc_market_cap'])
            btc_df['timestamp'] = pd.to_datetime(btc_df['timestamp'], unit='ms')
            
            eth_df = pd.DataFrame(eth_data['market_caps'], columns=['timestamp', 'eth_market_cap'])
            eth_df['timestamp'] = pd.to_datetime(eth_df['timestamp'], unit='ms')
            
            # Merge data
            market_cap_df = pd.merge(btc_df, eth_df, on='timestamp', how='inner')
            market_cap_df['eth_btc_market_cap_ratio'] = market_cap_df['eth_market_cap'] / market_cap_df['btc_market_cap']
            market_cap_df['btc_eth_market_cap_ratio'] = market_cap_df['btc_market_cap'] / market_cap_df['eth_market_cap']
            market_cap_df.set_index('timestamp', inplace=True)
            
            # Data is already filtered to the requested time range by the API
            
            return market_cap_df
            
        except Exception as e:
            print(f"Error fetching historical market cap data: {e}")
            return pd.DataFrame()

    def load_local_market_cap_data(self, filename: str = "../../crypto_data_2025-07-03.json") -> Dict:
        """
        Load market cap data from local JSON file
        
        Args:
            filename: Path to the JSON file with crypto data
            
        Returns:
            Dictionary with BTC and ETH market cap data
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            btc_data = next((item for item in data if item['ticker'] == 'BTC'), None)
            eth_data = next((item for item in data if item['ticker'] == 'ETH'), None)
            
            if btc_data and eth_data:
                return {
                    'btc_market_cap': btc_data['market_cap'],
                    'eth_market_cap': eth_data['market_cap'],
                    'eth_btc_market_cap_ratio': eth_data['market_cap'] / btc_data['market_cap'],
                    'btc_price': btc_data['current_price'],
                    'eth_price': eth_data['current_price'],
                    'btc_supply': btc_data['circulating_supply'],
                    'eth_supply': eth_data['circulating_supply']
                }
            else:
                return None
                
        except Exception as e:
            print(f"Error loading local market cap data: {e}")
            return None

    def create_comprehensive_chart(self, days: int = 365, save_chart: bool = True) -> None:
        """
        Create a comprehensive ETH/BTC analysis chart with both price and market cap ratios
        
        Args:
            days: Number of days of historical data (default: 365 = max for free tier)
            save_chart: Whether to save the chart as PNG
        """
        # Get historical price data
        print("Fetching historical price data...")
        eth_btc_price_df = self.get_historical_ohlcv('ETH/BTC', '1d', days)
        btc_usd_df = self.get_historical_ohlcv('BTC/USDT', '1d', days)
        eth_usd_df = self.get_historical_ohlcv('ETH/USDT', '1d', days)
        
        # Get historical market cap data
        print("Fetching historical market cap data...")
        market_cap_df = self.get_historical_market_cap_data(days)
        
        # Get current data
        print("Fetching current market data...")
        current_data = self.get_current_market_data()
        
        # Load local data for comparison
        local_data = self.load_local_market_cap_data()
        
        if eth_btc_price_df.empty:
            print("Unable to fetch price data for charting")
            return
            
        if market_cap_df.empty:
            print("Warning: Historical market cap data unavailable, creating simplified chart...")
            # Create simplified chart with just price data
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
            fig.suptitle('ETH vs BTC Analysis - Price Data Only (Historical Market Cap Data Unavailable)', fontsize=16, fontweight='bold')
        else:
            # Create 3-panel chart: Price Ratio, USD Prices, Market Caps with Ratio Overlay
            fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(24, 8))
            fig.suptitle(f'ETH vs BTC Analysis - Market Cap Ratio Insights (Last {len(market_cap_df)} Days)', fontsize=16, fontweight='bold')
        
        # Chart creation is now handled above based on data availability
        
        # Chart 1: ETH/BTC Price Ratio
        ax1.plot(eth_btc_price_df.index, eth_btc_price_df['close'], 
                color='purple', linewidth=2, label='ETH/BTC Price Ratio')
        ax1.set_title('ETH/BTC Price Ratio', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price Ratio', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Add current price ratio annotation
        if current_data:
            current_price_ratio = current_data['eth_btc_price_ratio']
            ax1.axhline(y=current_price_ratio, color='red', linestyle='--', alpha=0.7)
            ax1.text(0.02, 0.98, f'Current: {current_price_ratio:.6f}', 
                    transform=ax1.transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        # Chart 2: BTC and ETH USD Prices
        ax2_twin = ax2.twinx()
        
        line1 = ax2.plot(btc_usd_df.index, btc_usd_df['close'], 
                        color='orange', linewidth=2, label='BTC Price (USD)')
        line2 = ax2_twin.plot(eth_usd_df.index, eth_usd_df['close'], 
                             color='blue', linewidth=2, label='ETH Price (USD)')
        
        ax2.set_title('BTC and ETH USD Prices', fontsize=14, fontweight='bold')
        ax2.set_ylabel('BTC Price (USD)', fontsize=12, color='orange')
        ax2_twin.set_ylabel('ETH Price (USD)', fontsize=12, color='blue')
        ax2.tick_params(axis='y', labelcolor='orange')
        ax2_twin.tick_params(axis='y', labelcolor='blue')
        ax2.grid(True, alpha=0.3)
        
        # Combine legends
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Chart 3: Market Cap Values with ETH/BTC Ratio Overlay (only if market cap data available)
        if not market_cap_df.empty:
            # Left y-axis: BTC Market Cap
            ax3.plot(market_cap_df.index, market_cap_df['btc_market_cap'] / 1e12, 
                    color='orange', linewidth=2.5, label='BTC Market Cap (T USD)')
            
            # First twin y-axis: ETH Market Cap  
            ax3_twin1 = ax3.twinx()
            ax3_twin1.plot(market_cap_df.index, market_cap_df['eth_market_cap'] / 1e12,
                          color='blue', linewidth=2.5, label='ETH Market Cap (T USD)')
            
            # Second twin y-axis: ETH/BTC Market Cap Ratio
            ax3_twin2 = ax3.twinx()
            ax3_twin2.spines['right'].set_position(('outward', 60))  # Offset the second twin axis
            ax3_twin2.plot(market_cap_df.index, market_cap_df['eth_btc_market_cap_ratio'],
                          color='purple', linewidth=3, alpha=0.8, linestyle='--', 
                          label='ETH/BTC Market Cap Ratio')
            
            ax3.set_title('Market Caps with ETH/BTC Ratio Overlay', fontsize=14, fontweight='bold')
            ax3.set_ylabel('BTC Market Cap (Trillion USD)', fontsize=12, color='orange')
            ax3_twin1.set_ylabel('ETH Market Cap (Trillion USD)', fontsize=12, color='blue')
            ax3_twin2.set_ylabel('ETH/BTC Ratio', fontsize=12, color='purple')
            
            ax3.tick_params(axis='y', labelcolor='orange')
            ax3_twin1.tick_params(axis='y', labelcolor='blue')
            ax3_twin2.tick_params(axis='y', labelcolor='purple')
            ax3.grid(True, alpha=0.3)
            
            # Combine all legends
            lines1, labels1 = ax3.get_legend_handles_labels()
            lines2, labels2 = ax3_twin1.get_legend_handles_labels()
            lines3, labels3 = ax3_twin2.get_legend_handles_labels()
            ax3.legend(lines1 + lines2 + lines3, labels1 + labels2 + labels3, loc='upper left')
            
            # Add current ratio annotation
            if current_data:
                current_mc_ratio = current_data['eth_btc_market_cap_ratio']
                ax3_twin2.axhline(y=current_mc_ratio, color='purple', linestyle=':', alpha=0.8)
                ax3.text(0.02, 0.98, f'Current ETH/BTC Ratio: {current_mc_ratio:.4f}', 
                        transform=ax3.transAxes, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='plum', alpha=0.7))
        
        # Format x-axes for all charts
        axes_to_format = [ax1, ax2]
        if not market_cap_df.empty:
            axes_to_format.append(ax3)
            
        for ax in axes_to_format:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Add summary statistics text box
        if current_data and local_data:
            stats_text = f"""Current Market Data ({len(market_cap_df)} Days Historical):
BTC Price: ${current_data['btc_price_usd']:,.0f}
ETH Price: ${current_data['eth_price_usd']:,.0f}
ETH/BTC Price: {current_data['eth_btc_price_ratio']:.6f}

Market Cap Ratios:
BTC Market Cap: ${current_data['btc_market_cap']/1e12:.2f}T
ETH Market Cap: ${current_data['eth_market_cap']/1e12:.2f}T
ETH/BTC MC Ratio: {current_data['eth_btc_market_cap_ratio']:.4f}
BTC/ETH MC Ratio: {1/current_data['eth_btc_market_cap_ratio']:.2f}

Local Data Comparison:
ETH/BTC MC Ratio: {local_data['eth_btc_market_cap_ratio']:.4f}
BTC/ETH MC Ratio: {1/local_data['eth_btc_market_cap_ratio']:.2f}"""
            
            fig.text(0.02, 0.02, stats_text, fontsize=10, 
                    bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8),
                    verticalalignment='bottom')
        elif local_data:
            # Show local data only if current data unavailable
            stats_text = f"""Local Data (2025-07-03):
ETH/BTC MC Ratio: {local_data['eth_btc_market_cap_ratio']:.4f}
BTC/ETH MC Ratio: {1/local_data['eth_btc_market_cap_ratio']:.2f}
BTC Price: ${local_data['btc_price']:,.0f}
ETH Price: ${local_data['eth_price']:,.0f}

Note: Live API data unavailable"""
            
            fig.text(0.02, 0.02, stats_text, fontsize=10, 
                    bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8),
                    verticalalignment='bottom')
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.90, bottom=0.15, right=0.85)
        
        if save_chart:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"eth_btc_market_cap_analysis_{timestamp}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Chart saved as: {filename}")
        
        plt.show()

    def get_real_time_data_stream(self, duration_minutes: int = 60) -> None:
        """
        Stream real-time ETH/BTC market cap ratio data
        
        Args:
            duration_minutes: How long to stream data (in minutes)
        """
        print(f"Starting real-time data stream for {duration_minutes} minutes...")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        data_points = []
        
        try:
            while time.time() < end_time:
                current_data = self.get_current_market_data()
                
                if current_data:
                    data_points.append(current_data)
                    
                    print(f"[{current_data['timestamp'].strftime('%H:%M:%S')}] "
                          f"ETH/BTC Price: {current_data['eth_btc_price_ratio']:.6f} | "
                          f"Market Cap Ratio: {current_data['eth_btc_market_cap_ratio']:.4f}")
                
                time.sleep(60)  # Update every minute
                
        except KeyboardInterrupt:
            print("\nReal-time stream stopped by user")
        
        if data_points:
            # Create a quick chart of the real-time data
            df = pd.DataFrame(data_points)
            df.set_index('timestamp', inplace=True)
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
            
            ax1.plot(df.index, df['eth_btc_price_ratio'], 'b-', linewidth=2)
            ax1.set_title('Real-Time ETH/BTC Price Ratio')
            ax1.set_ylabel('Price Ratio')
            ax1.grid(True)
            
            ax2.plot(df.index, df['eth_btc_market_cap_ratio'], 'r-', linewidth=2)
            ax2.set_title('Real-Time ETH/BTC Market Cap Ratio')
            ax2.set_ylabel('Market Cap Ratio')
            ax2.grid(True)
            
            plt.tight_layout()
            plt.show()

def main():
    """
    Main function to demonstrate the ETH/BTC Market Cap Analyzer
    """
    print("ETH/BTC Market Cap Analysis Tool")
    print("=" * 50)
    
    # Initialize the analyzer
    analyzer = ETHBTCMarketCapAnalyzer()
    
    # Get current market data
    current_data = analyzer.get_current_market_data()
    if current_data:
        print(f"\nCurrent Market Data:")
        print(f"BTC Price: ${current_data['btc_price_usd']:,.2f}")
        print(f"ETH Price: ${current_data['eth_price_usd']:,.2f}")
        print(f"ETH/BTC Price Ratio: {current_data['eth_btc_price_ratio']:.6f}")
        print(f"ETH/BTC Market Cap Ratio: {current_data['eth_btc_market_cap_ratio']:.4f}")
    
    # Create comprehensive analysis chart
    print("\nGenerating comprehensive analysis chart...")
    # Try to get data from 2021 (will be limited to 365 days by API)
    analyzer.create_comprehensive_chart(days=1460, save_chart=True)  # ~4 years from 2021
    
    # Option for real-time streaming
    user_input = input("\nWould you like to start real-time data streaming? (y/n): ")
    if user_input.lower() == 'y':
        duration = int(input("Enter duration in minutes (default 30): ") or "30")
        analyzer.get_real_time_data_stream(duration)

if __name__ == "__main__":
    main() 