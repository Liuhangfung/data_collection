import cloudscraper
from bs4 import BeautifulSoup
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# === 讀取 .env ===
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
CALENDAR_TABLE_NAME = "calendar"

# === 驗證 .env 是否讀取成功 ===
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("❌ 無法讀取 .env 中的 SUPABASE_URL 或 SUPABASE_ANON_KEY")
    exit()

print("✅ 已讀取環境變數")
print("🔗 SUPABASE_URL:", SUPABASE_URL)
print("🔑 SUPABASE_ANON_KEY:", SUPABASE_ANON_KEY[:8], "...")
print("🔑 SUPABASE_ANON_KEY length:", len(SUPABASE_ANON_KEY))

# Debug: Print first few characters of the key to verify format
print("🔑 SUPABASE_ANON_KEY format check:", SUPABASE_ANON_KEY.startswith("eyJ"))

headers = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

# === 目標事件
target_events = [
    'Unemployment Rate',
    'ISM Manufacturing PMI',
    'CPI y/y',
    'FOMC Press Conference',
    'Core Retail Sales m/m',
    'Non-Farm Employment Change',
    'Federal Funds Rate',
    'GDP Growth Rate',
    'CPI YoY',
    'PPI YoY',
    'President Trump Speaks',
    'Unemployment Claims'
]
target_events_lower = [e.lower() for e in target_events]

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# === US HOLIDAYS FUNCTIONS ===
def fetch_us_holidays(year):
    """Fetch US public holidays from Nager.Date API"""
    try:
        url = f"https://date.nager.at/api/v3/publicholidays/{year}/US"
        response = requests.get(url)
        
        if response.status_code == 200:
            holidays = response.json()
            print(f"✅ 成功獲取 {year} 年美國公共假期: {len(holidays)} 個")
            return holidays
        else:
            print(f"❌ 獲取假期失敗: HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 獲取假期時發生錯誤: {str(e)}")
        return []

def filter_holidays_by_month(holidays, target_months):
    """Filter holidays to only include those in target months"""
    filtered_holidays = []
    for holiday in holidays:
        holiday_date = datetime.strptime(holiday['date'], '%Y-%m-%d')
        holiday_month = holiday_date.month
        if holiday_month in target_months:
            filtered_holidays.append(holiday)
    return filtered_holidays

def check_holiday_exists(event_name, timestamp):
    """Check if holiday already exists in calendar table"""
    try:
        res = supabase.table(CALENDAR_TABLE_NAME).select("*").eq("event_name", event_name).eq("time", timestamp).execute()
        return len(res.data) > 0, res.data[0] if len(res.data) > 0 else None
    except Exception as e:
        print(f"❌ 查詢假期錯誤: {str(e)}")
        return False, None

def insert_holiday_to_calendar(holiday_data):
    """Insert holiday data to calendar table"""
    try:
        # Check if holiday already exists
        exists, existing_record = check_holiday_exists(holiday_data['event_name'], holiday_data['time'])
        
        if exists:
            print(f"ℹ️ 假期已存在: {holiday_data['event_name']} ({holiday_data['time']})")
            return
            
        # Insert new holiday
        res = supabase.table(CALENDAR_TABLE_NAME).insert(holiday_data).execute()
        if res.data:
            print(f"✅ 已新增假期: {holiday_data['event_name']} ({holiday_data['time']})")
        else:
            print(f"❌ 新增假期失敗: {holiday_data['event_name']} → {res}")
    except Exception as e:
        print(f"❌ Supabase 假期操作錯誤: {str(e)}")
        raise

