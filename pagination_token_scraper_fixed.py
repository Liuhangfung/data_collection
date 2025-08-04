#!/usr/bin/env python3
"""
Fixed Pagination Token Scraper

Fixes the viewport and scrolling issues to properly click pagination buttons.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime


async def capture_pagination_tokens(pages=5, headless=True):
    """
    Navigate through pagination and capture unique tokens for each page.
    Fixed version that handles viewport and scrolling issues.
    """
    from playwright.async_api import async_playwright
    
    print(f"🔐 Capturing pagination tokens for {pages} pages...")
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=headless,
        args=['--disable-blink-features=AutomationControlled', '--start-maximized']
    )
    
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    )
    
    page = await context.new_page()
    
    # Store tokens for each page
    page_tokens = {}
    
    async def handle_request(request):
        if 'quote-api' in request.url and 'heat-list' in request.url:
            headers = dict(request.headers)
            
            # Extract offset to determine page number
            import re
            offset_match = re.search(r'offset=(\d+)', request.url)
            offset = int(offset_match.group(1)) if offset_match else 0
            page_num = (offset // 50) + 1
            
            # Store tokens for this page
            page_tokens[page_num] = {
                'url': request.url,
                'headers': headers,
                'csrf_token': headers.get('futu-x-csrf-token'),
                'quote_token': headers.get('quote-token'),
                'offset': offset,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"🎯 Page {page_num}: Captured tokens (offset={offset})")
            print(f"   CSRF: {headers.get('futu-x-csrf-token', 'None')[:20]}...")
            print(f"   Quote: {headers.get('quote-token', 'None')}")
    
    page.on('request', handle_request)
    
    try:
        # Step 1: Navigate to Heat List
        print("🌐 Navigating to Heat List...")
        await page.goto('https://www.futunn.com/en/quote/us/most-active-stocks')
        await page.wait_for_load_state('networkidle')
        
        # Wait longer for initial API call (page 1)
        print("⏰ Waiting for initial API call (page 1)...")
        wait_start = time.time()
        while 1 not in page_tokens and (time.time() - wait_start) < 65:
            await asyncio.sleep(2)
            elapsed = time.time() - wait_start
            print(f"   ⏳ {elapsed:.0f}s", end='\r')
        
        if 1 not in page_tokens:
            print(f"\n⚠️ No initial API call captured in 65 seconds")
            # Try to trigger an API call by refreshing
            print("🔄 Refreshing page to trigger API call...")
            await page.reload()
            await asyncio.sleep(10)
        
        if 1 not in page_tokens:
            print("❌ Still no initial API call. Continuing anyway...")
        else:
            print(f"\n✅ Got initial API call after {time.time() - wait_start:.1f}s")
        
        # Get cookies (same for all pages)
        cookies = await context.cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        
        # Step 2: Scroll down to make pagination visible
        print(f"\n📜 Scrolling to pagination...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)
        
        # Wait for pagination to be visible
        try:
            await page.wait_for_selector('.base-pagination', timeout=10000, state='visible')
            print("✅ Pagination is visible")
        except Exception as e:
            print(f"⚠️ Pagination selector issue: {e}")
        
        # Step 3: Click through pagination pages
        for target_page in range(2, pages + 1):
            print(f"\n📄 Navigating to page {target_page}...")
            
            try:
                # More specific selector that should work
                page_selectors = [
                    f'span.item:has-text("{target_page}"):not(.current)',
                    f'.base-pagination span.item:text("{target_page}")',
                    f'span[data-v-51fb8c0d]:has-text("{target_page}")',
                ]
                
                clicked = False
                for selector in page_selectors:
                    try:
                        # Check if element exists and is clickable
                        element = await page.query_selector(selector)
                        if element:
                            # Scroll element into view
                            await element.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)
                            
                            # Force click
                            await element.click(force=True)
                            print(f"   ✅ Clicked page {target_page} (selector: {selector})")
                            clicked = True
                            break
                    except Exception as sel_e:
                        print(f"   ⚠️ Selector {selector} failed: {sel_e}")
                        continue
                
                if not clicked:
                    # Try JavaScript click as fallback
                    try:
                        js_code = f"""
                        const pageElements = document.querySelectorAll('span.item');
                        for (let el of pageElements) {{
                            if (el.textContent.trim() === '{target_page}' && !el.classList.contains('current')) {{
                                el.click();
                                break;
                            }}
                        }}
                        """
                        await page.evaluate(js_code)
                        print(f"   ✅ Clicked page {target_page} with JavaScript")
                        clicked = True
                    except Exception as js_e:
                        print(f"   ❌ JavaScript click failed: {js_e}")
                
                if clicked:
                    # Wait for the API call for this page
                    print(f"   ⏳ Waiting for API call for page {target_page}...")
                    wait_start = time.time()
                    while target_page not in page_tokens and (time.time() - wait_start) < 10:
                        await asyncio.sleep(0.5)
                    
                    if target_page in page_tokens:
                        print(f"   ✅ Got tokens for page {target_page}")
                    else:
                        print(f"   ⚠️ No tokens captured for page {target_page}")
                else:
                    print(f"   ❌ Failed to click page {target_page}")
                
            except Exception as e:
                print(f"   ❌ Error with page {target_page}: {e}")
                continue
        
        # Add cookies to all captured page tokens
        for page_num in page_tokens:
            page_tokens[page_num]['cookies'] = cookie_dict
        
        print(f"\n📊 Token capture summary:")
        print(f"   Total pages: {len(page_tokens)}")
        for page_num in sorted(page_tokens.keys()):
            tokens = page_tokens[page_num]
            csrf_ok = "✅" if tokens.get('csrf_token') else "❌"
            quote_ok = "✅" if tokens.get('quote_token') else "❌"
            print(f"   Page {page_num}: CSRF {csrf_ok} Quote {quote_ok} (offset={tokens.get('offset')})")
        
        return page_tokens
        
    finally:
        await browser.close()
        await playwright.stop()


async def scrape_with_pagination_tokens(page_tokens):
    """
    Use captured pagination tokens to scrape all pages quickly with HTTP.
    """
    if not page_tokens:
        print("❌ No page tokens to use")
        return []
    
    print(f"\n🚀 Scraping {len(page_tokens)} pages with captured tokens...")
    
    all_stocks = []
    
    async with aiohttp.ClientSession() as session:
        for page_num in sorted(page_tokens.keys()):
            tokens = page_tokens[page_num]
            
            # Build headers from captured tokens
            headers = tokens['headers'].copy()
            
            # Add cookies
            cookie_str = '; '.join([f"{k}={v}" for k, v in tokens['cookies'].items()])
            headers['cookie'] = cookie_str
            
            url = tokens['url']
            offset = tokens['offset']
            
            print(f"📄 Page {page_num} (offset={offset})")
            
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('code') == 0:
                            items = data.get('data', {}).get('list', [])
                            
                            for item in items:
                                symbol = item.get('stockCode', '').upper()
                                if symbol:
                                    all_stocks.append({
                                        'symbol': symbol,
                                        'name': item.get('name', 'N/A'),
                                        'price': item.get('price'),
                                        'change_ratio': item.get('changeRatio'),
                                        'page': page_num
                                    })
                            
                            print(f"   ✅ Got {len(items)} stocks")
                        else:
                            print(f"   ❌ API Error: {data.get('message')}")
                    else:
                        print(f"   ❌ HTTP {response.status}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            await asyncio.sleep(0.2)  # Small delay between requests
    
    return all_stocks


async def main():
    """Run the fixed pagination scraper."""
    import sys
    
    # Parse command line arguments
    pages = 50
    headless = True
    
    for arg in sys.argv[1:]:
        if arg.startswith('pages='):
            pages = int(arg.split('=')[1])
        elif arg == 'visible':
            headless = False
        elif arg == 'help':
            print("Usage: python pagination_token_scraper_fixed.py [options]")
            print("Options:")
            print("  pages=N    Number of pages to scrape (default: 3)")
            print("  visible    Run browser in visible mode")
            print("  help       Show this help")
            return
    
    print("🎯 Fixed Pagination Token Scraper")
    print("=" * 45)
    print("✅ Handles viewport scrolling")
    print("✅ Better element targeting") 
    print("✅ JavaScript fallback clicks")
    print("✅ Longer wait times for API calls")
    print()
    
    start_time = time.time()
    
    # Capture tokens by clicking through pagination
    page_tokens = await capture_pagination_tokens(pages=pages, headless=headless)
    
    if not page_tokens:
        print("❌ Failed to capture any pagination tokens")
        return
    
    # Save tokens
    with open('pagination_tokens.json', 'w') as f:
        json.dump(page_tokens, f, indent=2)
    print(f"💾 Pagination tokens saved to pagination_tokens.json")
    
    # Scrape using captured tokens
    all_stocks = await scrape_with_pagination_tokens(page_tokens)
    
    elapsed = time.time() - start_time
    
    if all_stocks:
        print(f"\n🎉 SUCCESS! Got {len(all_stocks)} stocks in {elapsed:.2f}s")
        
        # Show top 10 stocks
        print(f"\n🏆 Top 10 stocks:")
        for i, stock in enumerate(all_stocks[:10], 1):
            page_info = f" (p{stock.get('page', '?')})" 
            print(f"  {i:2d}. {stock['symbol']:6} - {stock['name'][:30]}{page_info}")
        
        print(f"\n✅ Fixed pagination method working!")
        print(f"   📄 Pages: {len(page_tokens)}")
        print(f"   📊 Stocks: {len(all_stocks)}")
        print(f"   ⏰ Time: {elapsed:.2f}s")
    else:
        print(f"\n❌ No stocks retrieved")


if __name__ == "__main__":
    asyncio.run(main()) 