from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import re
import unicodedata
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from datetime import date

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get today's date
today = date.today().isoformat()

# Set up Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

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

def parse_bitcoin_amount(bitcoin_text):
    """Convert bitcoin text like '₿ 9,720' to raw number"""
    if not bitcoin_text:
        return 0
    
    try:
        # Remove bitcoin symbol and commas
        clean_text = bitcoin_text.replace('₿', '').replace(',', '').strip()
        value = float(clean_text)
        return int(value)
    except:
        return 0

def parse_usd_value(usd_text):
    """Convert USD text like '$1.03B' to raw number"""
    if not usd_text:
        return 0
    
    try:
        clean_text = usd_text.replace('$', '').replace(',', '').strip()
        
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

def scrape_country_holdings():
    """Scrape government/country Bitcoin holdings from bitcointreasuries.net"""
    
    print("🌍 Bitcoin Treasuries - Government/Country Holdings Scraper")
    print("=" * 80)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Navigate to the government holdings page
        url = 'https://bitcointreasuries.net/embed?component=MainTable&embedConfig=%7B%22limit%22%3A20%2C%22disableGrouping%22%3Atrue%2C%22role%22%3A%22holder%22%2C%22entityTypes%22%3A%5B%22GOVERNMENT%22%5D%7D'
        print(f"🌐 Navigating to: {url}")
        driver.get(url)
        
        # Wait for page to load
        print("⏳ Waiting for page to load...")
        time.sleep(10)
        
        # Debug: Check page source
        page_source = driver.page_source
        if 'table' in page_source.lower():
            print("✅ Found table elements in page source")
        else:
            print("⚠️  No table elements found, checking for other structures...")
        
        # Look for table rows
        countries = []
        
        # Try multiple selectors to find the data
        selectors_to_try = [
            'table tbody tr',
            'table tr',
            '[role="row"]',
            '.table-row',
            'tr'
        ]
        
        rows = []
        for selector in selectors_to_try:
            try:
                found_rows = driver.find_elements(By.CSS_SELECTOR, selector)
                if found_rows and len(found_rows) > 1:  # More than just header
                    rows = found_rows
                    print(f"✅ Found {len(rows)} rows using selector: {selector}")
                    break
            except:
                continue
        
        if not rows:
            print("❌ No table rows found")
            return []
        
        print(f"📊 Processing {len(rows)} rows...")
        
        for i, row in enumerate(rows):
            try:
                row_text = row.text.strip()
                print(f"\n🔍 Row {i+1}: '{row_text[:100]}{'...' if len(row_text) > 100 else ''}'")
                
                # Skip empty rows
                if not row_text or len(row_text.strip()) < 3:
                    print(f"   Skipping empty row")
                    continue
                
                # Skip header rows
                if any(header in row_text.lower() for header in ['rank', 'name', 'bitcoin', 'usd value', 'entity']):
                    print(f"   Skipping header row")
                    continue
                
                # Get all td elements
                tds = row.find_elements(By.TAG_NAME, 'td')
                if len(tds) < 3:
                    print(f"   Not enough columns ({len(tds)}), trying div elements...")
                    # Try div elements as fallback
                    tds = row.find_elements(By.TAG_NAME, 'div')
                
                print(f"   Found {len(tds)} columns")
                
                # Initialize variables
                rank = None
                country_name = ""
                bitcoin_amount = ""
                usd_value = ""
                
                # Extract data from columns
                if len(tds) >= 3:
                    # Try to extract rank from first column
                    try:
                        rank_text = tds[0].text.strip()
                        if rank_text and rank_text.isdigit():
                            rank = int(rank_text)
                            print(f"   📊 Rank: {rank}")
                    except:
                        pass
                    
                    # Extract country name (usually second column)
                    try:
                        name_text = tds[1].text.strip()
                        if name_text and len(name_text) > 1:
                            country_name = normalize_text(name_text)
                            print(f"   🌍 Country: {country_name}")
                    except:
                        pass
                    
                    # Extract Bitcoin amount (look for ₿ symbol)
                    for td in tds:
                        td_text = td.text.strip()
                        if '₿' in td_text or 'btc' in td_text.lower():
                            bitcoin_amount = td_text
                            print(f"   ₿ Bitcoin: {bitcoin_amount}")
                            break
                    
                    # Extract USD value (look for $ symbol)
                    for td in tds:
                        td_text = td.text.strip()
                        if '$' in td_text and not '₿' in td_text:
                            usd_value = td_text
                            print(f"   💵 USD Value: {usd_value}")
                            break
                
                # If we didn't find structured data, try parsing from row text
                if not country_name or not bitcoin_amount:
                    print(f"   🔄 Fallback: Parsing from row text...")
                    
                    # Try to extract Bitcoin amount from row text
                    if not bitcoin_amount:
                        bitcoin_match = re.search(r'₿\s*[\d,]+', row_text)
                        if bitcoin_match:
                            bitcoin_amount = bitcoin_match.group(0)
                            print(f"   ₿ Bitcoin (fallback): {bitcoin_amount}")
                    
                    # Try to extract USD value from row text
                    if not usd_value:
                        usd_match = re.search(r'\$[\d,]+\.?\d*[BMT]?', row_text)
                        if usd_match:
                            usd_value = usd_match.group(0)
                            print(f"   💵 USD Value (fallback): {usd_value}")
                    
                    # Extract country name (remove numbers and symbols)
                    if not country_name:
                        # Remove rank numbers, bitcoin symbols, and USD values
                        clean_text = re.sub(r'^\d+\s*', '', row_text)  # Remove leading numbers
                        clean_text = re.sub(r'₿[\d,\s]+', '', clean_text)  # Remove bitcoin amounts
                        clean_text = re.sub(r'\$[\d,]+\.?\d*[BMT]?', '', clean_text)  # Remove USD amounts
                        clean_text = clean_text.strip()
                        
                        if clean_text and len(clean_text) > 2:
                            country_name = normalize_text(clean_text)
                            print(f"   🌍 Country (fallback): {country_name}")
                
                # Only save if we have at least a country name and some financial data
                if country_name and (bitcoin_amount or usd_value):
                    country_data = {
                        "rank": rank,
                        "government_name": country_name,  # Changed to match table schema
                        "bitcoin_amount": bitcoin_amount,
                        "bitcoin_raw": parse_bitcoin_amount(bitcoin_amount),
                        "usd_value": usd_value,
                        "usd_raw": parse_usd_value(usd_value),
                        "snapshot_date": today
                    }
                    
                    countries.append(country_data)
                    print(f"   ✅ SAVED: {country_name} - {bitcoin_amount} - {usd_value}")
                else:
                    print(f"   ❌ Insufficient data, skipping")
                
            except Exception as e:
                print(f"   ❌ Error processing row {i+1}: {e}")
                continue
        
        return countries
        
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        return []
    
    finally:
        driver.quit()