def process_us_holidays():
    """Process and store US holidays for this month and next month"""
    print("\n🎉 正在處理美國公共假期...\n")
    
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    # Calculate next month
    next_month_date = current_date.replace(day=28) + timedelta(days=4)
    next_month = next_month_date.month
    next_year = next_month_date.year
    
    target_months = [current_month, next_month]
    years_to_check = [current_year]
    if next_year != current_year:
        years_to_check.append(next_year)
    
    print(f"📅 目標月份: {target_months}")
    print(f"📅 檢查年份: {years_to_check}")
    
    all_holidays = []
    for year in years_to_check:
        print(f"📅 獲取 {year} 年假期...")
        holidays = fetch_us_holidays(year)
        all_holidays.extend(holidays)
    
    # Filter holidays to only this month and next month
    filtered_holidays = filter_holidays_by_month(all_holidays, target_months)
    print(f"🎯 篩選後的假期數量: {len(filtered_holidays)}")
    
    for holiday in filtered_holidays:
        try:
            # Parse the holiday date and create timestamp
            holiday_date = datetime.strptime(holiday['date'], '%Y-%m-%d')
            # Set time to 00:00 for holidays
            holiday_timestamp = holiday_date.replace(hour=0, minute=0, second=0).isoformat()
            
            # Create holiday data in calendar table format
            holiday_data = {
                "event_name": f"🎉 {holiday['name']} (US Holiday)",
                "forecast": "",
                "actual": "",
                "previous": "",
                "time": holiday_timestamp
            }
            
            print(f"🎊 假期: {holiday['name']}")
            print(f"📅 日期: {holiday['date']}")
            print(f"🏛️ 類型: {', '.join(holiday.get('types', ['Public']))}")
            print(f"🌍 全國性: {'是' if holiday.get('global', True) else '否'}")
            print()
            
            insert_holiday_to_calendar(holiday_data)
            
        except Exception as e:
            print(f"❌ 處理假期失敗: {holiday.get('name', 'Unknown')} → {str(e)}")

# === ECONOMIC CALENDAR FUNCTIONS ===
def extract_time_from_row(row):
    time_td = row.find("td", class_="calendar__cell calendar__time")
    if time_td:
        for tag in ["span", "div"]:
            node = time_td.find(tag)
            if node:
                return node.text.strip()
        return time_td.text.strip()
    return None

def safe_text(row, cls):
    cell = row.find("td", class_=cls)
    if not cell:
        return ""
    if cell.find("span"):
        return cell.find("span").text.strip()
    elif cell.find("div"):
        return cell.find("div").text.strip()
    else:
        return cell.text.strip()

def check_event_exists(event_name, timestamp):
    try:
        # Query to check if record with same event_name and time exists
        res = supabase.table(CALENDAR_TABLE_NAME).select("*").eq("event_name", event_name).eq("time", timestamp).execute()
        if len(res.data) > 0:
            return True, res.data[0]
        return False, None
    except Exception as e:
        print(f"❌ 查詢錯誤: {str(e)}")
        return False, None

def insert_to_supabase(event_name, forecast, actual, previous, timestamp):
    try:
        # Check if event already exists
        exists, existing_record = check_event_exists(event_name, timestamp)
        
        if exists:
            # Check if any fields are empty in the existing record and need updating
            update_data = {}
            
            if forecast and (not existing_record.get("forecast") or existing_record.get("forecast") == ""):
                update_data["forecast"] = forecast
                
            if actual and (not existing_record.get("actual") or existing_record.get("actual") == ""):
                update_data["actual"] = actual
                
            if previous and (not existing_record.get("previous") or existing_record.get("previous") == ""):
                update_data["previous"] = previous
                
            if update_data:
                # Update the record with new data
                res = supabase.table(CALENDAR_TABLE_NAME).update(update_data).eq("id", existing_record.get("id")).execute()
                print(f"✅ 已更新部分資料: {event_name} @ {timestamp}")
            else:
                print(f"ℹ️ 資料已存在且完整: {event_name} @ {timestamp}")
            return
            
        # If event doesn't exist, insert new record
        data = {
            "event_name": event_name,
            "forecast": forecast,
            "actual": actual,
            "previous": previous,
            "time": timestamp
        }
        # Insert into public.calendar using supabase-py
        res = supabase.table(CALENDAR_TABLE_NAME).insert(data).execute()
        if res.data:
            print(f"✅ 已新增: {event_name} @ {timestamp}")
        else:
            print(f"❌ 新增失敗: {event_name} → {res}")
    except Exception as e:
        print(f"❌ Supabase 操作錯誤: {str(e)}")
        raise

