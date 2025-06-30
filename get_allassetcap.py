from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from datetime import date
import re
import unicodedata
import openai
import json

# Set up Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

# Load environment variables from .env file
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Get today's date
today = date.today().isoformat()

def normalize_text(text):
    """Normalize Unicode text to fix encoding issues"""
    if not text:
        return ""
    
    # First apply character replacements before Unicode normalization
    normalized = text.replace('癡', 'è')
    normalized = normalized.replace('脙', 'Ã')
    normalized = normalized.replace('陇', 'ç')
    
    # Additional common encoding fixes
    normalized = normalized.replace('Ã¨', 'è')
    normalized = normalized.replace('Ã©', 'é')
    normalized = normalized.replace('Ã§', 'ç')
    normalized = normalized.replace('Ã¡', 'á')
    normalized = normalized.replace('Ã­', 'í')
    normalized = normalized.replace('Ã³', 'ó')
    normalized = normalized.replace('Ãº', 'ú')
    normalized = normalized.replace('Ã±', 'ñ')
    
    # Then apply Unicode normalization
    normalized = unicodedata.normalize('NFC', normalized)
    
    return normalized.strip()

def scrape_8marketcap_page(driver, page_num):
    """Scrape a single page from 8marketcap.com"""
    try:
        print(f"🔍 Scraping page {page_num}...")
        
        # Navigate to the page
        url = f'https://8marketcap.com/?page={page_num}'
        print(f"🌐 Navigating to: {url}")
        driver.get(url)
        
        # Wait for page to load and verify content
        max_wait_time = 15
        wait_start = time.time()
        page_loaded = False
        
        while time.time() - wait_start < max_wait_time:
            try:
                # Check if the page has loaded by looking for table content
                test_rows = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr, .dataTable tbody tr')
                if test_rows and len(test_rows) > 5:  # Should have multiple rows
                    page_loaded = True
                    print(f"✅ Page loaded successfully with {len(test_rows)} table rows")
                    break
            except:
                pass
            
            time.sleep(1)
        
        if not page_loaded:
            print(f"⚠️  Page may not have loaded completely after {max_wait_time}s, proceeding anyway...")
        
        # Debug: Print page source snippet to understand structure
        try:
            page_source = driver.page_source
            # Look for table-related content
            if 'table' in page_source.lower():
                print("✅ Found table elements in page source")
            if 'dataTable' in page_source:
                print("✅ Found dataTable in page source")
            if 'company-name' in page_source:
                print("✅ Found company-name class in page source")
            
            # Check for specific content indicators
            if 'Apple' in page_source or 'Microsoft' in page_source:
                print("✅ Found known companies in page source")
        except:
            pass
        
        # Look for table rows - target 8marketcap.com specific structure
        rows = []
        
        # Method 1: Try the specific 8marketcap table structure (most reliable)
        try:
            all_rows = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
            print(f"📊 Found {len(all_rows)} total rows using table tbody tr")
            
            # DON'T filter - keep ALL rows and let the processing logic decide
            # This ensures we don't accidentally skip any data rows
            rows = all_rows
            
            # Debug: Print first few rows to understand structure
            for i, row in enumerate(rows[:5]):
                try:
                    row_text = row.text.strip()
                    data_sort_count = len(row.find_elements(By.CSS_SELECTOR, 'td[data-sort]'))
                    print(f"   Row {i+1}: data-sort elements={data_sort_count}, text='{row_text[:50]}{'...' if len(row_text) > 50 else ''}'")
                except:
                    pass
            
            print(f"📊 Will process ALL {len(rows)} rows without filtering")
            
        except Exception as e:
            print(f"❌ Error finding table rows: {e}")
            rows = []
        
        # Method 2: Fallback to all table rows if filtering failed
        if not rows:
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, 'table tr')
                print(f"📊 Found {len(rows)} rows using table tr (fallback)")
            except:
                pass
        
        # Method 3: Try finding specific rows with data
        if not rows:
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, 'tr:has(td[data-sort])')
                print(f"📊 Found {len(rows)} rows with data-sort")
            except:
                pass
        
        if not rows:
            print("❌ No rows found on this page")
            return []
        
        companies = []
        
        for i, row in enumerate(rows):
            try:
                print(f"🔎 Processing row {i+1}/{len(rows)}")
                
                # Get full row text for debugging
                row_text = row.text.strip()
                print(f"📝 Full row text: '{row_text[:100]}{'...' if len(row_text) > 100 else ''}'")
                
                # ONLY skip truly empty rows - be very aggressive about keeping potential data
                if not row_text or len(row_text.strip()) < 1:
                    print(f"🔍 Skipping truly empty row")
                    continue
                
                # Check for obvious header patterns but be very conservative
                try:
                    row_text_lower = row_text.lower()
                    # Only skip if it's clearly a header (contains multiple header keywords and is very short)
                    header_keywords = ['rank', 'company', 'market cap', 'price', 'symbol']
                    header_count = sum(1 for keyword in header_keywords if keyword in row_text_lower)
                    if header_count >= 3 and len(row_text) < 50:
                        print(f"🔍 Skipping obvious header row: {row_text[:50]}")
                        continue
                except:
                    pass
                
                # Initialize variables
                rank = None
                name = ""
                symbol = ""
                market_cap = ""
                price = ""
                change_24h = ""
                
                # ULTRA-AGGRESSIVE RANK EXTRACTION - Try every possible method
                
                # Get all td elements first
                try:
                    all_tds = row.find_elements(By.TAG_NAME, 'td')
                    print(f"🔍 Found {len(all_tds)} td elements")
                except:
                    all_tds = []
                
                # Method 1: Check the expected position (td[1])
                try:
                    if len(all_tds) >= 2:
                        rank_td = all_tds[1]
                        data_sort = rank_td.get_attribute('data-sort')
                        td_class = rank_td.get_attribute('class')
                        td_text = rank_td.text.strip()
                        
                        print(f"   td[1]: class='{td_class}', data-sort='{data_sort}', text='{td_text}'")
                        
                        if data_sort and data_sort.isdigit():
                            rank_val = int(data_sort)
                            if 1 <= rank_val <= 500:
                                rank = rank_val
                                print(f"📊 Found rank from td[1] data-sort: {rank}")
                        
                        if not rank and td_text and td_text.isdigit():
                            rank_val = int(td_text)
                            if 1 <= rank_val <= 500:
                                rank = rank_val
                                print(f"📊 Found rank from td[1] text: {rank}")
                except Exception as e:
                    print(f"❌ Error checking td[1]: {e}")
                
                # Method 2: Check ALL td elements for data-sort with valid rank
                if not rank:
                    try:
                        for j, td in enumerate(all_tds):
                            data_sort = td.get_attribute('data-sort')
                            if data_sort and data_sort.isdigit():
                                rank_val = int(data_sort)
                                if 1 <= rank_val <= 500:
                                    rank = rank_val
                                    print(f"📊 Found rank from td[{j}] data-sort: {rank}")
                                    break
                    except Exception as e:
                        print(f"❌ Error checking all tds for data-sort: {e}")
                
                # Method 3: Check ALL td elements for text with valid rank
                if not rank:
                    try:
                        for j, td in enumerate(all_tds):
                            td_text = td.text.strip()
                            if td_text and td_text.isdigit():
                                rank_val = int(td_text)
                                if 1 <= rank_val <= 500:
                                    rank = rank_val
                                    print(f"📊 Found rank from td[{j}] text: {rank}")
                                    break
                    except Exception as e:
                        print(f"❌ Error checking all tds for text: {e}")
                
                # Method 4: Parse entire row text for any valid rank number
                if not rank:
                    try:
                        # Extract all numbers from the row text
                        all_numbers = re.findall(r'\b(\d{1,3})\b', row_text)
                        print(f"🔍 Found numbers in row text: {all_numbers}")
                        for num_str in all_numbers:
                            rank_val = int(num_str)
                            if 1 <= rank_val <= 500:
                                rank = rank_val
                                print(f"📊 Found rank from row text: {rank}")
                                break
                    except Exception as e:
                        print(f"❌ Error parsing row text for rank: {e}")
                
                # Method 5: Estimate rank from row position if all else fails
                if not rank and page_num and i >= 0:
                    try:
                        estimated_rank = (page_num - 1) * 100 + i + 1
                        if 1 <= estimated_rank <= 500:
                            rank = estimated_rank
                            print(f"📊 Using estimated rank based on position: {rank}")
                    except:
                        pass
                
                print(f"🎯 Final rank for row {i+1}: {rank}")
                
                # Extract company name from exact structure: td.name-td > div.name-div > div.company-name
                try:
                    # Find the name-td (should be the third td - index 2)
                    if len(all_tds) >= 3:
                        name_td = all_tds[2]  # Third td element
                        td_class = name_td.get_attribute('class')
                        print(f"   td[2]: class='{td_class}'")
                        
                        if 'name-td' in td_class:
                            # Follow the exact structure from the image
                            company_name_elem = name_td.find_element(By.CSS_SELECTOR, '.company-name')
                            name = company_name_elem.text.strip()
                            print(f"🏢 Found company name from td[2]: {name}")
                        else:
                            print(f"⚠️  td[2] is not name-td, searching for .company-name")
                            company_name_elem = row.find_element(By.CSS_SELECTOR, '.company-name')
                            name = company_name_elem.text.strip()
                            print(f"🏢 Found company name (search): {name}")
                    else:
                        # Fallback search
                        company_name_elem = row.find_element(By.CSS_SELECTOR, '.company-name')
                        name = company_name_elem.text.strip()
                        print(f"🏢 Found company name (fallback): {name}")
                        
                except Exception as e:
                    print(f"❌ Error extracting company name: {e}")
                    pass
                
                # Extract symbol from exact structure: td.name-td > div.name-div > div.company-code
                try:
                    # Find symbol in the name-td structure
                    if len(all_tds) >= 3:
                        name_td = all_tds[2]  # Third td element
                        td_class = name_td.get_attribute('class')
                        
                        if 'name-td' in td_class:
                            # Follow the exact structure from the image
                            symbol_element = name_td.find_element(By.CSS_SELECTOR, '.company-code')
                            symbol = symbol_element.text.strip().upper()
                            print(f"🎯 Found symbol from td[2]: {symbol}")
                        else:
                            print(f"⚠️  td[2] is not name-td, searching for .company-code")
                            symbol_element = row.find_element(By.CSS_SELECTOR, '.company-code')
                            symbol = symbol_element.text.strip().upper()
                            print(f"🎯 Found symbol (search): {symbol}")
                    else:
                        # Fallback search
                        symbol_element = row.find_element(By.CSS_SELECTOR, '.company-code')
                        symbol = symbol_element.text.strip().upper()
                        print(f"🎯 Found symbol (fallback): {symbol}")
                        
                except Exception as e:
                    print(f"❌ Error extracting symbol: {e}")
                    pass
                
                # PRECISE COLUMN-BASED EXTRACTION based on HTML structure
                try:
                    print(f"🎯 PRECISE EXTRACTION: Using exact column positions")
                    print(f"   Total tds: {len(all_tds)}")
                    
                    # Based on HTML structure analysis:
                    # td[0] = fav, td[1] = rank, td[2] = name, td[3] = ?, td[4] = market cap, td[5] = price
                    
                    # Extract market cap from td[4] (5th column)
                    if not market_cap and len(all_tds) >= 5:
                        market_cap_td = all_tds[4]
                        market_cap_text = market_cap_td.text.strip()
                        market_cap_data_sort = market_cap_td.get_attribute('data-sort')
                        print(f"📊 Market cap column td[4]: text='{market_cap_text}', data-sort='{market_cap_data_sort}'")
                        
                        if market_cap_text and re.search(r'[TMB]', market_cap_text):
                            market_cap = market_cap_text
                            print(f"💰 Market cap from td[4]: {market_cap}")
                    
                    # Extract price from td[5] (6th column) - THE CORRECT PRICE COLUMN
                    if not price and len(all_tds) >= 6:
                        price_td = all_tds[5]
                        price_text = price_td.text.strip()
                        price_data_sort = price_td.get_attribute('data-sort')
                        print(f"💵 Price column td[5]: text='{price_text}', data-sort='{price_data_sort}'")
                        
                        # Method 1: Use visible text if it contains $ and looks like a price
                        if price_text and '$' in price_text and not re.search(r'[TMB]', price_text):
                            price = price_text
                            print(f"💵 Price from td[5] visible text: {price}")
                        
                        # Method 2: Use data-sort value (this should be the accurate price value)
                        elif price_data_sort and price_data_sort.replace('.', '').replace('-', '').isdigit():
                            try:
                                price_val = float(price_data_sort)
                                if 0.01 <= price_val <= 500000:  # Reasonable price range
                                    price = f"${price_val:.2f}".replace('.00', '')
                                    print(f"💵 Price from td[5] data-sort: {price} (raw: {price_data_sort})")
                            except Exception as e:
                                print(f"❌ Error parsing price data-sort: {e}")
                    
                    # Fallback: scan financial columns if precise extraction fails
                    if not market_cap or not price:
                        print(f"🔍 Fallback: Scanning financial columns")
                        financial_tds = all_tds[3:] if len(all_tds) > 3 else []
                        
                        for i, elem in enumerate(financial_tds):
                            text = elem.text.strip()
                            data_sort = elem.get_attribute('data-sort')
                            td_class = elem.get_attribute('class')
                            print(f"   financial_td[{i}] (td[{i+3}]): class='{td_class}', text='{text}', data-sort='{data_sort}'")
                            
                            # Market cap fallback
                            if not market_cap and text and re.search(r'[TMB]', text):
                                market_cap = text
                                print(f"💰 Fallback market cap from td[{i+3}]: {market_cap}")
                            
                            # Price fallback
                            if not price and text and '$' in text and not re.search(r'[TMB]', text):
                                price = text
                                print(f"💵 Fallback price from td[{i+3}]: {price}")
                            
                            # Price from data-sort fallback
                            if not price and data_sort and data_sort.replace('.', '').replace('-', '').isdigit():
                                try:
                                    data_sort_val = float(data_sort)
                                    # Look for reasonable price values
                                    if 0.01 <= abs(data_sort_val) <= 500000:
                                        price = f"${abs(data_sort_val):.2f}".replace('.00', '')
                                        print(f"💵 Fallback price from data-sort td[{i+3}]: {price}")
                                except:
                                    pass
                    
                    # Fallback: Look for any text with market cap indicators
                    if not market_cap:
                        for i, elem in enumerate(financial_tds):
                            text = elem.text.strip()
                            if text and re.search(r'[TMB]', text, re.IGNORECASE):
                                market_cap = text
                                print(f"💰 Fallback market cap: {market_cap}")
                                break
                    
                    # Fallback: Look for any text with dollar signs (but not market cap)
                    if not price:
                        for i, elem in enumerate(financial_tds):
                            text = elem.text.strip()
                            if text and '$' in text and not re.search(r'[TMB]', text):
                                # Extract the dollar amount
                                price_match = re.search(r'\$[\d,]+\.?\d*', text)
                                if price_match:
                                    potential_price = price_match.group(0)
                                    try:
                                        price_val = float(potential_price.replace('$', '').replace(',', ''))
                                        if 0.50 <= price_val <= 1000000:  # Reasonable range
                                            price = potential_price
                                            print(f"💵 Fallback price: {price}")
                                            break
                                    except:
                                        continue
                            
                except Exception as e:
                    print(f"❌ Error extracting financial data: {e}")
                    pass
                
                # Extract 24h change from td-center elements (percentage changes)
                try:
                    center_elements = row.find_elements(By.CSS_SELECTOR, '.td-center')
                    print(f"🔍 Found {len(center_elements)} td-center elements")
                    for i, elem in enumerate(center_elements):
                        text = elem.text.strip()
                        elem_class = elem.get_attribute('class')
                        print(f"   td-center[{i}]: class='{elem_class}', text='{text}'")
                        if text and re.search(r'[+-]?\d+\.?\d*%', text):
                            change_24h = text
                            print(f"📈 Found 24h change: {change_24h}")
                            break
                except Exception as e:
                    print(f"❌ Error extracting 24h change: {e}")
                    pass
                
                # AGGRESSIVE MARKET CAP FALLBACK
                if not market_cap:
                    try:
                        print(f"🔍 Market cap not found via standard methods, scanning all td elements...")
                        for i, td in enumerate(all_tds):
                            td_text = td.text.strip()
                            # Look for any text with B/T/M indicators
                            if td_text and re.search(r'[BTM]', td_text, re.IGNORECASE):
                                market_cap_patterns = [
                                    r'\$?[\d,]+\.?\d*\s*[TMB]',
                                    r'[\d,]+\.?\d*\s*[Tt]rillion',
                                    r'[\d,]+\.?\d*\s*[Bb]illion',
                                    r'[\d,]+\.?\d*\s*[Mm]illion',
                                ]
                                
                                for pattern in market_cap_patterns:
                                    if re.search(pattern, td_text, re.IGNORECASE):
                                        market_cap = td_text
                                        print(f"💰 Found market cap via fallback in td[{i}]: {market_cap}")
                                        break
                                
                                if market_cap:
                                    break
                    except Exception as e:
                        print(f"❌ Error in market cap fallback: {e}")
                
                # AGGRESSIVE PRICE FALLBACK - Check all td elements for any price-like data
                if not price:
                    try:
                        print(f"🔍 Price not found via standard methods, scanning all td elements...")
                        for i, td in enumerate(all_tds):
                            td_text = td.text.strip()
                            if td_text and '$' in td_text and not re.search(r'[TMB]', td_text):
                                # Extract any dollar amount
                                price_matches = re.findall(r'\$?[\d,]+\.?\d*', td_text)
                                for match in price_matches:
                                    try:
                                        # Clean and validate the price
                                        clean_price = match.replace(',', '')
                                        if not clean_price.startswith('$'):
                                            clean_price = '$' + clean_price
                                        
                                        price_val = float(clean_price.replace('$', ''))
                                        if 0.01 <= price_val <= 50000:  # Reasonable range
                                            price = clean_price
                                            print(f"💵 Found price via fallback in td[{i}]: {price}")
                                            break
                                    except:
                                        continue
                                if price:
                                    break
                    except Exception as e:
                        print(f"❌ Error in price fallback: {e}")
                
                # ULTRA-AGGRESSIVE PRICE FALLBACK - Try to extract ANY reasonable numeric value as price
                if not price:
                    try:
                        print(f"🔍 Ultra-aggressive: Looking for ANY reasonable price value...")
                        for i, td in enumerate(all_tds):
                            td_text = td.text.strip()
                            if td_text:
                                # Try multiple extraction methods
                                price_candidates = []
                                
                                # Method 1: Look for currency symbols (not just $)
                                currency_patterns = [
                                    r'[$¥€£₹][\d,]+\.?\d*',  # Various currency symbols
                                    r'[\d,]+\.?\d*\s*[$¥€£₹]',  # Currency after number
                                    r'USD\s*[\d,]+\.?\d*',   # USD prefix
                                    r'[\d,]+\.?\d*\s*USD',   # USD suffix
                                ]
                                
                                for pattern in currency_patterns:
                                    matches = re.findall(pattern, td_text)
                                    price_candidates.extend(matches)
                                
                                # Method 2: Look for standalone numbers in reasonable price range
                                numeric_matches = re.findall(r'[\d,]+\.?\d*', td_text)
                                for match in numeric_matches:
                                    try:
                                        value = float(match.replace(',', ''))
                                        
                                        # SMART FILTERING - avoid rank numbers and tiny values
                                        # Skip if it looks like a rank (1-500 without decimals)
                                        if 1 <= value <= 500 and '.' not in match:
                                            print(f"🚫 Skipping potential rank in td[{i}]: {match}")
                                            continue
                                        
                                        # Skip very small values that are likely percentages or ranks
                                        if value < 0.10:
                                            print(f"🚫 Skipping too small value in td[{i}]: {match}")
                                            continue
                                        
                                        # Reasonable price range
                                        if 0.10 <= value <= 100000:
                                            price_candidates.append(f"${match}")
                                    except:
                                        continue
                                
                                # Method 3: Extract from data-sort attribute as potential price
                                data_sort = td.get_attribute('data-sort')
                                if data_sort and data_sort.replace('.', '').isdigit():
                                    try:
                                        value = float(data_sort)
                                        if 0.01 <= value <= 50000:
                                            price_candidates.append(f"${data_sort}")
                                    except:
                                        pass
                                
                                # Choose the best price candidate
                                for candidate in price_candidates:
                                    if candidate:
                                        price = candidate
                                        print(f"💵 Found price via ultra-aggressive in td[{i}]: {price}")
                                        break
                                
                                if price:
                                    break
                    except Exception as e:
                        print(f"❌ Error in ultra-aggressive price fallback: {e}")
                
                # DESPERATE PRICE ATTEMPT - Use any numeric data from the entire row
                if not price:
                    try:
                        print(f"🚨 DESPERATE: Extracting ANY numeric data from entire row as potential price...")
                        # Get all text from the row
                        all_row_text = row_text
                        
                        # Extract all numeric values from entire row but be SMART about it
                        all_numbers = re.findall(r'[\d,]+\.?\d*', all_row_text)
                        print(f"🔍 All numbers found in row: {all_numbers}")
                        
                        for num_str in all_numbers:
                            try:
                                value = float(num_str.replace(',', ''))
                                
                                # SMART FILTERING in desperate mode
                                # Skip rank numbers (1-500 without decimals)
                                if 1 <= value <= 500 and '.' not in num_str:
                                    print(f"🚫 DESPERATE: Skipping potential rank: {num_str}")
                                    continue
                                
                                # Skip very small values
                                if value < 1.0:
                                    print(f"🚫 DESPERATE: Skipping small value: {num_str}")
                                    continue
                                
                                # Look for values that could be reasonable prices
                                if 1.0 <= value <= 200000:  # Bitcoin could be $100k+
                                    price = f"${num_str}"
                                    print(f"💵 DESPERATE: Found price from row text: {price}")
                                    break
                            except:
                                continue
                    except Exception as e:
                        print(f"❌ Error in desperate price attempt: {e}")
                
                # ULTRA-AGGRESSIVE 24H CHANGE EXTRACTION
                if not change_24h:
                    try:
                        print(f"🔍 Ultra-aggressive: Looking for ANY percentage value...")
                        for i, elem in enumerate(all_tds):
                            text = elem.text.strip()
                            if text:
                                # Try multiple percentage patterns
                                percentage_patterns = [
                                    r'[+-]?\d+\.?\d*%',          # Standard: +1.23%
                                    r'[+-]?\d+\.?\d*\s*%',       # With space: +1.23 %
                                    r'[+-]?\s*\d+\.?\d*%',       # Space before: + 1.23%
                                    r'\d+\.?\d*%\s*[↑↓]',        # With arrows: 1.23%↑
                                    r'[↑↓]\s*\d+\.?\d*%',        # Arrow first: ↑1.23%
                                    r'\(\d+\.?\d*%\)',           # Parentheses: (1.23%)
                                    r'[+-]\d+\.?\d*\s*percent',   # Written out: +1.23 percent
                                ]
                                
                                for pattern in percentage_patterns:
                                    matches = re.findall(pattern, text, re.IGNORECASE)
                                    if matches:
                                        change_24h = matches[0]
                                        print(f"📈 Found 24h change in td[{i}]: {change_24h}")
                                        break
                                
                                if change_24h:
                                    break
                                
                                # Also check data-sort for percentage values
                                data_sort = elem.get_attribute('data-sort')
                                if data_sort and (data_sort.startswith('-') or data_sort.startswith('+')):
                                    try:
                                        # If data-sort looks like a percentage value
                                        value = float(data_sort)
                                        if -100 <= value <= 1000:  # Reasonable percentage range
                                            change_24h = f"{data_sort}%"
                                            print(f"📈 Found 24h change from data-sort in td[{i}]: {change_24h}")
                                            break
                                    except:
                                        pass
                    except Exception as e:
                        print(f"❌ Error in 24h change extraction: {e}")
                
                # DESPERATE 24H CHANGE ATTEMPT - Extract from entire row
                if not change_24h:
                    try:
                        print(f"🚨 DESPERATE: Looking for ANY percentage in entire row...")
                        
                        # Search entire row text for percentage patterns
                        desperate_patterns = [
                            r'[+-]?\d+\.?\d*%',
                            r'[+-]?\d+\.?\d*\s*percent',
                            r'\d+\.?\d*%',  # Even without +/- signs
                        ]
                        
                        for pattern in desperate_patterns:
                            matches = re.findall(pattern, row_text, re.IGNORECASE)
                            if matches:
                                # Take the first reasonable percentage found
                                for match in matches:
                                    try:
                                        # Extract numeric part to validate
                                        num_part = re.search(r'[\d.]+', match)
                                        if num_part:
                                            value = float(num_part.group())
                                            if 0 <= value <= 1000:  # Very generous range
                                                change_24h = match
                                                print(f"📈 DESPERATE: Found 24h change from row text: {change_24h}")
                                                break
                                    except:
                                        continue
                                if change_24h:
                                    break
                        
                    except Exception as e:
                        print(f"❌ Error in desperate 24h change attempt: {e}")
                
                # Method 2: Fallback to generic cell parsing
                if not (rank and name and (market_cap or price)):
                    print(f"🔄 Using fallback parsing for row {i+1}")
                    
                    # Try to extract data from the row
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    
                    # If no td elements, try div elements
                    if not cells:
                        cells = row.find_elements(By.TAG_NAME, 'div')
                    
                    if len(cells) < 4:
                        print(f"⚠️  Row {i+1}: Not enough cells ({len(cells)}), trying alternative extraction")
                        
                        # Method 3: Try extracting from row text directly
                        try:
                            row_text = row.text.strip()
                            print(f"🔍 Row text: '{row_text}'")
                            
                            # Try to parse rank from the beginning
                            if not rank:
                                rank_match = re.search(r'^(\d{1,3})\s', row_text)
                                if rank_match:
                                    rank = int(rank_match.group(1))
                                    print(f"📊 Extracted rank from text: {rank}")
                            
                            # Skip this row if we still can't get basic data
                            if not rank:
                                print(f"❌ Row {i+1}: Cannot extract rank, skipping")
                                continue
                                
                        except Exception as e:
                            print(f"❌ Row {i+1}: Alternative extraction failed: {e}")
                            continue
                    
                    # Extract text from all cells to analyze
                    cell_texts = [cell.text.strip() for cell in cells]
                    print(f"📝 Row {i+1} fallback data: {cell_texts[:6]}")
                    
                    # Try to extract rank from first cell
                    if not rank and len(cell_texts) > 0:
                        first_cell = cell_texts[0].strip()
                        rank_match = re.search(r'^(\d+)', first_cell)
                        if rank_match:
                            rank = int(rank_match.group(1))
                            print(f"📊 Found fallback rank: {rank}")
                    
                    # First, try to find symbol badges in the row
                    if not symbol:
                        try:
                            badge_elements = row.find_elements(By.CSS_SELECTOR, '.badge, [class*="badge"]')
                            for badge in badge_elements:
                                badge_text = badge.text.strip().upper()
                                if badge_text and re.match(r'^[A-Z0-9]{1,8}$', badge_text):
                                    symbol = badge_text
                                    print(f"🎯 Found symbol badge: {symbol}")
                                    break
                        except:
                            pass
                
                    # Parse remaining data if needed using fallback logic
                    for j, cell_text in enumerate(cell_texts):
                        if not cell_text:
                            continue
                        
                        # Clean up cell text and remove rank numbers
                        clean_text = re.sub(r'\n\d+$', '', cell_text)  # Remove trailing "\n1", "\n2", etc.
                        clean_text = re.sub(r'^\d+\s*', '', clean_text)  # Remove leading numbers
                        clean_text = clean_text.strip()
                        
                        # Look for company name patterns if not found
                        if not name:
                            # Pattern: "Company Name (SYMBOL)" or "Company Name SYMBOL"
                            symbol_match = re.search(r'([^(]+)\s*\(([A-Z0-9]{1,8})\)', clean_text)
                            if symbol_match:
                                name = symbol_match.group(1).strip()
                                if not symbol:  # Only use symbol from text if we didn't find badge
                                    symbol = symbol_match.group(2).strip()
                                print(f"✅ Found fallback name: {name} (symbol: {symbol})")
                                continue
                            
                            # Look for company names without symbols
                            if len(clean_text) > 2 and not re.match(r'^[\d$%+-.,\s]+$', clean_text):
                                if not re.search(r'\$|%|\d{4,}', clean_text):
                                    name = clean_text
                                    print(f"🏢 Found fallback name: {name}")
                                    continue
                        
                        # Look for market cap patterns if not found
                        if not market_cap and re.search(r'\$[\d,]+\.?\d*\s*[TMB]', clean_text):
                            market_cap = clean_text
                            print(f"💰 Found fallback market cap: {market_cap}")
                            continue
                        
                        # Look for price patterns if not found - ULTRA AGGRESSIVE
                        if not price:
                            # SMART fallback price detection
                            price_patterns = [
                                r'\$[\d,]+\.?\d*',   # Dollar amounts with $
                                r'[\d,]+\.?\d*\$',   # Dollar amounts with $ after
                            ]
                            
                            for pattern in price_patterns:
                                price_match = re.search(pattern, clean_text)
                                if price_match:
                                    potential_price = price_match.group(0)
                                    try:
                                        # Extract numeric value
                                        num_val = re.sub(r'[^\d.]', '', potential_price)
                                        if num_val:
                                            value = float(num_val)
                                            
                                            # SMART VALIDATION - avoid ranks and tiny values
                                            if 1 <= value <= 500 and '.' not in num_val:
                                                print(f"🚫 Fallback: Skipping potential rank: {potential_price}")
                                                continue
                                            
                                            if 0.50 <= value <= 200000:  # Reasonable price range
                                                if not potential_price.startswith('$'):
                                                    potential_price = '$' + potential_price
                                                price = potential_price
                                                print(f"💵 Found fallback price: {price}")
                                                break
                                    except:
                                        continue
                            
                            if price:
                                continue
                        
                        # Look for percentage change patterns if not found - ULTRA AGGRESSIVE
                        if not change_24h:
                            # Try multiple percentage patterns
                            percentage_patterns = [
                                r'[+-]?\d+\.?\d*%',
                                r'[+-]?\d+\.?\d*\s*%',
                                r'\d+\.?\d*%',  # Even without +/- 
                                r'[+-]?\d+\.?\d*\s*percent',
                            ]
                            
                            for pattern in percentage_patterns:
                                if re.search(pattern, clean_text, re.IGNORECASE):
                                    change_24h = clean_text
                                    print(f"📈 Found fallback 24h change: {change_24h}")
                                    break
                            
                            if change_24h:
                                continue
                
                # Normalize the name text
                if name:
                    name = normalize_text(name)
                
                # Final validation - ensure we have a rank for data rows
                if rank is None:
                    print(f"⚠️  CRITICAL: Could not extract rank from row {i+1} with text: '{row_text[:100]}'")
                
                # FORCE SAVE IF WE HAVE A RANK - Don't let any rank slip through!
                if rank:
                    print(f"🎯 Processing rank {rank} - ensuring it gets saved!")
                    
                    # AGGRESSIVE NAME EXTRACTION - try everything
                    if not name:
                        print(f"🔍 Name not found via standard methods, trying aggressive extraction...")
                        
                        # Method 1: Parse from row text
                        try:
                            # Remove rank and numbers, look for text that could be a name
                            text_parts = row_text.split()
                            for part in text_parts:
                                clean_part = re.sub(r'[0-9$%+\-.,]', '', part).strip()
                                if len(clean_part) > 2 and clean_part.isalpha():
                                    name = part
                                    print(f"🏢 Found name from text parsing: {name}")
                                    break
                        except:
                            pass
                        
                        # Method 2: Try all td elements for any meaningful text
                        if not name:
                            try:
                                all_tds = row.find_elements(By.TAG_NAME, 'td')
                                for td in all_tds:
                                    td_text = td.text.strip()
                                    # Skip if it looks like a number, price, or percentage
                                    if (td_text and len(td_text) > 2 and 
                                        not td_text.replace('.', '').replace(',', '').isdigit() and
                                        '$' not in td_text and '%' not in td_text and
                                        not re.match(r'^[0-9.,\s]+$', td_text)):
                                        name = td_text
                                        print(f"🏢 Found name from td scan: {name}")
                                        break
                            except:
                                pass
                        
                        # Method 3: Use fallback name if still nothing
                        if not name:
                            name = f"Asset_Rank_{rank}"
                            print(f"🏢 Using fallback name: {name}")
                    
                    # Clean up the name
                    if name:
                        name = normalize_text(name)
                    
                    # Create the company data - ALWAYS save if we have a rank
                    company_data = {
                        "rank": rank,
                        "name": name[:255] if name else f"Asset_Rank_{rank}",
                        "symbol": symbol[:20] if symbol else "N/A",
                        "market_cap": market_cap or "",
                        "market_cap_raw": parse_market_cap_to_number(market_cap) if market_cap else 0,
                        "price": price or "",
                        "price_raw": parse_price_to_number(price) if price else 0.0,
                        "change_24h": change_24h or "",
                        "category": "",  # Will be filled by ChatGPT later
                        "snapshot_date": today
                    }
                    
                    companies.append(company_data)
                    
                    # Enhanced logging to track missing data and price extraction
                    missing_data = []
                    if not market_cap: missing_data.append("market_cap")
                    if not price: missing_data.append("price") 
                    if not change_24h: missing_data.append("24h_change")
                    
                    if missing_data:
                        print(f"⚠️  SAVED with missing data: Rank {rank} - {name} ({symbol}) - Missing: {', '.join(missing_data)}")
                        print(f"   Row text for debugging: '{row_text[:150]}{'...' if len(row_text) > 150 else ''}'")
                    else:
                        print(f"✅ SAVED: Rank {rank} - {name} ({symbol}) - {market_cap or 'N/A'} - {price or 'N/A'} - {change_24h or 'N/A'}")
                        
                        # Special debugging for ICBC-like cases
                        if name and 'icbc' in name.lower() and price:
                            print(f"🔍 ICBC DEBUG: Extracted price '{price}' from row text: '{row_text[:100]}'")
                        
                        # Debug for any price that looks wrong
                        if price:
                            try:
                                price_val = float(price.replace('$', '').replace(',', ''))
                                if price_val > 1000:  # Very high prices might be wrong
                                    print(f"🔍 HIGH PRICE DEBUG: {name} price {price} - check if correct")
                            except:
                                pass
                
                else:
                    # This is critical - we should have found a rank if this is a data row
                    print(f"🚨 CRITICAL: Row {i+1} has no rank but may be a data row!")
                    print(f"   Full row text: '{row_text}'")
                    print(f"   HTML: {row.get_attribute('outerHTML')[:200]}...")
                    
                    # Try one final desperate attempt to extract rank
                    all_numbers = re.findall(r'\b(\d{1,3})\b', row_text)
                    for num_str in all_numbers:
                        num = int(num_str)
                        if 1 <= num <= 500:
                            print(f"🚨 EMERGENCY: Found potential rank {num} in text")
                            emergency_data = {
                                "rank": num,
                                "name": f"Emergency_Asset_Rank_{num}",
                                "symbol": "N/A",
                                "market_cap": "",
                                "market_cap_raw": 0,
                                "price": "",
                                "price_raw": 0.0,
                                "change_24h": "",
                                "category": "",
                                "snapshot_date": today
                            }
                            companies.append(emergency_data)
                            print(f"🚨 EMERGENCY SAVED: Rank {num}")
                            break
                
            except Exception as e:
                print(f"❌ Error processing row {i+1}: {e}")
                # Try to extract at least the rank if possible
                try:
                    row_text = row.text.strip()
                    if row_text:
                        rank_match = re.search(r'^(\d{1,3})\s', row_text)
                        if rank_match:
                            emergency_rank = int(rank_match.group(1))
                            if 1 <= emergency_rank <= 500:
                                print(f"🚨 Emergency extraction: Found rank {emergency_rank} in failed row")
                                emergency_data = {
                                    "rank": emergency_rank,
                                    "name": f"Emergency_Asset_Rank_{emergency_rank}",
                                    "symbol": "N/A",
                                    "market_cap": "",
                                    "market_cap_raw": 0,
                                    "price": "",
                                    "price_raw": 0.0,
                                    "change_24h": "",
                                    "category": "",
                                    "snapshot_date": today
                                }
                                companies.append(emergency_data)
                                print(f"🚨 Emergency save: Rank {emergency_rank}")
                except:
                    pass
                continue
        
        # Comprehensive analysis of what we found vs what we expected
        found_ranks = [comp["rank"] for comp in companies]
        found_ranks.sort()
        
        print(f"\n📊 PAGE {page_num} SUMMARY:")
        print(f"   Processed rows: {len(rows)}")
        print(f"   Found companies: {len(companies)}")
        
        if found_ranks:
            print(f"   Rank range: {found_ranks[0]}-{found_ranks[-1]}")
            print(f"   All ranks found: {found_ranks}")
            
            # Check for missing ranks in the expected range
            expected_start = (page_num - 1) * 100 + 1
            expected_end = min(page_num * 100, 500)  # Cap at 500
            expected_ranks = set(range(expected_start, expected_end + 1))
            actual_ranks = set(found_ranks)
            missing_ranks = expected_ranks - actual_ranks
            
            if missing_ranks:
                missing_list = sorted(list(missing_ranks))
                print(f"⚠️  MISSING RANKS: {missing_list}")
                print(f"   Expected {len(expected_ranks)} ranks, found {len(actual_ranks)}")
                
                # Show which specific ranks we're missing
                for rank in missing_list:
                    print(f"      Missing rank {rank} (should be on page {page_num})")
            else:
                print(f"✅ All expected ranks found for page {page_num}")
        else:
            print(f"❌ NO COMPANIES FOUND - CRITICAL ISSUE!")
            print(f"   This indicates a fundamental scraping problem")
        
        return companies
        
    except Exception as e:
        print(f"❌ Error scraping page {page_num}: {e}")
        return []

