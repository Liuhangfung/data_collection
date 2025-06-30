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

# Set up Chrome options for headless mode (no browser window)
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
# Add UTF-8 encoding support
chrome_options.add_argument('--lang=en-US,en')
chrome_options.add_argument('--accept-charset=utf-8')

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

# Check if we already have data for today - if so, delete today's data only
try:
    existing_today = supabase.table("largest_companies").select("*").eq("snapshot_date", today).execute()
    if existing_today.data:
        supabase.table("largest_companies").delete().eq("snapshot_date", today).execute()
except Exception:
    pass

def scrape_page(driver, page_num):
    """Scrape a single page of companies"""
    try:
        # Navigate to the page
        if page_num == 1:
            url = 'https://companiesmarketcap.com/'
        else:
            url = f'https://companiesmarketcap.com/page/{page_num}/'
        
        driver.get(url)
        time.sleep(5)
        
        # Try different table selectors
        rows = []
        
        # Method 1: Try standard table rows
        try:
            rows = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
        except:
            pass
        
        # Method 2: Try without tbody
        if not rows:
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, 'table tr')
            except:
                pass
        
        # Method 3: Try direct tr elements
        if not rows:
            try:
                rows = driver.find_elements(By.TAG_NAME, 'tr')
            except:
                pass
        
        # Method 4: Try specific class if it exists
        if not rows:
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, '.table-row, .company-row, [class*="row"]')
            except:
                pass
        
        if not rows:
            return []
        
        companies = []
        
        for i, row in enumerate(rows):
            try:
                cells = row.find_elements(By.TAG_NAME, 'td')
                
                if len(cells) < 4:
                    continue

                # Check if this is actually a header row
                is_header = False
                if i == 0:
                    cell_texts = [cell.text.strip().lower() for cell in cells[:4]]
                    header_keywords = ['rank', 'company', 'market cap', 'price', 'name', 'symbol', 'ticker']
                    if any(keyword in ' '.join(cell_texts) for keyword in header_keywords):
                        is_header = True
                        continue

                rank = None
                company_name = ""
                ticker = ""
                market_cap = ""
                price = ""
                today_change = ""
                country = ""
                img_link = None
                
                # Try to get the company logo image
                try:
                    for cell in cells:
                        images = cell.find_elements(By.TAG_NAME, 'img')
                        for img_elem in images:
                            img_src = img_elem.get_attribute('src')
                            if img_src and not any(skip in img_src.lower() for skip in ['fav.svg', 'favicon', 'icon.svg', 'logo.svg']):
                                if any(pattern in img_src.lower() for pattern in ['logo', 'brand', 'company', '.png', '.jpg', '.jpeg']):
                                    img_link = img_src
                                    break
                        if img_link:
                            break
                    
                    if not img_link:
                        for cell in cells:
                            images = cell.find_elements(By.TAG_NAME, 'img')
                            for img_elem in images:
                                img_src = img_elem.get_attribute('src')
                                if img_src and not any(skip in img_src.lower() for skip in ['fav.svg', 'favicon']):
                                    img_link = img_src
                                    break
                            if img_link:
                                break
                except:
                    pass
                
                if img_link and any(skip in img_link.lower() for skip in ['fav.svg', 'favicon']):
                    img_link = None
                
                # Parse cell 2 for company name and ticker
                if len(cells) >= 3:
                    cell2_text = cells[2].text.strip()
                    if cell2_text:
                        cell2_text = cell2_text.replace('\n', ' ')
                        
                        match = re.match(r'^(.*?)\s+(\d{1,3})([A-Z0-9.\-]+)$', cell2_text)
                        if match:
                            company_name = match.group(1).strip()
                            rank_part = match.group(2)
                            ticker_part = match.group(3)
                            ticker = ticker_part
                            company_name = normalize_text(company_name)
                        else:
                            parts = cell2_text.split()
                            if len(parts) >= 2:
                                company_name = ' '.join(parts[:-1]).strip()
                                company_name = normalize_text(company_name)
                                last_part = parts[-1]
                                
                                ticker_match = re.match(r'^(\d{1,2})(\d*[A-Z0-9.\-]+)$', last_part)
                                if ticker_match:
                                    rank_part = ticker_match.group(1)
                                    ticker = ticker_match.group(2)
                                else:
                                    ticker = last_part
                            else:
                                company_name = cell2_text.strip()
                                company_name = normalize_text(company_name)
                                ticker = "UNKNOWN"
                
                # Parse cell 3 for market cap
                if len(cells) >= 4:
                    cell3_text = cells[3].text.strip()
                    if cell3_text and re.search(r'\$[\d,]+\.?\d*\s*[TMB]', cell3_text):
                        market_cap = cell3_text
                
                # Parse cell 4 for price
                price_raw = 0.0
                if len(cells) >= 5:
                    cell4_text = cells[4].text.strip()
                    if cell4_text and re.search(r'\$[\d,]+\.?\d*$', cell4_text):
                        price = cell4_text
                        price_raw = parse_price_to_number(cell4_text)
                
                # Parse cell 5 for change
                if len(cells) >= 6:
                    cell5_text = cells[5].text.strip()
                    if cell5_text and re.search(r'[+-]?\d+\.?\d*%', cell5_text):
                        # Check for color classes to determine positive/negative
                        try:
                            # Look for percentage elements with color classes
                            percentage_elements = cells[5].find_elements(By.CSS_SELECTOR, '[class*="percentage"], [class*="change"], span, div')
                            
                            is_negative = False
                            is_positive = False
                            
                            for elem in percentage_elements:
                                class_attr = elem.get_attribute('class') or ''
                                class_attr = class_attr.lower()
                                
                                # Check for red/negative indicators
                                if any(indicator in class_attr for indicator in ['red', 'negative', 'down', 'loss']):
                                    is_negative = True
                                    break
                                # Check for green/positive indicators  
                                elif any(indicator in class_attr for indicator in ['green', 'positive', 'up', 'gain']):
                                    is_positive = True
                                    break
                            
                            # If no specific class found, check the cell itself
                            if not is_negative and not is_positive:
                                cell_class = cells[5].get_attribute('class') or ''
                                cell_class = cell_class.lower()
                                
                                if any(indicator in cell_class for indicator in ['red', 'negative', 'down', 'loss']):
                                    is_negative = True
                                elif any(indicator in cell_class for indicator in ['green', 'positive', 'up', 'gain']):
                                    is_positive = True
                            
                            # Apply the correct sign
                            if is_negative and not cell5_text.startswith('-'):
                                today_change = '-' + cell5_text
                            elif is_positive and cell5_text.startswith('-'):
                                today_change = cell5_text[1:]  # Remove negative sign
                            else:
                                today_change = cell5_text
                                
                        except Exception:
                            # Fallback to original text if class checking fails
                            today_change = cell5_text
                
                # Country and industry will be determined by ChatGPT API later
                country = ""
                industry = ""
                
                # Generate ticker if we don't have one
                if not ticker:
                    ticker = "UNKNOWN"
                
                # Only add if we have essential data
                if company_name and market_cap:
                    company_data = {
                        "name": company_name[:255],
                        "ticker": ticker[:20] if ticker else "UNKNOWN",
                        "market_cap": market_cap,
                        "market_cap_raw": parse_market_cap_to_number(market_cap),
                        "price": price,
                        "price_raw": price_raw,
                        "today": today_change,
                        "country": country,
                        "industry": industry,
                        "primary_exchange": "Global",
                        "description": f"{company_name} - Global company ranked by market cap",
                        "homepage_url": "",
                        "image": img_link,
                        "snapshot_date": today
                    }
                    companies.append(company_data)
                    print(f"Found: {company_name} ({ticker}) - {market_cap}")
                
            except:
                continue
        
        return companies
            
    except:
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
    """Convert price text like '$142.83' or '$1,220' to raw number"""
    if not price_text:
        return 0.0
    
    try:
        clean_text = price_text.replace('$', '').replace(',', '').strip()
        value = float(clean_text)
        return round(value, 2)
    except:
        return 0.0

