from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from supabase import create_client
import os
import time
import tempfile
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Always use headless mode on server
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # Use a unique user data directory to avoid session conflicts
    user_data_dir = tempfile.mkdtemp()
    chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def get_aave_markets_data():
    driver = setup_driver()
    try:
        driver.get('https://app.aave.com/markets/')
        print("Page loaded. You have 30 seconds to interact with the browser (accept cookies, etc.) if needed...")
        time.sleep(30)
        html = driver.page_source
    finally:
        driver.quit()

    soup = BeautifulSoup(html, 'html.parser')
    printed_assets = set()
    data = []
    # Find all divs that contain an h4 (asset name)
    for card in soup.find_all('div'):
        h4 = card.find('h4')
        if not h4:
            continue
        asset_name = h4.get_text(strip=True)
        if asset_name in printed_assets:
            continue
        # Find all APY values in this card
        apys = card.find_all('p', attrs={'data-cy': 'apy'})
        supply_apy = apys[0].get_text(strip=True) if len(apys) > 0 else 'N/A'
        borrow_apy = apys[1].get_text(strip=True) if len(apys) > 1 else 'N/A'
        # Find total supplied
        total_supplied = 'N/A'
        for desc in card.find_all('div'):
            if desc.get_text(strip=True) == 'Total supplied':
                sib = desc.find_next('p')
                if sib:
                    total_supplied = sib.get_text(strip=True)
                break
        # Find total borrowed
        total_borrowed = 'N/A'
        for desc in card.find_all('div'):
            if desc.get_text(strip=True) == 'Total borrowed':
                sib = desc.find_next('p')
                if sib:
                    total_borrowed = sib.get_text(strip=True)
                break
        # Only print if at least one value is not N/A (to avoid printing empty cards)
        if supply_apy != 'N/A' or borrow_apy != 'N/A' or total_borrowed != 'N/A' or total_supplied != 'N/A':
            print(f"Asset: {asset_name}")
            print(f"  Total Supplied: {total_supplied}")
            print(f"  Supply APY: {supply_apy}")
            print(f"  Total Borrowed: {total_borrowed}")
            print(f"  Borrow APY: {borrow_apy}")
            print('-' * 40)
            printed_assets.add(asset_name)
            data.append({
                "asset_name": asset_name,
                "total_supplied": total_supplied,
                "supply_apy": supply_apy,
                "total_borrowed": total_borrowed,
                "borrow_apy": borrow_apy,
            })
    return data

def save_to_supabase(data):
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Supabase credentials are not set. Please set SUPABASE_URL and SUPABASE_ANON_KEY as environment variables.")
        return
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Delete all existing rows first
    print("Deleting all existing rows from aave_assets table...")
    supabase.table("aave_assets").delete().neq('id', 0).execute()
    # Insert new data
    for row in data:
        response = supabase.table("aave_assets").insert(row).execute()
        try:
            if response.status_code >= 300:
                print(f"Failed to insert: {row} | Response: {response}")
        except AttributeError:
            print(f"Unexpected response object: {response}")


def main():
    print("Fetching Aave markets data...")
    data = get_aave_markets_data()
    if data:
        print(f"Saving {len(data)} records to Supabase...")
        save_to_supabase(data)
    print("Done.")

if __name__ == "__main__":
    main()