def process_economic_calendar():
    """Process economic calendar data from ForexFactory for this month and next month"""
    print("📅 正在處理美國經濟數據...\n")
    
    # Get current date info
    current_date = datetime.now()
    current_month = current_date.month
    next_month_date = current_date.replace(day=28) + timedelta(days=4)
    next_month = next_month_date.month
    
    print(f"📅 處理月份: {current_month} 月 和 {next_month} 月")
    
    # URLs for this month and next month
    urls = [
        ("this", "https://www.forexfactory.com/calendar?month=this"),
        ("next", "https://www.forexfactory.com/calendar?month=next")
    ]
    
    scraper = cloudscraper.create_scraper()
    
    for month_name, url in urls:
        print(f"\n📊 處理 {month_name} 月的經濟數據...")
        
        try:
            res = scraper.get(url)
            if res.status_code != 200:
                print(f"❌ 抓取 {month_name} 月失敗，HTTP {res.status_code}")
                continue

            soup = BeautifulSoup(res.text, "html.parser")
            rows = soup.find_all("tr")

            current_date_str = "N/A"
            current_time = "00:00am"
            events_found = 0

# === 主邏輯
for i, row in enumerate(rows):
    row_classes = row.get("class", [])

    if "calendar__row" in row_classes and "calendar__row--new-day" in row_classes:
        date_td = row.find("td", class_="calendar__cell calendar__date")
        if date_td:
            raw_date = date_td.get_text(separator=" ", strip=True)
            parts = raw_date.split(" ")
                        current_date_str = " ".join(parts[-2:]) if len(parts) >= 2 else raw_date

    if "calendar__row" not in row_classes:
        continue

    currency_td = row.find("td", class_="calendar__cell calendar__currency")
    if not currency_td or currency_td.text.strip() != "USD":
        continue

    event_span = row.find("span", class_="calendar__event-title")
    if not event_span:
        continue
    event_name = event_span.text.strip()
    if event_name.lower() not in target_events_lower:
        continue

    time_text = extract_time_from_row(row)
    if time_text:
        current_time = time_text
    else:
        for prev in reversed(rows[:i]):
            prev_time = extract_time_from_row(prev)
            if prev_time:
                current_time = prev_time
                break

    forecast = safe_text(row, "calendar__cell calendar__forecast")
    actual = safe_text(row, "calendar__cell calendar__actual")
    previous = safe_text(row, "calendar__cell calendar__previous")

    try:
                    # Determine the year based on the month
                    if month_name == "this":
                        target_year = datetime.now().year
                    else:  # next month
                        if next_month < current_month:  # Next month is in next year
                            target_year = datetime.now().year + 1
                        else:
                            target_year = datetime.now().year
                    
                    full_datetime_str = f"{current_date_str} {current_time}"
        # Add year to the format string
                    full_datetime_obj = datetime.strptime(f"{target_year} {full_datetime_str}", "%Y %b %d %I:%M%p")
        timestamp = full_datetime_obj.isoformat()
    except Exception as e:
        print(f"⚠️ 日期轉換錯誤：{e}")
        timestamp = None

    print(f"🔔 Event: {event_name}")
                print(f"📅 Date: {current_date_str} | 🕒 Time: {current_time}")
    print(f"📊 Forecast: {forecast}")
    print(f"📈 Actual: {actual}")
    print(f"📉 Previous: {previous}")
                print(f"🕓 Timestamp: {timestamp}")
                print(f"📆 Month: {month_name}\n")

    if timestamp:
        try:
            insert_to_supabase(event_name, forecast, actual, previous, timestamp)
                        events_found += 1
        except Exception as e:
            print(f"❌ 新增失敗: {event_name} → {str(e)}")
            
            print(f"✅ {month_name} 月處理完成，找到 {events_found} 個目標事件")
            
        except Exception as e:
            print(f"❌ 處理 {month_name} 月時發生錯誤: {str(e)}")

# === MAIN EXECUTION ===
if __name__ == "__main__":
    print("🚀 開始數據收集程序...\n")
    
    # Process US holidays
    process_us_holidays()
    
    print("\n" + "="*50 + "\n")
    
    # Process economic calendar
    process_economic_calendar()
    
    print("\n✅ 數據收集完成！")
