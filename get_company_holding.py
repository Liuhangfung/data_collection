#!/usr/bin/env python3
"""
Top Bitcoin Treasury Public Companies Scraper
Gets only the top public companies with Bitcoin treasury holdings
"""

import requests
from bs4 import BeautifulSoup

import re
from datetime import datetime, date
import logging
import os
from supabase import create_client, Client
from decimal import Decimal
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TopBitcoinTreasuryCompaniesScraper:
    def __init__(self, token_url=None):
        self.base_url = "https://bitcointreasuries.net/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.top_companies = []
        self.token_url = token_url
        
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.supabase = None
        
        if supabase_url and supabase_key:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                logger.info("Supabase client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase: {e}")
    
    def authenticate(self):
        """Authenticate using JWT token URL"""
        if not self.token_url:
            logger.warning("No token URL - limited data access")
            return False
        
        try:
            response = self.session.get(self.token_url, timeout=10)
            if response.status_code == 200:
                logger.info("Authentication successful!")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def parse_number(self, text):
        """Parse numeric values from text"""
        if not text or text.strip() in ['-', '', 'N/A', '?', '—']:
            return 0.0
        
        text = str(text).strip().replace(',', '').replace('$', '').replace('₿', '').replace('%', '')
        
        # Handle B, M, K suffixes
        if 'B' in text.upper():
            match = re.search(r'([\d.-]+)', text)
            return float(match.group(1)) * 1_000_000_000 if match else 0.0
        elif 'M' in text.upper():
            match = re.search(r'([\d.-]+)', text)
            return float(match.group(1)) * 1_000_000 if match else 0.0
        elif 'K' in text.upper():
            match = re.search(r'([\d.-]+)', text)
            return float(match.group(1)) * 1_000 if match else 0.0
        
        # Regular numbers
        match = re.search(r'([\d.-]+)', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return 0.0
        return 0.0
    
    def clean_company_name(self, name):
        """Clean company name"""
        if not name:
            return ""
        
        name = str(name).strip()
        # Remove rank numbers from beginning
        name = re.sub(r'^\d+\s*', '', name)
        # Remove common prefixes
        name = name.replace('Update ', '').replace('New ', '')
        
        # Debug: log original name for companies without country codes
        original_name = name
        # Replace flag emojis and other unicode characters
        # Handle various flag representations
        flag_patterns = [
            (r'ð\x9f\x87ºð\x9f\x87¸', 'US'),  # US flag
            (r'ð\x9f\x87¨ð\x9f\x87¦', 'CA'),  # Canada flag  
            (r'ð\x9f\x87¯ð\x9f\x87µ', 'JP'),  # Japan flag
            (r'ð\x9f\x87¨ð\x9f\x87³', 'CN'),  # China flag
            (r'ð\x9f\x87©ð\x9f\x87ª', 'DE'),  # Germany flag
            (r'ð\x9f\x87­ð\x9f\x87°', 'HK'),  # Hong Kong flag
            (r'ð\x9f\x87¬ð\x9f\x87§', 'GB'),  # UK flag
            (r'ð\x9f\x87¸ð\x9f\x87¬', 'SG'),  # Singapore flag
            (r'ð\x9f\x87¦ð\x9f\x87º', 'AU'),  # Australia flag
            (r'ð\x9f\x87³ð\x9f\x87±', 'NL'),  # Netherlands flag
            (r'ð\x9f\x87¸ð\x9f\x87ª', 'SE'),  # Sweden flag
                         (r'ð\x9f\x87³ð\x9f\x87´', 'NO'),  # Norway flag
             (r'ð\x9f\x87°ð\x9f\x87·', 'KR'),  # South Korea flag
             (r'ð\x9f\x87¨ð\x9f\x87¾', 'CY'),  # Cyprus flag
             (r'ð\x9f\x87§ð\x9f\x87²', 'BM'),  # Bermuda flag
             (r'ð\x9f\x87»ð\x9f\x87¬', 'VG'),  # British Virgin Islands flag
             (r'ð\x9f\x87°ð\x9f\x87¾', 'KY'),  # Cayman Islands flag
             (r'ð\x9d\x87°ð\x9d\x87¾', 'KY'),  # Alternative Cayman Islands flag encoding
             # Add more patterns as needed
         ]
        
        for pattern, code in flag_patterns:
            name = re.sub(pattern, f'{code} ', name)
        
        # Remove other problematic unicode characters
        name = re.sub(r'[^\x00-\x7F]+', ' ', name)  # Remove non-ASCII characters
        # Clean up
        name = re.sub(r'[^\w\s&.-]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Manual fixes for companies with missing country codes
        # (Remove the HK fix since KY flag should be handled by pattern matching)
        
        # Debug: check if we missed a flag pattern
        if 'microcloud' in name.lower():
            logger.debug(f"Microcloud processing: '{original_name}' -> '{name}'")
        
        return name
    
    def scrape_top_companies(self):
        """Scrape top Bitcoin treasury public companies using API endpoint with better filtering"""
        logger.info("Scraping top Bitcoin treasury public companies...")
        
        # Authenticate if token provided
        if self.token_url:
            self.authenticate()
        
        # Use the public companies specific API endpoint
        api_url = "https://bitcointreasuries.net/embed?component=MainTable&embedConfig=%7B%22limit%22%3A500%2C%22disableGrouping%22%3Atrue%2C%22role%22%3A%22holder%22%2C%22entityTypes%22%3A%5B%22PUBLIC_COMPANY%22%5D%7D"
        
        # Get data from API endpoint
        try:
            logger.info("Fetching data from public companies API endpoint...")
            response = self.session.get(api_url, timeout=15)
            response.raise_for_status()
            html = response.text
        except Exception as e:
            logger.error(f"Failed to fetch API data: {e}")
            return
        
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        
        if not tables:
            logger.error("No tables found in API response")
            return
        
        # Get the main table (should be the only one or the largest one)
        main_table = tables[0] if len(tables) == 1 else max(tables, key=lambda t: len(t.find_all('tr')))
        rows = main_table.find_all('tr')
        logger.info(f"Processing {len(rows)} rows from public companies API")
        
        companies = []
        
        for i, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:
                continue
            
            # Skip header rows
            row_text = row.get_text().lower()
            if 'bitcoin' in cells[0].get_text().lower() and 'usd' in row_text:
                continue  # Skip header row
            
            # Extract company data - should all be public companies from this API
            company_data = self.extract_company_data_from_api(cells, i)
            if company_data and self.is_valid_public_company(company_data):
                companies.append(company_data)
                if len(companies) <= 10:  # Log first 10 companies for debugging
                    logger.info(f"Added company {len(companies)}: {company_data['name']} with {company_data['bitcoin']} BTC")
                elif len(companies) % 25 == 0:  # Log every 25 companies after that
                    logger.info(f"Progress: {len(companies)} public companies found so far...")
            else:
                # Log failed extractions for first few rows to debug
                if i <= 10 and company_data:
                    logger.debug(f"Filtered out: {company_data.get('name', 'Unknown')}")
        
        # Sort by Bitcoin holdings (descending)
        companies = [c for c in companies if c.get('bitcoin', 0) > 0]
        companies.sort(key=lambda x: x.get('bitcoin', 0), reverse=True)
        
        # Add proper ranking
        for i, company in enumerate(companies, 1):
            company['rank'] = i
        
        self.top_companies = companies
        logger.info(f"Found {len(self.top_companies)} public companies with Bitcoin treasury holdings")
    
    def is_public_company(self, name):
        """Check if the name represents a public company (not a country, government, or private entity)"""
        if not name:
            return False
        
        name_lower = name.lower().strip()
        
        # Exclude summary rows and totals
        if any(word in name_lower for word in ['grand total', 'total', 'subtotal', 'sum']):
            return False
        
        # Exclude countries and regions (be comprehensive)
        countries_and_regions = [
            'china', 'united states', 'united kingdom', 'north korea', 'ukraine', 'el salvador', 'bhutan',
            'germany', 'japan', 'canada', 'france', 'australia', 'singapore', 'hong kong',
            'switzerland', 'netherlands', 'sweden', 'norway', 'south korea', 'russia', 'brazil',
            'argentina', 'mexico', 'venezuela', 'colombia', 'peru', 'chile', 'india', 'thailand',
            'vietnam', 'malaysia', 'indonesia', 'philippines', 'new zealand', 'south africa'
        ]
        
        # Exclude if it matches country names exactly or starts with "Auto" + country
        for country in countries_and_regions:
            if name_lower == country or name_lower.startswith(f'auto {country}'):
                return False
        
        # Exclude government and official entities
        government_indicators = [
            'holdings of public', 'government', 'ministry', 'department of', 'central bank',
            'reserve bank', 'federal reserve', 'treasury', 'sovereign', 'state', 'national'
        ]
        
        if any(indicator in name_lower for indicator in government_indicators):
            return False
        
        # Exclude foundations and non-profit entities
        non_profit_indicators = ['foundation', 'trust', 'endowment', 'charity']
        if any(indicator in name_lower for indicator in non_profit_indicators):
            return False
        
        # Exclude known private companies (not publicly traded)
        private_companies = ['block.one', 'spacex', 'strike', 'zap solutions']
        if any(private in name_lower for private in private_companies):
            return False
        
        # Now check for PUBLIC company indicators
        # Must have corporate structure indicators
        corporate_indicators = [
            'inc', 'corp', 'ltd', 'llc', 'plc', 'ag', 'sa', 'gmbh', 'asa',
            'company', 'group', 'holdings', 'technologies', 'systems',
            'solutions', 'services', 'digital', 'mining', 'platforms'
        ]
        
        has_corporate_indicator = any(indicator in name_lower for indicator in corporate_indicators)
        
        # Must have stock ticker pattern (like "MSTR", "TSLA", etc.)
        has_ticker = re.search(r'\b[A-Z]{2,5}(?:\.[A-Z]+)?\b', name)
        
        # For a company to be considered public, it should have BOTH:
        # 1. Corporate structure indicator OR stock ticker
        # 2. NOT be in exclusion lists
        
        if has_corporate_indicator or has_ticker:
            return True
        
        # Special cases for well-known single-name public companies
        known_public_companies = ['tesla', 'paypal', 'amazon', 'google', 'facebook', 'microsoft']
        if any(known in name_lower for known in known_public_companies):
            return True
        
        # If it doesn't meet the criteria above, it's likely not a public company
        return False

    def is_valid_public_company(self, company_data):
        """Enhanced validation for public companies"""
        if not company_data or not company_data.get('name'):
            return False
        
        name = company_data['name'].lower().strip()
        
        # Exclude specific non-public entities that might slip through
        excluded_entities = [
            'tether holdings', 'stone ridge holdings', 'el salvador', 'ukraine', 'china',
            'north korea', 'bhutan', 'government', 'treasury', 'central bank', 'auto ',
            'holdings of public', 'foundation', 'trust fund', 'endowment'
        ]
        
        for excluded in excluded_entities:
            if excluded in name:
                return False
        
        # Must be a proper public company
        return self.is_public_company(company_data['name'])

    def get_current_btc_price(self):
        """Get current Bitcoin price from CoinGecko API"""
        try:
            response = self.session.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd', timeout=10)
            if response.status_code == 200:
                data = response.json()
                btc_price = data['bitcoin']['usd']
                logger.info(f"Current BTC price: ${btc_price:,.2f}")
                return btc_price
        except Exception as e:
            logger.warning(f"Failed to get BTC price: {e}")
        
        # Fallback to approximate price
        return 107000  # Approximate current BTC price

    def calculate_mnav(self, bitcoin_holdings, market_cap, btc_price):
        """Calculate mNAV (Market-to-NAV ratio) manually"""
        if not bitcoin_holdings or not market_cap or market_cap <= 0:
            return 0.0
        
        try:
            # mNAV = (Bitcoin Holdings × BTC Price) / Market Cap × 100
            btc_value = bitcoin_holdings * btc_price
            mnav_percentage = (btc_value / market_cap) * 100
            
            # Reasonable bounds for mNAV (0.1% to 5000%)
            if 0.1 <= mnav_percentage <= 5000:
                return round(mnav_percentage, 2)
            else:
                return 0.0
        except Exception as e:
            logger.debug(f"Error calculating mNAV: {e}")
            return 0.0

    def extract_company_data_from_api(self, cells, row_index):
        """Extract company data from API response table row"""
        try:
            if len(cells) < 3:
                logger.debug(f"Row {row_index}: Not enough cells ({len(cells)})")
                return None
            
            company = {}
            cell_idx = 0
            
            # Debug: log the row content for first few rows
            if row_index <= 3:
                cell_texts = [cell.get_text().strip() for cell in cells[:12]]
                logger.info(f"Row {row_index} all cells: {cell_texts}")
            
            # Rank (first column)
            rank_text = cells[cell_idx].get_text().strip()
            if rank_text and rank_text.replace('.', '').isdigit():
                company['rank'] = int(float(rank_text))
                cell_idx += 1
            
            # Company name (should be clean from API)
            if cell_idx < len(cells):
                raw_name = cells[cell_idx].get_text().strip()
                name = self.clean_company_name(raw_name)
                
                if name and len(name) > 1:
                    company['name'] = name
                    cell_idx += 1
                else:
                    return None
            
            # Bitcoin holdings
            if cell_idx < len(cells):
                bitcoin_amount = self.parse_number(cells[cell_idx].get_text().strip())
                company['bitcoin'] = bitcoin_amount
                cell_idx += 1
            
            # USD value
            if cell_idx < len(cells):
                usd_value = self.parse_number(cells[cell_idx].get_text().strip())
                company['usd_value'] = usd_value
                cell_idx += 1
            
            # Market cap
            if cell_idx < len(cells):
                market_cap = self.parse_number(cells[cell_idx].get_text().strip())
                company['market_cap'] = market_cap
                cell_idx += 1
            
            # Look for mNAV in the "mNAV" column (column 9 based on screenshot)
            # The actual mNAV values are small like "1.70%", not the large "/M.Cap" values
            company['mnav'] = 0  # Default value
            found_mnav = False
            
            # Based on HTML inspection, mNAV appears before the /M.Cap column
            # The mNAV value (like "1.701") comes before the /M.Cap value (like "58.78%")
            mnav_column_idx = 8  # Adjusted position - one column before /M.Cap
            
            # Only look at column 8 first (the actual mNAV column)
            if mnav_column_idx < len(cells):
                try:
                    cell_text = cells[mnav_column_idx].get_text().strip()
                    
                    if row_index <= 3:  # Debug for first few rows
                        logger.debug(f"mNAV Column {mnav_column_idx}: '{cell_text}'")
                    
                    # Skip obfuscated data (asterisks)
                    if '*' not in cell_text and cell_text and cell_text not in ['-', '', 'N/A', '?', '—']:
                        # mNAV appears as small decimal numbers (like 1.702, 0.073, 5.768)
                        # NOT as percentages - those are in the /M.Cap column
                        decimal_value = self.parse_number(cell_text)
                        
                        # Real mNAV values are small decimals (0.01 to 1000)
                        # Based on screenshot: 1.702, 1.010, 0.073, 1.824, 5.768, etc.
                        if 0.01 <= decimal_value <= 1000.0:
                            company['mnav'] = decimal_value
                            found_mnav = True
                            if row_index <= 3:
                                logger.debug(f"Found mNAV decimal: {decimal_value} at column {mnav_column_idx}")
                except Exception as e:
                    if row_index <= 3:
                        logger.debug(f"Error parsing mNAV column {mnav_column_idx}: {e}")
            
            # If not found in column 8, try nearby columns but look for decimal values
            if not found_mnav:
                search_columns = [7, 9]  # Adjacent columns to mNAV
                for col_idx in search_columns:
                    if col_idx < len(cells):
                        try:
                            cell_text = cells[col_idx].get_text().strip()
                            
                            if row_index <= 3:
                                logger.debug(f"Backup search Column {col_idx}: '{cell_text}'")
                            
                            # Skip obfuscated data and look for decimal values (not percentages)
                            if ('*' not in cell_text and cell_text and 
                                cell_text not in ['-', '', 'N/A', '?', '—'] and '%' not in cell_text):
                                decimal_value = self.parse_number(cell_text)
                                # Only accept small decimal values for mNAV (like 1.702, 0.073, etc.)
                                if 0.01 <= decimal_value <= 1000.0:
                                    company['mnav'] = decimal_value
                                    found_mnav = True
                                    if row_index <= 3:
                                        logger.debug(f"Found mNAV in backup: {decimal_value} at column {col_idx}")
                                    break
                        except Exception as e:
                            continue
            
            # If mNAV not found in API data, calculate the proper mNAV ratio (not percentage)
            if not found_mnav and company.get('bitcoin', 0) > 0 and company.get('market_cap', 0) > 0:
                if not hasattr(self, '_btc_price'):
                    self._btc_price = self.get_current_btc_price()
                
                # Calculate mNAV as a ratio (like 1.702, not 170.2%)
                btc_value = company['bitcoin'] * self._btc_price
                mnav_ratio = btc_value / company['market_cap']
                
                # mNAV should be a small decimal (0.001 to 20.0 typically)
                if 0.001 <= mnav_ratio <= 20.0:
                    company['mnav'] = round(mnav_ratio, 3)
                    if row_index <= 3:
                        logger.debug(f"Calculated mNAV ratio: {mnav_ratio:.3f} for {company['name']}")
                else:
                    company['mnav'] = 0
            
            # Look for /21M column (typically column 11 based on structure)
            company['supply_ratio'] = 0  # /21M represents percentage of total Bitcoin supply
            supply_ratio_column_idx = 11  # /21M column position
            
            if supply_ratio_column_idx < len(cells):
                try:
                    cell_text = cells[supply_ratio_column_idx].get_text().strip()
                    
                    if row_index <= 3:
                        logger.debug(f"/21M Column {supply_ratio_column_idx}: '{cell_text}'")
                    
                    # Skip obfuscated data (asterisks)
                    if '*' not in cell_text and cell_text and cell_text not in ['-', '', 'N/A', '?', '—']:
                        # /21M appears as percentage (like "2.821%", "0.237%")
                        if '%' in cell_text:
                            percent_value = self.parse_number(cell_text.replace('%', ''))
                            # /21M percentages are typically small (0.001% to 5%)
                            if 0.001 <= percent_value <= 5.0:
                                company['supply_ratio'] = percent_value
                                if row_index <= 3:
                                    logger.debug(f"Found /21M: {percent_value}% at column {supply_ratio_column_idx}")
                        else:
                            # Check if it's a decimal
                            decimal_value = self.parse_number(cell_text)
                            if 0.00001 <= decimal_value <= 0.05:  # Convert decimal to percentage
                                company['supply_ratio'] = round(decimal_value * 100, 4)
                                if row_index <= 3:
                                    logger.debug(f"Found /21M decimal: {decimal_value} ({decimal_value*100:.4f}%) at column {supply_ratio_column_idx}")
                except Exception as e:
                    if row_index <= 3:
                        logger.debug(f"Error parsing /21M column: {e}")
            
            # If /21M not found, calculate it manually
            # /21M = (Bitcoin Holdings / 21,000,000) * 100
            if company['supply_ratio'] == 0 and company.get('bitcoin', 0) > 0:
                supply_percentage = (company['bitcoin'] / 21_000_000) * 100
                if 0.001 <= supply_percentage <= 5.0:  # Reasonable range
                    company['supply_ratio'] = round(supply_percentage, 4)
                    if row_index <= 3:
                        logger.debug(f"Calculated /21M: {supply_percentage:.4f}% for {company['name']}")
            
            # Add metadata
            company['scraped_at'] = datetime.now().isoformat()
            company['category'] = 'public_companies'
            
            # Since this comes from the PUBLIC_COMPANY API, we trust it's a public company
            if company.get('name') and company.get('bitcoin', 0) > 0:
                return company
                
        except Exception as e:
            logger.debug(f"Error extracting company data from API row {row_index}: {e}")
        
        return None

    def extract_company_data_from_main_site(self, cells, row_index):
        """Extract company data from main website table row"""
        try:
            if len(cells) < 3:
                logger.debug(f"Row {row_index}: Not enough cells ({len(cells)})")
                return None
            
            company = {}
            cell_idx = 0
            
            # Debug: log the row content for first few rows
            if row_index <= 3:
                cell_texts = [cell.get_text().strip() for cell in cells[:12]]
                logger.info(f"Row {row_index} all cells: {cell_texts}")
            
            # Rank (first column)
            rank_text = cells[cell_idx].get_text().strip()
            if rank_text and rank_text.replace('.', '').isdigit():
                company['rank'] = int(float(rank_text))
                cell_idx += 1
            
            # Company name
            if cell_idx < len(cells):
                raw_name = cells[cell_idx].get_text().strip()
                name = self.clean_company_name(raw_name)
                
                if name and len(name) > 1:
                    company['name'] = name
                    cell_idx += 1
                else:
                    return None
            
            # Bitcoin holdings
            if cell_idx < len(cells):
                bitcoin_amount = self.parse_number(cells[cell_idx].get_text().strip())
                company['bitcoin'] = bitcoin_amount
                cell_idx += 1
            
            # USD value
            if cell_idx < len(cells):
                usd_value = self.parse_number(cells[cell_idx].get_text().strip())
                company['usd_value'] = usd_value
                cell_idx += 1
            
            # Market cap
            if cell_idx < len(cells):
                market_cap = self.parse_number(cells[cell_idx].get_text().strip())
                company['market_cap'] = market_cap
                cell_idx += 1
            
            # Look for mNAV - should be column 9 based on header structure
            company['mnav'] = 0
            mnav_column_idx = 9  # mNAV column
            
            if mnav_column_idx < len(cells):
                try:
                    cell_text = cells[mnav_column_idx].get_text().strip()
                    
                    if row_index <= 3:
                        logger.debug(f"mNAV Column {mnav_column_idx}: '{cell_text}'")
                    
                    # Look for small decimal values (not percentages)
                    if cell_text and cell_text not in ['-', '', 'N/A', '?', '—'] and '*' not in cell_text:
                        decimal_value = self.parse_number(cell_text)
                        # mNAV should be small decimal like 1.702, 0.073, 5.768
                        if 0.001 <= decimal_value <= 1000.0:
                            company['mnav'] = decimal_value
                            if row_index <= 3:
                                logger.debug(f"Found mNAV: {decimal_value} at column {mnav_column_idx}")
                except Exception as e:
                    if row_index <= 3:
                        logger.debug(f"Error parsing mNAV: {e}")
            
            # Add metadata
            company['scraped_at'] = datetime.now().isoformat()
            company['category'] = 'public_companies'
            
            if company.get('name') and company.get('bitcoin', 0) > 0:
                return company
                
        except Exception as e:
            logger.debug(f"Error extracting company data from main site row {row_index}: {e}")
        
        return None

    def scrape_from_api(self):
        """Fallback method to scrape from API endpoint"""
        logger.info("Falling back to API endpoint...")
        
        api_url = "https://bitcointreasuries.net/embed?component=MainTable&embedConfig=%7B%22limit%22%3A500%2C%22disableGrouping%22%3Atrue%2C%22role%22%3A%22holder%22%2C%22entityTypes%22%3A%5B%22PUBLIC_COMPANY%22%5D%7D"
        
        try:
            response = self.session.get(api_url, timeout=15)
            response.raise_for_status()
            html = response.text
        except Exception as e:
            logger.error(f"Failed to fetch API data: {e}")
            return
        
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        
        if not tables:
            logger.error("No tables found in API response")
            return
        
        main_table = tables[0] if len(tables) == 1 else max(tables, key=lambda t: len(t.find_all('tr')))
        rows = main_table.find_all('tr')
        logger.info(f"Processing {len(rows)} rows from API endpoint")
        
        companies = []
        
        for i, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:
                continue
            
            # Skip header rows
            row_text = row.get_text().lower()
            if 'bitcoin' in cells[0].get_text().lower() and 'usd' in row_text:
                continue
            
            company_data = self.extract_company_data_from_api(cells, i)
            if company_data:
                companies.append(company_data)
        
        companies = [c for c in companies if c.get('bitcoin', 0) > 0]
        companies.sort(key=lambda x: x.get('bitcoin', 0), reverse=True)
        
        self.top_companies = companies
        logger.info(f"Found {len(self.top_companies)} companies from API endpoint")

    def extract_company_data(self, cells):
        """Extract company data from table row"""
        try:
            if len(cells) < 3:
                return None
            
            company = {}
            cell_idx = 0
            
            # Rank (if present)
            rank_text = cells[cell_idx].get_text().strip()
            if rank_text and rank_text.replace('.', '').isdigit():
                company['rank'] = int(float(rank_text))
                cell_idx += 1
            
            # Company name
            if cell_idx < len(cells):
                raw_name = cells[cell_idx].get_text().strip()
                name = self.clean_company_name(raw_name)
                
                # Check if this is actually a public company
                if name and len(name) > 1:
                    if self.is_public_company(name):
                        company['name'] = name
                        cell_idx += 1
                    else:
                        # Not a public company, skip this row
                        logger.debug(f"Skipping non-public company: {name}")
                        return None
                else:
                    return None
            
            # Bitcoin holdings
            if cell_idx < len(cells):
                bitcoin_amount = self.parse_number(cells[cell_idx].get_text().strip())
                company['bitcoin'] = bitcoin_amount
                cell_idx += 1
            
            # USD value
            if cell_idx < len(cells):
                usd_value = self.parse_number(cells[cell_idx].get_text().strip())
                company['usd_value'] = usd_value
                cell_idx += 1
            
            # Market cap
            if cell_idx < len(cells):
                market_cap = self.parse_number(cells[cell_idx].get_text().strip())
                company['market_cap'] = market_cap
            
            # Add metadata
            company['scraped_at'] = datetime.now().isoformat()
            company['category'] = 'public_companies'
            
            # Only return if valid company with Bitcoin holdings
            if company.get('name') and company.get('bitcoin', 0) > 0:
                return company
                
        except Exception as e:
            logger.debug(f"Error extracting company data: {e}")
        
        return None
    
    def print_results(self):
        """Print top companies"""
        if not self.top_companies:
            print("No top Bitcoin treasury companies found")
            return
        
        print("\n" + "="*100)
        print("TOP BITCOIN TREASURY PUBLIC COMPANIES")
        print("="*100)
        
        print(f"{'#':<3} {'Company':<35} {'Bitcoin Holdings':<18} {'USD Value':<12} {'Market Cap':<12} {'mNAV':<8} {'/21M':<8}")
        print("-" * 108)
        
        for i, company in enumerate(self.top_companies[:50], 1):  # Show top 50
            rank = company.get('rank', i)
            name = company.get('name', 'Unknown')[:33]
            bitcoin = company.get('bitcoin', 0)
            usd_value = company.get('usd_value', 0)
            market_cap = company.get('market_cap', 0)
            mnav = company.get('mnav', 0)
            supply_ratio = company.get('supply_ratio', 0)
            
            # Format Bitcoin
            if bitcoin >= 1000:
                btc_str = f"{bitcoin:>14,.0f} BTC"
            else:
                btc_str = f"{bitcoin:>14,.1f} BTC"
            
            # Format USD
            def format_usd(value):
                if value == 0:
                    return "-"
                elif value >= 1_000_000_000:
                    return f"${value/1_000_000_000:.1f}B"
                elif value >= 1_000_000:
                    return f"${value/1_000_000:.0f}M"
                else:
                    return f"${value:,.0f}"
            
            # Format mNAV (as decimal, not percentage)
            def format_mnav(value):
                if value == 0:
                    return "-"
                else:
                    return f"{value:.3f}"
            
            # Format /21M (as percentage)
            def format_supply_ratio(value):
                if value == 0:
                    return "-"
                else:
                    return f"{value:.3f}%"
            
            usd_str = format_usd(usd_value)
            mcap_str = format_usd(market_cap)
            mnav_str = format_mnav(mnav)
            supply_ratio_str = format_supply_ratio(supply_ratio)
            
            print(f"{rank:<3} {name:<35} {btc_str:<18} {usd_str:<12} {mcap_str:<12} {mnav_str:<8} {supply_ratio_str:<8}")
        
        # Summary
        total_btc = sum(c.get('bitcoin', 0) for c in self.top_companies)
        total_usd = sum(c.get('usd_value', 0) for c in self.top_companies)
        
        print("-" * 108)
        print(f"TOTAL: {len(self.top_companies)} companies | {total_btc:,.0f} BTC | ${total_usd/1_000_000_000:.1f}B USD")
        print("="*108)



    def upload_to_supabase(self):
        """Upload to Supabase database"""
        if not self.supabase or not self.top_companies:
            return False
        
        upload_data = []
        snapshot_date = date.today().isoformat()
        
        for company in self.top_companies:
            upload_data.append({
                'rank': company.get('rank'),
                'company_name': company.get('name', ''),
                'bitcoin_holdings': str(Decimal(str(company.get('bitcoin', 0)))),
                'usd_value': str(Decimal(str(company.get('usd_value', 0)))),
                'market_cap': str(Decimal(str(company.get('market_cap', 0)))),
                'mnav': str(Decimal(str(company.get('mnav', 0)))),
                'supply_ratio': str(Decimal(str(company.get('supply_ratio', 0)))),
                'category': 'public_companies',
                'snapshot_date': snapshot_date,
                'scraped_at': company.get('scraped_at', datetime.now().isoformat())
            })
        
        try:
            result = self.supabase.table('public_company_holding').upsert(
                upload_data, on_conflict='company_name,snapshot_date'
            ).execute()
            
            if result.data:
                print(f"✅ Uploaded {len(result.data)} companies to Supabase")
                return True
            return False
        except Exception as e:
            logger.error(f"Supabase upload error: {e}")
            return False

def main():
    """Main function"""
    print("🔍 Top Bitcoin Treasury Public Companies Scraper")
    print("=" * 50)
    
    # Token URL for authentication
    token_url = "https://bitcointreasuries.net/login/eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..s2wtnOFtQGb5O0ix.4k4unnF9glUCv90kgCo7MBVRKAkqCwZJ0oXRRFLLvkiL8SOdH6ut_0wQd6qbqHrsVP3rxAdAs3K6bh1AkaOCYr-4pbg1Uk3CsYWH-PjJAOXyOE6Gt0HjTtoaHjH6ky-D_xaQBpLsZGM.7Gr9gQFGWsV2MNNezF5ACw"
    
    scraper = TopBitcoinTreasuryCompaniesScraper(token_url)
    
    try:
        # Scrape data
        scraper.scrape_top_companies()
        
        # Show results
        scraper.print_results()
        
        # Upload to Supabase
        scraper.upload_to_supabase()
        
        print(f"\n✅ Successfully found {len(scraper.top_companies)} top Bitcoin treasury companies!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 