def print_country_holdings(countries):
    """Print the country holdings data in a formatted table"""
    
    if not countries:
        print("❌ No country data found!")
        return
    
    print(f"\n" + "=" * 100)
    print("🌍 GOVERNMENT/COUNTRY BITCOIN HOLDINGS")
    print("=" * 100)
    print(f"{'Rank':<6} {'Country':<30} {'Bitcoin Holdings':<20} {'USD Value':<15} {'Raw BTC':<12} {'Raw USD':<15}")
    print("-" * 100)
    
    total_btc = 0
    total_usd = 0
    
    for country in countries:
        rank = country['rank'] if country['rank'] else 'N/A'
        name = country['government_name'][:28] if len(country['government_name']) > 28 else country['government_name']
        bitcoin = country['bitcoin_amount'] if country['bitcoin_amount'] else 'N/A'
        usd = country['usd_value'] if country['usd_value'] else 'N/A'
        btc_raw = country['bitcoin_raw']
        usd_raw = country['usd_raw']
        
        total_btc += btc_raw
        total_usd += usd_raw
        
        print(f"{str(rank):<6} {name:<30} {bitcoin:<20} {usd:<15} {btc_raw:>12,} {usd_raw:>15,}")
    
    print("-" * 100)
    print(f"{'TOTAL':<6} {'':<30} {'':<20} {'':<15} {total_btc:>12,} {total_usd:>15,}")
    print("=" * 100)
    
    # Summary statistics
    print(f"\n📊 SUMMARY:")
    print(f"   Total Countries/Governments: {len(countries)}")
    print(f"   Total Bitcoin Holdings: {total_btc:,} BTC")
    print(f"   Total USD Value: ${total_usd:,}")
    print(f"   Average Holdings per Country: {total_btc // len(countries):,} BTC")
    
    # Top holders
    if len(countries) > 1:
        sorted_countries = sorted(countries, key=lambda x: x['bitcoin_raw'], reverse=True)
        print(f"\n🏆 TOP HOLDERS:")
        for i, country in enumerate(sorted_countries[:5], 1):
            btc_pct = (country['bitcoin_raw'] / total_btc * 100) if total_btc > 0 else 0
            print(f"   {i}. {country['government_name']}: {country['bitcoin_raw']:,} BTC ({btc_pct:.1f}%)")

def save_to_supabase(countries):
    """Save country holdings data to Supabase"""
    if not countries:
        print("❌ No data to save!")
        return False
    
    try:
        print(f"\n💾 Saving {len(countries)} country holdings to Supabase...")
        
        # First, try to clear existing data for today
        try:
            print(f"🗑️  Clearing existing data for {today}...")
            delete_result = supabase.table("government_holding").delete().eq("snapshot_date", today).execute()
            print(f"✅ Cleared existing records for {today}")
        except Exception as e:
            print(f"⚠️  Warning: Could not clear existing data: {e}")
        
        # Insert new data using upsert to handle duplicates
        try:
            result = supabase.table("government_holding").upsert(
                countries,
                on_conflict="government_name,snapshot_date"
            ).execute()
            
            if result.data:
                print(f"✅ Successfully saved {len(result.data)} country holdings to Supabase!")
                return True
            else:
                print(f"⚠️  Warning: Insert returned no data, but no error occurred")
                return False
                
        except Exception as e:
            print(f"❌ Error saving to Supabase: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error during Supabase save: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Starting Government Bitcoin Holdings Scraper...")
    
    countries = scrape_country_holdings()
    
    if countries:
        print_country_holdings(countries)
        
        # Save to Supabase
        save_success = save_to_supabase(countries)
        
        if save_success:
            print(f"\n🎉 Complete! Successfully scraped and saved {len(countries)} country holdings!")
        else:
            print(f"\n⚠️  Scraping completed but saving to database failed.")
            
    else:
        print("❌ No country holdings data found!")
        print("\n🔍 Debug suggestions:")
        print("   1. Check if the website structure has changed")
        print("   2. Verify the URL is accessible")
        print("   3. Try running without headless mode for debugging")

if __name__ == "__main__":
    main()
