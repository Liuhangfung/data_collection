#!/usr/bin/env python3

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directories to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
assets_dir = os.path.dirname(current_dir)
src_dir = os.path.dirname(assets_dir)
project_root = os.path.dirname(src_dir)

sys.path.append(src_dir)
sys.path.append(project_root)

# Import data fetchers
from assets.crypto.market.get_coingecko_top10 import get_coingecko_top10

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, will use system environment variables
    pass

# Supabase functionality integrated directly
SUPABASE_AVAILABLE = True
try:
    from supabase import create_client, Client
except ImportError:
    print("⚠️  Supabase package not installed. Install with: pip install supabase")
    SUPABASE_AVAILABLE = False

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        # logging.FileHandler('combine_all_assets.log', encoding='utf-8'),  # Disabled to prevent log file generation
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AssetCombiner:
    def __init__(self):
        self.supabase = None
        
        if SUPABASE_AVAILABLE:
            try:
                # Get Supabase credentials from environment
                supabase_url = os.environ.get('SUPABASE_URL')
                supabase_key = os.environ.get('SUPABASE_ANON_KEY')
                
                if not supabase_url or not supabase_key:
                    logger.error("SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required")
                    self.supabase = None
                else:
                    # Create Supabase client directly
                    self.supabase = create_client(supabase_url, supabase_key)
                    logger.info("Supabase connection configured successfully")
                    
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase client: {e}")
                self.supabase = None
        else:
            logger.warning("Supabase package not available")
            
        # Emergency currency conversion rates (backup if Go conversion fails)
        self.emergency_rates = {
            'IDR': 0.000065,  # Indonesian Rupiah
            'CLP': 0.0010,    # Chilean Peso
            'SAR': 0.267,     # Saudi Riyal
            'ILS': 0.27,      # Israeli Shekel
            'COP': 0.00025,   # Colombian Peso
            'PEN': 0.27,      # Peruvian Sol
            'EGP': 0.020,     # Egyptian Pound
            'TRY': 0.029,     # Turkish Lira
            'RUB': 0.010,     # Russian Ruble
            'KRW': 0.00075,   # South Korean Won
            'INR': 0.012,     # Indian Rupee
            'BRL': 0.18,      # Brazilian Real
            'MXN': 0.058,     # Mexican Peso
            'ZAR': 0.055,     # South African Rand
            'THB': 0.029,     # Thai Baht
            'MYR': 0.22,      # Malaysian Ringgit
            'PHP': 0.018,     # Philippine Peso
            'VND': 0.000040,  # Vietnamese Dong
            'TWD': 0.031,     # Taiwan Dollar
            'HKD': 0.128,     # Hong Kong Dollar
            'SGD': 0.74,      # Singapore Dollar
            'JPY': 0.0067,    # Japanese Yen
            'CNY': 0.14,      # Chinese Yuan
            'AUD': 0.64,      # Australian Dollar
            'CAD': 0.74,      # Canadian Dollar
            'EUR': 1.08,      # Euro
            'GBP': 1.26,      # British Pound
            'ARS': 0.0010,    # Argentine Peso (~1000 ARS = 1 USD)
        }
        
    def detect_currency_from_symbol(self, symbol: str, country: str = '') -> str:
        """Detect currency from stock symbol or country"""
        symbol_upper = symbol.upper()
        country_upper = country.upper()
        
        # Symbol-based detection (most reliable)
        if symbol_upper.endswith('.JK') or country_upper == 'ID':
            return 'IDR'
        elif symbol_upper.endswith('.SN') or country_upper == 'CL':
            return 'CLP'
        elif symbol_upper.endswith('.SR') or country_upper == 'SA':
            return 'SAR'
        elif symbol_upper.endswith('.TA') or country_upper == 'IL':
            return 'ILS'
        elif symbol_upper.endswith('.BA') or country_upper == 'AR':
            return 'ARS'
        elif symbol_upper.endswith('.L') or country_upper == 'GB':
            return 'GBP'
        elif symbol_upper.endswith('.JO') or country_upper == 'ZA':
            return 'ZAR'
        elif symbol_upper.endswith('.CO') or country_upper == 'CO':
            return 'COP'
        elif symbol_upper.endswith('.LM') or country_upper == 'PE':
            return 'PEN'
        elif symbol_upper.endswith('.EG') or country_upper == 'EG':
            return 'EGP'
        elif symbol_upper.endswith('.IS') or country_upper == 'TR':
            return 'TRY'
        elif symbol_upper.endswith('.ME') or country_upper == 'RU':
            return 'RUB'
        elif symbol_upper.endswith('.KS') or symbol_upper.endswith('.KQ') or country_upper == 'KR':
            return 'KRW'
        elif symbol_upper.endswith('.BO') or symbol_upper.endswith('.NS') or country_upper == 'IN':
            return 'INR'
        elif symbol_upper.endswith('.SA') or country_upper == 'BR':
            return 'BRL'
        elif symbol_upper.endswith('.MX') or country_upper == 'MX':
            return 'MXN'
        elif symbol_upper.endswith('.BK') or country_upper == 'TH':
            return 'THB'
        elif symbol_upper.endswith('.KL') or country_upper == 'MY':
            return 'MYR'
        elif symbol_upper.endswith('.PS') or country_upper == 'PH':
            return 'PHP'
        elif symbol_upper.endswith('.VN') or country_upper == 'VN':
            return 'VND'
        elif symbol_upper.endswith('.TW') or country_upper == 'TW':
            return 'TWD'
        elif symbol_upper.endswith('.HK') or country_upper == 'HK':
            return 'HKD'
        elif symbol_upper.endswith('.SI') or country_upper == 'SG':
            return 'SGD'
        elif symbol_upper.endswith('.T') or country_upper == 'JP':
            return 'JPY'
        elif symbol_upper.endswith('.SS') or symbol_upper.endswith('.SZ') or country_upper == 'CN':
            return 'CNY'
        elif symbol_upper.endswith('.AX') or country_upper == 'AU':
            return 'AUD'
        elif symbol_upper.endswith('.TO') or country_upper == 'CA':
            return 'CAD'
        elif symbol_upper.endswith('.PA') or symbol_upper.endswith('.DE') or country_upper in ['FR', 'DE', 'IT', 'ES', 'NL', 'BE', 'AT', 'PT', 'GR', 'FI', 'IE']:
            return 'EUR'
        else:
            return 'USD'
    
    def validate_and_fix_market_cap(self, asset: Dict) -> Dict:
        """Validate and fix market cap values with emergency currency conversion"""
        
        symbol = asset.get('ticker', '')
        country = asset.get('country', '')
        data_source = asset.get('data_source', '')
        
        # Skip crypto and commodities (they should be in USD already)
        if asset.get('asset_type') in ['crypto', 'commodity']:
            return asset
        
        # IMPORTANT: For FMP data (from Go programs), market_cap is already in USD
        if data_source == 'FMP':
            # Go programs already converted to USD - use market_cap field directly
            market_cap = asset.get('market_cap', 0)
            logger.debug(f"Using pre-converted USD market cap for {symbol}: ${market_cap/1e9:.1f}B")
        else:
            # For non-FMP sources, apply emergency currency conversion if needed
            market_cap = asset.get('market_cap', 0)
            
            # Emergency currency conversion ONLY for non-FMP sources
            if market_cap > 1e12:  # > $1 trillion - likely foreign currency
                detected_currency = self.detect_currency_from_symbol(symbol, country)
                
                if detected_currency != 'USD' and detected_currency in self.emergency_rates:
                    original_market_cap = market_cap
                    market_cap = market_cap * self.emergency_rates[detected_currency]
                    
                    logger.warning(f"Emergency currency conversion: {symbol} | {original_market_cap/1e12:.1f}T {detected_currency} -> ${market_cap/1e9:.1f}B USD")
                    
                    # Update all USD values for non-FMP sources
                    asset['current_price'] = asset.get('current_price', 0) * self.emergency_rates[detected_currency]
                    asset['previous_close'] = asset.get('previous_close', 0) * self.emergency_rates[detected_currency]
        
        # Update the market_cap field with the USD value (whether pre-converted or converted)
        asset['market_cap'] = market_cap
        
        # Cap market cap at $4 trillion (even Apple is ~$3.5T)
        if market_cap > 4e12:
            logger.warning(f"Capping {symbol} market cap from ${market_cap/1e12:.1f}T to $4.0T")
            asset['market_cap'] = 4e12
        
        # Skip stocks with unrealistic market caps (likely corrupted data)
        if market_cap > 10e12:
            logger.error(f"Removing {symbol}: Market cap too large (${market_cap/1e12:.1f}T)")
            return None
        
        return asset
    
    def run_all_country_go_files(self) -> List[Dict]:
        """Run all country-specific Go files and collect their Supabase-formatted output"""
        
        # Define all country Go files
        country_files = [
            'fmp_us.go',       # United States
            'fmp_ca.go',       # Canada  
            'fmp_hk.go',       # Hong Kong
            'fmp_pa.go',       # France (Paris)
            'fmp_uk.go',       # United Kingdom
            'fmp_ge.go',       # Germany
            'fmp_sw.go',       # Switzerland
            'fmp_jp.go',       # Japan
            'fmp_kr.go',       # Korea
            'fmp_sa.go',       # Saudi Arabia
            'fmp_nl.go',       # Netherlands
            'fmp_commodity.go', # Global Commodities
        ]
        
        # Corresponding Supabase output files
        supabase_files = [
            'us_supabase.json',
            'ca_supabase.json', 
            'hk_supabase.json',
            'pa_supabase.json',
            'uk_supabase.json',
            'ge_supabase.json',
            'sw_supabase.json',
            'jp_supabase.json',
            'kr_supabase.json',
            'sa_supabase.json',
            'nl_supabase.json',
            'commodity_supabase.json',
        ]
        
        all_stock_data = []
        
        # Run each Go file
        for i, go_file in enumerate(country_files):
            country_name = go_file.replace('fmp_', '').replace('.go', '').upper()
            supabase_file = supabase_files[i]
            
            logger.info(f"🚀 Running {country_name} stock analysis...")
            
            try:
                # Get the directory where this script is located
                script_dir = os.path.dirname(os.path.abspath(__file__))
                # Go up two levels from assets/utils/ to reach backend/
                backend_dir = os.path.join(script_dir, '..', '..')
                # Construct path to Go file from backend directory  
                go_file_path = os.path.join('assets', 'stocks', go_file)
                
                # Set environment to use UTF-8 to handle encoding issues
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                
                result = subprocess.run(['go', 'run', go_file_path], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE,
                                      text=True, timeout=900,  # Increased to 15 minutes for US large dataset
                                      encoding='utf-8', errors='ignore',
                                      env=env, cwd=backend_dir)
                
                if result.returncode == 0:
                    logger.info(f"✅ {country_name} analysis completed successfully")
                    
                    # Read the Supabase-formatted output and clean up immediately
                    # JSON files are created in the assets/stocks directory
                    json_file_path = os.path.join(backend_dir, 'assets', 'stocks', supabase_file)
                    
                    if os.path.exists(json_file_path):
                        try:
                            with open(json_file_path, 'r', encoding='utf-8') as f:
                                country_data = json.load(f)
                                all_stock_data.extend(country_data)
                                logger.info(f"📊 Loaded {len(country_data)} {country_name} stocks from {supabase_file}")
                            
                            # Clean up JSON file immediately after reading
                            os.remove(json_file_path)
                            logger.debug(f"🗑️ Cleaned up {supabase_file}")
                            
                        except Exception as e:
                            logger.error(f"❌ Failed to read {supabase_file}: {e}")
                    else:
                        logger.warning(f"⚠️ {supabase_file} not found for {country_name} at {json_file_path}")
                        
                else:
                    logger.error(f"❌ {country_name} Go execution failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                logger.error(f"❌ {country_name} Go execution timed out (5 minutes)")
            except Exception as e:
                logger.error(f"❌ Failed to run {country_name} Go file: {e}")
                
            # Small delay between executions to avoid overwhelming the API
            time.sleep(2)
            
        # Clean up any remaining rank JSON files in backend directory (not needed for Supabase)
        rank_files = ['us_rank.json', 'ca_rank.json', 'hk_rank.json', 'pa_rank.json',
                     'uk_rank.json', 'ge_rank.json', 'sw_rank.json', 'jp_rank.json',
                     'kr_rank.json', 'sa_rank.json', 'nl_rank.json', 'commodity_rank.json']
        
        # Get backend directory (calculated earlier)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.join(script_dir, '..', '..')
        
        for rank_file in rank_files:
            rank_file_path = os.path.join(backend_dir, rank_file)
            if os.path.exists(rank_file_path):
                try:
                    os.remove(rank_file_path)
                    logger.debug(f"🗑️ Cleaned up {rank_file}")
                except Exception as e:
                    logger.warning(f"Could not remove {rank_file}: {e}")
        
        logger.info(f"🌍 Total stock data collected: {len(all_stock_data)} assets from all countries")
        logger.info("🗑️ JSON files cleaned up - direct Supabase storage only")
        return all_stock_data
    
    def advanced_deduplication(self, assets: List[Dict]) -> List[Dict]:
        """Advanced deduplication to handle cross-listings and same companies with different symbols"""
        import difflib
        
        # Group assets by normalized company name
        company_groups = {}
        for asset in assets:
            # Normalize company name for grouping
            name = asset.get('name', '').strip()
            if not name:
                continue
                
            # Clean up company name for better matching
            normalized_name = self.normalize_company_name(name)
            
            if normalized_name not in company_groups:
                company_groups[normalized_name] = []
            company_groups[normalized_name].append(asset)
        
        # For each group, choose the best representative
        unique_assets = []
        duplicates_removed = 0
        
        for normalized_name, group in company_groups.items():
            if len(group) == 1:
                # No duplicates, keep the asset
                unique_assets.append(group[0])
            else:
                # Multiple assets with same/similar name - choose the best one
                best_asset = self.choose_best_asset(group)
                unique_assets.append(best_asset)
                duplicates_removed += len(group) - 1
                
                # Log the deduplication
                removed_symbols = [asset.get('ticker', '') for asset in group if asset != best_asset]
                logger.info(f"🔄 Deduplicated {normalized_name}: kept {best_asset.get('ticker', '')} | removed {', '.join(removed_symbols)}")
        
        logger.info(f"🧹 Removed {duplicates_removed} duplicate assets from {len(company_groups)} company groups")
        return unique_assets
    
    def normalize_company_name(self, name: str) -> str:
        """Normalize company name for better matching"""
        import re
        
        # Convert to uppercase for case-insensitive matching
        normalized = name.upper()
        
        # Remove common corporate suffixes and variations
        suffixes_to_remove = [
            r'\s+CORPORATION$', r'\s+CORP\.?$', r'\s+INC\.?$', r'\s+LTD\.?$', 
            r'\s+LLC$', r'\s+LP$', r'\s+PLC$', r'\s+LIMITED$', r'\s+COMPANY$',
            r'\s+CO\.?$', r'\s+GROUP$', r'\s+HOLDINGS?$', r'\s+&\s+CO\.?$',
            r'\s+S\.A\.?$', r'\s+N\.V\.?$', r'\s+A\.G\.?$'
        ]
        
        for suffix in suffixes_to_remove:
            normalized = re.sub(suffix, '', normalized)
        
        # Remove extra whitespace and punctuation
        normalized = re.sub(r'[^\w\s]', ' ', normalized)  # Replace punctuation with spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()  # Normalize whitespace
        
        return normalized
    
    def is_preferred_share(self, ticker: str) -> bool:
        """Check if a ticker represents a preferred share or warrant"""
        if not ticker:
            return False
            
        ticker_upper = ticker.upper()
        
        # Check for preferred share patterns
        preferred_patterns = [
            '-P',   # JPM-PA, JPM-PB, JPM-PC, etc.
            '.P',   # Alternative format
            '-W',   # Warrants
            '.W',   # Alternative warrant format
            '-U',   # Units
            '.U',   # Alternative unit format
        ]
        
        for pattern in preferred_patterns:
            if pattern in ticker_upper:
                return True
        
        # Check for "PR" in longer symbols (but not short ones like "PR" company)
        if 'PR' in ticker_upper and len(ticker) > 4:
            return True
            
        return False
    
    def choose_best_asset(self, assets: List[Dict]) -> Dict:
        """Choose the best asset from a group of duplicates"""
        
        # First, filter out preferred shares if we have common stock alternatives
        common_stocks = [asset for asset in assets if not self.is_preferred_share(asset.get('ticker', ''))]
        
        # If we have common stocks, only consider those; otherwise use all assets
        candidates = common_stocks if common_stocks else assets
        
        # Scoring criteria for choosing the best asset
        def calculate_score(asset):
            score = 0
            
            # Strongly prefer common stock over preferred shares
            if not self.is_preferred_share(asset.get('ticker', '')):
                score += 10000  # Very high preference for common stock
            
            # Prefer higher market cap (indicates more accurate/recent data)
            market_cap = asset.get('market_cap', 0)
            score += market_cap / 1e9  # Add market cap in billions to score
            
            # Prefer higher volume (more liquid/actively traded)
            volume = asset.get('volume', 0)
            score += volume / 1e6  # Add volume in millions to score
            
            # Prefer major exchanges
            exchange = asset.get('primary_exchange', '').upper()
            major_exchanges = ['NYSE', 'NASDAQ', 'LSE', 'HKSE', 'TSX', 'XETRA', 'SIX']
            if any(major in exchange for major in major_exchanges):
                score += 100
            
            # Prefer USD pricing for easier comparison
            if asset.get('country', '') in ['US', 'USA']:
                score += 50
            
            return score
        
        # Sort by score and return the best asset
        sorted_assets = sorted(candidates, key=calculate_score, reverse=True)
        best_asset = sorted_assets[0]
        
        return best_asset
    
    def combine_all_assets(self) -> List[Dict]:
        """Combine all asset data from different sources by calling functions directly"""
        
        logger.info("🚀 Starting data collection from all sources...")
        
        # Get crypto data directly from function
        logger.info("📱 Fetching cryptocurrency data...")
        try:
            crypto_data = get_coingecko_top10()
            logger.info(f"✅ Loaded {len(crypto_data)} cryptocurrencies")
        except Exception as e:
            logger.error(f"❌ Failed to fetch crypto data: {e}")
            crypto_data = []
        
        # Get stock data by running all individual Go files
        logger.info("📊 Fetching global stock data from all countries...")
        stock_data = self.run_all_country_go_files()
        
        # If no stock data, proceed with crypto only for testing
        if not stock_data and crypto_data:
            logger.warning("No stock data found, proceeding with crypto only")
        
        # Stock data is already in Supabase format - no additional processing needed
        logger.info(f"📊 Stock data: {len(stock_data)} assets (already in Supabase format)")
        
        # Convert crypto data to Supabase format to match stock data structure
        processed_crypto = []
        for asset in crypto_data:
            supabase_crypto = {
                'symbol': asset.get('ticker', ''),
                'ticker': asset.get('ticker', ''),
                'name': asset.get('name', ''),
                'current_price': asset.get('current_price', 0),
                'previous_close': asset.get('previous_close', 0),
                'percentage_change': asset.get('percentage_change', 0),
                'market_cap': int(asset.get('market_cap', 0)),
                'volume': int(asset.get('volume', 0)),
                'circulating_supply': int(asset.get('circulating_supply', 0)) if asset.get('circulating_supply') else None,
                'primary_exchange': 'CoinGecko',
                'country': 'Global',
                'sector': 'Cryptocurrency',
                'industry': 'Digital Currency',
                'asset_type': 'crypto',
                'rank': 0,  # Will be updated after sorting
                'snapshot_date': datetime.now().strftime('%Y-%m-%d'),
                'data_source': 'CoinGecko',
                'price_raw': asset.get('current_price', 0),
                'market_cap_raw': int(asset.get('market_cap', 0)),
                'category': 'crypto',
                'image': asset.get('image', '')
            }
            processed_crypto.append(supabase_crypto)
        
        # Combine all assets (both already in Supabase format)
        all_assets = stock_data + processed_crypto
        logger.info(f"📊 Combined assets: {len(all_assets)} total (stocks: {len(stock_data)}, crypto: {len(processed_crypto)})")
        
        # Advanced deduplication: handle cross-listings and same companies
        unique_assets = self.advanced_deduplication(all_assets)
        
        logger.info(f"📊 After advanced deduplication: {len(unique_assets)} unique assets")
        
        # Skip validation for stock data (already validated by Go), only validate crypto if needed
        validated_assets = []
        for asset in unique_assets:
            if asset.get('data_source') == 'FMP':
                # Stock data from Go files is already validated and in correct format
                validated_assets.append(asset)
            else:
                # Validate crypto data
                validated_asset = self.validate_and_fix_market_cap(asset)
                if validated_asset:
                    validated_assets.append(validated_asset)
        
        logger.info(f"📊 After validation: {len(validated_assets)} valid assets")
        
        # Sort by market cap (descending)
        validated_assets.sort(key=lambda x: x.get('market_cap', 0), reverse=True)
        
        # Limit to top 500 assets only (no JSON storage)
        top_assets = validated_assets[:500]
        logger.info(f"🏆 Limited to top 500 assets (from {len(validated_assets)} total) for Supabase storage")
        
        # Add ranking and metadata
        for i, asset in enumerate(top_assets):
            asset['rank'] = i + 1
            asset['snapshot_date'] = datetime.now().strftime('%Y-%m-%d')
            
            # Add missing fields with defaults
            asset.setdefault('circulating_supply', None)
            asset.setdefault('price_raw', asset.get('current_price', 0))
            asset.setdefault('market_cap_raw', asset.get('market_cap', 0))
            asset.setdefault('category', 'Global')
            
            # Log the data source for top assets to verify correct processing
            if i < 10:  # Top 10 assets
                source = asset.get('data_source', 'Unknown')
                country = asset.get('country', 'Unknown')
                logger.debug(f"Top {i+1}: {asset.get('ticker')} | Source: {source} | Country: {country}")
        
        return top_assets
    
    def save_to_json(self, data: List[Dict], filename: str = 'all_assets_combined.json'):
        """Save combined data to JSON file with proper UTF-8 encoding"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(data)} assets to {filename}")
        except Exception as e:
            logger.error(f"Error saving to {filename}: {e}")
    
    def prepare_for_database(self, asset: Dict) -> Dict:
        """Prepare asset data for database insertion with overflow protection"""
        
        # PostgreSQL bigint max value: 9,223,372,036,854,775,807
        MAX_BIGINT = 9_223_372_036_854_775_807
        
        def safe_number(value, max_val=MAX_BIGINT, as_int=False):
            if value is None:
                return None
            try:
                num = float(value)
                if num > max_val:
                    num = max_val
                return int(num) if as_int else num
            except (ValueError, TypeError):
                return None
        
        # Map fields and ensure safe values
        db_asset = {
            'symbol': str(asset.get('ticker', ''))[:50],
            'ticker': str(asset.get('ticker', ''))[:50],
            'name': str(asset.get('name', ''))[:200],
            'current_price': safe_number(asset.get('current_price', 0)),
            'previous_close': safe_number(asset.get('previous_close', 0)),
            'percentage_change': safe_number(asset.get('percentage_change', 0)),
            'market_cap': safe_number(asset.get('market_cap', 0), as_int=True),
            'volume': safe_number(asset.get('volume', 0), as_int=True),
            'circulating_supply': safe_number(asset.get('circulating_supply'), as_int=True),
            'primary_exchange': str(asset.get('primary_exchange', ''))[:50],
            'country': str(asset.get('country', ''))[:50],
            'sector': str(asset.get('sector', ''))[:100],
            'industry': str(asset.get('industry', ''))[:100],
            'asset_type': str(asset.get('asset_type', 'unknown'))[:50],
            'image': str(asset.get('image', ''))[:500],
            'rank': int(asset.get('rank', 0)),
            'snapshot_date': asset.get('snapshot_date', datetime.now().strftime('%Y-%m-%d')),
            'price_raw': safe_number(asset.get('price_raw', 0)),
            'market_cap_raw': safe_number(asset.get('market_cap_raw', 0), as_int=True),
            'category': str(asset.get('category', ''))[:50],
            'data_source': str(asset.get('data_source', ''))[:50],
        }
        
        return db_asset
    
    def upload_to_supabase(self, assets: List[Dict], clear_existing=False):
        """Upload assets to Supabase with upsert handling for duplicates"""
        if not self.supabase:
            logger.warning("No Supabase connection configured")
            return
        

        
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            if clear_existing:
                # Clear only today's data, not all historical data
                logger.info(f"Clearing existing data for today ({today})...")
                
                # First check if data exists for today
                existing = self.supabase.table('assets').select('id').eq('snapshot_date', today).limit(1).execute()
                
                if existing.data:
                    # Delete existing data for today
                    result = self.supabase.table('assets').delete().eq('snapshot_date', today).execute()
                    logger.info(f"Deleted existing records for today")
                else:
                    logger.info("No existing records found for today")
            else:
                logger.info("Using upsert mode (update existing, insert new)")
            
            # Prepare data for database
            db_assets = []
            for asset in assets:
                db_asset = self.prepare_for_database(asset)
                db_assets.append(db_asset)
            
            # Upload in batches with upsert
            batch_size = 100
            total_processed = 0
            
            for i in range(0, len(db_assets), batch_size):
                batch = db_assets[i:i+batch_size]
                
                try:
                    if clear_existing:
                        # Use regular insert when database was cleared
                        result = self.supabase.table('assets').insert(batch).execute()
                    else:
                        # Try upsert first, fall back to insert if constraint doesn't exist
                        try:
                            logger.info(f"Attempting upsert for batch {i//batch_size + 1} with {len(batch)} assets")
                            result = self.supabase.table('assets').upsert(batch, on_conflict='symbol,snapshot_date').execute()
                            logger.info(f"Upsert successful for batch {i//batch_size + 1}")
                        except Exception as upsert_error:
                            error_code = str(upsert_error)
                            logger.warning(f"Upsert failed: {error_code}")
                            
                            if '42P10' in error_code:
                                # No unique constraint exists, use regular insert
                                logger.info("Error 42P10: No unique constraint found, switching to insert mode")
                                try:
                                    result = self.supabase.table('assets').insert(batch).execute()
                                    logger.info(f"Insert successful for batch {i//batch_size + 1}")
                                except Exception as insert_error:
                                    logger.error(f"Insert also failed: {insert_error}")
                                    raise insert_error
                            elif '23505' in error_code:
                                logger.info("Error 23505: Duplicate key constraint violation (this should not happen with upsert)")
                                raise upsert_error
                            else:
                                logger.error(f"Unknown error during upsert: {error_code}")
                                raise upsert_error
                    
                    if result.data:
                        total_processed += len(batch)
                        logger.info(f"Processed batch {i//batch_size + 1} ({len(batch)} assets)")
                        
                except Exception as batch_error:
                    # If batch fails, try individual inserts
                    logger.warning(f"Batch operation failed, trying individual inserts: {batch_error}")
                    successful = 0
                    for individual_asset in batch:
                        try:
                            if clear_existing:
                                individual_result = self.supabase.table('assets').insert([individual_asset]).execute()
                            else:
                                try:
                                    individual_result = self.supabase.table('assets').upsert([individual_asset], on_conflict='symbol,snapshot_date').execute()
                                except Exception as upsert_error:
                                    if '42P10' in str(upsert_error):
                                        # No unique constraint exists, use regular insert
                                        individual_result = self.supabase.table('assets').insert([individual_asset]).execute()
                                    else:
                                        raise upsert_error
                            if individual_result.data:
                                successful += 1
                        except Exception as individual_error:
                            logger.warning(f"Failed to insert {individual_asset.get('ticker', 'unknown')}: {individual_error}")
                    logger.info(f"Successfully inserted {successful}/{len(batch)} assets individually")
                    total_processed += successful
                
                # Rate limiting
                import time
                time.sleep(0.1)
            
            logger.info(f"Successfully processed {total_processed} assets to Supabase")
            
        except Exception as e:
            error_msg = str(e)
            if "duplicate key value violates unique constraint" in error_msg and "snapshot_date" in error_msg:
                today = datetime.now().strftime('%Y-%m-%d')
                logger.info(f"Data for today ({today}) already exists in Supabase")
                logger.info("To replace today's data only, set CLEAR_EXISTING_DATA=true in your .env file")
                logger.info("Note: This will only clear today's data, not historical data")
            else:
                logger.error(f"Error uploading to Supabase: {e}")
                logger.warning("Supabase upload failed")
    
    def print_summary(self, assets: List[Dict]):
        """Print summary of the combined assets"""
        if not assets:
            logger.info("No assets to summarize")
            return
        
        logger.info(f"\nSUMMARY:")
        logger.info(f"   Total assets processed: {len(assets)}")
        
        # Data source breakdown
        data_sources = {}
        countries = {}
        for asset in assets:
            data_source = asset.get('data_source', 'unknown')
            data_sources[data_source] = data_sources.get(data_source, 0) + 1
            
            # Track countries for FMP data
            if data_source == 'FMP':
                country = asset.get('country', 'Unknown')
                countries[country] = countries.get(country, 0) + 1
        
        logger.info(f"   Data source breakdown:")
        for source, count in sorted(data_sources.items()):
            logger.info(f"      {source}: {count}")
            
        # Show country breakdown for FMP data
        if countries:
            logger.info(f"   FMP countries breakdown:")
            for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"      {country}: {count} stocks")
        
        # Asset type breakdown
        asset_types = {}
        for asset in assets:
            asset_type = asset.get('asset_type', 'unknown')
            asset_types[asset_type] = asset_types.get(asset_type, 0) + 1
        
        logger.info(f"   Asset breakdown:")
        for asset_type, count in sorted(asset_types.items()):
            logger.info(f"      {asset_type}: {count}")
        
        # Top 10 assets
        logger.info(f"   Top 10 assets by market cap:")
        for i, asset in enumerate(assets[:10]):
            market_cap = asset.get('market_cap', 0)
            if market_cap >= 1e12:
                cap_str = f"${market_cap/1e12:.1f}T"
            else:
                cap_str = f"${market_cap/1e9:.1f}B"
            logger.info(f"     {i+1:2d}. {asset.get('ticker', 'N/A'):<12} | {asset.get('name', 'Unknown'):<30} | {cap_str}")
        
        # Check for major stocks
        major_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'LVMUY', 'RHHVF']
        found_in_top_50 = []
        for asset in assets[:50]:
            if asset.get('ticker') in major_stocks:
                found_in_top_50.append(asset.get('ticker'))
        
        if len(found_in_top_50) >= 8:
            logger.info(f"   Found {len(found_in_top_50)} major stocks in top 50: {', '.join(found_in_top_50)}")
        else:
            logger.info(f"   Major stocks not found in top 50")
    
    def run(self):
        """Main execution method"""
        logger.info("Starting Global Asset Ranking System")
        
        # Combine all assets by calling functions directly
        combined_assets = self.combine_all_assets()
        
        if not combined_assets:
            logger.error("No assets to process")
            return
        
        # No JSON file generation - direct Supabase storage only
        
        # Upload to Supabase (default: clear today's data for fresh daily updates)
        clear_existing = os.environ.get('CLEAR_EXISTING_DATA', 'true').lower() == 'true'
        if clear_existing:
            today = datetime.now().strftime('%Y-%m-%d')
            logger.info(f"🗑️ Will delete existing data for today ({today}) before fresh update (runs every 4 hours)")
        else:
            logger.info("🔄 Using upsert mode (keeping existing data) - set CLEAR_EXISTING_DATA=false if intentional")
        self.upload_to_supabase(combined_assets, clear_existing=clear_existing)
        
        # Print summary
        self.print_summary(combined_assets)
        
        logger.info("Global Asset Ranking System completed successfully!")

def combine_all_assets():
    """
    Main function to combine all asset data sources.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        combiner = AssetCombiner()
        combiner.run()
        return True
    except Exception as e:
        logger.error(f"Error in combine_all_assets: {e}")
        return False

if __name__ == "__main__":
    combiner = AssetCombiner()
    combiner.run() 