def normalize_text(text):
    """Normalize Unicode text to fix encoding issues"""
    if not text:
        return ""
    
    normalized = unicodedata.normalize('NFC', text)
    normalized = normalized.replace('癡', 'è')
    normalized = normalized.replace('脙', 'Ã')
    normalized = normalized.replace('陇', 'ç')
    
    return normalized.strip()

def classify_companies_with_gpt(companies_batch):
    """Use ChatGPT API to classify companies by country and GICS industry sector"""
    if not companies_batch:
        return companies_batch
    
    # Prepare the company list for the API
    company_list = []
    for company in companies_batch:
        company_info = {
            "name": company["name"],
            "ticker": company["ticker"]
        }
        company_list.append(company_info)
    
    # GICS 11 sectors
    gics_sectors = [
        "Energy",
        "Materials", 
        "Industrials",
        "Consumer Discretionary",
        "Consumer Staples",
        "Health Care",
        "Financials",
        "Information Technology",
        "Communication Services",
        "Utilities",
        "Real Estate"
    ]
    
    prompt = f"""
    Please classify the following companies by their country of origin and GICS industry sector.
    
    Companies to classify:
    {json.dumps(company_list, indent=2)}
    
    GICS Sectors to choose from:
    {', '.join(gics_sectors)}
    
    Please respond with a JSON array where each object contains:
    - "name": company name (exactly as provided)
    - "ticker": ticker symbol (exactly as provided)  
    - "country": country of origin (use these standardized names: USA, UK, China, Japan, Germany, France, Canada, Australia, India, South Korea, Taiwan, Netherlands, Switzerland, Denmark, Sweden, Norway, Italy, Spain, Brazil, Mexico, Saudi Arabia, UAE, Russia, etc.)
    - "industry": one of the GICS sectors listed above
    
    IMPORTANT: Use consistent country names:
    - Use "USA" not "United States"
    - Use "UK" not "United Kingdom" or "Great Britain"  
    - Use "UAE" not "United Arab Emirates"
    - Use "South Korea" not "Korea"
    - Use short, standardized country names consistently
    
    Example format:
    [
      {{"name": "Apple", "ticker": "AAPL", "country": "USA", "industry": "Information Technology"}},
      {{"name": "Toyota", "ticker": "TM", "country": "Japan", "industry": "Consumer Discretionary"}},
      {{"name": "ASML", "ticker": "ASML", "country": "Netherlands", "industry": "Information Technology"}}
    ]
    
    Respond with only the JSON array, no additional text.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial analyst expert in company classification. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        
        # Parse the response
        response_content = response.choices[0].message.content.strip()
        
        # Clean up the response in case there are markdown code blocks
        if response_content.startswith('```json'):
            response_content = response_content[7:]
        if response_content.endswith('```'):
            response_content = response_content[:-3]
        
        classifications = json.loads(response_content)
        
        # Update the companies with the classifications
        for company in companies_batch:
            for classification in classifications:
                if (classification["name"].lower() == company["name"].lower() or 
                    classification["ticker"].lower() == company["ticker"].lower()):
                    company["country"] = classification["country"]
                    company["industry"] = classification["industry"]
                    break
        
        print(f"Successfully classified {len(companies_batch)} companies with ChatGPT")
        return companies_batch
        
    except Exception as e:
        print(f"Error with ChatGPT classification: {e}")
        # Return companies with default values if API fails
        for company in companies_batch:
            if not company.get("country"):
                company["country"] = "Unknown"
            company["industry"] = "Unknown"
        return companies_batch

def main():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        all_companies = []
        
        print("Starting to scrape pages...")
        for page in range(1, 6):
            print(f"Scraping page {page}...")
            companies = scrape_page(driver, page)
            all_companies.extend(companies)
            print(f"Page {page}: Found {len(companies)} companies")
            time.sleep(2)
        
        print(f"Total companies scraped: {len(all_companies)}")
        
        if not all_companies:
            print("No companies found!")
            return
        
        all_companies.sort(key=lambda x: parse_market_cap_to_number(x['market_cap']), reverse=True)
        top_500 = all_companies[:500]
        
        print(f"Classifying {len(top_500)} companies using ChatGPT API...")
        
        # Process companies in batches of 50
        classified_companies = []
        batch_size = 50
        
        for i in range(0, len(top_500), batch_size):
            batch = top_500[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(top_500) + batch_size - 1)//batch_size} ({len(batch)} companies)")
            
            # Classify this batch using ChatGPT
            classified_batch = classify_companies_with_gpt(batch)
            classified_companies.extend(classified_batch)
            
            # Add a small delay between API calls to avoid rate limiting
            time.sleep(2)
        
        # Add rank and update descriptions
        for i, company in enumerate(classified_companies):
            company['rank'] = i + 1
            company['description'] = f"{company['name']} - Global company ranked #{i + 1} by market cap"
        
        print(f"Inserting top {len(classified_companies)} companies into database...")
        try:
            result = supabase.table("largest_companies").insert(classified_companies).execute()
            print(f"Successfully inserted {len(classified_companies)} companies into database!")
            
            # Refresh analysis views after successful data insertion
            print("\n🔄 Refreshing analysis views...")
            try:
                import subprocess
                result = subprocess.run(['python', 'refresh_analysis_views.py'], 
                                      capture_output=True, text=True, cwd='.')
                if result.returncode == 0:
                    print("✅ Analysis views refreshed successfully!")
                    if result.stdout:
                        print(result.stdout)
                else:
                    print(f"⚠️  Warning: View refresh had issues: {result.stderr}")
            except Exception as refresh_error:
                print(f"⚠️  Warning: Could not refresh views automatically: {refresh_error}")
                print("💡 Please run 'python refresh_analysis_views.py' manually")
            
            print("✅ Data insertion completed successfully!")
                
        except Exception as e:
            print(f"Error inserting into database: {e}")

    finally:
        driver.quit()
        print("Chrome driver closed.")

if __name__ == "__main__":
    main()
