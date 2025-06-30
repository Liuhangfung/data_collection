"""
Enhanced Selenium configuration for Docker environments
Replace your Chrome options with this for better success rates
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import random
import time

def get_docker_chrome_options():
    """Get optimized Chrome options for Docker environment"""
    
    chrome_options = Options()
    
    # Essential headless options
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    
    # Anti-detection measures
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Realistic browser profile
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_argument('--accept-lang=en-US,en;q=0.9')
    
    # Window and display settings
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--start-maximized')
    
    # Memory and performance optimization
    chrome_options.add_argument('--memory-pressure-off')
    chrome_options.add_argument('--disable-background-timer-throttling')
    chrome_options.add_argument('--disable-renderer-backgrounding')
    chrome_options.add_argument('--disable-backgrounding-occluded-windows')
    
    # Network and security
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    
    # Additional stealth options
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--no-first-run')
    chrome_options.add_argument('--disable-default-apps')
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument('--disable-gpu-logging')
    
    return chrome_options

def setup_stealth_driver():
    """Create a stealthier Chrome driver instance"""
    
    chrome_options = get_docker_chrome_options()
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Execute stealth scripts
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def human_like_page_load(driver, url, min_wait=10, max_wait=20):
    """Load a page with human-like behavior"""
    
    print(f"🌐 Loading: {url}")
    driver.get(url)
    
    # Random wait time
    wait_time = random.uniform(min_wait, max_wait)
    print(f"⏳ Waiting {wait_time:.1f} seconds...")
    
    # Simulate human scrolling behavior
    try:
        # Scroll down slowly
        for i in range(3):
            scroll_pos = (i + 1) * (1080 // 4)
            driver.execute_script(f"window.scrollTo(0, {scroll_pos});")
            time.sleep(random.uniform(1, 3))
        
        # Scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(random.uniform(2, 4))
        
    except Exception as e:
        print(f"⚠️ Scrolling simulation failed: {e}")
    
    # Final wait
    time.sleep(wait_time)
    print("✅ Page loaded with human-like behavior")

# Example usage in your scrapers:
if __name__ == "__main__":
    driver = setup_stealth_driver()
    try:
        human_like_page_load(driver, "https://8marketcap.com")
        
        # Your scraping logic here
        tables = driver.find_elements("tag name", "table")
        print(f"Found {len(tables)} tables")
        
    finally:
        driver.quit() 