def parse_market_cap_to_number(market_cap_text):
    """Convert market cap text like '$3.512 T' to raw number"""
    if not market_cap_text:
        return 0
    
    try:
        clean_text = market_cap_text.replace('$', '').replace(',', '').strip()
        
        if 'T' in clean_text:
            value = float(clean_text.replace('T', '').strip()) * 1_000_000_000_000
        elif 'B' in clean_text:
            value = float(clean_text.replace('B', '').strip()) * 1_000_000_000
        elif 'M' in clean_text:
            value = float(clean_text.replace('M', '').strip()) * 1_000_000
        else:
            value = float(clean_text)
        
        return int(value)
    except:
        return 0

def parse_price_to_number(price_text):
    """Convert price text like '$142.83' to raw number"""
    if not price_text:
        return 0.0
    
    try:
        clean_text = price_text.replace('$', '').replace(',', '').strip()
        value = float(clean_text)
        return round(value, 2)
    except:
        return 0.0

def classify_companies_with_gpt(companies_batch):
    """Use ChatGPT API to classify assets by category, provide correct ticker symbols, and verify USD prices"""
    if not companies_batch:
        return companies_batch
    
    # Prepare the company list for the API - clean up names
    company_list = []
    for company in companies_batch:
        # Clean up company name further
        clean_name = company["name"]
        clean_name = re.sub(r'\n\d+$', '', clean_name)  # Remove trailing "\n1", "\n2", etc.
        clean_name = re.sub(r'^\d+\s*', '', clean_name)  # Remove leading numbers
        clean_name = normalize_text(clean_name.strip())
        
        company_info = {
            "name": clean_name,
            "scraped_symbol": company["symbol"] if company["symbol"] != "N/A" else "NONE",
            "market_cap": company["market_cap"],
            "rank": company["rank"]
        }
        company_list.append(company_info)
    
    # Asset categories (broader than GICS for different asset types)
    asset_categories = [
        "Technology Stock", "Financial Stock", "Healthcare Stock", "Energy Stock",
        "Consumer Stock", "Industrial Stock", "Telecom Stock", "Utility Stock",
        "Precious Metals", "Commodities", "Cryptocurrency", "ETF", 
        "REIT", "Index Fund", "Bond", "Currency", "Other"
    ]
    
    prompt = f"""
    Please classify these assets by category and provide correct ticker symbols ONLY.
    DO NOT provide prices - I will use the scraped price data.
    
    Assets to classify:
    {json.dumps(company_list, indent=2)}
    
    Categories to choose from:
    {', '.join(asset_categories)}
    
    CRITICAL REQUIREMENTS:
    1. PRIORITIZE scraped_symbol - if it exists and looks valid, KEEP IT UNCHANGED
    2. Each symbol must be UNIQUE - never assign the same symbol to different companies
    3. For cryptocurrencies, use format like BTC-USD, ETH-USD, etc.
    4. For commodities, use ETF tickers (GLD for Gold, SLV for Silver, etc.)
    5. For stocks, use the exact ticker that traders search for
    
    Symbol Priority Rules:
    - If scraped_symbol exists and is 2-5 characters → KEEP IT
    - If scraped_symbol is "NONE" → provide correct ticker
    
    Respond with JSON array only (NO PRICES - just symbol and category):
    [
      {{"name": "Microsoft", "symbol": "MSFT", "category": "Technology Stock"}},
      {{"name": "ICBC", "symbol": "IDCBY", "category": "Financial Stock"}}
    ]
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial analyst expert in asset classification and ticker symbols. CRITICAL: 1) Use scraped symbols as primary reference when valid, 2) Ensure ALL symbols are UNIQUE, 3) Respond only with valid JSON including name, symbol, and category (NO PRICES)."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        
        response_content = response.choices[0].message.content.strip()
        
        # Clean up response
        if response_content.startswith('```json'):
            response_content = response_content[7:]
        if response_content.endswith('```'):
            response_content = response_content[:-3]
        
        classifications = json.loads(response_content)
        
        # Verify symbol uniqueness from ChatGPT response
        used_symbols = set()
        duplicate_symbols = []
        for classification in classifications:
            symbol = classification.get("symbol", "")
            if symbol and symbol != "N/A":
                if symbol in used_symbols:
                    duplicate_symbols.append(symbol)
                else:
                    used_symbols.add(symbol)
        
        if duplicate_symbols:
            print(f"⚠️  Warning: ChatGPT returned duplicate symbols: {duplicate_symbols}")
        
        # Update companies with classifications and verified prices
        for company in companies_batch:
            # Clean up the company name for matching
            clean_company_name = re.sub(r'\n\d+$', '', company["name"])
            clean_company_name = re.sub(r'^\d+\s*', '', clean_company_name).strip()
            clean_company_name = normalize_text(clean_company_name)
            
            for classification in classifications:
                if (classification["name"].lower() in clean_company_name.lower() or 
                    clean_company_name.lower() in classification["name"].lower()):
                    # Update the name to the cleaned version
                    company["name"] = clean_company_name
                    # Update symbol and category (KEEP SCRAPED PRICE)
                    company["symbol"] = classification["symbol"]
                    company["category"] = classification["category"]
                    
                    print(f"✅ Updated: {company['name']} → {company['symbol']}, {company['category']} (Price: {company['price']})")
                    break
        
        print(f"✅ Classified {len(companies_batch)} assets with ChatGPT (symbols and categories only)")
        
        # Assign fallback categories for unclassified assets
        for company in companies_batch:
            if not company.get("category") or company["category"] == "":
                company["category"] = assign_fallback_category(company["name"])
        
        return companies_batch
        
    except Exception as e:
        print(f"⚠️  ChatGPT classification error: {e}")
        # Set default values if API fails
        for company in companies_batch:
            # Clean up the name even if classification fails
            clean_name = re.sub(r'\n\d+$', '', company["name"])
            clean_name = re.sub(r'^\d+\s*', '', clean_name).strip()
            company["name"] = normalize_text(clean_name)
            
            if not company.get("category"):
                company["category"] = assign_fallback_category(company["name"])
        return companies_batch

def assign_fallback_category(asset_name):
    """Assign fallback category based on asset name patterns"""
    name_lower = asset_name.lower()
    
    # Technology companies
    if any(tech in name_lower for tech in ['microsoft', 'apple', 'google', 'meta', 'nvidia', 'intel', 'amd', 'tesla', 'amazon', 'netflix', 'adobe', 'salesforce', 'oracle', 'ibm']):
        return "Technology Stock"
    
    # Financial companies
    if any(fin in name_lower for fin in ['bank', 'jpmorgan', 'wells fargo', 'goldman sachs', 'morgan stanley', 'citigroup', 'visa', 'mastercard', 'paypal', 'berkshire hathaway']):
        return "Financial Stock"
    
    # Healthcare/Pharma
    if any(health in name_lower for health in ['johnson', 'pfizer', 'merck', 'abbott', 'bristol myers', 'eli lilly', 'roche', 'novartis', 'health', 'pharma', 'medical']):
        return "Healthcare Stock"
    
    # Energy companies
    if any(energy in name_lower for energy in ['exxon', 'chevron', 'shell', 'bp', 'conocophillips', 'energy', 'oil', 'gas']):
        return "Energy Stock"
    
    # Consumer companies
    if any(consumer in name_lower for consumer in ['coca cola', 'pepsi', 'procter', 'walmart', 'target', 'home depot', 'nike', 'starbucks', 'mcdonald']):
        return "Consumer Stock"
    
    # Precious metals and commodities
    if any(metal in name_lower for metal in ['gold', 'silver', 'platinum', 'copper', 'aluminum']):
        return "Precious Metals"
    
    # Cryptocurrencies
    if any(crypto in name_lower for crypto in ['bitcoin', 'ethereum', 'coin', 'crypto', 'blockchain']):
        return "Cryptocurrency"
    
    # ETFs
    if any(etf in name_lower for etf in ['etf', 'fund', 'trust', 'spdr', 'ishares', 'vanguard']):
        return "ETF"
    
    # Default category
    return "Other"



def retry_missing_assets(driver, all_companies, max_retries=3):
    """Retry scraping to find missing assets"""
    all_ranks = [comp["rank"] for comp in all_companies]
    expected_ranks = set(range(1, 501))
    found_ranks = set(all_ranks)
    missing_ranks = expected_ranks - found_ranks
    
    if not missing_ranks:
        print("✅ All ranks 1-500 found!")
        return all_companies
    
    print(f"⚠️  Missing {len(missing_ranks)} ranks: {sorted(list(missing_ranks))[:20]}{'...' if len(missing_ranks) > 20 else ''}")
    
    retry_count = 0
    while missing_ranks and retry_count < max_retries:
        retry_count += 1
        print(f"\n🔄 Retry attempt {retry_count}/{max_retries} for {len(missing_ranks)} missing assets...")
        
        # Determine which pages to re-scrape based on missing ranks
        pages_to_retry = set()
        for rank in missing_ranks:
            page_num = ((rank - 1) // 100) + 1
            pages_to_retry.add(page_num)
        
        print(f"🎯 Re-scraping pages: {sorted(pages_to_retry)}")
        
        # Re-scrape the needed pages
        retry_companies = []
        for page in sorted(pages_to_retry):
            print(f"\n📄 Re-scraping page {page}...")
            companies = scrape_8marketcap_page(driver, page)
            retry_companies.extend(companies)
            time.sleep(3)
        
        # Add newly found companies that were missing
        newly_found = 0
        for company in retry_companies:
            if company["rank"] in missing_ranks:
                # Check if we already have this rank
                existing_ranks = [comp["rank"] for comp in all_companies]
                if company["rank"] not in existing_ranks:
                    all_companies.append(company)
                    newly_found += 1
                    print(f"✅ Found missing rank {company['rank']}: {company['name']}")
        
        # Update missing ranks
        all_ranks = [comp["rank"] for comp in all_companies]
        found_ranks = set(all_ranks)
        missing_ranks = expected_ranks - found_ranks
        
        print(f"📊 Retry {retry_count}: Found {newly_found} new assets, {len(missing_ranks)} still missing")
        
        if not missing_ranks:
            print("🎉 All assets found after retry!")
            break
    
    if missing_ranks:
        print(f"⚠️  After {max_retries} retries, still missing {len(missing_ranks)} ranks")
        missing_list = sorted(list(missing_ranks))
        print(f"   Missing ranks: {missing_list}")
    
    return all_companies

def main():
    """Main scraping function"""
    print("🚀 Starting 8marketcap.com scraper...")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        all_companies = []
        
        # Initial scrape of all pages
        print("📋 Phase 1: Initial scraping of all pages...")
        for page in range(1, 6):  # Pages 1-5
            print(f"\n📄 Scraping page {page}...")
            companies = scrape_8marketcap_page(driver, page)
            all_companies.extend(companies)
            print(f"📊 Page {page}: Found {len(companies)} companies")
            time.sleep(3)  # Be respectful to the server
        
        print(f"\n📈 Phase 1 complete: {len(all_companies)} companies scraped")
        
        # Check for missing ranks and retry if needed
        print("\n📋 Phase 2: Checking for missing assets and retrying...")
        all_companies = retry_missing_assets(driver, all_companies, max_retries=3)
        
        print(f"\n📈 Total companies after retries: {len(all_companies)}")
        
        # Final verification
        if all_companies:
            all_ranks = [comp["rank"] for comp in all_companies]
            all_ranks.sort()
            print(f"📊 Final rank range: {all_ranks[0]} to {all_ranks[-1]}")
            
            # Check for any remaining gaps
            rank_set = set(all_ranks)
            expected_ranks = set(range(1, 501))  # Expecting ranks 1-500
            missing_ranks = expected_ranks - rank_set
            if missing_ranks:
                missing_list = sorted(list(missing_ranks))
                print(f"⚠️  Final missing ranks ({len(missing_ranks)}): {missing_list}")
            else:
                print(f"✅ SUCCESS: All ranks 1-{max(all_ranks)} found!")
        
        if not all_companies:
            print("❌ No companies found!")
            return
        
        # Sort by market cap
        all_companies.sort(key=lambda x: x['market_cap_raw'], reverse=True)
        top_500 = all_companies[:500]
        
        print(f"🤖 Classifying {len(top_500)} assets using ChatGPT...")
        
        # Process in batches for ChatGPT
        classified_companies = []
        batch_size = 50
        
        for i in range(0, len(top_500), batch_size):
            batch = top_500[i:i+batch_size]
            print(f"🔄 Processing batch {i//batch_size + 1}/{(len(top_500) + batch_size - 1)//batch_size}")
            
            classified_batch = classify_companies_with_gpt(batch)
            classified_companies.extend(classified_batch)
            time.sleep(2)  # Rate limiting
        
        # Final verification: Check for duplicate symbols across all assets
        print(f"\n🔍 Verifying symbol uniqueness across all {len(classified_companies)} assets...")
        symbol_map = {}
        duplicates = []
        
        for i, company in enumerate(classified_companies):
            symbol = company.get("symbol", "")
            if symbol and symbol != "N/A":
                if symbol in symbol_map:
                    duplicates.append({
                        "symbol": symbol,
                        "companies": [symbol_map[symbol], {"name": company["name"], "index": i}]
                    })
                else:
                    symbol_map[symbol] = {"name": company["name"], "index": i}
        
        if duplicates:
            print(f"⚠️  Found {len(duplicates)} duplicate symbols, fixing...")
            for dup in duplicates:
                # Keep the first occurrence, modify the second
                second_company = classified_companies[dup["companies"][1]["index"]]
                original_symbol = dup["symbol"]
                # Add a suffix to make it unique
                new_symbol = f"{original_symbol}2"
                # Check if the new symbol is also taken
                counter = 2
                while new_symbol in symbol_map:
                    counter += 1
                    new_symbol = f"{original_symbol}{counter}"
                
                second_company["symbol"] = new_symbol
                symbol_map[new_symbol] = {"name": second_company["name"], "index": dup["companies"][1]["index"]}
                print(f"   Fixed: {second_company['name']} → {original_symbol} changed to {new_symbol}")
        else:
            print(f"✅ All symbols are unique!")
        
        print(f"\n📊 Data Verification Summary:")
        print(f"   Total assets: {len(classified_companies)}")
        
        # Show sample data for verification
        print(f"\n🔍 Sample Data (first 5 assets):")
        for i, company in enumerate(classified_companies[:5], 1):
            print(f"   {i}. {company['name']} ({company['symbol']})")
            print(f"      Market Cap: {company['market_cap']} | Price: {company['price']} | 24h: {company['change_24h']}")
            print(f"      Category: {company['category']}")
            print()
        
        # Data quality checks
        print(f"📈 Data Quality Analysis:")
        companies_with_market_cap = sum(1 for c in classified_companies if c['market_cap'])
        companies_with_price = sum(1 for c in classified_companies if c['price'])
        companies_with_24h = sum(1 for c in classified_companies if c['change_24h'])
        companies_with_symbol = sum(1 for c in classified_companies if c['symbol'] and c['symbol'] != 'N/A')
        companies_with_category = sum(1 for c in classified_companies if c['category'] and c['category'] != '')
        companies_with_fallback = sum(1 for c in classified_companies if c['category'] == 'Other')
        companies_with_gpt_category = sum(1 for c in classified_companies if c['category'] and c['category'] not in ['Other', 'Unknown', ''])
        
        print(f"   Assets with Market Cap: {companies_with_market_cap}/{len(classified_companies)} ({companies_with_market_cap/len(classified_companies)*100:.1f}%)")
        print(f"   Assets with Price: {companies_with_price}/{len(classified_companies)} ({companies_with_price/len(classified_companies)*100:.1f}%)")
        print(f"   Assets with 24h Change: {companies_with_24h}/{len(classified_companies)} ({companies_with_24h/len(classified_companies)*100:.1f}%)")
        print(f"   Assets with Symbol: {companies_with_symbol}/{len(classified_companies)} ({companies_with_symbol/len(classified_companies)*100:.1f}%)")
        print(f"   Assets with Category: {companies_with_category}/{len(classified_companies)} ({companies_with_category/len(classified_companies)*100:.1f}%)")
        print(f"   Assets with ChatGPT Category: {companies_with_gpt_category}/{len(classified_companies)} ({companies_with_gpt_category/len(classified_companies)*100:.1f}%)")
        print(f"   Assets with Fallback Category: {companies_with_fallback}/{len(classified_companies)} ({companies_with_fallback/len(classified_companies)*100:.1f}%)")
        
        # Final cleanup - normalize all asset names before saving
        print(f"\n🔤 Applying final name normalization...")
        for company in classified_companies:
            company["name"] = normalize_text(company["name"])
        
        # Final deduplication step to remove assets with the same rank
        print(f"\n🔍 Deduplicating {len(classified_companies)} assets before saving...")
        unique_assets = {}
        for company in classified_companies:
            rank = company.get("rank")
            if rank is not None:
                # Keep the first asset found for a given rank
                if rank not in unique_assets:
                    unique_assets[rank] = company
            else:
                # If rank is None, use name as a key to deduplicate
                name = company.get("name", "")
                if name and name not in unique_assets:
                    unique_assets[name] = company

        final_assets = list(unique_assets.values())
        
        if len(final_assets) < len(classified_companies):
            print(f"⚠️  Removed {len(classified_companies) - len(final_assets)} duplicate assets.")
        
        classified_companies = final_assets

        # Save to Supabase database 
        print(f"\n💾 Saving {len(classified_companies)} assets to Supabase database...")
        
        # First, try to clear existing data for today
        try:
            print(f"🗑️  Clearing existing data for {today}...")
            delete_result = supabase.table("assets").delete().eq("snapshot_date", today).execute()
            print(f"✅ Cleared existing records for {today}")
        except Exception as e:
            print(f"⚠️  Warning: Could not clear existing data: {e}")
        
        # Now insert the new data
        try:
            result = supabase.table("assets").insert(classified_companies).execute()
            if result.data:
                print(f"✅ Successfully saved {len(result.data)} assets to assets table!")
            else:
                print(f"⚠️  Warning: Insert returned no data, but no error occurred")
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
            if "23505" in str(e) or "duplicate key" in str(e).lower():
                print(f"💡 Duplicate key error detected. Trying batch processing...")
                # Try inserting in smaller batches to isolate problematic records
                success_count = 0
                batch_size = 50
                
                for i in range(0, len(classified_companies), batch_size):
                    batch = classified_companies[i:i+batch_size]
                    try:
                        batch_result = supabase.table("assets").insert(batch).execute()
                        if batch_result.data:
                            success_count += len(batch_result.data)
                        print(f"✅ Batch {i//batch_size + 1}: {len(batch)} records")
                    except Exception as batch_error:
                        print(f"❌ Batch {i//batch_size + 1} failed: {batch_error}")
                        # Try individual records in this batch
                        for j, record in enumerate(batch):
                            try:
                                single_result = supabase.table("assets").insert([record]).execute()
                                if single_result.data:
                                    success_count += 1
                            except Exception as single_error:
                                print(f"⚠️  Skipped duplicate: {record.get('symbol', 'Unknown')} - {single_error}")
                
                print(f"✅ Successfully saved {success_count} assets using batch processing!")
            else:
                print(f"💡 Make sure your assets table is properly set up")
        
        # Show top assets by market cap
        print(f"\n🏆 Top 10 Assets by Market Cap:")
        top_10 = sorted(classified_companies, key=lambda x: x['market_cap_raw'], reverse=True)[:10]
        for i, company in enumerate(top_10, 1):
            market_cap_billions = company['market_cap_raw'] / 1_000_000_000
            print(f"   {i:2d}. {company['name']:<30} {company['symbol']:<8} {company['market_cap']:<10} (${market_cap_billions:.1f}B)")
    
    finally:
        driver.quit()
        print("🏁 Scraper finished!")

if __name__ == "__main__":
    main()
